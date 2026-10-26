"""Boletins de Urna publicados em CSV ("bweb") — seleção do cargo Presidente.

Gera:
- dados/processados/bweb/presidente_{ano}_{turno}t_{uf}.parquet  (formato longo, 1 linha por votável)
- secoes_bu_{ano}.parquet (formato largo, 1 linha por seção/turno) via `consolidar`.
"""
from __future__ import annotations

import glob
from pathlib import Path

import duckdb

from .catalogo import carregar_inventario
from .config import PROCESSADOS
from .download import caminho_local
from .tabelas import csv_zip_para_parquet

DIR = PROCESSADOS / "bweb"


def converter(ano: int, turno: int, uf: str) -> int:
    inv = [l for l in carregar_inventario() if l["tipo"] == "bu_csv" and l["ano"] == str(ano)
           and l["turno"] == str(turno) and l["uf"] == uf]
    if not inv:
        raise FileNotFoundError(f"bweb {ano} {turno}t {uf} não está no inventário")
    z = caminho_local(inv[0]["url"])
    if not z.exists():
        raise FileNotFoundError(f"{z} ainda não baixado")
    saida = DIR / f"presidente_{ano}_{turno}t_{uf}.parquet"
    return csv_zip_para_parquet(z, saida, "bweb_*.csv", filtro_sql="CD_CARGO_PERGUNTA = '1'",
                                prefiltro=b'"Presidente";')


def consolidar(ano: int) -> Path:
    """Tabela larga por seção (Presidente) a partir dos parquets longos."""
    arquivos = sorted(glob.glob(str(DIR / f"presidente_{ano}_*t_*.parquet")))
    saida = PROCESSADOS / f"secoes_bu_{ano}.parquet"
    con = duckdb.connect()
    con.execute("SET enable_progress_bar=false")
    lista = "[" + ",".join(f"'{a}'" for a in arquivos) + "]"
    con.execute(f"""
    CREATE VIEW l AS SELECT * FROM read_parquet({lista}, union_by_name=true);
    COPY (
    SELECT
      CAST(ANO_ELEICAO AS INT) ano, CAST(NR_TURNO AS INT) turno, SG_UF uf,
      CAST(CD_MUNICIPIO AS INT) cd_municipio, any_value(NM_MUNICIPIO) nm_municipio,
      CAST(NR_ZONA AS INT) nr_zona, CAST(NR_SECAO AS INT) nr_secao,
      any_value(CAST(CD_PLEITO AS INT)) cd_pleito,
      any_value(CAST(NR_LOCAL_VOTACAO AS INT)) nr_local_votacao,
      count(DISTINCT CAST(QT_APTOS AS INT)) n_valores_aptos,
      any_value(CAST(QT_APTOS AS INT)) qt_aptos,
      any_value(CAST(QT_COMPARECIMENTO AS INT)) qt_comparecimento,
      any_value(CAST(QT_ABSTENCOES AS INT)) qt_abstencoes,
      -- O BU relaciona apenas os votáveis que receberam votos: a ausência da linha de
      -- branco/nulo/nominal significa zero voto naquele tipo. A regra é verificada pelo
      -- teste B1 (comparecimento = soma dos votos) em 100% das seções; não é imputação.
      coalesce(sum(CASE WHEN DS_TIPO_VOTAVEL='Nominal' THEN CAST(QT_VOTOS AS INT) END), 0) votos_nominais,
      coalesce(sum(CASE WHEN DS_TIPO_VOTAVEL='Branco' THEN CAST(QT_VOTOS AS INT) END), 0) votos_brancos,
      coalesce(sum(CASE WHEN DS_TIPO_VOTAVEL='Nulo' THEN CAST(QT_VOTOS AS INT) END), 0) votos_nulos,
      sum(CASE WHEN DS_TIPO_VOTAVEL NOT IN ('Nominal','Branco','Nulo') THEN CAST(QT_VOTOS AS INT) END) votos_outros_tipos,
      string_agg(DISTINCT DS_TIPO_VOTAVEL, '|') tipos_votavel,
      sum(CAST(QT_VOTOS AS INT)) votos_total,
      count(*) n_linhas,
      count(DISTINCT CAST(NR_VOTAVEL AS INT)) n_votaveis_distintos,
      map_from_entries(list(struct_pack(k := CAST(NR_VOTAVEL AS INT), v := CAST(QT_VOTOS AS INT)))
                       FILTER (WHERE DS_TIPO_VOTAVEL='Nominal')) votos_candidato,
      any_value(DS_TIPO_URNA) ds_tipo_urna, count(DISTINCT DS_TIPO_URNA) n_tipos_urna,
      any_value(NR_URNA_EFETIVADA) nr_urna_efetivada,
      any_value(CD_CARGA_1_URNA_EFETIVADA) cd_carga_1, any_value(CD_CARGA_2_URNA_EFETIVADA) cd_carga_2,
      any_value(CD_FLASHCARD_URNA_EFETIVADA) cd_flashcard,
      any_value(DT_CARGA_URNA_EFETIVADA) dt_carga,
      any_value(DS_AGREGADAS) ds_agregadas,
      any_value(DT_ABERTURA) dt_abertura, any_value(DT_ENCERRAMENTO) dt_encerramento,
      any_value(DT_EMISSAO_BU) dt_emissao_bu, any_value(DT_BU_RECEBIDO) dt_bu_recebido,
      any_value(TRY_CAST(QT_ELEITORES_BIOMETRIA_NH AS INT)) qt_eleitores_biometria_nh,
      any_value(QT_ELEITORES_BIOMETRIA_NH) qt_eleitores_biometria_nh_txt,
      any_value(NR_JUNTA_APURADORA) nr_junta, any_value(NR_TURMA_APURADORA) nr_turma,
      any_value(DT_GERACAO || ' ' || HH_GERACAO) dt_geracao_arquivo,
      any_value(filename) arquivo_origem
    FROM l
    GROUP BY ALL
    ) TO '{saida}' (FORMAT parquet, COMPRESSION zstd)""")
    con.close()
    return saida
