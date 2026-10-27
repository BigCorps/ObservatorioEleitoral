"""Confronta a extração própria do 2º turno de 2026 com as pesquisas independentes.

Uso: python scripts/comparar_estudos_externos.py [caminho/secoes_logs_brasil.parquet]

Os números dos terceiros são tratados como afirmações a verificar, nunca como dado.
Saídas:
  resultados/2026/estudos_externos_2t.csv     Verificação | Nossa extração | Pesquisa independente | Diferença
  resultados/2026/agnoletto_secao_a_secao.csv concordância seção a seção (quando o parquet público é informado)
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from observatorio.fusos import sql_desloc_brt  # noqa: E402

LOGS = sorted((RAIZ / "dados/processados/logs").glob("2026_2t_*.parquet"))
SAIDA = RAIZ / "resultados/2026"
H17, H18, H19 = 17 * 3600, 18 * 3600, 19 * 3600


def nossa_extracao(con) -> dict:
    lista = [str(p) for p in LOGS if not p.stem.endswith("_amostra")]
    con.execute(f"""
    CREATE OR REPLACE VIEW s AS
      SELECT uf, cd_municipio, nr_zona, nr_secao, log_modelos, n_votos_computados, n_habilitados,
        hab_biometrica, hab_manual_apos_falha, hab_sem_biometria, votos_s, dur_voto, dur_voto_mod,
        t_primeiro_voto, t_ultimo_voto, t_inicio_encerramento_primeiro, {sql_desloc_brt()} AS desloc
      FROM read_parquet({lista}, union_by_name=true) WHERE tem_log""")
    con.execute(f"""
    CREATE OR REPLACE VIEW v AS
      SELECT *,
        len(list_filter(votos_s, lambda x: x + desloc > {H17})) a17,
        len(list_filter(votos_s, lambda x: x + desloc >= {H17})) a17ge,
        len(list_filter(votos_s, lambda x: x + desloc >= {H17} AND x + desloc < {H17} + 300)) a17_5min,
        len(list_filter(votos_s, lambda x: x + desloc > {H18})) a18,
        len(list_filter(votos_s, lambda x: x + desloc > {H19})) a19,
        CASE WHEN len(votos_s) = len(dur_voto_mod) THEN
          len(list_filter(list_zip(votos_s, dur_voto_mod), lambda z: z[1] + desloc > {H17} AND z[2] = 3)) END a17_manual
      FROM s""")
    q = lambda sql: con.execute(sql).fetchone()  # noqa: E731
    br = "uf <> 'ZZ'"
    r = {}
    r["secoes_com_log_total"], r["secoes_com_log_sem_zz"] = q(f"SELECT count(*), count(*) FILTER ({br}) FROM v")
    r["votos_log_sem_zz"], = q(f"SELECT sum(n_votos_computados) FROM v WHERE {br}")
    (r["votos_apos_17h"], r["votos_a_partir_17h"], r["votos_17h_17h05"], r["votos_apos_18h"], r["votos_apos_19h"],
     r["secoes_sem_voto_apos_17h"], r["secoes_com_voto_apos_17h"]) = q(
        f"SELECT sum(a17), sum(a17ge), sum(a17_5min), sum(a18), sum(a19), count(*) FILTER (a17 = 0),"
        f" count(*) FILTER (a17 > 0) FROM v WHERE {br}")
    r["votos_apos_17h_manual"], r["secoes_alinhadas_modalidade"], r["votos_apos_17h_secoes_alinhadas"] = q(
        f"SELECT sum(a17_manual), count(a17_manual), sum(a17) FILTER (a17_manual IS NOT NULL) FROM v WHERE {br}")
    r["secoes_encerradas_19h_ou_depois"], = q(
        f"SELECT count(*) FROM v WHERE {br} AND t_inicio_encerramento_primeiro + desloc >= {H19} - 300")
    r["mediana_duracao_voto_s"], = q(f"SELECT median(d) FROM (SELECT unnest(dur_voto) d FROM v WHERE {br})")
    r["pct_manual_por_modelo"] = con.execute(f"""
      SELECT log_modelos, round(100.0 * sum(hab_manual_apos_falha) / sum(n_habilitados), 1)
      FROM v WHERE {br} AND log_modelos IN ('UE2013','UE2015','UE2020','UE2022') GROUP BY 1 ORDER BY 1""").fetchall()
    r["habilitados"], r["bio"], r["manual"], r["sem_bio"] = q(
        f"SELECT sum(n_habilitados), sum(hab_biometrica), sum(hab_manual_apos_falha), sum(hab_sem_biometria) FROM v WHERE {br}")
    return r


# Afirmações publicadas (copiadas literalmente das fontes, ver docs/auditoria-estudos-externos.md)
CNN = {"urnas": 497_895, "votos_apos_17h": 34_330, "votos_17h_5min": 29_001, "votos_apos_18h": 1_993,
       "votos_apos_19h": 11, "urnas_sem_voto_apos_17h": 468_043}
AGN = {"urnas_sem_zz": 497_896, "votos_apos_fech": 31_060, "manual_apos_fech": 2_512, "urnas_19h": 7_577,
       "mediana_voto_s": 10, "manual_modelo": {"UE2013": 11.0, "UE2015": 9.8, "UE2020": 6.2, "UE2022": 6.2}}


def tabela(r: dict) -> pd.DataFrame:
    L = []

    def add(verif, nosso, ext, fonte, nota=""):
        dif = (nosso - ext) if isinstance(nosso, (int, float)) and isinstance(ext, (int, float)) else None
        L.append({"verificacao": verif, "fonte_externa": fonte, "nossa_extracao": nosso,
                  "pesquisa_independente": ext, "diferenca": dif, "nota": nota})
    add("Seções com log processadas (sem exterior)", r["secoes_com_log_sem_zz"], CNN["urnas"], "CNN/setup.news")
    add("Seções com log processadas (sem exterior)", r["secoes_com_log_sem_zz"], AGN["urnas_sem_zz"], "Agnoletto")
    add("Votos após 17h de Brasília (sem exterior)", r["votos_apos_17h"], CNN["votos_apos_17h"], "CNN/setup.news",
        "CNN não informa fuso nem se 17:00:00 conta; a partir de 17:00:00 = " + str(r["votos_a_partir_17h"]))
    add("Votos a partir de 17:00:00 de Brasília (sem exterior)", r["votos_a_partir_17h"], CNN["votos_apos_17h"],
        "CNN/setup.news", "mesma definição que reproduz o número da CNN (inclui o segundo 17:00:00)")
    add("Votos após o encerramento previsto (17h Brasília)", r["votos_apos_17h"], AGN["votos_apos_fech"], "Agnoletto",
        "Agnoletto usa o horário local previsto por seção")
    add("Votos entre 17h00 e 17h05", r["votos_17h_17h05"], CNN["votos_17h_5min"], "CNN/setup.news")
    add("Votos após 18h de Brasília", r["votos_apos_18h"], CNN["votos_apos_18h"], "CNN/setup.news",
        "inclui seções prorrogadas até 19h por decisão do STF")
    add("Votos após 19h de Brasília", r["votos_apos_19h"], CNN["votos_apos_19h"], "CNN/setup.news")
    add("Seções sem voto após 17h", r["secoes_sem_voto_apos_17h"], CNN["urnas_sem_voto_apos_17h"], "CNN/setup.news")
    add("Votos manuais após 17h (seções com modalidade alinhada)", r["votos_apos_17h_manual"], AGN["manual_apos_fech"],
        "Agnoletto", f"{r['secoes_alinhadas_modalidade']} seções com modalidade por voto alinhada")
    add("Seções com início de encerramento a partir de 18h55", r["secoes_encerradas_19h_ou_depois"], AGN["urnas_19h"],
        "Agnoletto")
    add("Mediana da duração do voto (s)", r["mediana_duracao_voto_s"], AGN["mediana_voto_s"], "Agnoletto")
    for m, pct in r["pct_manual_por_modelo"]:
        add(f"% habilitação manual após falha biométrica · {m}", pct, AGN["manual_modelo"].get(m), "Agnoletto")
    add("Arquivos e resultados publicados", None, None, "kakaroto.dev",
        "não reproduzido: site fora do ar (HTTP 530 em 26–27/10/2026) e sem código público")
    return pd.DataFrame(L)


def secao_a_secao(con, caminho: Path) -> pd.DataFrame:
    con.execute(f"CREATE OR REPLACE VIEW a AS SELECT * FROM read_parquet('{caminho}')")
    campos = [("votos", "n_votos_computados", "log_votos"), ("habilitados", "n_habilitados", "log_habilitados"),
              ("biometria", "hab_biometrica", "log_bio"), ("manual", "hab_manual_apos_falha", "log_manual"),
              ("sem_biometria", "hab_sem_biometria", "log_sem_biometria"),
              ("primeiro_voto_local_s", "t_primeiro_voto", "(epoch(primeiro_voto)::BIGINT % 86400)"),
              ("ultimo_voto_local_s", "t_ultimo_voto", "(epoch(ultimo_voto)::BIGINT % 86400)")]
    sel = ", ".join(f"count(*) FILTER (v.{n} IS NOT DISTINCT FROM {e}) AS {c}_iguais,"
                    f" sum(abs(v.{n} - {e})) AS {c}_soma_abs_dif" for c, n, e in campos)
    con.execute(f"""COPY (SELECT v.uf, v.cd_municipio, v.nr_zona, v.nr_secao, v.n_votos_computados AS votos_nossa,
        a.log_votos AS votos_agnoletto, o.qt_comparecimento AS comparecimento_oficial
      FROM s v JOIN a ON v.uf = a.SG_UF AND v.cd_municipio = a.CD_MUNICIPIO AND v.nr_zona = a.NR_ZONA AND v.nr_secao = a.NR_SECAO
      LEFT JOIN '{RAIZ}/dados/processados/secoes_oficiais_2026_2t.parquet' o ON o.uf = v.uf AND o.cd_municipio = v.cd_municipio
        AND o.nr_zona = v.nr_zona AND o.nr_secao = v.nr_secao
      WHERE v.n_votos_computados IS DISTINCT FROM a.log_votos) TO '{SAIDA}/agnoletto_secoes_votos_diferentes.csv' (HEADER)""")
    df = con.execute(f"""
      WITH j AS (SELECT * FROM s v FULL JOIN a ON v.uf = a.SG_UF AND v.cd_municipio = a.CD_MUNICIPIO
                 AND v.nr_zona = a.NR_ZONA AND v.nr_secao = a.NR_SECAO)
      SELECT count(*) FILTER (v.uf IS NOT NULL AND SG_UF IS NOT NULL) AS secoes_em_ambos,
        count(*) FILTER (SG_UF IS NULL AND v.uf <> 'ZZ') AS so_nossa_sem_zz,
        count(*) FILTER (SG_UF IS NULL AND v.uf = 'ZZ') AS so_nossa_zz,
        count(*) FILTER (v.uf IS NULL) AS so_agnoletto,
        {sel}
      FROM j v""").df()
    return df.T.rename(columns={0: "valor"})


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    r = nossa_extracao(con)
    t = tabela(r)
    t.to_csv(SAIDA / "estudos_externos_2t.csv", index=False)
    print(t.to_string())
    print({k: v for k, v in r.items() if k not in ("pct_manual_por_modelo",)})
    if len(sys.argv) > 1 and Path(sys.argv[1]).exists():
        s = secao_a_secao(con, Path(sys.argv[1]))
        s.to_csv(SAIDA / "agnoletto_secao_a_secao.csv")
        print(s.to_string())


if __name__ == "__main__":
    main()
