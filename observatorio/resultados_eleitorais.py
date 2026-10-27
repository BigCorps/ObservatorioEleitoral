"""Testes G e H — comparecimento, abstenção, brancos, nulos e mudanças entre turnos.

Base: BU publicado em CSV (bweb), cargo Presidente, seção a seção.
Definições (mesmo cargo, mesma base, mesma abrangência):
  comparecimento = válidos (nominais) + brancos + nulos
  aptos          = comparecimento + abstenções
  % abstenção, % comparecimento: sobre aptos; % brancos/nulos/válidos: sobre comparecimento.
Reconciliação entre turnos (identidade contábil, vale em qualquer agregado comparável):
  Δválidos = Δcomparecimento − Δ(brancos + nulos)
Seções com aptos diferentes entre os turnos são sinalizadas (base não idêntica).
"""
from __future__ import annotations

import duckdb

from .config import PROCESSADOS, RESULTADOS

NIVEIS = {
    "brasil": "'BR'",
    "uf": "uf",
    "municipio": "uf, cd_municipio, nm_municipio",
    "zona": "uf, cd_municipio, nr_zona",
}


def _agregado(con, nivel: str, chaves: str, ano: int, pasta) -> None:
    sel = chaves if nivel != "brasil" else "'BR' AS abrangencia"
    grp = chaves if nivel != "brasil" else "1"
    con.execute(f"""
    CREATE OR REPLACE TEMP VIEW a AS
    SELECT turno, {sel}, count(*) secoes, sum(qt_aptos) aptos, sum(qt_comparecimento) comparecimento,
      sum(qt_abstencoes) abstencoes, sum(votos_nominais) validos, sum(votos_brancos) brancos,
      sum(votos_nulos) nulos,
      sum(votos_candidato[13]) votos_13, sum(votos_candidato[22]) votos_22
    FROM bweb GROUP BY turno, {grp}""")
    cols_join = (chaves if nivel != "brasil" else "abrangencia")
    if con.execute("SELECT count(DISTINCT turno) FROM bweb").fetchone()[0] < 2:
        # apenas um turno disponível (ex.: 2026 enquanto o 2º turno não é publicado)
        con.execute(f"""COPY (SELECT *, round(100.0*abstencoes/aptos,4) pct_abstencao,
            round(100.0*comparecimento/aptos,4) pct_comparecimento, round(100.0*brancos/comparecimento,4) pct_brancos,
            round(100.0*nulos/comparecimento,4) pct_nulos, round(100.0*(brancos+nulos)/comparecimento,4) pct_brancos_nulos,
            round(100.0*validos/comparecimento,4) pct_validos FROM a ORDER BY ALL)
            TO '{pasta}/resultados_{nivel}.csv' (HEADER)""")
        return
    con.execute(f"""COPY (
      WITH t AS (SELECT * ,
          round(100.0 * abstencoes / aptos, 4) pct_abstencao,
          round(100.0 * comparecimento / aptos, 4) pct_comparecimento,
          round(100.0 * brancos / comparecimento, 4) pct_brancos,
          round(100.0 * nulos / comparecimento, 4) pct_nulos,
          round(100.0 * (brancos + nulos) / comparecimento, 4) pct_brancos_nulos,
          round(100.0 * validos / comparecimento, 4) pct_validos,
          round(100.0 * votos_13 / validos, 4) pct_validos_13,
          round(100.0 * votos_22 / validos, 4) pct_validos_22
        FROM a)
      SELECT t1.* EXCLUDE (turno), t2.* EXCLUDE (turno, {cols_join}) ,
        t2.comparecimento - t1.comparecimento AS delta_comparecimento,
        (t2.brancos + t2.nulos) - (t1.brancos + t1.nulos) AS delta_brancos_nulos,
        t2.validos - t1.validos AS delta_validos,
        (t2.validos - t1.validos) - ((t2.comparecimento - t1.comparecimento)
          - ((t2.brancos + t2.nulos) - (t1.brancos + t1.nulos))) AS residuo_reconciliacao,
        t2.abstencoes - t1.abstencoes AS delta_abstencoes,
        round(t2.pct_abstencao - t1.pct_abstencao, 4) delta_pp_abstencao,
        round(t2.pct_brancos - t1.pct_brancos, 4) delta_pp_brancos,
        round(t2.pct_nulos - t1.pct_nulos, 4) delta_pp_nulos,
        t2.votos_13 - t1.votos_13 AS delta_votos_13, t2.votos_22 - t1.votos_22 AS delta_votos_22,
        t2.aptos - t1.aptos AS delta_aptos
      FROM (SELECT * FROM t WHERE turno = 1) t1
      JOIN (SELECT * FROM t WHERE turno = 2) t2 USING ({cols_join})
      ORDER BY ALL) TO '{pasta}/resultados_{nivel}.csv' (HEADER)""")


def executar(ano: int = 2022) -> dict:
    con = duckdb.connect()
    con.execute("SET enable_progress_bar=false")
    cols = ("turno, uf, cd_municipio, nm_municipio, nr_zona, nr_secao, qt_aptos, qt_comparecimento, qt_abstencoes, "
            "votos_nominais, votos_brancos, votos_nulos, votos_candidato")
    base = f"SELECT {cols}, 'BU-CSV' fonte FROM '{PROCESSADOS}/secoes_bu_{ano}.parquet'"
    turnos_bu = {r[0] for r in con.execute(f"SELECT DISTINCT turno FROM '{PROCESSADOS}/secoes_bu_{ano}.parquet'").fetchall()}
    for t in (1, 2):
        of = PROCESSADOS / f"secoes_oficiais_{ano}_{t}t.parquet"
        if t not in turnos_bu and of.exists():
            # turno sem BU em CSV publicado: usa Detalhe por seção + Votação por seção (fonte registrada)
            base += f" UNION ALL SELECT {cols}, fonte FROM '{of}'"
    con.execute(f"CREATE VIEW bweb AS {base}")
    pasta = RESULTADOS / str(ano)
    pasta.mkdir(parents=True, exist_ok=True)
    for nivel, chaves in NIVEIS.items():
        _agregado(con, nivel, chaves, ano, pasta)
    if con.execute("SELECT count(DISTINCT turno) FROM bweb").fetchone()[0] < 2:
        con.close()
        return {"turnos": 1}
    # nível de seção: grava em Parquet (grande) + resumo de consistência
    con.execute(f"""COPY (
      SELECT b1.uf, b1.cd_municipio, b1.nr_zona, b1.nr_secao,
        b1.qt_aptos aptos_1t, b2.qt_aptos aptos_2t, b1.qt_comparecimento comp_1t, b2.qt_comparecimento comp_2t,
        b1.votos_nominais validos_1t, b2.votos_nominais validos_2t,
        b1.votos_brancos + b1.votos_nulos bn_1t, b2.votos_brancos + b2.votos_nulos bn_2t,
        b1.votos_candidato[13] l_1t, b2.votos_candidato[13] l_2t,
        b1.votos_candidato[22] b_1t, b2.votos_candidato[22] b_2t,
        (b2.votos_nominais - b1.votos_nominais) - ((b2.qt_comparecimento - b1.qt_comparecimento)
          - ((b2.votos_brancos + b2.votos_nulos) - (b1.votos_brancos + b1.votos_nulos))) residuo
      FROM (SELECT * FROM bweb WHERE turno = 1) b1
      FULL JOIN (SELECT * FROM bweb WHERE turno = 2) b2 USING (uf, cd_municipio, nr_zona, nr_secao))
      TO '{PROCESSADOS}/secoes_turnos_{ano}.parquet' (FORMAT parquet)""")
    # nomes explícitos por turno nos CSVs agregados
    import pandas as pd
    for nivel in NIVEIS:
        f = pasta / f"resultados_{nivel}.csv"
        d = pd.read_csv(f, dtype={"cd_municipio": "Int64"})
        chaves_n = {"abrangencia", "uf", "cd_municipio", "nm_municipio", "nr_zona"}
        ren = {}
        for c in d.columns:
            if c in chaves_n or c.startswith(("delta_", "residuo")):
                continue
            ren[c] = c[:-2] + "_2t" if c.endswith("_1") else c + "_1t"
        d.rename(columns=ren).to_csv(f, index=False)
    r = con.execute(f"""SELECT count(*) secoes,
        count(*) FILTER (WHERE aptos_1t IS NULL OR aptos_2t IS NULL) sem_par_entre_turnos,
        count(*) FILTER (WHERE aptos_1t <> aptos_2t) aptos_diferentes,
        count(*) FILTER (WHERE residuo <> 0) residuo_nao_nulo
      FROM '{PROCESSADOS}/secoes_turnos_{ano}.parquet'""").df()
    r.to_csv(pasta / "consistencia_secoes_entre_turnos.csv", index=False)
    con.close()
    return r.to_dict("records")[0]


def aptos_vs_transferencias(ano: int = 2022) -> dict:
    """Teste C2: a variação de aptos por seção entre turnos é explicada pela
    transferência temporária de eleitores (TTE: voto em trânsito, mesários, presos,
    militares, etc.)? Hipótese: aptos(t) = base − saídas(t) + entradas(t), logo
    aptos(2t) − aptos(1t) = líquido_TTE(2t) − líquido_TTE(1t)."""
    from .tabelas import csv_zip_para_parquet, parquet
    from .oficiais import _zip
    p = parquet(f"tte_secao_{ano}")
    if not p.exists():
        csv_zip_para_parquet(_zip("transf_temporaria_secao", ano), p, "*.csv")
    con = duckdb.connect()
    con.execute("SET enable_progress_bar=false")
    con.execute(f"""CREATE VIEW t AS SELECT CAST(NR_TURNO AS INT) turno,
        SG_UF_ORIGEM uo, CAST(CD_MUNICIPIO_ORIGEM AS INT) mo, CAST(NR_ZONA_ORIGEM AS INT) zo, CAST(NR_SECAO_ORIGEM AS INT) so,
        SG_UF_DESTINO ud, CAST(CD_MUNICIPIO_DESTINO AS INT) md, CAST(NR_ZONA_DESTINO AS INT) zd, CAST(NR_SECAO_DESTINO AS INT) sd,
        CAST(QT_ELEITOR AS INT) q FROM '{p}'""")
    con.execute("""CREATE VIEW liq AS SELECT uf, cd_municipio, nr_zona, nr_secao,
        coalesce(sum(e - s) FILTER (WHERE turno = 1), 0) liq_1t, coalesce(sum(e - s) FILTER (WHERE turno = 2), 0) liq_2t,
        sum(e) FILTER (WHERE turno = 1) entradas_1t, sum(s) FILTER (WHERE turno = 1) saidas_1t,
        sum(e) FILTER (WHERE turno = 2) entradas_2t, sum(s) FILTER (WHERE turno = 2) saidas_2t
      FROM (SELECT turno, ud uf, md cd_municipio, zd nr_zona, sd nr_secao, q e, 0 s FROM t
            UNION ALL SELECT turno, uo, mo, zo, so, 0, q FROM t) GROUP BY ALL""")
    pasta = RESULTADOS / str(ano)
    con.execute(f"""CREATE TABLE r AS SELECT s.uf, s.cd_municipio, s.nr_zona, s.nr_secao, s.aptos_1t, s.aptos_2t,
        s.aptos_2t - s.aptos_1t delta_aptos, coalesce(l.liq_2t - l.liq_1t, 0) delta_liquido_tte,
        l.entradas_1t, l.saidas_1t, l.entradas_2t, l.saidas_2t
      FROM '{PROCESSADOS}/secoes_turnos_{ano}.parquet' s LEFT JOIN liq l USING (uf, cd_municipio, nr_zona, nr_secao)""")
    con.execute(f"""COPY (SELECT *, delta_aptos - delta_liquido_tte residuo FROM r
        WHERE delta_aptos <> delta_liquido_tte ORDER BY uf, cd_municipio, nr_zona, nr_secao)
        TO '{pasta}/aptos_entre_turnos_nao_explicados_por_tte.csv' (HEADER)""")
    res = con.execute("""SELECT count(*) secoes,
        count(*) FILTER (WHERE delta_aptos <> 0) secoes_aptos_mudaram,
        count(*) FILTER (WHERE delta_aptos <> 0 AND delta_aptos = delta_liquido_tte) explicadas_exatamente_por_tte,
        count(*) FILTER (WHERE delta_aptos <> delta_liquido_tte) nao_explicadas,
        sum(abs(delta_aptos - delta_liquido_tte)) soma_abs_residuo,
        sum(delta_aptos) soma_delta_aptos FROM r""").df()
    res.to_csv(pasta / "aptos_entre_turnos_resumo.csv", index=False)
    con.close()
    return res.to_dict("records")[0]
