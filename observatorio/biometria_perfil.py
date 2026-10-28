"""Falha de biometria (liberação manual) × concentração de votos × perfil do eleitorado.

Grupos (2º turno de cada ano): seções em que um mesmo candidato teve mais de 80% dos votos
válidos nos dois turnos (conc_13, conc_22) e demais seções. Taxas do log da urna (2º turno,
sem exterior). Perfil por seção: Dados Abertos do TSE (scripts/baixar_perfil_idade_secao.py).

Padronização direta: a taxa "esperada" de um grupo é a taxa das demais seções da mesma célula
(UF/município × quinto nacional de % 60+ × quinto nacional de % baixa escolaridade), ponderada
pelos habilitados do grupo; células de referência com menos de 300 habilitados são descartadas.

Descritivo: diferenças não identificam causa e não são indício de irregularidade.
"""
from __future__ import annotations

import duckdb
import pandas as pd

from .config import PROCESSADOS, RESULTADOS

PASTA = RESULTADOS / "comparativo"
FONTES = {2022: (PROCESSADOS / "secoes_bu_2022.parquet", PROCESSADOS / "secoes_bu_2022.parquet"),
          2026: (PROCESSADOS / "secoes_bu_2026.parquet", PROCESSADOS / "secoes_oficiais_2026_2t.parquet")}
LIMIAR = 0.8
MIN_REF = 300


def _view(con, nome, src, turno):
    con.execute(f"""CREATE OR REPLACE VIEW {nome} AS SELECT uf, cd_municipio m, nr_zona z, nr_secao s, votos_nominais v,
      list_max(map_values(votos_candidato)) mx,
      map_keys(votos_candidato)[list_position(map_values(votos_candidato), list_max(map_values(votos_candidato)))] lider
      FROM '{src}' WHERE turno = {turno}""")


def _base(con, ano: int):
    s1, s2 = FONTES[ano]
    _view(con, "a", s1, 1)
    _view(con, "b", s2, 2)
    con.execute(f"""CREATE OR REPLACE TABLE grp AS SELECT uf, m, z, s,
        CASE WHEN a.v > 0 AND b.v > 0 AND a.mx > {LIMIAR} * a.v AND b.mx > {LIMIAR} * b.v AND a.lider = b.lider
             THEN 'conc_' || b.lider ELSE 'demais' END grupo
      FROM a JOIN b USING (uf, m, z, s)""")
    con.execute(f"""CREATE OR REPLACE TABLE lg AS SELECT uf, cd_municipio m, nr_zona z, nr_secao s, n_habilitados h,
        hab_biometrica bio, hab_manual_apos_falha man, hab_sem_biometria sem
      FROM read_parquet('{PROCESSADOS}/logs/{ano}_2t_*.parquet', union_by_name=true)
      WHERE tem_log AND uf <> 'ZZ' AND n_habilitados > 0""")
    con.execute(f"""CREATE OR REPLACE TABLE pf AS SELECT uf, CD_MUNICIPIO m, NR_ZONA z, NR_SECAO s, eleitores,
        100.0 * ("60_69" + "70_mais") / eleitores p60, 100.0 * "70_mais" / eleitores p70,
        100.0 * baixa_escolaridade / eleitores pbaixa
      FROM read_parquet('{PROCESSADOS}/tabelas/perfil_idade_secao/{ano}_*.parquet', union_by_name=true)
      WHERE eleitores > 0""")
    con.execute("""CREATE OR REPLACE TABLE j AS SELECT g.grupo, l.*, p.* EXCLUDE (uf, m, z, s),
        ntile(5) OVER (ORDER BY p.p60) qa, ntile(5) OVER (ORDER BY p.pbaixa) qe
      FROM lg l JOIN grp g USING (uf, m, z, s) JOIN pf p USING (uf, m, z, s)""")


def executar() -> dict:
    PASTA.mkdir(parents=True, exist_ok=True)
    perfil, gradiente, padron = [], [], []
    con = duckdb.connect()
    con.execute("SET memory_limit='6GB'")
    for ano in FONTES:
        _base(con, ano)
        cob = con.execute("SELECT (SELECT count(*) FROM lg), (SELECT count(*) FROM j)").fetchone()
        p = con.execute("""SELECT grupo, count(*) secoes, sum(h) habilitados,
            round(sum(eleitores * p60) / sum(eleitores), 2) pct_60_mais,
            round(sum(eleitores * p70) / sum(eleitores), 2) pct_70_mais,
            round(sum(eleitores * pbaixa) / sum(eleitores), 2) pct_baixa_escolaridade,
            round(100.0 * sum(bio) / sum(h), 2) pct_biometria,
            round(100.0 * sum(man) / sum(h), 2) pct_falha_liberacao_manual,
            round(100.0 * sum(sem) / sum(h), 2) pct_sem_biometria_cadastrada
          FROM j GROUP BY 1 ORDER BY 1""").df()
        p.insert(0, "ano", ano)
        p["secoes_com_log"], p["secoes_cruzadas"] = cob
        perfil.append(p)
        for var, rot in (("p60", "pct_60_mais"), ("pbaixa", "pct_baixa_escolaridade")):
            g = con.execute(f"""WITH q AS (SELECT *, ntile(5) OVER (ORDER BY {var}) qi FROM j)
                SELECT qi quinto, round(min({var}), 1) de_pct, round(max({var}), 1) ate_pct, count(*) secoes,
                  round(100.0 * sum(man) / sum(h), 2) pct_falha_liberacao_manual
                FROM q GROUP BY 1 ORDER BY 1""").df()
            g.insert(0, "variavel", rot)
            g.insert(0, "ano", ano)
            gradiente.append(g)
        for nome, cel in (("mesma UF + idade + escolaridade", "uf, qa, qe"), ("mesmo município", "uf, m"),
                          ("mesmo município + idade + escolaridade", "uf, m, qa, qe")):
            d = con.execute(f"""WITH ref AS (SELECT {cel}, sum(man) / sum(h) r FROM j WHERE grupo = 'demais'
                                  GROUP BY ALL HAVING sum(h) >= {MIN_REF})
                SELECT grupo, count(*) secoes_com_referencia, round(100.0 * sum(man) / sum(h), 2) observado,
                  round(100.0 * sum(h * r) / sum(h), 2) esperado,
                  round(100.0 * sum(man) / sum(h) - 100.0 * sum(h * r) / sum(h), 2) excesso_pp
                FROM j JOIN ref USING ({cel}) WHERE grupo <> 'demais' GROUP BY 1 ORDER BY 1""").df()
            d.insert(0, "comparacao", nome)
            d.insert(0, "ano", ano)
            padron.append(d)
    con.close()
    pd.concat(perfil).to_csv(PASTA / "biometria_concentracao_perfil.csv", index=False)
    pd.concat(gradiente).to_csv(PASTA / "biometria_gradiente_idade_escolaridade.csv", index=False)
    pd.concat(padron).to_csv(PASTA / "biometria_concentracao_padronizada.csv", index=False)
    return {"anos": list(FONTES)}


# ---------------------------------------------------------------- abstenção por faixa etária
GRUPOS_IDADE = [(16, 17, "16_17"), (18, 69, "18_69"), (70, 79, "70_79"), (80, 999, "80_mais")]


def abstencao_idade() -> pd.DataFrame:
    """Abstenção por faixa etária e turno (Perfil do comparecimento e abstenção, TSE).
    Faixa não informada (código -3) fica em 'nao_informada', nunca somada a outra faixa."""
    t = pd.read_parquet(PROCESSADOS / "tabelas" / "comparecimento_faixa_etaria_municipio.parquet")
    lim = t.CD_FAIXA_ETARIA // 100

    def grupo(i):
        for a, b, rot in GRUPOS_IDADE:
            if a <= i <= b:
                return rot
        return "nao_informada"
    t["grupo"] = lim.map(grupo)
    saidas = []
    for nivel, chave in (("BR", ["ANO", "NR_TURNO"]), ("UF", ["ANO", "NR_TURNO", "SG_UF"])):
        for col, nome in (("grupo", "grupo_idade"), ("DS_FAIXA_ETARIA", "faixa_etaria")):
            g = t.groupby(chave + [col])[["QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCAO"]].sum().reset_index()
            g = g.rename(columns={col: "faixa"})
            g["tipo_faixa"], g["abrangencia"] = nome, nivel
            if nivel == "BR":
                g["SG_UF"] = "BR"
            g["pct_abstencao"] = (100 * g.QT_ABSTENCAO / g.QT_APTOS).round(3)
            saidas.append(g)
    d = pd.concat(saidas)[["ANO", "NR_TURNO", "abrangencia", "SG_UF", "tipo_faixa", "faixa", "QT_APTOS",
                           "QT_COMPARECIMENTO", "QT_ABSTENCAO", "pct_abstencao"]]
    d.columns = ["ano", "turno", "abrangencia", "uf", "tipo_faixa", "faixa", "aptos", "comparecimento",
                 "abstencao", "pct_abstencao"]
    d = d.sort_values(["ano", "turno", "abrangencia", "uf", "tipo_faixa", "faixa"])
    d.to_csv(PASTA / "abstencao_faixa_etaria.csv", index=False)
    return d
