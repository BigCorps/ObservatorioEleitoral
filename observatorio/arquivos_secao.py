"""Coleta seção a seção dos arquivos de urna no Portal de Resultados do TSE.

Usado quando os pacotes consolidados ("arquivos transmitidos para totalização")
ainda não foram publicados nos Dados Abertos — caso do 2º turno de 2026.

Fonte oficial (verificada em 27/10/2026):
  https://resultados.tse.jus.br/oficial/ele{ANO}/arquivo-urna/{PLEITO}/dados/{uf}/{mun5}/{zona4}/{sec4}/
      p00{PLEITO}-{uf}-m{mun5}-z{zona4}-s{sec4}-aux.json      (índice da seção)
      {hash}/{arquivo}                                         (arquivos de cada versão)
O pleito 3221 (25/10/2026) contém a eleição 6258 "Eleição Ordinária Federal - 2026 2º
Turno" (Presidente), conforme https://resultados.tse.jus.br/oficial/comum/config/ele-c.json.

Integridade (cadeia verificada para cada seção):
  1. `hash` do aux.json = SHA-256 do arquivo `-vota.vsc` (hex de texto base64 com "/" → "-");
  2. `-vota.vsc` (ASN.1, assinatura.asn1 v2) lista o SHA-512 de `-bu.dat` e `-log.jez`,
     assinados por software (CEPESC) e pelo hardware da urna (EdDSA). As assinaturas
     criptográficas em si não são verificadas aqui; os hashes sim.

Saídas no mesmo formato de `arquivos_urna.py` (logs/{ano}_{t}t_{UF}.parquet, bu/*.zip,
manifestos/cobertura_arquivos_urna.csv). Manifesto por seção (HTTP, versões, hashes,
integridade) completo em dados/processados/manifestos_portal/ e, no Git, só as exceções em
manifestos/secoes_portal/{ano}_{t}t_{UF}_excecoes.csv.
"""
from __future__ import annotations

import base64
import csv
import hashlib
import json
import time
import zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from functools import lru_cache

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
import requests

from . import logs as L
from .arquivos_urna import DATAS_ELEICAO, _registrar_cobertura, resumir
from .config import BRUTOS, MANIFESTOS, PROCESSADOS, RAIZ

PLEITOS = {(2026, 1): 3220, (2026, 2): 3221}
BASE = "https://resultados.tse.jus.br/oficial/ele{ano}/arquivo-urna/{pleito}/dados"
_sess = None


def _s() -> requests.Session:
    global _sess
    if _sess is None:
        _sess = requests.Session()
        _sess.headers["User-Agent"] = "ObservatorioEleitoral/0.1 (pesquisa; github.com/BigCorps/ObservatorioEleitoral)"
        _sess.mount("https://", requests.adapters.HTTPAdapter(pool_connections=4, pool_maxsize=4))
    return _sess


def _get(url: str, tentativas: int = 6):
    """GET com novas tentativas, respeitando 429/Retry-After. Retorna (status, bytes|None, headers)."""
    ult = None
    for t in range(tentativas):
        try:
            r = _s().get(url, timeout=60)
            if r.status_code == 429 or r.status_code >= 500:
                espera = float(r.headers.get("Retry-After", 2 ** (t + 1)))
                ult = f"HTTP {r.status_code}"
                time.sleep(min(espera, 60))
                continue
            return r.status_code, (r.content if r.status_code == 200 else None), r.headers
        except requests.RequestException as e:
            ult = repr(e)[:120]
            time.sleep(min(2 ** (t + 1), 30))
    return f"ERRO {ult}", None, {}


@lru_cache(maxsize=1)
def _asn1_assinatura():
    import asn1tools
    return asn1tools.compile_files([str(RAIZ / "especificacoes" / "asn1_2026" / "assinatura.asn1")], codec="ber")


def _tl(b: bytes, o: int):
    t = b[o]; o += 1; n = b[o]; o += 1
    if n & 0x80:
        k = n & 0x7F; n = int.from_bytes(b[o:o + k], "big"); o += k
    return t, n, o


def hashes_vsc(vsc: bytes) -> tuple[dict, str]:
    """SHA-512 por arquivo (assinatura de software e de hardware) e modelo do equipamento.

    Estrutura observada em 2026: SEQUENCE { EntidadeAssinatura(SW), EntidadeAssinatura(HW),
    SEQUENCE { modelo ENUMERATED, ... } } — ordem diferente da declarada na especificação v2."""
    c = _asn1_assinatura()
    _, _, o = _tl(vsc, 0)
    saida, modelo = {}, ""
    for k in range(3):
        ini = o
        _, n, o2 = _tl(vsc, o)
        o = o2 + n
        if k < 2:
            e = c.decode("EntidadeAssinatura", vsc[ini:o])
            a = c.decode("Assinatura", e["conteudoAutoAssinado"])
            for f in a["arquivosAssinados"]:
                saida.setdefault(f["nomeArquivo"], set()).add(bytes(f["assinatura"]["hash"]))
        else:
            corpo = vsc[o2:o]
            if len(corpo) >= 3 and corpo[0] == 0x0A:
                modelo = str(corpo[2])
    return saida, modelo


def hash_publicado(texto_hex: str) -> bytes:
    """`hash` do aux.json: hex de um texto base64 em que "/" vira "-" (uso em caminho de URL)."""
    return base64.b64decode(bytes.fromhex(texto_hex).decode().replace("-", "/"))


def _processar(base: str, uf: str, mun: int, zona: int, sec: int, d_eleicao: str, d_seguinte: str):
    """Executado em processo filho. Retorna (linha, bu_bytes, manifesto)."""
    caminho = f"{base}/{uf}/{mun:05d}/{zona:04d}/{sec:04d}"
    aux_url = f"{caminho}/p00{base.rsplit('/', 2)[-2]}-{uf}-m{mun:05d}-z{zona:04d}-s{sec:04d}-aux.json"
    man = {"aux_url": aux_url}
    st, corpo, h = _get(aux_url)
    man["aux_http"] = st
    man["aux_last_modified"] = h.get("last-modified", "") if h else ""
    if corpo is None:
        return None, None, man
    aux = json.loads(corpo)
    versoes = aux.get("hashes", []) or []
    man.update(aux_st=aux.get("st", ""), n_versoes=len(versoes),
               versoes="; ".join(f"{v.get('dr','')} {v.get('hr','')} {v.get('st','')}" for v in versoes))
    if not versoes:
        return None, None, man
    # versão adotada: a última com situação "Totalizado"; na falta, a última publicada
    tot = [v for v in versoes if v.get("st", "").lower().startswith("totaliz")]
    v = (tot or versoes)[-1]
    arqs = {a["tp"]: a["nm"] for a in v.get("arq", [])}
    man.update(versao_adotada=f"{v.get('dr','')} {v.get('hr','')} {v.get('st','')}", hash_publicado=v["hash"],
               arquivos=",".join(sorted(arqs)))
    conteudo = {}
    tipos = [tp for tp in ("vota", "bu", "busa", "log") if tp in arqs]
    # os arquivos da versão são independentes: baixados em paralelo para reduzir a latência
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(len(tipos) or 1) as tx:
        res = list(tx.map(lambda tp: (tp, _get(f"{caminho}/{v['hash']}/{arqs[tp]}")), tipos))
    for tp, (st, b, _) in res:
        man[f"http_{tp}"] = st
        if b is not None:
            conteudo[tp] = b
    # cadeia de integridade
    try:
        esperado = hash_publicado(v["hash"])
        man["vsc_confere_hash_publicado"] = ("vota" in conteudo and hashlib.sha256(conteudo["vota"]).digest() == esperado)
    except Exception as e:  # noqa: BLE001
        man["vsc_confere_hash_publicado"] = f"erro: {e!r}"[:100]
    modelo = ""
    if "vota" in conteudo:
        # verificação rápida: o SHA-512 exato de cada arquivo deve constar do .vsc assinado
        # (equivalente à decodificação completa de `hashes_vsc`, validada em amostra; uma
        # coincidência acidental de 64 bytes é desprezível). Modelo: últimos bytes do .vsc.
        vsc = conteudo["vota"]
        for tp in ("bu", "busa", "log"):
            if tp in conteudo:
                man[f"{tp}_confere_vsc"] = hashlib.sha512(conteudo[tp]).digest() in vsc
        if len(vsc) > 8 and vsc[-6] == 0x0A:
            modelo = str(vsc[-4])
    man["modelo_vsc"] = modelo
    linha = {"tem_bu": "bu" in conteudo or "busa" in conteudo, "tem_log": "log" in conteudo,
             "bu_tipo_arquivo_origem": "bu" if "bu" in conteudo else ("busa" if "busa" in conteudo else ""),
             "extensoes_presentes": "|".join(sorted(arqs)), "portal_n_versoes": len(versoes)}
    if "log" in conteudo:
        try:
            arquivos = L.extrair_7z(conteudo["log"])
            sel, outros = L.selecionar_arquivos(arquivos, d_eleicao, (mun, zona, sec))
            linha.update(resumir(L.interpretar(sel, d_eleicao, d_seguinte)))
            linha["log_n_arquivos_total"] = len(arquivos)
            linha["log_arquivos_outras_secoes"] = "; ".join(
                f"{n}={'/'.join('-'.join(map(str, i)) for i in ids)}" for n, ids in outros)
            linha["log_n_arquivos_outras_secoes"] = len(outros)
            linha["erro_log"] = ""
        except Exception as e:  # noqa: BLE001
            linha["erro_log"] = repr(e)[:300]
    return linha, conteudo.get("bu", conteudo.get("busa")), man


def secoes_oficiais(ano: int, turno: int, uf: str) -> list[tuple[int, int, int]]:
    """Seções instaladas segundo o Detalhe da apuração por seção (fonte oficial)."""
    f = PROCESSADOS / "tabelas" / f"detalhe_secao_{ano}.parquet"
    return [tuple(r) for r in duckdb.sql(f"""
        SELECT DISTINCT CAST(CD_MUNICIPIO AS INT), CAST(NR_ZONA AS INT), CAST(NR_SECAO AS INT)
        FROM '{f}' WHERE NR_TURNO = '{turno}' AND SG_UF = '{uf}' AND ST_SECAO_INSTALADA NOT IN ('Não', 'N')
        ORDER BY 1, 2, 3""").fetchall()]


def processar(ano: int, turno: int, uf: str, workers: int = 24, limite: int | None = None,
              secoes: list | None = None) -> dict:
    pleito = PLEITOS[(ano, turno)]
    base = BASE.format(ano=ano, pleito=pleito)
    d = DATAS_ELEICAO[(ano, turno)]
    d_eleicao, d_seguinte = d.strftime("%d/%m/%Y"), (d + timedelta(days=1)).strftime("%d/%m/%Y")
    lista = secoes or secoes_oficiais(ano, turno, uf)
    if limite:
        lista = lista[:limite]
    inicio = time.time()
    sufixo = "" if not (limite or secoes) else "_amostra"
    saida = PROCESSADOS / "logs" / f"{ano}_{turno}t_{uf}{sufixo}.parquet"
    saida_bu = BRUTOS / "bu" / f"{ano}_{turno}t_{uf}{sufixo}.zip"
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida_bu.parent.mkdir(parents=True, exist_ok=True)
    linhas, manif = [], []
    zbu = zipfile.ZipFile(saida_bu, "w", zipfile.ZIP_DEFLATED, compresslevel=6)
    with ProcessPoolExecutor(workers) as ex:
        futs = {ex.submit(_processar, base, uf.lower(), m, z, s, d_eleicao, d_seguinte): (m, z, s) for m, z, s in lista}
        for f in as_completed(futs):
            m, z, s = futs[f]
            stem = f"o{pleito:05d}{uf.lower()}{m:05d}{z:04d}{s:04d}"
            try:
                linha, bu, man = f.result()
            except Exception as e:  # noqa: BLE001
                linha, bu, man = None, None, {"erro": repr(e)[:200]}
            chave = {"ano": ano, "turno": turno, "uf": uf, "arquivo": stem, "cd_pleito": pleito,
                     "cd_municipio": m, "nr_zona": z, "nr_secao": s}
            manif.append({**chave, **man})
            if linha is not None:
                linhas.append({**chave, **linha})
            if bu is not None:
                zbu.writestr(stem + ".bu", bu)
    zbu.close()
    if linhas:
        chaves = list(dict.fromkeys(k for l in linhas for k in l))
        pq.write_table(pa.Table.from_pylist([{k: l.get(k) for k in chaves} for l in linhas]), saida, compression="zstd")
    # manifesto por seção: completo em Parquet (fora do Git) e exceções em CSV (no Git)
    pm = PROCESSADOS / "manifestos_portal" / f"{ano}_{turno}t_{uf}{sufixo}.parquet"
    pm.parent.mkdir(parents=True, exist_ok=True)
    campos = list(dict.fromkeys(k for l in manif for k in l))
    manif.sort(key=lambda x: (x["cd_municipio"], x["nr_zona"], x["nr_secao"]))
    pq.write_table(pa.Table.from_pylist([{k: (str(r.get(k)) if r.get(k) is not None else None) for k in campos}
                                         for r in manif]), pm, compression="zstd")
    excecoes = [r for r in manif if r.get("aux_http") != 200 or (r.get("n_versoes") or 0) != 1
                or r.get("vsc_confere_hash_publicado") is not True or r.get("log_confere_vsc") is not True
                or r.get("bu_confere_vsc") is not True]
    pe = MANIFESTOS / "secoes_portal" / f"{ano}_{turno}t_{uf}{sufixo}_excecoes.csv"
    pe.parent.mkdir(parents=True, exist_ok=True)
    with pe.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        w.writerows(excecoes)
    def conta(cond):
        return sum(1 for r in manif if cond(r))
    cob = {
        "ano": ano, "turno": turno, "uf": uf, "url": base + f"/{uf.lower()}/ (por seção, aux.json)",
        "etag": "", "last_modified": max((r.get("aux_last_modified", "") for r in manif), default=""),
        "tamanho_pacote_bytes": "", "membros_no_pacote": "", "secoes_no_pacote": len(lista),
        "secoes_incompletas": conta(lambda r: r.get("aux_http") == 200 and "log" not in r.get("arquivos", "")),
        "exemplos_incompletas": "", "membros_inesperados": "", "exemplos_inesperados": "",
        "secoes_processadas": len(linhas), "secoes_com_falha": conta(lambda r: r.get("aux_http") not in (200, 404)),
        "secoes_sem_log": len(lista) - sum(1 for l in linhas if l.get("tem_log")),
        "secoes_erro_log": sum(1 for l in linhas if l.get("erro_log")),
        "secoes_sem_bu": len(lista) - sum(1 for l in linhas if l.get("tem_bu")),
        "limite_aplicado": limite or "",
        "processado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "duracao_s": round(time.time() - inicio),
        "fonte": "Portal de Resultados (seção a seção)",
        "aux_404": conta(lambda r: r.get("aux_http") == 404),
        "secoes_varias_versoes": conta(lambda r: (r.get("n_versoes") or 0) > 1),
        "integridade_vsc_ok": conta(lambda r: r.get("vsc_confere_hash_publicado") is True),
        "integridade_log_ok": conta(lambda r: r.get("log_confere_vsc") is True),
        "integridade_bu_ok": conta(lambda r: r.get("bu_confere_vsc") is True or r.get("busa_confere_vsc") is True),
    }
    if not (limite or secoes):
        _registrar_cobertura(cob)
    return cob
