"""Teste F — identificação biométrica e alternativa.

Fontes e definições (não se presume que anos ou arquivos usem as mesmas categorias):
- Cadastro: perfil do eleitorado por seção (QT_ELEITORES_BIOMETRIA / QT_ELEITORES_PERFIL).
- BU (CSV): QT_ELEITORES_BIOMETRIA_NH (2022) / QT_ELEI_BIOM_SEM_HABILITACAO (2026) =
  "eleitores com biometria, mas que não foram habilitados por meio dela".
- Log: modalidade de cada eleitor que votou (ver logs.py): biométrica; sem biometria
  cadastrada; manual após falha biométrica; sem etapa biométrica (exterior).
Habilitação alternativa é procedimento regular (Res. 23.669/2021, arts. 114-115;
Res. 23.751/2026, arts. 134-135) e não indica, por si, irregularidade.
Quantis de duração são aproximados (t-digest do DuckDB) por causa do volume (~250 milhões de votos).
"""
from __future__ import annotations

import duckdb

from .config import logs_concluidos, PROCESSADOS, RESULTADOS
from .fusos import sql_desloc_brt

T = PROCESSADOS / "tabelas"


def executar(ano: int) -> dict:
    con = duckdb.connect()
    con.execute("SET enable_progress_bar=false")
    con.execute("SET memory_limit='6GB'")
    con.execute(f"SET temp_directory='{PROCESSADOS}/duckdb_tmp'")
    pasta = RESULTADOS / str(ano)
    pasta.mkdir(parents=True, exist_ok=True)
    con.execute(f"""CREATE VIEW lg AS SELECT turno, uf, cd_municipio, nr_zona, nr_secao, log_modelos,
        n_votos_computados, {sql_desloc_brt()} desloc, hab_s, hab_mod, dur_voto, dur_voto_mod
      FROM read_parquet({logs_concluidos(ano)}, union_by_name=true) WHERE tem_log""")
    cols = ("turno, uf, cd_municipio, nr_zona, nr_secao, qt_aptos, qt_comparecimento, qt_eleitores_biometria_nh")
    base = f"SELECT {cols} FROM '{PROCESSADOS}/secoes_bu_{ano}.parquet'"
    turnos_bu = {r[0] for r in con.execute(f"SELECT DISTINCT turno FROM '{PROCESSADOS}/secoes_bu_{ano}.parquet'").fetchall()}
    for t in (1, 2):
        of = PROCESSADOS / f"secoes_oficiais_{ano}_{t}t.parquet"
        if t not in turnos_bu and of.exists():  # turno sem BU em CSV: tabela oficial (sem campo de biometria)
            base += (f" UNION ALL SELECT turno, uf, cd_municipio, nr_zona, nr_secao, qt_aptos, qt_comparecimento, "
                     f"NULL::INT FROM '{of}'")
    con.execute(f"CREATE VIEW bw AS {base}")
    # BU binário: detalhamento por forma de habilitação (formato v2, 2026)
    try:
        con.execute(f"""CREATE VIEW bub AS SELECT
            CAST(regexp_extract(filename, '_(\\d)t_', 1) AS INT) turno,
            regexp_extract(filename, '_([A-Z]{{2}})\\.parquet', 1) uf,
            sum(bu_qtd_hab_biometria) bu_bin_habilitados_biometria,
            sum(bu_qtd_hab_biografia) bu_bin_habilitados_biografia,
            sum(bu_qtd_sem_biometria) bu_bin_sem_biometria_cadastrada,
            count(bu_qtd_hab_biometria) bu_bin_secoes
          FROM read_parquet({logs_concluidos(ano, 'bu')}, union_by_name=true, filename=true) GROUP BY ALL""")
        tem_bub = "bu_qtd_hab_biometria" in {r[0] for r in con.execute(
            f"DESCRIBE SELECT * FROM read_parquet({logs_concluidos(ano, 'bu')}, union_by_name=true)").fetchall()}
    except Exception:
        tem_bub = False
    tem_perfil = bool(list((T / "perfil_secao").glob(f"{ano}_*.parquet"))) if (T / "perfil_secao").exists() else False
    if tem_perfil:
        con.execute(f"""CREATE VIEW pf AS SELECT SG_UF uf, CAST(CD_MUNICIPIO AS INT) cd_municipio,
            CAST(NR_ZONA AS INT) nr_zona, CAST(NR_SECAO AS INT) nr_secao, qt_eleitores, qt_eleitores_biometria
          FROM read_parquet('{T}/perfil_secao/{ano}_*.parquet', union_by_name=true)""")
    # 1) Por UF e turno: cadastro x uso efetivo (BU) x modalidade no log
    perfil_sel = ("sum(p.qt_eleitores) eleitores_cadastro, sum(p.qt_eleitores_biometria) com_biometria_cadastro, "
                  "round(100.0*sum(p.qt_eleitores_biometria)/sum(p.qt_eleitores),3) pct_biometria_cadastro,") if tem_perfil else ""
    perfil_join = "LEFT JOIN pf p USING (uf, cd_municipio, nr_zona, nr_secao)" if tem_perfil else ""
    con.execute(f"""COPY (
      WITH lm AS (SELECT turno, uf, cd_municipio, nr_zona, nr_secao,
          len(list_filter(dur_voto_mod, lambda x: x=1)) v_bio, len(list_filter(dur_voto_mod, lambda x: x=2)) v_sembio,
          len(list_filter(dur_voto_mod, lambda x: x=3)) v_manual, len(list_filter(dur_voto_mod, lambda x: x=0)) v_semetapa
        FROM lg)
      SELECT b.turno, b.uf, count(*) secoes, sum(b.qt_aptos) aptos, sum(b.qt_comparecimento) comparecimento,
        {perfil_sel}
        sum(b.qt_eleitores_biometria_nh) FILTER (WHERE b.qt_eleitores_biometria_nh >= 0) bu_biometria_nao_habilitados,
        round(100.0*sum(b.qt_eleitores_biometria_nh) FILTER (WHERE b.qt_eleitores_biometria_nh >= 0)/sum(b.qt_comparecimento),3) pct_bu_nh_sobre_comparecimento,
        sum(l.v_bio) log_votantes_biometria, sum(l.v_sembio) log_votantes_sem_biometria_cadastrada,
        sum(l.v_manual) log_votantes_manual_apos_falha, sum(l.v_semetapa) log_votantes_sem_etapa_biometrica,
        round(100.0*sum(l.v_bio)/nullif(sum(l.v_bio+l.v_sembio+l.v_manual+l.v_semetapa),0),3) pct_log_biometria,
        round(100.0*sum(l.v_manual)/nullif(sum(l.v_bio+l.v_sembio+l.v_manual+l.v_semetapa),0),3) pct_log_manual_apos_falha,
        round(100.0*sum(l.v_sembio)/nullif(sum(l.v_bio+l.v_sembio+l.v_manual+l.v_semetapa),0),3) pct_log_sem_biometria,
        count(l.nr_secao) secoes_com_log
      FROM bw b {perfil_join} LEFT JOIN lm l USING (turno, uf, cd_municipio, nr_zona, nr_secao)
      GROUP BY ALL ORDER BY 1, 2) TO '{pasta}/biometria_por_uf.csv' (HEADER)""")
    if tem_bub:
        import pandas as pd
        f = pasta / "biometria_por_uf.csv"
        d = pd.read_csv(f)
        b = con.execute("SELECT * FROM bub").df()
        d = d.merge(b, on=["turno", "uf"], how="left")
        tot = d[["bu_bin_habilitados_biometria", "bu_bin_habilitados_biografia", "bu_bin_sem_biometria_cadastrada"]].sum(axis=1)
        d["pct_bu_bin_biometria"] = (100 * d.bu_bin_habilitados_biometria / tot).round(3)
        d["pct_bu_bin_biografia"] = (100 * d.bu_bin_habilitados_biografia / tot).round(3)
        d["pct_bu_bin_sem_biometria"] = (100 * d.bu_bin_sem_biometria_cadastrada / tot).round(3)
        d.to_csv(f, index=False)
    # 2) Modalidade por hora (Brasília) — habilitações
    con.execute(f"""COPY (
      SELECT turno, CAST(floor((h + desloc)/3600) AS INT) hora_brasilia, m modalidade, count(*) habilitacoes
      FROM (SELECT turno, desloc, unnest(hab_s) h, unnest(hab_mod) m FROM lg WHERE uf <> 'ZZ') GROUP BY ALL ORDER BY ALL)
      TO '{pasta}/biometria_modalidade_por_hora.csv' (HEADER)""")
    # 3) Duração (habilitação -> voto) por modalidade e modelo de urna
    con.execute(f"""COPY (
      SELECT turno, log_modelos modelo, m modalidade, count(*) votos, approx_quantile(d, 0.5) mediana_s,
        approx_quantile(d, 0.1) p10_s, approx_quantile(d, 0.9) p90_s
      FROM (SELECT turno, log_modelos, unnest(dur_voto) d, unnest(dur_voto_mod) m FROM lg) GROUP BY ALL ORDER BY ALL)
      TO '{pasta}/biometria_duracao_por_modalidade_modelo.csv' (HEADER)""")
    # 4) Distribuição por seção do % de liberação manual (BU), para seções comparáveis
    con.execute(f"""COPY (
      SELECT turno, uf, CAST(least(floor(20.0*qt_eleitores_biometria_nh/qt_comparecimento), 19) * 5 AS INT) faixa_5pp_inicio,
        count(*) secoes
      FROM bw WHERE qt_comparecimento > 0 AND qt_eleitores_biometria_nh >= 0 AND uf <> 'ZZ'
      GROUP BY ALL ORDER BY ALL) TO '{pasta}/biometria_distribuicao_nh_secao.csv' (HEADER)""")
    r = con.execute(f"SELECT * FROM read_csv('{pasta}/biometria_por_uf.csv') LIMIT 3").df()
    con.close()
    return {"ok": True, "amostra": r}
