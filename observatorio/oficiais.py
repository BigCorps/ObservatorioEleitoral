"""Conversão das tabelas oficiais de resultados/eleitorado do TSE para Parquet.

Cada função lê o ZIP baixado (ver manifestos/downloads.csv) e grava em
dados/processados/tabelas/. Os filtros mantêm apenas o cargo Presidente.
"""
from __future__ import annotations

import duckdb

from .catalogo import carregar_inventario
from .config import UFS_COM_EXTERIOR
from .download import caminho_local
from .tabelas import csv_zip_para_parquet, parquet


def _zip(tipo: str, ano: int, uf: str | None = None):
    for l in carregar_inventario():
        if l["tipo"] == tipo and l["ano"] == str(ano) and (uf is None or l["uf"] == uf):
            return caminho_local(l["url"])
    raise FileNotFoundError(f"{tipo} {ano} {uf}")


def detalhe_secao(ano: int) -> int:
    return csv_zip_para_parquet(_zip("detalhe_votacao_secao", ano), parquet(f"detalhe_secao_{ano}"),
                                "*_BRASIL.csv", filtro_sql="CD_CARGO = '1'",
                                prefiltro=b'"Presidente"')


def detalhe_munzona(ano: int) -> int:
    return csv_zip_para_parquet(_zip("detalhe_votacao_munzona", ano), parquet(f"detalhe_munzona_{ano}"),
                                "*_BRASIL.csv", filtro_sql="CD_CARGO = '1'",
                                prefiltro=b'"Presidente"')


def candidato_munzona(ano: int) -> int:
    return csv_zip_para_parquet(_zip("votacao_candidato_munzona", ano), parquet(f"candidato_munzona_{ano}"),
                                "*_BRASIL.csv", filtro_sql="CD_CARGO = '1'",
                                prefiltro=b'"Presidente"')


def secoes_agregadas(ano: int) -> int:
    return csv_zip_para_parquet(_zip("secoes_agregadas", ano), parquet(f"secoes_agregadas_{ano}"), "*.csv")


def votacao_secao(ano: int) -> int:
    """Votação por seção (Presidente), por UF; caminho independente do bweb (Teste K)."""
    total = 0
    for uf in UFS_COM_EXTERIOR:
        try:
            total += csv_zip_para_parquet(_zip("votacao_secao", ano, uf),
                                          parquet(f"votacao_secao/{ano}_{uf}"), "*.csv",
                                          filtro_sql="CD_CARGO = '1'", prefiltro=b'"Presidente"')
        except FileNotFoundError as e:
            print("ausente:", e)
    return total


def perfil_secao(ano: int) -> int:
    """Eleitorado e biometria cadastrais agregados por seção."""
    total = 0
    for uf in UFS_COM_EXTERIOR:
        try:
            total += csv_zip_para_parquet(
                _zip("perfil_eleitor_secao", ano, uf), parquet(f"perfil_secao/{ano}_{uf}"), "*.csv",
                colunas="SG_UF, CD_MUNICIPIO, NR_ZONA, NR_SECAO, "
                        "sum(TRY_CAST(QT_ELEITORES_PERFIL AS BIGINT)) qt_eleitores, "
                        "sum(TRY_CAST(QT_ELEITORES_BIOMETRIA AS BIGINT)) qt_eleitores_biometria, "
                        "sum(TRY_CAST(QT_ELEITORES_DEFICIENCIA AS BIGINT)) qt_eleitores_deficiencia, "
                        "any_value(DT_GERACAO) dt_geracao",
                agrupar="SG_UF, CD_MUNICIPIO, NR_ZONA, NR_SECAO")
        except FileNotFoundError as e:
            print("ausente:", e)
    return total
