"""Teste I — diferenças por modelo de urna, controlando a geografia.

A comparação ingênua (média nacional por modelo) é confundida pela distribuição
geográfica dos modelos. O estimador principal compara seções do MESMO local de
votação (mesma escola/prédio) que usaram modelos diferentes:

  efeito_local = média ponderada(indicador | UE2020) − média ponderada(indicador | outros)
  efeito = média dos efeitos locais, ponderada pelo nº de votos válidos do local
Como poucos locais misturam modelos, repete-se o estimador dentro da mesma zona e do
mesmo município (controles mais fracos, com mais seções comparáveis).

Intervalo de confiança de 95% por bootstrap de locais (reamostragem com reposição).
Limitação: a alocação de modelos às seções de um mesmo local não é aleatória
(ex.: seções mais novas, acessibilidade), portanto diferença ≠ causa.
"""
from __future__ import annotations

import duckdb
import numpy as np

from .config import PROCESSADOS, RESULTADOS

T = PROCESSADOS / "tabelas"
INDICADORES = {
    "pct_validos_22": "100.0 * coalesce(votos_candidato[22], 0) / nullif(votos_nominais, 0)",
    "pct_validos_13": "100.0 * coalesce(votos_candidato[13], 0) / nullif(votos_nominais, 0)",
    "pct_comparecimento": "100.0 * qt_comparecimento / nullif(qt_aptos, 0)",
    "pct_brancos_nulos": "100.0 * (votos_brancos + votos_nulos) / nullif(qt_comparecimento, 0)",
    "pct_biometria_nh": "100.0 * qt_eleitores_biometria_nh / nullif(qt_comparecimento, 0)",
}


def _bootstrap(efeitos: np.ndarray, pesos: np.ndarray, n: int = 2000, semente: int = 2022):
    rng = np.random.default_rng(semente)
    k = len(efeitos)
    est = []
    for _ in range(n):
        i = rng.integers(0, k, k)
        est.append(np.average(efeitos[i], weights=pesos[i]))
    return np.percentile(est, [2.5, 97.5])


def executar(ano: int, modelo_ref: str = "UE 2020") -> list[dict]:
    con = duckdb.connect()
    con.execute("SET enable_progress_bar=false")
    con.execute(f"""CREATE VIEW s AS SELECT b.*, d.DS_MODELO_URNA modelo
      FROM '{PROCESSADOS}/secoes_bu_{ano}.parquet' b
      JOIN (SELECT CAST(NR_TURNO AS INT) turno, SG_UF uf, CAST(CD_MUNICIPIO AS INT) cd_municipio,
                   CAST(NR_ZONA AS INT) nr_zona, CAST(NR_SECAO AS INT) nr_secao, DS_MODELO_URNA
            FROM '{T}/detalhe_secao_{ano}.parquet') d USING (turno, uf, cd_municipio, nr_zona, nr_secao)
      WHERE d.DS_MODELO_URNA NOT LIKE '#%' AND b.uf <> 'ZZ'""")
    pasta = RESULTADOS / str(ano)
    saida = []
    # médias ingênuas por modelo
    cols = ", ".join(f"round(sum(({e}) * votos_nominais) / sum(votos_nominais), 4) {k}" for k, e in INDICADORES.items())
    con.execute(f"""COPY (SELECT turno, modelo, count(*) secoes, sum(votos_nominais) validos, {cols}
        FROM s GROUP BY ALL ORDER BY 1, 2) TO '{pasta}/modelos_medias_ingenuas.csv' (HEADER)""")
    niveis = {"mesmo_local": "uf, cd_municipio, nr_zona, nr_local_votacao",
              "mesma_zona": "uf, cd_municipio, nr_zona", "mesmo_municipio": "uf, cd_municipio"}
    for turno in sorted(x[0] for x in con.execute("SELECT DISTINCT turno FROM s").fetchall()):
      for nivel, grupo in niveis.items():
        for ind, expr in INDICADORES.items():
            df = con.execute(f"""
              WITH x AS (SELECT {grupo}, modelo = '{modelo_ref}' ref,
                           ({expr}) y, votos_nominais w FROM s WHERE turno = {turno} AND ({expr}) IS NOT NULL AND votos_nominais > 0)
              SELECT {grupo},
                sum(y*w) FILTER (WHERE ref) / sum(w) FILTER (WHERE ref) - sum(y*w) FILTER (WHERE NOT ref) / sum(w) FILTER (WHERE NOT ref) ef,
                sum(w) peso, count(*) FILTER (WHERE ref) n_ref, count(*) FILTER (WHERE NOT ref) n_outros
              FROM x GROUP BY ALL HAVING count(*) FILTER (WHERE ref) > 0 AND count(*) FILTER (WHERE NOT ref) > 0""").df()
            if df.empty:
                continue
            ef, w = df.ef.to_numpy(), df.peso.to_numpy()
            est = float(np.average(ef, weights=w))
            lo, hi = _bootstrap(ef, w)
            ing = con.execute(f"""SELECT sum(({expr})*votos_nominais) FILTER (WHERE modelo='{modelo_ref}')/sum(votos_nominais) FILTER (WHERE modelo='{modelo_ref}')
                 - sum(({expr})*votos_nominais) FILTER (WHERE modelo<>'{modelo_ref}')/sum(votos_nominais) FILTER (WHERE modelo<>'{modelo_ref}')
                 FROM s WHERE turno={turno} AND ({expr}) IS NOT NULL""").fetchone()[0]
            saida.append({"turno": turno, "controle": nivel, "indicador": ind, "referencia": modelo_ref,
                          "diferenca_ingenua_pp": round(ing, 4), "diferenca_controlada_pp": round(est, 4),
                          "ic95_inf": round(float(lo), 4), "ic95_sup": round(float(hi), 4),
                          "grupos_comparaveis": len(df), "secoes_ref": int(df.n_ref.sum()),
                          "secoes_outras": int(df.n_outros.sum())})
    import pandas as pd
    pd.DataFrame(saida).to_csv(pasta / "modelos_efeito_controlado.csv", index=False)
    con.close()
    return saida
