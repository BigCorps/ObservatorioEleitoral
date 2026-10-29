"""2º turno de 2026: votação por horário de voto e de encerramento da seção.

Grupos (cada seção conta uma vez por grupo; hora de Brasília no Brasil, hora local no exterior):
  A  pelo menos um voto após 17h00:00   (votos_apos_17h > 0; voto com hora > 61.200 s)
  B  pelo menos um voto após 19h00:00   (votos_apos_19h > 0; > 68.400 s)
  C  primeiro "Inicio do Encerramento" após 17h00:00 (encerramento_brt > 61.200 s)
  D  primeiro "Inicio do Encerramento" após 19h00:00 (encerramento_brt > 68.400 s)
"Último voto", "início do encerramento" e "geração do BU" são campos distintos do log
(ultimo_voto_brt, encerramento_brt, gera_bu_brt); só o segundo define C e D.

Votos por candidato, brancos, nulos, aptos e comparecimento: resultado oficial por seção
(Detalhe + Votação por seção, `secoes_oficiais_2026_2t.parquet`). Horários: log da urna
(`indicadores_temporais_2026.parquet` e `logs/2026_2t_*.parquet`).

O voto é secreto: nada aqui associa candidato a horário de voto. As comparações são entre
SEÇÕES (o resultado da seção inteira), nunca entre votos.
"""
from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd

from .config import PROCESSADOS, RESULTADOS
from .fusos import sql_desloc_brt

SAIDA = RESULTADOS / "2026"
H17, H19 = 61200, 68400
# Recortes por minuto, contíguos, em segundos desde a meia-noite (fim inclusivo)
RECORTES = [("ate_17h00", None, 61259, "até 17h00:59"),
            ("17h01_17h15", 61260, 62159, "17h01:00–17h15:59"),
            ("17h16_18h59", 62160, 68399, "17h16:00–18h59:59"),
            ("a_partir_19h00", 68400, None, "a partir de 19h00:00")]
GRUPOS = {"A": ("votos_apos_17h > 0", "Seções com pelo menos um voto após 17h"),
          "B": ("votos_apos_19h > 0", "Seções com pelo menos um voto após 19h"),
          "C": (f"encerramento_brt > {H17}", "Início do encerramento após 17h"),
          "D": (f"encerramento_brt > {H19}", "Início do encerramento após 19h")}


def _con():
    con = duckdb.connect()
    con.execute("SET memory_limit='6GB'")
    con.execute(f"""CREATE TABLE ofic AS SELECT uf, cd_municipio, nr_zona, nr_secao, nr_local_votacao,
        qt_aptos aptos, qt_comparecimento comparecimento, coalesce(votos_candidato[13], 0) v13,
        coalesce(votos_candidato[22], 0) v22, votos_brancos brancos, votos_nulos nulos, votos_nominais validos
      FROM '{PROCESSADOS}/secoes_oficiais_2026_2t.parquet'""")
    con.execute(f"""CREATE TABLE tmp AS SELECT uf, cd_municipio, nr_zona, nr_secao, votos_apos_17h, votos_apos_19h,
        encerramento_brt, ultimo_voto_brt, gera_bu_brt, n_votos_computados
      FROM '{PROCESSADOS}/indicadores_temporais_2026.parquet' WHERE turno = 2""")
    con.execute(f"""CREATE TABLE trn AS SELECT uf, cd_municipio, nr_zona, nr_secao, aptos_1t, comp_1t, validos_1t,
        l_1t, b_1t FROM '{PROCESSADOS}/secoes_turnos_2026.parquet'""")
    con.execute("""CREATE TABLE base AS SELECT o.*, t.* EXCLUDE (uf, cd_municipio, nr_zona, nr_secao),
        r.* EXCLUDE (uf, cd_municipio, nr_zona, nr_secao),
        CASE WHEN o.uf = 'ZZ' THEN 'Exterior (hora local)' ELSE 'Brasil (hora de Brasília)' END abrangencia
      FROM ofic o JOIN tmp t USING (uf, cd_municipio, nr_zona, nr_secao)
      LEFT JOIN trn r USING (uf, cd_municipio, nr_zona, nr_secao)""")
    return con


def _agregar(con, chave: str) -> pd.DataFrame:
    partes = []
    for g, (cond, desc) in GRUPOS.items():
        d = con.execute(f"""SELECT {chave}, '{g}' grupo, '{desc}' descricao, count(*) secoes,
            count(DISTINCT (uf, cd_municipio, nr_zona, nr_secao)) secoes_distintas,
            sum(aptos) aptos, sum(comparecimento) comparecimento, sum(v13) votos_13, sum(v22) votos_22,
            sum(brancos) brancos, sum(nulos) nulos, sum(validos) validos,
            round(100.0 * sum(v13) / sum(validos), 3) pct_validos_13, round(100.0 * sum(v22) / sum(validos), 3) pct_validos_22,
            sum(votos_apos_17h) votos_registrados_apos_17h, sum(votos_apos_19h) votos_registrados_apos_19h,
            sum(comparecimento) - sum(v13) - sum(v22) - sum(brancos) - sum(nulos) residuo_soma
          FROM base WHERE {cond} GROUP BY ALL ORDER BY ALL""").df()
        partes.append(d)
    return pd.concat(partes, ignore_index=True)


def _recortes(con) -> pd.DataFrame:
    lista = sorted(str(p) for p in (PROCESSADOS / "logs").glob("2026_2t_*.parquet") if "_amostra" not in p.name)
    con.execute(f"""CREATE TABLE v AS SELECT uf, unnest(votos_s) + {sql_desloc_brt()} t
      FROM read_parquet({lista}, union_by_name=true) WHERE tem_log""")
    casos = []
    for nome, ini, fim, rot in RECORTES:
        c = " AND ".join(x for x in ((f"t >= {ini}" if ini is not None else ""), (f"t <= {fim}" if fim is not None else "")) if x)
        casos.append(f"count(*) FILTER ({c}) AS \"{nome}\"")
    d = con.execute(f"""SELECT CASE WHEN uf = 'ZZ' THEN 'Exterior (hora local)' ELSE 'Brasil (hora de Brasília)' END abrangencia,
        count(*) total, {', '.join(casos)},
        count(*) FILTER (t = {H17}) exatamente_17h00_00, count(*) FILTER (t > {H17} AND t <= 61259) de_17h00_01_a_17h00_59,
        count(*) FILTER (t > {H17}) apos_17h00_00, count(*) FILTER (t >= {H17}) a_partir_17h00_00,
        count(*) FILTER (t > {H19}) apos_19h00_00
      FROM v GROUP BY 1 ORDER BY 1""").df()
    return d


def _pareado(con) -> pd.DataFrame:
    """Diferença de % do 13 (2º turno) entre seções 'tardias' e 'cedo' dentro do mesmo local/município,
    sem e com controles (FWL: regressão ponderada após retirar a média do local/município)."""
    df = con.execute(f"""SELECT uf, cd_municipio, nr_zona, nr_local_votacao, nr_secao, validos, aptos, comparecimento,
        100.0 * v13 / validos s13, 100.0 * comparecimento / aptos comp_pct,
        CASE WHEN validos_1t > 0 THEN 100.0 * l_1t / validos_1t END s13_1t,
        (encerramento_brt > {H19})::INT d_tarde, (encerramento_brt > 62100)::INT e_tarde,
        (votos_apos_17h > 0)::INT a_tarde
      FROM base WHERE uf <> 'ZZ' AND validos >= 50 AND aptos > 0""").df()
    df = df.dropna(subset=["s13_1t"])
    df["log_aptos"] = np.log(df.aptos)
    linhas = []
    nomes = {"a_tarde": "A (voto após 17h)", "d_tarde": "D (encerramento após 19h)",
             "e_tarde": "encerramento após 17h15 (auxiliar)"}
    for grp in ("a_tarde", "d_tarde", "e_tarde"):
        for nivel, cols in (("mesmo local de votação", ["uf", "cd_municipio", "nr_zona", "nr_local_votacao"]),
                            ("mesmo município", ["uf", "cd_municipio"])):
            key = df[cols].astype(str).agg("|".join, axis=1)
            mix = df.groupby(key)[grp].transform(lambda s: 0 < s.mean() < 1)
            d = df[mix].copy()
            k = key[mix]
            if len(d) < 30:
                continue
            w = d.validos.to_numpy(float)
            for controles in ([], ["s13_1t", "comp_pct", "log_aptos"]):
                cols_x = [grp] + controles
                Y = d["s13"].to_numpy(float)
                X = d[cols_x].to_numpy(float)
                # retira a média ponderada de cada célula (efeito fixo)
                wg = pd.Series(w, index=d.index).groupby(k).transform("sum").to_numpy()
                ym = pd.Series(Y * w, index=d.index).groupby(k).transform("sum").to_numpy() / wg
                Xm = np.column_stack([pd.Series(X[:, j] * w, index=d.index).groupby(k).transform("sum").to_numpy() / wg
                                      for j in range(X.shape[1])])
                yt, Xt = Y - ym, X - Xm
                sw = np.sqrt(w)
                beta, *_ = np.linalg.lstsq(Xt * sw[:, None], yt * sw, rcond=None)
                # erro-padrão robusto agrupado pela célula
                resid = (yt - Xt @ beta) * sw
                Xs = Xt * sw[:, None]
                bread = np.linalg.pinv(Xs.T @ Xs)
                sc = pd.DataFrame(Xs * resid[:, None]).groupby(k.to_numpy()).sum().to_numpy()
                V = bread @ (sc.T @ sc) @ bread
                linhas.append({"grupo_tardio": nomes[grp],
                               "comparacao": nivel, "controles": ", ".join(controles) or "nenhum",
                               "celulas_com_tardias_e_cedo": int(k.nunique()), "secoes": len(d),
                               "secoes_tardias": int(d[grp].sum()),
                               "dif_pct_13_pp": round(beta[0], 3), "erro_padrao_pp": round(float(np.sqrt(V[0, 0])), 3),
                               "ic95_inf": round(beta[0] - 1.96 * float(np.sqrt(V[0, 0])), 3),
                               "ic95_sup": round(beta[0] + 1.96 * float(np.sqrt(V[0, 0])), 3)})
    return pd.DataFrame(linhas)


def executar() -> dict:
    con = _con()
    br = _agregar(con, "abrangencia")
    uf = _agregar(con, "abrangencia, uf")
    rec = _recortes(con)
    par = _pareado(con)
    # todas as seções, para referência
    tot = con.execute("""SELECT abrangencia, count(*) secoes, sum(aptos) aptos, sum(comparecimento) comparecimento,
        sum(v13) votos_13, sum(v22) votos_22, sum(brancos) brancos, sum(nulos) nulos,
        round(100.0 * sum(v13) / sum(validos), 3) pct_validos_13, round(100.0 * sum(v22) / sum(validos), 3) pct_validos_22,
        sum(votos_apos_17h) votos_registrados_apos_17h, sum(votos_apos_19h) votos_registrados_apos_19h
      FROM base GROUP BY 1 ORDER BY 1""").df()
    sem_log = con.execute("SELECT count(*) FROM ofic WHERE (uf, cd_municipio, nr_zona, nr_secao) NOT IN (SELECT (uf, cd_municipio, nr_zona, nr_secao) FROM tmp)").fetchone()[0]
    con.close()
    br.to_csv(SAIDA / "horario_grupos_nacional.csv", index=False)
    uf.to_csv(SAIDA / "horario_grupos_uf.csv", index=False)
    rec.to_csv(SAIDA / "horario_recortes_votos.csv", index=False)
    par.to_csv(SAIDA / "horario_comparacao_pareada.csv", index=False)
    tot.to_csv(SAIDA / "horario_todas_secoes.csv", index=False)
    return {"nacional": br, "uf": uf, "recortes": rec, "pareado": par, "todas": tot, "secoes_sem_log": sem_log}
