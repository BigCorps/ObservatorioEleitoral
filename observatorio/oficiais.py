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
                                prefiltro=(b'"Presidente"', b'"PRESIDENTE"'))


def detalhe_munzona(ano: int) -> int:
    return csv_zip_para_parquet(_zip("detalhe_votacao_munzona", ano), parquet(f"detalhe_munzona_{ano}"),
                                "*_BRASIL.csv", filtro_sql="CD_CARGO = '1'",
                                prefiltro=(b'"Presidente"', b'"PRESIDENTE"'))


def candidato_munzona(ano: int) -> int:
    return csv_zip_para_parquet(_zip("votacao_candidato_munzona", ano), parquet(f"candidato_munzona_{ano}"),
                                "*_BRASIL.csv", filtro_sql="CD_CARGO = '1'",
                                prefiltro=(b'"Presidente"', b'"PRESIDENTE"'))


def secoes_agregadas(ano: int) -> int:
    return csv_zip_para_parquet(_zip("secoes_agregadas", ano), parquet(f"secoes_agregadas_{ano}"), "*.csv")


def votacao_secao(ano: int) -> int:
    """Votação por seção do cargo Presidente (arquivo nacional "BR"); caminho
    independente do bweb (Teste K). Os arquivos por UF trazem apenas os demais cargos."""
    return csv_zip_para_parquet(_zip("votacao_secao", ano, "BR"), parquet(f"votacao_secao/{ano}_BR"), "*.csv",
                                filtro_sql="CD_CARGO = '1'", prefiltro=(b'"Presidente"', b'"PRESIDENTE"'))


def perfil_secao(ano: int) -> int:
    """Eleitorado e biometria cadastrais agregados por seção."""
    total = 0
    for uf in UFS_COM_EXTERIOR:
        try:
            total += csv_zip_para_parquet(
                _zip("perfil_eleitor_secao", ano, uf), parquet(f"perfil_secao/{ano}_{uf}"), "*.csv",
                # 2026: QT_ELEITORES_PERFIL passou a se chamar QT_ELEITORES
                colunas="SG_UF, CD_MUNICIPIO, NR_ZONA, NR_SECAO, "
                        f"sum(TRY_CAST({'QT_ELEITORES_PERFIL' if ano <= 2024 else 'QT_ELEITORES'} AS BIGINT)) qt_eleitores, "
                        "sum(TRY_CAST(QT_ELEITORES_BIOMETRIA AS BIGINT)) qt_eleitores_biometria, "
                        "sum(TRY_CAST(QT_ELEITORES_DEFICIENCIA AS BIGINT)) qt_eleitores_deficiencia, "
                        "any_value(DT_GERACAO) dt_geracao",
                agrupar="SG_UF, CD_MUNICIPIO, NR_ZONA, NR_SECAO")
        except FileNotFoundError as e:
            print("ausente:", e)
    return total


def secoes_de_tabelas_oficiais(ano: int, turno: int):
    """Tabela por seção no mesmo formato de secoes_bu_{ano} construída a partir das
    tabelas oficiais (Detalhe por seção + Votação por seção), para turnos cujo BU em CSV
    ainda não foi publicado. Coluna `fonte` = 'DSEC+VSEC'."""
    from .config import PROCESSADOS
    T = PROCESSADOS / "tabelas"
    saida = PROCESSADOS / f"secoes_oficiais_{ano}_{turno}t.parquet"
    con = duckdb.connect()
    con.execute("SET enable_progress_bar=false")
    con.execute(f"""COPY (
      WITH d AS (SELECT CAST(NR_TURNO AS INT) turno, SG_UF uf, CAST(CD_MUNICIPIO AS INT) cd_municipio,
          any_value(NM_MUNICIPIO) nm_municipio, CAST(NR_ZONA AS INT) nr_zona, CAST(NR_SECAO AS INT) nr_secao,
          any_value(CAST(NR_LOCAL_VOTACAO AS INT)) nr_local_votacao,
          any_value(CAST(QT_APTOS AS INT)) qt_aptos, any_value(CAST(QT_COMPARECIMENTO AS INT)) qt_comparecimento,
          any_value(CAST(QT_ABSTENCOES AS INT)) qt_abstencoes, any_value(CAST(QT_VOTOS_NOMINAIS AS INT)) votos_nominais,
          any_value(CAST(QT_VOTOS_BRANCOS AS INT)) votos_brancos, any_value(CAST(QT_VOTOS_NULOS AS INT)) votos_nulos,
          any_value(ST_SECAO_INSTALADA) st_instalada, any_value(DS_ORIGEM_VOTO) ds_origem_voto, any_value(DS_MODELO_URNA) ds_modelo_urna
        FROM '{T}/detalhe_secao_{ano}.parquet' WHERE NR_TURNO = '{turno}' GROUP BY ALL),
      v AS (SELECT SG_UF uf, CAST(CD_MUNICIPIO AS INT) cd_municipio, CAST(NR_ZONA AS INT) nr_zona, CAST(NR_SECAO AS INT) nr_secao,
          map_from_entries(list(struct_pack(k := CAST(NR_VOTAVEL AS INT), v := CAST(QT_VOTOS AS INT)))
                           FILTER (WHERE CAST(NR_VOTAVEL AS INT) NOT IN (95, 96, 97, 98))) votos_candidato
        FROM '{T}/votacao_secao/{ano}_BR.parquet' WHERE NR_TURNO = '{turno}' GROUP BY ALL)
      SELECT {ano} ano, d.*, v.votos_candidato, 'DSEC+VSEC' fonte
      FROM d LEFT JOIN v USING (uf, cd_municipio, nr_zona, nr_secao)
      WHERE d.st_instalada NOT IN ('Não', 'N')) TO '{saida}' (FORMAT parquet)""")
    r = con.execute(f"SELECT count(*), sum(qt_comparecimento), count(votos_candidato) FROM '{saida}'").fetchone()
    con.close()
    return r
