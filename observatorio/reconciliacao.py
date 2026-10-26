"""Testes B, C e K — reconciliação entre fontes oficiais, seção a seção.

Fontes comparadas (todas do TSE):
  BWEB  = Boletim de Urna publicado em CSV (bweb)             -> secoes_bu_{ano}.parquet
  BUBIN = arquivo .bu binário transmitido pela urna (ASN.1)    -> processados/bu/*.parquet
  LOG   = log da urna (.logjez)                                -> processados/logs/*.parquet
  DSEC  = "Detalhe da apuração por seção eleitoral"            -> tabelas/detalhe_secao_{ano}
  VSEC  = "Votação por seção eleitoral" (por UF)               -> tabelas/votacao_secao/
  CMZ   = "Votação nominal por município e zona"               -> tabelas/candidato_munzona_{ano}
  DMZ   = "Detalhe da apuração por município e zona"           -> tabelas/detalhe_munzona_{ano}

Cada divergência é gravada individualmente (nenhuma é descartada) em
resultados/{ano}/incompatibilidades.csv; o resumo por teste vai para
resultados/{ano}/reconciliacao_resumo.csv. Valor ausente em uma das fontes é
registrado como "ausente", nunca tratado como zero.
"""
from __future__ import annotations

from pathlib import Path

import duckdb

from .config import PROCESSADOS, RESULTADOS

T = PROCESSADOS / "tabelas"


def _existe(padrao: str) -> bool:
    return bool(list(Path("/").glob(padrao.lstrip("/"))))


def preparar(con: duckdb.DuckDBPyConnection, ano: int) -> list[str]:
    """Cria as views normalizadas (chave: turno, uf, cd_municipio, nr_zona, nr_secao)."""
    disponiveis = []
    con.execute(f"CREATE OR REPLACE VIEW bweb AS SELECT * FROM '{PROCESSADOS}/secoes_bu_{ano}.parquet'")
    disponiveis.append("bweb")
    if _existe(f"{PROCESSADOS}/bu/{ano}_*.parquet"):
        con.execute(f"""CREATE OR REPLACE VIEW bubin AS
          SELECT CAST(regexp_extract(filename, '_(\\d)t_', 1) AS INT) turno,
                 regexp_extract(filename, '_([A-Z]{{2}})\\.parquet', 1) uf,
                 CAST(substr(arquivo, 8, 5) AS INT) cd_municipio, CAST(substr(arquivo, 13, 4) AS INT) nr_zona,
                 CAST(substr(arquivo, 17, 4) AS INT) nr_secao, *
          FROM read_parquet('{PROCESSADOS}/bu/{ano}_*.parquet', union_by_name=true, filename=true)""")
        disponiveis.append("bubin")
    if _existe(f"{PROCESSADOS}/logs/{ano}_*.parquet"):
        con.execute(f"""CREATE OR REPLACE VIEW logs AS
          SELECT * EXCLUDE (votos_s, hab_s, hab_mod, dur_voto, dur_voto_mod),
                 len(list_filter(dur_voto_mod, lambda x: x = 3)) man_votou,
                 len(list_filter(dur_voto_mod, lambda x: x = 1)) bio_votou,
                 len(list_filter(dur_voto_mod, lambda x: x = 2)) sembio_votou,
                 len(list_filter(dur_voto_mod, lambda x: x = 0)) semetapa_votou
          FROM read_parquet('{PROCESSADOS}/logs/{ano}_*.parquet', union_by_name=true)""")
        disponiveis.append("logs")
    if (T / f"detalhe_secao_{ano}.parquet").exists():
        con.execute(f"""CREATE OR REPLACE VIEW dsec AS SELECT
            CAST(NR_TURNO AS INT) turno, SG_UF uf, CAST(CD_MUNICIPIO AS INT) cd_municipio,
            CAST(NR_ZONA AS INT) nr_zona, CAST(NR_SECAO AS INT) nr_secao,
            TRY_CAST(QT_APTOS AS INT) qt_aptos, TRY_CAST(QT_COMPARECIMENTO AS INT) qt_comparecimento,
            TRY_CAST(QT_ABSTENCOES AS INT) qt_abstencoes, TRY_CAST(QT_VOTOS_NOMINAIS AS INT) votos_nominais,
            TRY_CAST(QT_VOTOS_BRANCOS AS INT) votos_brancos, TRY_CAST(QT_VOTOS_NULOS AS INT) votos_nulos,
            TRY_CAST(QT_VOTOS_LEGENDA AS INT) votos_legenda,
            TRY_CAST(QT_VOTOS_ANULADOS_APU_SEP AS INT) votos_anulados_apu_sep,
            ST_SECAO_INSTALADA, ST_SECAO_ANULADA, DS_MODELO_URNA, DS_ORIGEM_VOTO
          FROM '{T}/detalhe_secao_{ano}.parquet'""")
        disponiveis.append("dsec")
    if _existe(f"{T}/votacao_secao/{ano}_*.parquet"):
        con.execute(f"""CREATE OR REPLACE VIEW vsec AS SELECT
            CAST(NR_TURNO AS INT) turno, SG_UF uf, CAST(CD_MUNICIPIO AS INT) cd_municipio,
            CAST(NR_ZONA AS INT) nr_zona, CAST(NR_SECAO AS INT) nr_secao,
            CAST(NR_VOTAVEL AS INT) nr_votavel, sum(CAST(QT_VOTOS AS INT)) qt_votos
          FROM read_parquet('{T}/votacao_secao/{ano}_*.parquet', union_by_name=true) GROUP BY ALL""")
        disponiveis.append("vsec")
    for nome, arq in (("cmz", f"candidato_munzona_{ano}"), ("dmz", f"detalhe_munzona_{ano}")):
        if (T / f"{arq}.parquet").exists():
            con.execute(f"CREATE OR REPLACE VIEW {nome}_raw AS SELECT * FROM '{T}/{arq}.parquet'")
            disponiveis.append(nome)
    return disponiveis


CHAVE = "turno, uf, cd_municipio, nr_zona, nr_secao"


def _diff(con, teste: str, descricao: str, fonte_a: str, fonte_b: str, sql_join: str,
          campos: list[tuple[str, str, str]]) -> None:
    """Insere divergências campo a campo. `campos` = [(nome, expr_a, expr_b)]."""
    partes = []
    for nome, ea, eb in campos:
        partes.append(f"""SELECT '{teste}' teste, turno, uf, cd_municipio, nr_zona, nr_secao,
            '{nome}' campo, CAST({ea} AS BIGINT) valor_a, CAST({eb} AS BIGINT) valor_b
            FROM j""")
    con.execute(f"CREATE OR REPLACE TEMP VIEW j AS {sql_join}")
    total = con.execute("SELECT count(*) FROM j").fetchone()[0]
    uniao = " UNION ALL ".join(partes)
    con.execute(f"""INSERT INTO incompat SELECT teste, turno, uf, cd_municipio, nr_zona, nr_secao, campo,
            valor_a, '{fonte_a}', valor_b, '{fonte_b}', valor_a - valor_b,
            CASE WHEN valor_a IS NULL OR valor_b IS NULL THEN 'ausente' ELSE 'diferente' END
        FROM ({uniao}) WHERE valor_a IS DISTINCT FROM valor_b""")
    for nome, _, _ in campos:
        r = con.execute(f"""SELECT count(*) FILTER (WHERE campo='{nome}'),
                count(*) FILTER (WHERE campo='{nome}' AND situacao='ausente'),
                coalesce(sum(abs(diferenca)) FILTER (WHERE campo='{nome}'), 0)
            FROM incompat WHERE teste='{teste}'""").fetchone()
        con.execute("INSERT INTO resumo VALUES (?,?,?,?,?,?,?,?,?)",
                    [teste, descricao, nome, fonte_a, fonte_b, total, r[0], r[1], int(r[2])])


def executar(ano: int) -> dict:
    con = duckdb.connect()
    con.execute("SET enable_progress_bar=false")
    disp = preparar(con, ano)
    con.execute("""CREATE TABLE incompat (teste VARCHAR, turno INT, uf VARCHAR, cd_municipio INT, nr_zona INT,
        nr_secao INT, campo VARCHAR, valor_a BIGINT, fonte_a VARCHAR, valor_b BIGINT, fonte_b VARCHAR,
        diferenca BIGINT, situacao VARCHAR)""")
    con.execute("""CREATE TABLE resumo (teste VARCHAR, descricao VARCHAR, campo VARCHAR, fonte_a VARCHAR,
        fonte_b VARCHAR, registros_comparados BIGINT, divergencias BIGINT, ausencias BIGINT,
        soma_abs_diferencas BIGINT)""")

    # B1/C1 — identidades contábeis dentro do próprio BU (Presidente)
    _diff(con, "B1", "Comparecimento = nominais + brancos + nulos (BU-CSV, Presidente)", "BWEB", "BWEB",
          f"SELECT {CHAVE}, * EXCLUDE (turno, uf, cd_municipio, nr_zona, nr_secao) FROM bweb",
          [("comparecimento_vs_soma_votos", "qt_comparecimento",
            "coalesce(votos_nominais,0)+coalesce(votos_brancos,0)+coalesce(votos_nulos,0)+coalesce(votos_outros_tipos,0)")])
    _diff(con, "C1", "Aptos = comparecimento + abstenções (BU-CSV)", "BWEB", "BWEB",
          f"SELECT {CHAVE}, * EXCLUDE (turno, uf, cd_municipio, nr_zona, nr_secao) FROM bweb",
          [("aptos_vs_comp_mais_abst", "qt_aptos", "qt_comparecimento + qt_abstencoes")])

    if "bubin" in disp:
        # B2 — BU publicado (CSV) x BU binário transmitido pela urna
        _diff(con, "B2", "BU-CSV x BU binário (.bu)", "BWEB", "BUBIN",
              f"""SELECT b.turno, b.uf, b.cd_municipio, b.nr_zona, b.nr_secao, b.*, u.* EXCLUDE ({CHAVE})
                  FROM bweb b JOIN bubin u USING ({CHAVE})""",
              [("aptos", "b.qt_aptos", "u.bu_qtd_aptos"),
               ("comparecimento", "b.qt_comparecimento", "u.bu_qtd_comparecimento"),
               ("votos_nominais", "b.votos_nominais", "u.bu_votos_nominais"),
               ("brancos", "b.votos_brancos", "u.bu_votos_brancos"),
               ("nulos", "b.votos_nulos", "u.bu_votos_nulos"),
               ("biometria_nh_vs_lib_codigo", "b.qt_eleitores_biometria_nh", "u.bu_qtd_lib_codigo"),
               ("votos_por_candidato_soma_dif_abs",
                "list_sum(list_transform(map_keys(b.votos_candidato), lambda k: abs(b.votos_candidato[k] - coalesce(list_sum(list_transform(list_filter(u.bu_votos_candidato, lambda e: e.k = k), lambda e: e.v)), 0))))",
                "0")])
        # B2c — votos por candidato no binário que não aparecem no CSV
        _diff(con, "B2c", "Candidatos presentes no .bu e ausentes no BU-CSV", "BUBIN", "BWEB",
              f"""SELECT b.turno, b.uf, b.cd_municipio, b.nr_zona, b.nr_secao, b.votos_candidato, u.bu_votos_candidato
                  FROM bweb b JOIN bubin u USING ({CHAVE})""",
              [("votos_extra_no_bu", "list_sum(list_transform(list_filter(bu_votos_candidato, lambda e: NOT list_contains(map_keys(votos_candidato), e.k)), lambda e: e.v))", "0")])
        # cobertura entre BWEB e BUBIN
        _diff(con, "A2", "Seção presente no BU-CSV e ausente no pacote de arquivos de urna (e vice-versa)", "BWEB", "BUBIN",
              f"""SELECT coalesce(b.turno,u.turno) turno, coalesce(b.uf,u.uf) uf, coalesce(b.cd_municipio,u.cd_municipio) cd_municipio,
                  coalesce(b.nr_zona,u.nr_zona) nr_zona, coalesce(b.nr_secao,u.nr_secao) nr_secao,
                  CASE WHEN b.nr_secao IS NULL THEN NULL ELSE 1 END pa, CASE WHEN u.nr_secao IS NULL THEN NULL ELSE 1 END pb
                  FROM bweb b FULL JOIN bubin u USING ({CHAVE})
                  WHERE coalesce(b.turno,u.turno) IN (SELECT DISTINCT turno FROM bubin)
                    AND coalesce(b.uf,u.uf) IN (SELECT DISTINCT uf FROM bubin)""",
              [("presenca", "pa", "pb")])
    if "logs" in disp:
        _diff(con, "B6", "BU-CSV x log da urna (contagens)", "BWEB", "LOG",
              f"""SELECT b.turno, b.uf, b.cd_municipio, b.nr_zona, b.nr_secao, b.qt_comparecimento, b.qt_eleitores_biometria_nh,
                  l.n_votos_computados, l.man_votou, l.n_voto_presidente, l.n_nulo_suspensao_presidente, l.tem_log
                  FROM bweb b JOIN logs l USING ({CHAVE}) WHERE l.tem_log""",
              [("comparecimento_vs_votos_computados", "qt_comparecimento", "n_votos_computados"),
               ("comparecimento_vs_votos_presidente_mais_nulos_suspensao", "qt_comparecimento",
                "n_voto_presidente + n_nulo_suspensao_presidente"),
               ("biometria_nh_vs_liberacao_manual_no_log", "qt_eleitores_biometria_nh", "man_votou")])
    if "dsec" in disp:
        _diff(con, "B3", "BU-CSV x Detalhe da apuração por seção", "BWEB", "DSEC",
              f"""SELECT b.turno, b.uf, b.cd_municipio, b.nr_zona, b.nr_secao, b.qt_aptos a1, d.qt_aptos a2,
                  b.qt_comparecimento c1, d.qt_comparecimento c2, b.qt_abstencoes ab1, d.qt_abstencoes ab2,
                  b.votos_nominais n1, d.votos_nominais n2, b.votos_brancos br1, d.votos_brancos br2,
                  b.votos_nulos nu1, d.votos_nulos nu2
                  FROM bweb b JOIN dsec d USING ({CHAVE})""",
              [("aptos", "a1", "a2"), ("comparecimento", "c1", "c2"), ("abstencoes", "ab1", "ab2"),
               ("votos_nominais", "n1", "n2"), ("brancos", "br1", "br2"), ("nulos", "nu1", "nu2")])
        _diff(con, "A3", "Seções no Detalhe por seção sem BU-CSV (e vice-versa)", "DSEC", "BWEB",
              f"""SELECT coalesce(d.turno,b.turno) turno, coalesce(d.uf,b.uf) uf, coalesce(d.cd_municipio,b.cd_municipio) cd_municipio,
                  coalesce(d.nr_zona,b.nr_zona) nr_zona, coalesce(d.nr_secao,b.nr_secao) nr_secao,
                  CASE WHEN d.nr_secao IS NULL THEN NULL ELSE 1 END pa, CASE WHEN b.nr_secao IS NULL THEN NULL ELSE 1 END pb
                  FROM dsec d FULL JOIN bweb b USING ({CHAVE})""",
              [("presenca", "pa", "pb")])
    if "vsec" in disp:
        _diff(con, "K1", "BU-CSV x Votação por seção (caminho independente), por candidato", "BWEB", "VSEC",
              f"""WITH bl AS (SELECT turno, uf, cd_municipio, nr_zona, nr_secao, unnest(map_keys(votos_candidato)) k,
                         unnest(map_values(votos_candidato)) v FROM bweb
                  UNION ALL SELECT turno, uf, cd_municipio, nr_zona, nr_secao, 95, votos_brancos FROM bweb
                  UNION ALL SELECT turno, uf, cd_municipio, nr_zona, nr_secao, 96, votos_nulos FROM bweb)
                  SELECT coalesce(bl.turno,v.turno) turno, coalesce(bl.uf,v.uf) uf, coalesce(bl.cd_municipio,v.cd_municipio) cd_municipio,
                    coalesce(bl.nr_zona,v.nr_zona) nr_zona, coalesce(bl.nr_secao,v.nr_secao) nr_secao, bl.v, v.qt_votos,
                    coalesce(bl.k, v.nr_votavel) k
                  FROM bl FULL JOIN vsec v ON bl.turno=v.turno AND bl.uf=v.uf AND bl.cd_municipio=v.cd_municipio
                    AND bl.nr_zona=v.nr_zona AND bl.nr_secao=v.nr_secao AND bl.k=v.nr_votavel
                  WHERE coalesce(bl.v,0) <> 0 OR coalesce(v.qt_votos,0) <> 0""",
              [("votos_votavel", "v", "qt_votos")])
    if "cmz" in disp:
        # B4 — soma das seções x votação por município e zona, por candidato
        con.execute(f"""CREATE OR REPLACE TEMP VIEW cmz AS SELECT CAST(NR_TURNO AS INT) turno, SG_UF uf,
              CAST(CD_MUNICIPIO AS INT) cd_municipio, CAST(NR_ZONA AS INT) nr_zona, CAST(NR_CANDIDATO AS INT) k,
              sum(CAST(QT_VOTOS_NOMINAIS AS BIGINT)) v FROM cmz_raw GROUP BY ALL""")
        _diff(con, "B4", "Soma das seções (BU-CSV) x Votação nominal por município e zona", "BWEB", "CMZ",
              """WITH bl AS (SELECT turno, uf, cd_municipio, nr_zona, k, sum(v) v FROM (
                      SELECT turno, uf, cd_municipio, nr_zona, unnest(map_keys(votos_candidato)) k,
                             unnest(map_values(votos_candidato)) v FROM bweb) GROUP BY ALL)
                 SELECT coalesce(bl.turno,c.turno) turno, coalesce(bl.uf,c.uf) uf, coalesce(bl.cd_municipio,c.cd_municipio) cd_municipio,
                   coalesce(bl.nr_zona,c.nr_zona) nr_zona, NULL::INT nr_secao, bl.v va, c.v vb
                 FROM bl FULL JOIN cmz c USING (turno, uf, cd_municipio, nr_zona, k)
                 WHERE coalesce(bl.v,0)<>0 OR coalesce(c.v,0)<>0""",
              [("votos_candidato_zona", "va", "vb")])
    if "dmz" in disp:
        con.execute("""CREATE OR REPLACE TEMP VIEW dmz AS SELECT CAST(NR_TURNO AS INT) turno, SG_UF uf,
              CAST(CD_MUNICIPIO AS INT) cd_municipio, CAST(NR_ZONA AS INT) nr_zona,
              sum(CAST(QT_APTOS AS BIGINT)) aptos, sum(CAST(QT_COMPARECIMENTO AS BIGINT)) comp,
              sum(CAST(QT_ABSTENCOES AS BIGINT)) abst, sum(CAST(QT_VOTOS_BRANCOS AS BIGINT)) brancos,
              sum(CAST(QT_TOTAL_VOTOS_NULOS AS BIGINT)) nulos, sum(CAST(QT_TOTAL_VOTOS_VALIDOS AS BIGINT)) validos
              FROM dmz_raw GROUP BY ALL""")
        _diff(con, "B5", "Soma das seções (BU-CSV) x Detalhe por município e zona", "BWEB", "DMZ",
              """WITH bl AS (SELECT turno, uf, cd_municipio, nr_zona, sum(qt_aptos) aptos, sum(qt_comparecimento) comp,
                    sum(qt_abstencoes) abst, sum(votos_brancos) brancos, sum(votos_nulos) nulos,
                    sum(votos_nominais) validos FROM bweb GROUP BY ALL)
                 SELECT coalesce(b.turno,d.turno) turno, coalesce(b.uf,d.uf) uf, coalesce(b.cd_municipio,d.cd_municipio) cd_municipio,
                   coalesce(b.nr_zona,d.nr_zona) nr_zona, NULL::INT nr_secao,
                   b.aptos a1, d.aptos a2, b.comp c1, d.comp c2, b.abst ab1, d.abst ab2, b.brancos br1, d.brancos br2,
                   b.nulos n1, d.nulos n2, b.validos v1, d.validos v2
                 FROM bl b FULL JOIN dmz d USING (turno, uf, cd_municipio, nr_zona)""",
              [("aptos", "a1", "a2"), ("comparecimento", "c1", "c2"), ("abstencoes", "ab1", "ab2"),
               ("brancos", "br1", "br2"), ("nulos", "n1", "n2"), ("validos", "v1", "v2")])

    out = RESULTADOS / str(ano)
    out.mkdir(parents=True, exist_ok=True)
    con.execute(f"COPY (SELECT * FROM resumo ORDER BY teste, campo) TO '{out}/reconciliacao_resumo.csv' (HEADER)")
    con.execute(f"""COPY (SELECT * FROM incompat ORDER BY teste, campo, turno, uf, cd_municipio, nr_zona, nr_secao)
                    TO '{out}/incompatibilidades.csv' (HEADER)""")
    res = con.execute("SELECT * FROM resumo ORDER BY teste, campo").df()
    con.close()
    return {"disponiveis": disp, "resumo": res}
