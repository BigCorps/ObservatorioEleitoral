"""Comparação histórica 2022 × 2026 com indicadores padronizados.

Cada indicador só é calculado a partir de campos com a mesma definição nos dois anos
(ver docs/dicionario-dados.md). Saídas em resultados/comparativo/.
Correspondência de seções: o mesmo número de seção NÃO garante o mesmo eleitorado;
classifica-se cada par pela coincidência do local de votação e pela variação de aptos.
"""
from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from .config import PROCESSADOS, RESULTADOS

PASTA = RESULTADOS / "comparativo"


def _indicadores_bu(con, ano: int) -> pd.DataFrame:
    f = PROCESSADOS / f"secoes_bu_{ano}.parquet"
    if not f.exists():
        return pd.DataFrame()
    cols = ("turno, uf, cd_municipio, nr_zona, nr_secao, qt_aptos, qt_comparecimento, qt_abstencoes, votos_nominais, "
            "votos_brancos, votos_nulos, qt_eleitores_biometria_nh")
    src = f"SELECT {cols} FROM '{f}'"
    turnos = {r[0] for r in con.execute(f"SELECT DISTINCT turno FROM '{f}'").fetchall()}
    for t in (1, 2):
        of = PROCESSADOS / f"secoes_oficiais_{ano}_{t}t.parquet"
        if t not in turnos and of.exists():  # turno sem BU em CSV: tabelas oficiais por seção
            src += (f" UNION ALL SELECT turno, uf, cd_municipio, nr_zona, nr_secao, qt_aptos, qt_comparecimento, "
                    f"qt_abstencoes, votos_nominais, votos_brancos, votos_nulos, NULL::INT FROM '{of}'")
    f = f"({src})"
    q = f"""SELECT {ano} ano, turno, abr, count(*) secoes, sum(qt_aptos) aptos, sum(qt_comparecimento) comparecimento,
        round(100.0*sum(qt_abstencoes)/sum(qt_aptos),3) pct_abstencao,
        round(100.0*sum(votos_brancos)/sum(qt_comparecimento),3) pct_brancos,
        round(100.0*sum(votos_nulos)/sum(qt_comparecimento),3) pct_nulos,
        round(100.0*sum(votos_nominais)/sum(qt_comparecimento),3) pct_validos,
        round(100.0*sum(qt_eleitores_biometria_nh) FILTER (WHERE qt_eleitores_biometria_nh>=0 AND uf <> 'ZZ')/nullif(sum(qt_comparecimento) FILTER (WHERE uf <> 'ZZ'), 0),3) pct_biometria_nao_habilitados_bu
      FROM (SELECT *, uf abr FROM {f} UNION ALL SELECT *, 'BR' FROM {f})
      GROUP BY ALL"""
    return con.execute(q).df()


# Os indicadores dos logs permanecem baseados nas 27 UFs: as habilitações e
# os horários da zona exterior (ZZ) seguem cobertura e regras distintas.
def _indicadores_log(con, ano: int) -> pd.DataFrame:
    f = PROCESSADOS / f"indicadores_temporais_{ano}.parquet"
    if not f.exists():
        return pd.DataFrame()
    q = f"""SELECT {ano} ano, turno, abr, count(*) secoes_com_log,
        round(100.0*sum(votos_antes_8h)/sum(n_votos_computados),4) pct_votos_antes_8h,
        round(100.0*sum(votos_apos_17h)/sum(n_votos_computados),4) pct_votos_apos_17h,
        round(100.0*sum(votos_apos_19h)/sum(n_votos_computados),4) pct_votos_apos_19h,
        round(median(primeiro_voto_brt)/3600.0,3) mediana_primeiro_voto_h,
        round(median(ultimo_voto_brt)/3600.0,3) mediana_ultimo_voto_h,
        round(avg(ultimo_voto_brt-primeiro_voto_brt)/3600.0,3) duracao_media_votacao_h,
        round(100.0*avg((n_pronta>1)::INT),3) pct_secoes_reabertura,
        round(100.0*avg((n_modo_contingencia>0)::INT),3) pct_secoes_contingencia,
        round(100.0*sum(hab_biometrica)/sum(n_habilitados),3) pct_hab_biometrica_log,
        round(100.0*sum(hab_manual_apos_falha)/sum(n_habilitados),3) pct_hab_manual_apos_falha_log,
        round(100.0*sum(hab_sem_biometria)/sum(n_habilitados),3) pct_hab_sem_biometria_log,
        median(duracao_voto_mediana_s) mediana_duracao_voto_s
      FROM (SELECT *, uf abr FROM '{f}' UNION ALL SELECT *, 'BR' FROM '{f}' WHERE uf <> 'ZZ')
      GROUP BY ALL"""
    return con.execute(q).df()


def correspondencia_secoes(con) -> pd.DataFrame:
    a, b = PROCESSADOS / "secoes_bu_2022.parquet", PROCESSADOS / "secoes_bu_2026.parquet"
    if not (a.exists() and b.exists()):
        return pd.DataFrame()
    con.execute(f"""CREATE OR REPLACE TABLE corr AS
      SELECT coalesce(x.uf,y.uf) uf, coalesce(x.cd_municipio,y.cd_municipio) cd_municipio,
        coalesce(x.nr_zona,y.nr_zona) nr_zona, coalesce(x.nr_secao,y.nr_secao) nr_secao,
        x.nr_local_votacao local_2022, y.nr_local_votacao local_2026, x.qt_aptos aptos_2022, y.qt_aptos aptos_2026,
        CASE WHEN x.nr_secao IS NULL THEN 'apenas_2026'
             WHEN y.nr_secao IS NULL THEN 'apenas_2022'
             WHEN x.nr_local_votacao = y.nr_local_votacao AND abs(y.qt_aptos - x.qt_aptos) <= 0.10 * x.qt_aptos
               THEN 'correspondencia_provavel'
             WHEN x.nr_local_votacao = y.nr_local_votacao THEN 'mesmo_local_aptos_mudaram'
             ELSE 'local_mudou' END classe
      FROM (SELECT * FROM '{a}' WHERE turno=1) x FULL JOIN (SELECT * FROM '{b}' WHERE turno=1) y
      USING (uf, cd_municipio, nr_zona, nr_secao)""")
    PASTA.mkdir(parents=True, exist_ok=True)
    con.execute(f"COPY corr TO '{PASTA}/correspondencia_secoes_2022_2026.parquet' (FORMAT parquet)")
    r = con.execute("""SELECT uf, classe, count(*) secoes FROM corr GROUP BY ALL
                       UNION ALL SELECT 'BR', classe, count(*) FROM corr GROUP BY ALL ORDER BY 1, 2""").df()
    r.to_csv(PASTA / "correspondencia_secoes_resumo.csv", index=False)
    return r


def executar() -> pd.DataFrame:
    con = duckdb.connect()
    con.execute("SET enable_progress_bar=false")
    partes = []
    for ano in (2022, 2026):
        bu, lg = _indicadores_bu(con, ano), _indicadores_log(con, ano)
        if bu.empty:
            continue
        partes.append(bu.merge(lg, on=["ano", "turno", "abr"], how="left") if not lg.empty else bu)
    PASTA.mkdir(parents=True, exist_ok=True)
    t = pd.concat(partes, ignore_index=True).rename(columns={"abr": "abrangencia"})
    t = t.sort_values(["abrangencia", "ano", "turno"])
    t.to_csv(PASTA / "indicadores_2022_2026.csv", index=False)
    # formato largo: uma linha por abrangência e indicador
    longo = t.melt(id_vars=["ano", "turno", "abrangencia"], var_name="indicador", value_name="valor")
    longo["col"] = longo.ano.astype(str) + "_" + longo.turno.astype(str) + "t"
    largo = longo.pivot_table(index=["abrangencia", "indicador"], columns="col", values="valor", aggfunc="first").reset_index()
    for c in ("2022_1t", "2022_2t", "2026_1t", "2026_2t"):
        if c not in largo:
            largo[c] = None
    largo["dif_turnos_2022"] = largo["2022_2t"] - largo["2022_1t"]
    largo["dif_turnos_2026"] = largo["2026_2t"] - largo["2026_1t"] if largo["2026_2t"].notna().any() else None
    largo["dif_1t_2026_menos_2022"] = largo["2026_1t"] - largo["2022_1t"]
    largo.to_csv(PASTA / "comparativo_largo.csv", index=False)
    correspondencia_secoes(con)
    con.close()
    return largo
