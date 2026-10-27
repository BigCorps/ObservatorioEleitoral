"""Teste J — testes estatísticos adicionais sobre contagens por seção.

Executados apenas quando a hipótese de referência é justificável:
- Último dígito (uniforme): justificável para contagens com amplitude grande em
  relação a 10 (aplicado a seções com ≥ 50 votos no candidato).
- Segundo dígito (Benford 2BL): uso controverso na literatura (Mebane 2006; Deckert,
  Myagkov & Ordeshook 2011). Reportado apenas como descrição, com tamanho de efeito.
- Impressão digital (Klimek et al. 2012): histograma 2D comparecimento × proporção do
  candidato, para inspeção visual; não é teste de hipótese.
- Seções com 100% dos votos válidos para um único candidato.
Correção para múltiplas comparações: Holm-Bonferroni sobre todos os testes por UF.
Um valor-p pequeno NÃO é evidência de fraude: com centenas de milhares de seções,
desvios minúsculos tornam-se "significantes". Por isso o tamanho do efeito
(Cramér V e maior desvio absoluto em pontos percentuais) acompanha cada teste.
"""
from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd
from scipy import stats

from .config import PROCESSADOS, RESULTADOS

BENFORD2 = np.array([sum(np.log10(1 + 1 / (10 * k + d)) for k in range(1, 10)) for d in range(10)])


def _teste(obs: np.ndarray, esperado_prop: np.ndarray) -> dict:
    n = obs.sum()
    if n == 0:
        return {}
    chi2, p = stats.chisquare(obs, esperado_prop * n)
    v = float(np.sqrt(chi2 / (n * (len(obs) - 1))))
    desvio = float(np.max(np.abs(obs / n - esperado_prop)) * 100)
    return {"n": int(n), "qui2": round(float(chi2), 3), "p": float(p), "cramer_v": round(v, 5),
            "maior_desvio_pp": round(desvio, 4)}


def _d2(s: np.ndarray) -> np.ndarray:
    return (s // 10 ** (np.floor(np.log10(s)).astype(int) - 1)) % 10


def _simular(n: np.ndarray, p: np.ndarray, rep: int = 20, semente: int = 2022):
    """Distribuição esperada do último dígito (contagens ≥ 50) e do 2º dígito (≥ 10)
    sob o modelo nulo binomial com a proporção da zona. O modelo ignora a
    heterogeneidade entre seções de uma zona (sobredispersão), logo é uma referência
    aproximada, não uma verdade."""
    rng = np.random.default_rng(semente)
    cu, cd = np.zeros(10), np.zeros(10)
    for _ in range(rep):
        x = rng.binomial(n.astype(np.int64), np.clip(p, 0, 1))
        cu += np.bincount(x[x >= 50] % 10, minlength=10)
        cd += np.bincount(_d2(x[x >= 10]), minlength=10)
    return cu / cu.sum(), cd / cd.sum()


def holm(p: pd.Series) -> pd.Series:
    ordem = p.sort_values().index
    m = len(p)
    ajust = pd.Series(index=p.index, dtype=float)
    acum = 0.0
    for i, idx in enumerate(ordem):
        acum = max(acum, min(1.0, (m - i) * p[idx]))
        ajust[idx] = acum
    return ajust


def executar(ano: int) -> pd.DataFrame:
    con = duckdb.connect()
    con.execute("SET enable_progress_bar=false")
    con.execute(f"CREATE VIEW b AS SELECT * FROM '{PROCESSADOS}/secoes_bu_{ano}.parquet'")
    cands = [r[0] for r in con.execute("""SELECT k FROM (SELECT unnest(map_keys(votos_candidato)) k,
        unnest(map_values(votos_candidato)) v FROM b WHERE turno=(SELECT max(turno) FROM b)) GROUP BY k ORDER BY sum(v) DESC LIMIT 2""").fetchall()]
    linhas = []
    for turno in (1, 2):
        dados = con.execute(f"""SELECT uf, votos_nominais n,
            {', '.join(f'coalesce(votos_candidato[{c}],0) c{c}' for c in cands)},
            {', '.join(f'sum(coalesce(votos_candidato[{c}],0)) OVER (PARTITION BY uf, cd_municipio, nr_zona) / sum(votos_nominais) OVER (PARTITION BY uf, cd_municipio, nr_zona) p{c}' for c in cands)}
            FROM b WHERE turno={turno} AND votos_nominais > 0""").df()
        if dados.empty:
            continue
        for c in cands:
            for uf, g in [("BR", dados)] + list(dados.groupby("uf")):
                x = g[f"c{c}"].to_numpy()
                u = x[x >= 50] % 10
                r = _teste(np.bincount(u, minlength=10), np.full(10, 0.1))
                if r:
                    linhas.append({"turno": turno, "candidato": c, "abrangencia": uf, "teste": "ultimo_digito_uniforme", **r})
                s = x[x >= 10]
                r = _teste(np.bincount(_d2(s), minlength=10), BENFORD2)
                if r:
                    linhas.append({"turno": turno, "candidato": c, "abrangencia": uf, "teste": "segundo_digito_benford_descritivo", **r})
                # referência simulada: X ~ Binomial(válidos da seção, proporção do candidato na zona)
                sim_u, sim_d = _simular(g["n"].to_numpy(), g[f"p{c}"].to_numpy())
                r = _teste(np.bincount(u, minlength=10), sim_u)
                if r:
                    linhas.append({"turno": turno, "candidato": c, "abrangencia": uf, "teste": "ultimo_digito_vs_simulacao_binomial_zona", **r})
                r = _teste(np.bincount(_d2(s), minlength=10), sim_d)
                if r:
                    linhas.append({"turno": turno, "candidato": c, "abrangencia": uf, "teste": "segundo_digito_vs_simulacao_binomial_zona", **r})
    df = pd.DataFrame(linhas)
    df["p_holm"] = holm(df["p"])
    pasta = RESULTADOS / str(ano)
    df.to_csv(pasta / "estatistica_testes_digitos.csv", index=False)
    # Seções com 100% dos válidos para um candidato, por faixa de tamanho
    con.execute(f"""COPY (
      WITH x AS (SELECT turno, uf, votos_nominais, list_max(map_values(votos_candidato)) maxv FROM b WHERE votos_nominais > 0)
      SELECT turno, CASE WHEN votos_nominais < 50 THEN '<50' WHEN votos_nominais < 100 THEN '50-99' ELSE '100+' END faixa_validos,
        count(*) secoes, count(*) FILTER (WHERE maxv = votos_nominais) secoes_100pct_um_candidato
      FROM x GROUP BY ALL ORDER BY ALL) TO '{pasta}/estatistica_secoes_100pct.csv' (HEADER)""")
    # Impressão digital (Klimek): histograma 2D comparecimento x proporção do mais votado no 2º turno
    con.execute(f"""COPY (
      SELECT turno, CAST(floor(100.0*qt_comparecimento/qt_aptos) AS INT) pct_comparecimento,
        CAST(floor(100.0*coalesce(votos_candidato[{cands[0]}],0)/votos_nominais) AS INT) pct_candidato_{cands[0]}, count(*) secoes
      FROM b WHERE qt_aptos > 0 AND votos_nominais > 0 AND uf <> 'ZZ' GROUP BY ALL ORDER BY ALL)
      TO '{pasta}/estatistica_impressao_digital.csv' (HEADER)""")
    con.close()
    return df
