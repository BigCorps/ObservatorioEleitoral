"""Cronologia de publicação dos arquivos oficiais (2022 × 2026), por tipo de arquivo e turno.

Para cada tipo/turno registra, separadamente:
  data da eleição; data de geração no nome do arquivo (quando existe); criação do recurso no CKAN;
  Last-Modified do servidor (versão atual); primeira observação no nosso sistema (snapshots do
  inventário preservados) e data das nossas coletas.
O Last-Modified indica a versão vigente, não a primeira disponibilidade: um arquivo republicado
recebe nova data. Sem cópia da versão anterior não se afirma se houve ou não alteração de conteúdo.
"""
from __future__ import annotations

import re
from email.utils import parsedate_to_datetime

import pandas as pd

from .config import MANIFESTOS, RESULTADOS

ELEICOES = {(2022, "1"): "2022-10-02", (2022, "2"): "2022-10-30", (2026, "1"): "2026-10-04", (2026, "2"): "2026-10-25"}
TIPOS = ["bu_csv", "arquivos_urna", "detalhe_votacao_secao", "votacao_secao", "historico_totalizacao_presidente",
         "relatorio_totalizacao"]
SNAPSHOTS = {  # inventários preservados: momento da consulta → arquivo
    "2026-10-26T23:25Z": MANIFESTOS / "historico" / "antes_consolidado_2026-10-29" / "inventario_fontes.csv",
}


def _lm(s):
    try:
        return parsedate_to_datetime(s).astimezone(tz=None).strftime("%Y-%m-%d %H:%M UTC") if isinstance(s, str) and s else None
    except Exception:
        return None


def _geracao(url: str):
    m = re.search(r"_(\d{2})(\d{2})(\d{4})(\d{2})(\d{2})\.zip$", url)
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)} {m.group(4)}:{m.group(5)}" if m else None


def _portal() -> dict | None:
    """Arquivos de urna do 2º turno de 2026 no Portal de Resultados (fonte da nossa coleta)."""
    import duckdb
    from .config import PROCESSADOS
    arqs = list((PROCESSADOS / "manifestos_portal").glob("2026_2t_*.parquet"))
    if not arqs:
        return None
    r = duckdb.sql(f"""SELECT count(*),
        min(strptime(split_part(versao_adotada, ' ', 1) || ' ' || split_part(versao_adotada, ' ', 2), '%d/%m/%Y %H:%M:%S')),
        max(strptime(split_part(versao_adotada, ' ', 1) || ' ' || split_part(versao_adotada, ' ', 2), '%d/%m/%Y %H:%M:%S')),
        min(strptime(aux_last_modified, '%a, %d %b %Y %H:%M:%S GMT')), max(strptime(aux_last_modified, '%a, %d %b %Y %H:%M:%S GMT'))
      FROM read_parquet({[str(a) for a in arqs]}, union_by_name=true) WHERE versao_adotada IS NOT NULL""").fetchall()[0]
    cob = pd.read_csv(MANIFESTOS / "cobertura_arquivos_urna.csv", dtype=str)
    cob = cob[(cob.ano == "2026") & (cob.turno == "2")]
    return {"ano": 2026, "tipo": "arquivos_urna_portal_resultados", "turno": "2", "arquivos": int(r[0]),
            "data_eleicao": "2026-10-25",
            "observacao": (f"Portal de Resultados (por seção): versão totalizada adotada com data entre {r[1]} e {r[2]} "
                           f"(hora do portal); aux.json Last-Modified entre {r[3]} e {r[4]} UTC; "
                           f"nossa coleta entre {cob.processado_em.min()} e {cob.processado_em.max()}"),
            "nossa_primeira_coleta": cob.processado_em.min()}


def executar() -> pd.DataFrame:
    inv = pd.read_csv(MANIFESTOS / "inventario_fontes.csv", dtype=str)
    inv = inv[inv.tipo.isin(TIPOS)].copy()
    inv["lm"] = pd.to_datetime(inv.last_modified, format="%a, %d %b %Y %H:%M:%S GMT", errors="coerce", utc=True)
    inv["ckan"] = pd.to_datetime(inv.ckan_created, errors="coerce", utc=True)
    inv["geracao_nome"] = inv.url.map(_geracao)
    dl = pd.read_csv(MANIFESTOS / "downloads.csv", dtype=str)[["url", "baixado_em"]]
    inv = inv.merge(dl.groupby("url").baixado_em.min().reset_index(), on="url", how="left")
    snaps = {k: set(pd.read_csv(v, dtype=str).url) for k, v in SNAPSHOTS.items() if v.exists()}
    linhas = []
    for (ano, tipo, turno), g in inv.groupby(["ano", "tipo", inv.turno.fillna("")]):
        ano = int(ano)
        eleicao = ELEICOES.get((ano, turno)) or (f"{ano} (arquivo com os dois turnos)" if turno == "" else None)
        vistos = {k: int(g.url.isin(s).sum()) for k, s in snaps.items()}
        linhas.append({
            "ano": ano, "tipo": tipo, "turno": turno or "ambos", "arquivos": len(g), "data_eleicao": eleicao,
            "geracao_no_nome_min": g.geracao_nome.dropna().min() if g.geracao_nome.notna().any() else None,
            "geracao_no_nome_max": g.geracao_nome.dropna().max() if g.geracao_nome.notna().any() else None,
            "ckan_criado_min": g.ckan.min(), "ckan_criado_max": g.ckan.max(),
            "fora_do_ckan": int(g.ckan.isna().sum()),
            "last_modified_min": g.lm.min(), "last_modified_max": g.lm.max(),
            **{f"presentes_no_inventario_{k}": v for k, v in vistos.items()},
            "nossa_primeira_coleta": g.baixado_em.min(),
        })
    if not ((inv.ano == "2026") & (inv.tipo == "arquivos_urna") & (inv.turno == "2")).any():
        linhas.append({"ano": 2026, "tipo": "arquivos_urna", "turno": "2", "arquivos": 0, "data_eleicao": "2026-10-25",
                       "observacao": "não publicado nos Dados Abertos até a consulta de "
                                     + inv.consultado_em.max()})
    portal = _portal()
    if portal:
        linhas.append(portal)
    d = pd.DataFrame(linhas)
    for c in ("ckan_criado_min", "ckan_criado_max", "last_modified_min", "last_modified_max"):
        d[c] = d[c].dt.strftime("%Y-%m-%d %H:%M UTC")
    for c, ref in (("dias_eleicao_ate_ckan", "ckan_criado_min"), ("dias_eleicao_ate_last_modified", "last_modified_min")):
        d[c] = [round((pd.Timestamp(r[ref][:16], tz="UTC") - pd.Timestamp(r.data_eleicao, tz="UTC")).total_seconds() / 86400, 1)
                if isinstance(r[ref], str) and r.data_eleicao and r.data_eleicao[:4].isdigit() and len(r.data_eleicao) == 10 else None
                for _, r in d.iterrows()]
    d = d.sort_values(["tipo", "turno", "ano"])
    d.to_csv(RESULTADOS / "comparativo" / "cronologia_publicacao.csv", index=False)
    return d
