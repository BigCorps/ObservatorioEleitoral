"""Processamento dos pacotes "arquivos transmitidos para totalização" por UF e turno.

Para cada seção: baixa por HTTP Range somente os membros .bu e .logjez (o .imgbu,
que fica entre eles no pacote, vem junto e é descartado), confere o CRC-32,
interpreta o log e guarda o .bu original (binário ASN.1) num ZIP local para
decodificação e reprocessamento sem novo download.

Saídas:
- dados/processados/logs/{ano}_{turno}t_{uf}.parquet  (uma linha por seção)
- dados/brutos/bu/{ano}_{turno}t_{uf}.zip            (arquivos .bu originais)
- manifestos/cobertura_arquivos_urna.csv             (cobertura e falhas)
"""
from __future__ import annotations

import csv
import re
import threading
import time
import traceback
import zipfile
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone

import pyarrow as pa
import pyarrow.parquet as pq
import requests

from . import logs as L
from .config import BRUTOS, MANIFESTOS, PROCESSADOS
from .remotezip import ArquivoHTTP, Membro, extrair_de_bloco, fim_membro, listar_membros

DATAS_ELEICAO = {
    (2022, 1): date(2022, 10, 2), (2022, 2): date(2022, 10, 30),
    (2026, 1): date(2026, 10, 4), (2026, 2): date(2026, 10, 25),
}
EXTENSOES = ("bu", "imgbu", "logjez", "rdv", "vscmr")
RE_NOME = re.compile(r"^o(\d{5})-(\d{5})(\d{4})(\d{4})\.(\w+)$")
COBERTURA = MANIFESTOS / "cobertura_arquivos_urna.csv"
_trava = threading.Lock()

_sess = None


def _sessao() -> requests.Session:
    global _sess
    if _sess is None:
        _sess = requests.Session()
        ad = requests.adapters.HTTPAdapter(pool_connections=4, pool_maxsize=4)
        _sess.mount("https://", ad)
    return _sess


def _faixa(url: str, ini: int, fim: int) -> bytes:
    ult = None
    for t in range(6):
        try:
            r = _sessao().get(url, headers={"Range": f"bytes={ini}-{fim - 1}"}, timeout=120)
            if r.status_code != 206:
                raise RuntimeError(f"HTTP {r.status_code}")
            if len(r.content) != fim - ini:
                raise RuntimeError("faixa incompleta")
            return r.content
        except Exception as e:
            ult = e
            time.sleep(min(2 ** (t + 1), 30))
    raise RuntimeError(f"faixa {ini}-{fim}: {ult!r}")


def _primeiro(v):
    return min(v) if v else None


def _ultimo(v):
    return max(v) if v else None


def resumir(r: L.ResumoLog) -> dict:
    ev = r.eventos
    d = {
        "log_arquivos": "|".join(r.arquivos), "log_n_arquivos": len(r.arquivos),
        "log_linhas_dia": r.linhas_dia, "log_linhas_dia_seguinte": r.linhas_dia_seguinte,
        "log_linhas_duplicadas": r.linhas_duplicadas, "log_linhas_malformadas": r.linhas_malformadas,
        "log_ids_urna": "|".join(sorted(r.ids_urna)), "log_n_ids_urna": len(r.ids_urna),
        "log_modelos": "|".join(sorted(r.modelos)), "log_versoes": "|".join(sorted(r.versoes)),
        "log_retrocessos_relogio": r.retrocessos_relogio, "log_maior_retrocesso_s": r.maior_retrocesso_s,
        "log_n_erro": r.n_erro, "log_n_alerta": r.n_alerta,
        "n_habilitados": len(r.hab_s), "n_votos_computados": len(r.votos_s),
        "hab_biometrica": sum(1 for m in r.hab_mod if m == L.HAB_BIOMETRICA),
        "hab_sem_biometria": sum(1 for m in r.hab_mod if m == L.HAB_SEM_BIOMETRIA),
        "hab_manual_apos_falha": sum(1 for m in r.hab_mod if m == L.HAB_MANUAL_APOS_FALHA),
        "hab_indeterminada": sum(1 for m in r.hab_mod if m == L.HAB_INDETERMINADA),
        "tipos_hab_outros": "|".join(f"{k}={v}" for k, v in r.tipos_hab_outros.items()),
        "t_primeira_hab": _primeiro(r.hab_s), "t_ultima_hab": _ultimo(r.hab_s),
        "t_primeiro_voto": _primeiro(r.votos_s), "t_ultimo_voto": _ultimo(r.votos_s),
        "votos_s": sorted(r.votos_s), "hab_s": r.hab_s, "hab_mod": r.hab_mod,
        "dur_voto": r.dur_voto, "dur_voto_mod": r.dur_voto_mod,
    }
    for ch in ("pronta", "ligada", "zeresima", "inicio_encerramento", "encerramento_confirmado",
               "gera_bu", "arquivo_bu", "imprime_bu", "desligada", "votacao_suspensa",
               "tentativa_encerramento_antecipado", "modo_contingencia", "contingencia_ok",
               "suspenso", "parcial_suspenso", "suspenso_sem_voto", "ja_votou",
               "habilitacao_cancelada", "voto_presidente", "nulo_suspensao_presidente", "titulo"):
        v = ev.get(ch, [])
        d[f"n_{ch}"] = len(v)
        if ch in ("pronta", "ligada", "zeresima", "inicio_encerramento", "encerramento_confirmado",
                  "gera_bu", "arquivo_bu", "imprime_bu", "desligada", "votacao_suspensa",
                  "tentativa_encerramento_antecipado", "modo_contingencia"):
            d[f"t_{ch}_primeiro"] = _primeiro(v)
            d[f"t_{ch}_ultimo"] = _ultimo(v)
    return d


def _processar_secao(url: str, stem: str, membros: list[Membro], d_eleicao: str, d_seguinte: str):
    """Executado em processo filho. Retorna (linha, bytes_do_bu, erro)."""
    try:
        if not membros:  # seção sem .bu e sem .logjez no pacote: registrada como ausência
            return stem, {"tem_bu": False, "tem_log": False}, None, ""
        ini = min(m.offset_cabecalho for m in membros)
        fim = max(fim_membro(m) for m in membros)
        bloco = _faixa(url, ini, fim)
        conteudos = {m.nome.rsplit(".", 1)[1]: extrair_de_bloco(bloco, ini, m) for m in membros}
        linha = {"tem_bu": "bu" in conteudos, "tem_log": "logjez" in conteudos}
        if "logjez" in conteudos:
            try:
                arqs = L.extrair_7z(conteudos["logjez"])
                linha.update(resumir(L.interpretar(arqs, d_eleicao, d_seguinte)))
                linha["erro_log"] = ""
            except Exception as e:
                linha["erro_log"] = repr(e)[:300]
        return stem, linha, conteudos.get("bu"), ""
    except Exception as e:
        return stem, None, None, repr(e)[:300] + " " + traceback.format_exc(limit=2)[-300:]


def _registrar_cobertura(linha: dict) -> None:
    campos = list(linha.keys())
    with _trava:
        linhas = []
        if COBERTURA.exists():
            with COBERTURA.open(encoding="utf-8") as f:
                linhas = [l for l in csv.DictReader(f)
                          if not (l["ano"] == str(linha["ano"]) and l["turno"] == str(linha["turno"])
                                  and l["uf"] == linha["uf"])]
        linhas.append(linha)
        for l in linhas:
            for k in l:
                if k not in campos:
                    campos.append(k)
        with COBERTURA.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=campos)
            w.writeheader()
            for l in sorted(linhas, key=lambda x: (str(x["ano"]), str(x["turno"]), x["uf"])):
                w.writerow(l)


def url_pacote(ano: int, turno: int, uf: str) -> str:
    return (f"https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes{ano}/arqurnatot/"
            f"bu_imgbu_logjez_rdv_vscmr_{ano}_{turno}t_{uf}.zip")


def processar(ano: int, turno: int, uf: str, workers: int = 8, limite: int | None = None,
              progresso: bool = True) -> dict:
    url = url_pacote(ano, turno, uf)
    saida = PROCESSADOS / "logs" / f"{ano}_{turno}t_{uf}.parquet"
    saida_bu = BRUTOS / "bu" / f"{ano}_{turno}t_{uf}.zip"
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida_bu.parent.mkdir(parents=True, exist_ok=True)
    d = DATAS_ELEICAO[(ano, turno)]
    d_eleicao, d_seguinte = d.strftime("%d/%m/%Y"), (d + timedelta(days=1)).strftime("%d/%m/%Y")
    inicio = time.time()
    arq = ArquivoHTTP(url)
    membros = listar_membros(arq)
    por_secao: dict[str, dict[str, Membro]] = defaultdict(dict)
    inesperados = []
    for m in membros:
        mm = RE_NOME.match(m.nome)
        if not mm or mm.group(5) not in EXTENSOES:
            inesperados.append(m.nome)
            continue
        stem = m.nome.rsplit(".", 1)[0]
        if mm.group(5) in por_secao[stem]:
            inesperados.append("DUPLICADO:" + m.nome)
        por_secao[stem][mm.group(5)] = m
    incompletas = {s: sorted(set(EXTENSOES) - set(v)) for s, v in por_secao.items() if set(v) != set(EXTENSOES)}
    stems = sorted(por_secao)
    if limite:
        stems = stems[:limite]
    linhas, falhas = [], []
    zbu = zipfile.ZipFile(saida_bu, "w", zipfile.ZIP_DEFLATED, compresslevel=6)
    with ProcessPoolExecutor(workers) as ex:
        futs = []
        for s in stems:
            ms = [por_secao[s][e] for e in ("bu", "logjez") if e in por_secao[s]]
            futs.append(ex.submit(_processar_secao, url, s, ms, d_eleicao, d_seguinte))
        for i, f in enumerate(as_completed(futs), 1):
            stem, linha, bu, erro = f.result()
            mm = RE_NOME.match(stem + ".bu")
            chave = {"ano": ano, "turno": turno, "uf": uf, "arquivo": stem,
                     "cd_pleito": int(mm.group(1)), "cd_municipio": int(mm.group(2)),
                     "nr_zona": int(mm.group(3)), "nr_secao": int(mm.group(4))}
            if erro:
                falhas.append({**chave, "erro": erro})
                continue
            linha["extensoes_presentes"] = "|".join(sorted(por_secao[stem]))
            linhas.append({**chave, **linha})
            if bu is not None:
                zbu.writestr(stem + ".bu", bu)
            if progresso and i % 2000 == 0:
                print(f"  {uf} {turno}t: {i}/{len(stems)} seções ({time.time() - inicio:.0f}s)", flush=True)
    zbu.close()
    if linhas:
        # schema pela união das chaves (from_pylist usa só a 1ª linha: perderia colunas)
        chaves = list(dict.fromkeys(k for l in linhas for k in l))
        tabela = pa.Table.from_pylist([{k: l.get(k) for k in chaves} for l in linhas])
        pq.write_table(tabela, saida, compression="zstd")
    cob = {
        "ano": ano, "turno": turno, "uf": uf, "url": url, "etag": arq.etag,
        "last_modified": arq.last_modified, "tamanho_pacote_bytes": arq.tamanho,
        "membros_no_pacote": len(membros), "secoes_no_pacote": len(por_secao),
        "secoes_incompletas": len(incompletas),
        "exemplos_incompletas": "; ".join(f"{k}:{'/'.join(v)}" for k, v in list(incompletas.items())[:5]),
        "membros_inesperados": len(inesperados), "exemplos_inesperados": "; ".join(inesperados[:5]),
        "secoes_processadas": len(linhas), "secoes_com_falha": len(falhas),
        "secoes_sem_log": sum(1 for l in linhas if not l.get("tem_log")),
        "secoes_sem_bu": sum(1 for l in linhas if not l.get("tem_bu")),
        "secoes_erro_log": sum(1 for l in linhas if l.get("erro_log")),
        "limite_aplicado": limite or "",
        "processado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "duracao_s": round(time.time() - inicio),
    }
    if falhas:
        fpath = MANIFESTOS / "falhas" / f"arquivos_urna_{ano}_{turno}t_{uf}.csv"
        fpath.parent.mkdir(parents=True, exist_ok=True)
        with fpath.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(falhas[0].keys()))
            w.writeheader()
            w.writerows(falhas)
    if not limite:
        _registrar_cobertura(cob)
    return cob
