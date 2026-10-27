"""Testes estatísticos da mudança entre turnos: 2026 (1º→2º) comparado a 2022 (1º→2º).

Dois níveis, ambos com controle de múltiplas comparações (Holm):

1. UF — diferença-em-diferenças por indicador:
     DiD = (2T26 − 1T26) − (2T22 − 1T22), em pontos percentuais.
   O DiD de cada UF é comparado com a distribuição dos DiD das demais UFs por escore
   robusto (mediana/MAD·1,4826); p bicaudal pela normal. Mede se a mudança entre turnos
   de uma UF em 2026 destoa do padrão nacional em relação a 2022.

2. Seção — mudança 1º→2º turno na mesma seção (Detalhe da apuração por seção):
   proporção de seções com mudança extrema (|Δ| > limiar em p.p.) em 2026 e em 2022,
   por UF; teste de duas proporções. Limiar fixo, escolhido antes de ver os dados
   (abstenção 15 p.p.; brancos e nulos 5 p.p.). Seções com menos de 50 aptos são
   excluídas (variação amostral domina).

Nenhum resultado aqui é prova de irregularidade: um efeito estatístico indica onde olhar.
"""
from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd
from scipy import stats

from .config import PROCESSADOS, RESULTADOS

PASTA = RESULTADOS / "comparativo"
IND_UF = ["pct_abstencao", "pct_brancos", "pct_nulos", "pct_votos_apos_17h", "pct_hab_biometrica_log",
          "pct_hab_manual_apos_falha_log", "pct_hab_sem_biometria_log", "pct_secoes_contingencia",
          "pct_secoes_reabertura"]
LIMIARES = {"abstencao": 15.0, "brancos": 5.0, "nulos": 5.0}
MIN_APTOS = 50


def holm(p: pd.Series) -> pd.Series:
    p = p.astype(float)
    ok = p.notna()
    v = p[ok].values
    ordem = np.argsort(v)
    m = len(v)
    aj = np.empty(m)
    corr = 0.0
    for k, i in enumerate(ordem):
        corr = max(corr, min(1.0, (m - k) * v[i]))
        aj[i] = corr
    out = pd.Series(np.nan, index=p.index)
    out[ok] = aj
    return out


def did_uf() -> pd.DataFrame:
    i = pd.read_csv(PASTA / "indicadores_2022_2026.csv")
    i = i[~i.abrangencia.isin(["BR", "ZZ"])]
    linhas = []
    for ind in IND_UF:
        w = i.pivot_table(index="abrangencia", columns=["ano", "turno"], values=ind)
        if w.isna().all().any():
            continue
        d26 = w[(2026, 2)] - w[(2026, 1)]
        d22 = w[(2022, 2)] - w[(2022, 1)]
        did = (d26 - d22).dropna()
        med = did.median()
        mad = (did - med).abs().median() * 1.4826
        for uf, v in did.items():
            z = (v - med) / mad if mad > 0 else np.nan
            linhas.append({"indicador": ind, "uf": uf, "delta_2026_pp": round(d26[uf], 4),
                           "delta_2022_pp": round(d22[uf], 4), "did_pp": round(v, 4),
                           "mediana_did_ufs": round(med, 4), "z_robusto": round(z, 3),
                           "p": 2 * stats.norm.sf(abs(z)) if pd.notna(z) else np.nan})
    df = pd.DataFrame(linhas)
    df["p_holm"] = holm(df.p)
    return df


def _secoes(con, ano: int, t: int) -> str:
    return f"""SELECT SG_UF uf, CAST(CD_MUNICIPIO AS INT) mun, CAST(NR_ZONA AS INT) z, CAST(NR_SECAO AS INT) s,
        sum(CAST(QT_APTOS AS BIGINT)) aptos, sum(CAST(QT_COMPARECIMENTO AS BIGINT)) comp,
        sum(CAST(QT_ABSTENCOES AS BIGINT)) abst, sum(CAST(QT_VOTOS_BRANCOS AS BIGINT)) br,
        sum(CAST(QT_VOTOS_NULOS AS BIGINT)) nu
      FROM '{PROCESSADOS}/tabelas/detalhe_secao_{ano}.parquet'
      WHERE CAST(NR_TURNO AS INT) = {t} AND coalesce(ST_SECAO_INSTALADA, 'Sim') NOT IN ('Não', 'N')
      GROUP BY ALL"""


def extremos_secao() -> pd.DataFrame:
    con = duckdb.connect()
    partes = []
    for ano in (2022, 2026):
        con.execute(f"""CREATE OR REPLACE TEMP VIEW m{ano} AS
          SELECT a.uf, a.aptos, 100.0 * b.abst / b.aptos - 100.0 * a.abst / a.aptos d_abstencao,
            CASE WHEN a.comp > 0 AND b.comp > 0 THEN 100.0 * b.br / b.comp - 100.0 * a.br / a.comp END d_brancos,
            CASE WHEN a.comp > 0 AND b.comp > 0 THEN 100.0 * b.nu / b.comp - 100.0 * a.nu / a.comp END d_nulos
          FROM ({_secoes(con, ano, 1)}) a JOIN ({_secoes(con, ano, 2)}) b USING (uf, mun, z, s)
          WHERE a.aptos >= {MIN_APTOS} AND b.aptos >= {MIN_APTOS}""")
        for ind, lim in LIMIARES.items():
            for nivel in ("uf", "'BR'"):
                q = con.execute(f"""SELECT {nivel} AS uf, count(d_{ind}) n,
                    count(*) FILTER (abs(d_{ind}) > {lim}) n_ext, median(d_{ind}) mediana_delta_pp
                    FROM m{ano} GROUP BY 1""").df()
                q["ano"], q["indicador"] = ano, ind
                partes.append(q)
    d = pd.concat(partes)
    w = d.pivot_table(index=["indicador", "uf"], columns="ano", values=["n", "n_ext", "mediana_delta_pp"])
    w.columns = [f"{a}_{b}" for a, b in w.columns]
    w = w.reset_index()
    p = []
    for r in w.itertuples():
        n1, x1, n2, x2 = r.n_2022, r.n_ext_2022, r.n_2026, r.n_ext_2026
        p1, p2 = x1 / n1, x2 / n2
        pp = (x1 + x2) / (n1 + n2)
        se = np.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n2)) if 0 < pp < 1 else np.nan
        z = (p2 - p1) / se if se and se > 0 else np.nan
        p.append({"pct_extremas_2022": round(100 * p1, 4), "pct_extremas_2026": round(100 * p2, 4),
                  "dif_pp": round(100 * (p2 - p1), 4), "z": round(z, 3) if pd.notna(z) else np.nan,
                  "p": 2 * stats.norm.sf(abs(z)) if pd.notna(z) else np.nan})
    w = pd.concat([w, pd.DataFrame(p)], axis=1)
    w["limiar_pp"] = w.indicador.map(LIMIARES)
    w["p_holm"] = holm(w.p)
    return w


def executar() -> dict:
    PASTA.mkdir(parents=True, exist_ok=True)
    a = did_uf()
    a.to_csv(PASTA / "testes_did_uf.csv", index=False)
    b = extremos_secao()
    b.to_csv(PASTA / "testes_extremos_secao.csv", index=False)
    return {"did_sig": int((a.p_holm < 0.01).sum()), "did_testes": len(a),
            "secao_sig": int((b.p_holm < 0.01).sum()), "secao_testes": len(b)}
