"""Confronto dos pacotes oficiais "Arquivos transmitidos para totalização — 2º turno de 2026" (Dados Abertos,
cadastrados no CKAN em 28/10/2026) com os arquivos coletados antes, seção a seção, no Portal de Resultados.

Sem baixar o pacote inteiro:
  1. diretório do ZIP (via HTTP Range): CRC32 e tamanho de cada BU × BU do Portal guardado localmente
     (dados/brutos/bu/2026_2t_UF.zip) — todas as seções da UF;
  2. seções selecionadas: baixa só `-vota.vsc` e `-log.jez` do pacote e confere
     SHA-256(vsc) = hash publicado no Portal, SHA-512(log) listado no vsc, e o log do pacote reinterpretado
     = indicadores já extraídos (votos computados, primeiro/último voto, encerramento, urnas).

Uso: python -m observatorio.confronto_pacotes_2t PE
"""
from __future__ import annotations

import hashlib
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import duckdb
import pandas as pd

from . import logs as L
from .arquivos_secao import hash_publicado
from .arquivos_urna import resumir, url_pacote
from .config import BRUTOS, PROCESSADOS, RESULTADOS
from .remotezip import ArquivoHTTP, extrair_de_bloco, fim_membro, listar_membros

SAIDA = RESULTADOS / "2026" / "consolidado_2t"
D_ELEICAO, D_SEGUINTE = "25/10/2026", "26/10/2026"
CAMPOS_LOG = ["n_votos_computados", "n_habilitados", "t_primeiro_voto", "t_ultimo_voto",
              "t_inicio_encerramento_primeiro", "t_encerramento_confirmado_primeiro", "log_ids_urna"]


def diretorio(uf: str):
    a = ArquivoHTTP(url_pacote(2026, 2, uf))
    membros = listar_membros(a)
    cab = {"url": url_pacote(2026, 2, uf), "etag": getattr(a, "etag", ""), "tamanho": getattr(a, "tamanho", "")}
    return a, membros, cab


def comparar_bu(uf: str, membros) -> pd.DataFrame:
    pac = {m.nome[:-len("-bu.dat")]: (m.tamanho, m.crc) for m in membros if m.nome.endswith("-bu.dat")}
    with zipfile.ZipFile(BRUTOS / "bu" / f"2026_2t_{uf}.zip") as z:
        por = {i.filename[:-len(".bu")]: (i.file_size, i.CRC) for i in z.infolist()}
    linhas = []
    for k in sorted(pac.keys() | por.keys()):
        a, b = pac.get(k), por.get(k)
        sit = ("só no pacote" if b is None else "só no Portal" if a is None else
               "idêntico (tamanho e CRC32)" if a == b else "diferente")
        linhas.append({"arquivo": k, "situacao": sit, "tamanho_pacote": a and a[0], "tamanho_portal": b and b[0]})
    return pd.DataFrame(linhas)


def selecionar(uf: str) -> pd.DataFrame:
    """Seções de interesse + amostra de controle (semente fixa)."""
    con = duckdb.connect()
    lg = f"'{PROCESSADOS}/logs/2026_2t_{uf}.parquet'"
    base = con.execute(f"""SELECT arquivo, cd_municipio, nr_zona, nr_secao, {', '.join(CAMPOS_LOG)},
        len(list_filter(votos_s, lambda x: x >= 64800 - 3600 * (CASE WHEN cd_municipio = 30015 THEN -1 ELSE 0 END))) votos_apos_18h_local_brt
      FROM {lg} WHERE tem_log""").df()
    man = con.execute(f"""SELECT arquivo, hash_publicado, versao_adotada FROM
      '{PROCESSADOS}/manifestos_portal/2026_2t_{uf}.parquet'""").df()
    con.close()
    base = base.merge(man, on="arquivo", how="left")
    motivo = pd.Series("", index=base.index)

    def marca(cond, rot):
        motivo[cond] = motivo[cond] + ("; " if True else "") + rot
    marca(base.cd_municipio == 30015, "Fernando de Noronha (fuso UTC−2)")
    pend = pd.read_csv(SAIDA / "divergencias_bu_csv_x_log_horarios_urna.csv")
    pend = pend[(pend.uf == uf) & (pend.classificacao != "Diferença explicada")]
    chaves = set(zip(pend.cd_municipio, pend.nr_zona, pend.nr_secao))
    marca(base.apply(lambda r: (r.cd_municipio, r.nr_zona, r.nr_secao) in chaves, axis=1), "pendência BU × log (E1/E2)")
    marca(base.votos_apos_18h_local_brt > 0, "voto após 18h")
    marca(base.versao_adotada.fillna("").str.contains("Recebido") &
          ~base.versao_adotada.fillna("").str.startswith("25/10"), "versão 'Recebido' em 26–27/10")
    controle = base[motivo == ""].sample(n=min(60, (motivo == "").sum()), random_state=20261029).index
    motivo[controle] = "controle aleatório"
    sel = base[motivo != ""].copy()
    sel["motivo"] = motivo[motivo != ""].str.lstrip("; ")
    return sel


def conferir(arq: ArquivoHTTP, idx: dict, r) -> dict:
    out = {"arquivo": r.arquivo, "cd_municipio": r.cd_municipio, "nr_zona": r.nr_zona, "nr_secao": r.nr_secao,
           "motivo": r.motivo}
    try:
        vsc_m, log_m = idx.get(r.arquivo + "-vota.vsc"), idx.get(r.arquivo + "-log.jez")
        if vsc_m is None:
            out["situacao"] = "sem vsc no pacote"
            return out
        vsc = extrair_de_bloco(arq.faixa(vsc_m.offset_cabecalho, fim_membro(vsc_m)), vsc_m.offset_cabecalho, vsc_m)
        out["vsc_sha256_igual_hash_portal"] = (isinstance(r.hash_publicado, str)
                                               and hashlib.sha256(vsc).digest() == hash_publicado(r.hash_publicado))
        if log_m is None:
            out["situacao"] = "sem log no pacote"
            return out
        log = extrair_de_bloco(arq.faixa(log_m.offset_cabecalho, fim_membro(log_m)), log_m.offset_cabecalho, log_m)
        out["log_sha512_no_vsc"] = hashlib.sha512(log).digest() in vsc
        arquivos = L.extrair_7z(log)
        sel, _ = L.selecionar_arquivos(arquivos, D_ELEICAO, (r.cd_municipio, r.nr_zona, r.nr_secao))
        novo = resumir(L.interpretar(sel, D_ELEICAO, D_SEGUINTE))
        iguais = []
        for c in CAMPOS_LOG:
            a, b = novo.get(c), getattr(r, c)
            ok = (str(a) == str(b)) or (pd.isna(b) and a in (None, ""))
            if not ok:
                out[f"{c}_pacote"], out[f"{c}_anterior"] = a, b
            iguais.append(ok)
        out["log_reinterpretado_igual"] = all(iguais)
        out["log_arquivos_no_pacote"] = "|".join(n for n, _ in arquivos)
        out["situacao"] = "conferido"
    except Exception as e:  # registra o erro e segue
        out["situacao"] = f"erro: {e!r}"[:300]
    return out


def executar(uf: str = "PE") -> dict:
    SAIDA.mkdir(parents=True, exist_ok=True)
    arq, membros, cab = diretorio(uf)
    bu = comparar_bu(uf, membros)
    sel = selecionar(uf)
    idx = {m.nome[:-len(m.nome.rsplit("-", 1)[-1]) - 1] + "-" + m.nome.rsplit("-", 1)[-1]: m for m in membros}
    with ThreadPoolExecutor(4) as ex:
        linhas = list(ex.map(lambda r: conferir(ArquivoHTTP(cab["url"]), idx, r), sel.itertuples()))
    det = pd.DataFrame(linhas)
    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    resumo = {"uf": uf, "consultado_em": agora, "pacote": cab["url"],
              "membros_no_pacote": len(membros), "secoes_bu": len(bu),
              "bu_identicos": int((bu.situacao == "idêntico (tamanho e CRC32)").sum()),
              "bu_diferentes_ou_ausentes": int((bu.situacao != "idêntico (tamanho e CRC32)").sum()),
              "secoes_conferidas_vsc_log": len(det),
              "vsc_igual_hash_portal": int(det.get("vsc_sha256_igual_hash_portal", pd.Series(dtype=bool)).fillna(False).sum()),
              "log_no_vsc": int(det.get("log_sha512_no_vsc", pd.Series(dtype=bool)).fillna(False).sum()),
              "log_reinterpretado_igual": int(det.get("log_reinterpretado_igual", pd.Series(dtype=bool)).fillna(False).sum()),
              "erros": int(det.situacao.str.startswith("erro").sum())}
    bu.to_csv(SAIDA / f"pacote_oficial_2t_{uf}_bu_x_portal.csv", index=False)
    det.to_csv(SAIDA / f"pacote_oficial_2t_{uf}_secoes_conferidas.csv", index=False)
    pd.DataFrame([resumo]).to_csv(SAIDA / f"pacote_oficial_2t_{uf}_resumo.csv", index=False)
    print(resumo)
    return {"resumo": resumo, "bu": bu, "detalhe": det}


if __name__ == "__main__":
    executar(sys.argv[1] if len(sys.argv) > 1 else "PE")
