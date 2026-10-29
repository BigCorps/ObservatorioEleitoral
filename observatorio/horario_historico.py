"""Compara seções com votos após 17h em 2022 e 2026 (2º turno).

Requer os Parquets processados locais do Observatório, não publicados no Git.
Reproduz os grupos A/B e as comparações do mesmo local/município em cada ano;
também compara seções com correspondência conservadora entre anos.
Não associa horário do voto a um candidato (sigilo do voto).
Execução: python -m observatorio.horario_historico
"""
from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from .config import PROCESSADOS, RESULTADOS

SAIDA = RESULTADOS / "comparativo"
CHAVES = ["uf", "cd_municipio", "nr_zona", "nr_secao"]
LOCAL = ["uf", "cd_municipio", "nr_zona", "nr_local_votacao"]
H17, H19 = 61200, 68400


def _fonte_urna(ano: int) -> Path:
    if ano == 2022:
        return PROCESSADOS / "secoes_bu_2022.parquet"
    if ano == 2026:
        return PROCESSADOS / "secoes_oficiais_2026_2t.parquet"
    raise ValueError("Ano deve ser 2022 ou 2026")


def carregar(con: duckdb.DuckDBPyConnection, ano: int) -> None:
    """Cria uma linha por seção com votos oficiais, horário e primeiro turno."""
    fonte = _fonte_urna(ano)
    horarios = PROCESSADOS / f"indicadores_temporais_{ano}.parquet"
    anterior = PROCESSADOS / f"secoes_turnos_{ano}.parquet"
    for p in (fonte, horarios, anterior):
        if not p.exists():
            raise FileNotFoundError(
                f"Parquet local ausente: {p}. Execute no ambiente com dados processados; "
                "não inicie novos downloads automaticamente."
            )
    con.execute(f"""
      CREATE OR REPLACE TABLE b{ano} AS
      SELECT o.uf, o.cd_municipio, o.nr_zona, o.nr_secao,
             o.nr_local_votacao,
             o.qt_aptos AS aptos, o.qt_comparecimento AS comparecimento,
             o.votos_nominais AS validos,
             coalesce(o.votos_candidato[13], 0) AS v13,
             coalesce(o.votos_candidato[22], 0) AS v22,
             o.votos_brancos AS brancos, o.votos_nulos AS nulos,
             t.votos_apos_17h, t.votos_apos_19h, t.encerramento_brt,
             r.validos_1t, r.l_1t, r.b_1t
      FROM (SELECT * FROM '{fonte}' WHERE turno = 2 AND uf <> 'ZZ') o
      JOIN (SELECT uf, cd_municipio, nr_zona, nr_secao,
                   votos_apos_17h, votos_apos_19h, encerramento_brt
            FROM '{horarios}' WHERE turno = 2 AND uf <> 'ZZ') t
      USING (uf, cd_municipio, nr_zona, nr_secao)
      LEFT JOIN '{anterior}' r USING (uf, cd_municipio, nr_zona, nr_secao)
    """)
    duplicadas = con.execute(f"""
      SELECT count(*) - count(DISTINCT (uf, cd_municipio, nr_zona, nr_secao))
      FROM b{ano}
    """).fetchone()[0]
    if duplicadas:
        raise ValueError(f"Seções duplicadas no cruzamento de {ano}: {duplicadas}")
    falhas = con.execute(f"""
      SELECT count(*) FROM b{ano}
      WHERE coalesce(v13,0) + coalesce(v22,0) + coalesce(brancos,0)
            + coalesce(nulos,0) <> comparecimento
    """).fetchone()[0]
    if falhas:
        raise ValueError(f"Falhas de soma dos BUs em {ano}: {falhas}")


def _resumo(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    rows = []
    for ano in (2022, 2026):
        for grupo, cond, descricao in (
            ("A", "votos_apos_17h > 0", "Pelo menos um voto após 17h"),
            ("B", "votos_apos_19h > 0", "Pelo menos um voto após 19h"),
            ("todos", "TRUE", "Todas as seções com log"),
        ):
            d = con.execute(f"""
              SELECT {ano} ano, '{grupo}' grupo, '{descricao}' descricao,
                uf, count(*) secoes, sum(aptos) aptos,
                sum(comparecimento) comparecimento, sum(validos) validos,
                sum(v13) votos_13, sum(v22) votos_22,
                sum(brancos) brancos, sum(nulos) nulos,
                sum(votos_apos_17h) votos_apos_17h,
                sum(votos_apos_19h) votos_apos_19h,
                round(100.0 * sum(v13) / nullif(sum(validos),0), 4) pct_13,
                round(100.0 * sum(l_1t) / nullif(sum(validos_1t),0), 4) pct_13_primeiro_turno,
                round(100.0 * sum(v22) / nullif(sum(validos),0), 4) pct_22,
                round(100.0 * sum(b_1t) / nullif(sum(validos_1t),0), 4) pct_22_primeiro_turno,
                sum(validos_1t) validos_1t, sum(l_1t) votos_13_1t, sum(b_1t) votos_22_1t
              FROM b{ano} WHERE {cond} GROUP BY uf
            """).df()
            rows.append(d)
    return pd.concat(rows, ignore_index=True)


def _base_regressao(con: duckdb.DuckDBPyConnection, ano: int) -> pd.DataFrame:
    df = con.execute(f"""
      SELECT uf, cd_municipio, nr_zona, nr_local_votacao, nr_secao,
             validos, aptos, comparecimento,
             100.0*v13/nullif(validos,0) s13,
             100.0*l_1t/nullif(validos_1t,0) s13_1t,
             100.0*comparecimento/nullif(aptos,0) comp_pct,
             (votos_apos_17h > 0)::INTEGER late17
      FROM b{ano}
      WHERE validos >= 50 AND aptos > 0
        AND validos_1t > 0 AND nr_local_votacao IS NOT NULL
    """).df()
    df["log_aptos"] = np.log(df.aptos.astype(float))
    colunas = ["s13", "s13_1t", "comp_pct", "log_aptos", "late17", "validos"]
    return df[np.isfinite(df[colunas].to_numpy(dtype=float)).all(axis=1)].reset_index(drop=True)


def _wls_fe(
    df: pd.DataFrame, grupo: str, y: str, peso: str,
    nivel: list[str], controles: list[str],
) -> dict | None:
    """FWL ponderado + erros agrupados no local/município, como análise 2026."""
    if df.empty:
        return None
    k_all = pd.factorize(pd.MultiIndex.from_frame(df[nivel]))[0]
    m = pd.Series(df[grupo].to_numpy(float)).groupby(k_all).transform("mean").to_numpy()
    sel = (m > 0) & (m < 1)
    if not sel.any():
        return None
    d = df.loc[sel].reset_index(drop=True)
    k = pd.factorize(pd.MultiIndex.from_frame(d[nivel]))[0]
    w = d[peso].to_numpy(float)
    x = d[[grupo, *controles]].to_numpy(float)
    vals = d[y].to_numpy(float)
    if not (np.isfinite(x).all() and np.isfinite(vals).all() and (w > 0).all()):
        raise ValueError("Regressão com dados não finitos")
    wg = np.bincount(k, weights=w)
    yd = vals - (np.bincount(k, weights=vals*w)/wg)[k]
    xd = np.column_stack([
        x[:,i] - (np.bincount(k, weights=x[:,i]*w)/wg)[k]
        for i in range(x.shape[1])
    ])
    sw = np.sqrt(w)
    xs, ys = xd*sw[:,None], yd*sw
    inv = np.linalg.pinv(xs.T@xs)
    beta = inv@(xs.T@ys)
    residual = ys-xs@beta
    sc = np.column_stack([np.bincount(k, weights=xs[:,i]*residual)
                          for i in range(xs.shape[1])])
    cov = inv@(sc.T@sc)@inv
    ep = float(np.sqrt(max(0.0,cov[0,0])))
    ef = float(beta[0])
    return {
        "locais_comparaveis": int(k.max()+1),
        "secoes": int(len(d)), "secoes_tardias": int(d[grupo].sum()),
        "efeito_pp": round(ef, 4), "erro_padrao_pp": round(ep, 4),
        "ic95_inf": round(ef - 1.96*ep, 4),
        "ic95_sup": round(ef + 1.96*ep, 4),
    }


def _comparacao_anual(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    rows = []
    for ano in (2022, 2026):
        df = _base_regressao(con, ano)
        for nome, nivel in (("mesmo_local", LOCAL),
                            ("mesmo_municipio", ["uf", "cd_municipio"])):
            for controles in ([], ["s13_1t", "comp_pct", "log_aptos"]):
                result = _wls_fe(df, "late17", "s13", "validos", nivel, controles)
                if result:
                    rows.append({"ano":ano,"criterio":"seção com voto após 17h",
                                 "comparacao":nome,
                                 "controles":",".join(controles) or "nenhum",
                                 **result})
    return pd.DataFrame(rows)


def _comparacao_por_uf(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Mesmo método da comparação anual, separadamente por UF (mesmo local de votação)."""
    rows = []
    for ano in (2022, 2026):
        df = _base_regressao(con, ano)
        for uf, d in df.groupby("uf"):
            d = d.reset_index(drop=True)
            for controles in ([], ["s13_1t", "comp_pct", "log_aptos"]):
                result = _wls_fe(d, "late17", "s13", "validos", LOCAL, controles)
                if result and result["secoes_tardias"] >= 30:
                    rows.append({"ano": ano, "uf": uf, "comparacao": "mesmo_local",
                                 "controles": ",".join(controles) or "nenhum", **result})
    return pd.DataFrame(rows)


def _historico_mesmas_secoes(con: duckdb.DuckDBPyConnection) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Pares conservadores: mesmo código, local e aptos com variação de até 10%."""
    df = con.execute("""
      SELECT a.uf, a.cd_municipio, a.nr_zona, a.nr_secao, a.nr_local_votacao,
        a.aptos aptos22, b.aptos aptos26, a.validos validos22,
        b.validos validos26, a.comparecimento comp22, b.comparecimento comp26,
        100.0*a.v13/nullif(a.validos,0) s13_2022,
        100.0*b.v13/nullif(b.validos,0) s13_2026,
        100.0*a.v22/nullif(a.validos,0) s22_2022,
        100.0*b.v22/nullif(b.validos,0) s22_2026,
        100.0*b.l_1t/nullif(b.validos_1t,0) s13_1t_2026,
        (a.votos_apos_17h > 0)::INT late22,
        (b.votos_apos_17h > 0)::INT late26
      FROM b2022 a JOIN b2026 b
      USING (uf, cd_municipio, nr_zona, nr_secao)
      WHERE a.nr_local_votacao = b.nr_local_votacao
        AND a.aptos > 0 AND b.aptos > 0
        AND abs(a.aptos - b.aptos)*1.0/a.aptos <= 0.10
        AND a.validos >= 50 AND b.validos >= 50
        AND b.validos_1t > 0
    """).df()
    df["pct_comparecimento26"] = 100.0*df.comp26/df.aptos26
    df["log_aptos26"] = np.log(df.aptos26.astype(float))
    df["delta_13_pp"] = df.s13_2026-df.s13_2022
    df["peso"] = np.minimum(df.validos22,df.validos26)
    cols=["s13_2022","s13_2026","s13_1t_2026","pct_comparecimento26",
          "log_aptos26","delta_13_pp","peso"]
    df = df[np.isfinite(df[cols].to_numpy(dtype=float)).all(axis=1)].reset_index(drop=True)
    tabela = []
    for (l22,l26), d in df.groupby(["late22","late26"]):
        tabela.append({
            "voto_tardio_2022":int(l22), "voto_tardio_2026":int(l26),
            "secoes":len(d), "validos_2022":int(d.validos22.sum()),
            "validos_2026":int(d.validos26.sum()),
            "pct_13_2022":round(np.sum(d.s13_2022*d.validos22)/d.validos22.sum(),4),
            "pct_13_2026":round(np.sum(d.s13_2026*d.validos26)/d.validos26.sum(),4),
            "pct_22_2022":round(np.sum(d.s22_2022*d.validos22)/d.validos22.sum(),4),
            "pct_22_2026":round(np.sum(d.s22_2026*d.validos26)/d.validos26.sum(),4),
            "pct_comparecimento_2022":round(100.0*d.comp22.sum()/d.aptos22.sum(),4),
            "pct_comparecimento_2026":round(100.0*d.comp26.sum()/d.aptos26.sum(),4),
        })
    linha = []
    for nome,nivel in (("mesmo_local",LOCAL),("mesmo_municipio",["uf","cd_municipio"])):
        for grupo in ("late26", "late22"):
            for controles in ([], ["s13_2022","s13_1t_2026","pct_comparecimento26","log_aptos26"]):
                result = _wls_fe(df,grupo,"delta_13_pp","peso",nivel,controles)
                if result:
                    linha.append({
                        "grupo_tardio": {"late26": "voto após 17h em 2026", "late22": "voto após 17h em 2022"}[grupo],
                        "comparacao":nome, "controles":",".join(controles) or "nenhum",
                        "variavel":"delta_13_pp_2026_menos_2022",
                        **result})
    return pd.DataFrame(tabela),pd.DataFrame(linha)


def executar() -> dict:
    SAIDA.mkdir(parents=True,exist_ok=True)
    con = duckdb.connect()
    con.execute("SET memory_limit='6GB'")
    for ano in (2022,2026):
        carregar(con,ano)
    resumo = _resumo(con)
    controle = _comparacao_anual(con)
    por_uf = _comparacao_por_uf(con)
    pares, historico = _historico_mesmas_secoes(con)
    con.close()
    # Coberturas que já tinham sido publicadas na auditoria, para detectar regressão.
    for ano,secoes,votos in ((2022,34455,40698),(2026,29609,34050)):
        r = resumo[(resumo.ano==ano)&(resumo.grupo=="A")]
        if int(r.secoes.sum())!=secoes or int(r.votos_apos_17h.sum())!=votos:
            raise AssertionError(f"Cobertura inesperada em {ano}: "+str(r[["secoes","votos_apos_17h"]].sum().to_dict()))
    resumo.to_csv(SAIDA/"horario_historico_por_uf.csv",index=False)
    controle.to_csv(SAIDA/"horario_historico_pareado.csv",index=False)
    pares.to_csv(SAIDA/"horario_historico_mesmas_secoes.csv",index=False)
    historico.to_csv(SAIDA/"horario_historico_delta_mesmo_local.csv",index=False)
    por_uf.to_csv(SAIDA/"horario_historico_pareado_uf.csv",index=False)
    return {"resumo":resumo,"controle":controle,"pares":pares,"historico":historico,"por_uf":por_uf}


if __name__ == "__main__":
    r=executar()
    for nome,df in r.items():
        print(nome, len(df),"linhas")
