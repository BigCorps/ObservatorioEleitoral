"""Biometria nas seções com votos após 17h: 2022/2026, dois turnos.

Usa somente Parquets locais já processados: logs, indicadores temporais,
BU em CSV e Detalhe por seção. Não faz downloads nem atribui horário a candidato.

Produz:
- biometria_secoes_tardias_por_uf.csv: seções tardias versus outras no mesmo ano
  (votos após 17h no SEGUNDO TURNO definem grupo, para ambos os turnos).
- biometria_secoes_tardias_mesmas_secoes.csv: coortes 2022×2026 em seção
  correspondida (mesma chave + local + aptos em ±10%).
- biometria_secoes_tardias_pareado.csv: efeitos no mesmo local/município com
  controles de 1º turno, comparecimento, aptos e sem cadastro biométrico.

Uso: python -m observatorio.biometria_secoes_tardias
"""
from __future__ import annotations

from pathlib import Path
import duckdb
import numpy as np
import pandas as pd

from .config import PROCESSADOS, RESULTADOS
from .fusos import sql_desloc_brt
from .horario_historico import _wls_fe, LOCAL

SAIDA = RESULTADOS / "comparativo"
H17 = 17 * 3600
KEY = "uf, cd_municipio, nr_zona, nr_secao"
METRICS = [
    "secoes", "habilitados", "classificados", "bio", "sem_cadastro",
    "manual_apos_falha", "desconhecidos",
    "habilitacoes_17mais", "manuais_17mais", "bio_17mais",
    "sem_cadastro_17mais", "votos_apos17",
    "bu_biometria_nao_habilitados",
]


def _prepare(con: duckdb.DuckDBPyConnection, year: int, turno: int) -> None:
    """Tabela temporária única por seção: separa falha de ausência de cadastro."""
    padrao = PROCESSADOS / "logs" / f"{year}_{turno}t_*.parquet"
    arquivos = sorted((PROCESSADOS / "logs").glob(f"{year}_{turno}t_*.parquet"))
    arquivos = [p for p in arquivos if "_amostra" not in p.name]
    indicadores = PROCESSADOS / f"indicadores_temporais_{year}.parquet"
    if not arquivos or not indicadores.exists():
        raise FileNotFoundError(f"Faltam logs/indicadores locais para {year}, turno {turno}: {padrao}")
    fontes = "[" + ", ".join("'" + str(p).replace("'", "''") + "'" for p in arquivos) + "]"
    des = sql_desloc_brt()
    # A classificação das modalidades vem de observatorio/logs.py:
    # 1 biométrica; 2 sem cadastro; 3 manual após falha; 0 não classificada.
    con.execute(f"""
      CREATE OR REPLACE TABLE s{year}_{turno} AS
      WITH log AS (
        SELECT {KEY}, n_habilitados, log_modelos, hab_biometrica,
          hab_manual_apos_falha, hab_sem_biometria, hab_s, hab_mod, {des} desloc
        FROM read_parquet({fontes}, union_by_name=true)
        WHERE tem_log AND uf <> 'ZZ'
      ), agg AS (
        SELECT {KEY}, log_modelos,
          coalesce(n_habilitados, 0) AS habilitados,
          coalesce(hab_biometrica, 0) AS bio,
          coalesce(hab_sem_biometria, 0) AS sem_cadastro,
          coalesce(hab_manual_apos_falha, 0) AS manual_apos_falha,
          len(list_filter(
            list_zip(hab_s, hab_mod), lambda x: x[1]+desloc >= {H17}
          )) habilitacoes_17mais,
          len(list_filter(
            list_zip(hab_s, hab_mod), lambda x: x[1]+desloc >= {H17} AND x[2]=1
          )) bio_17mais,
          len(list_filter(
            list_zip(hab_s, hab_mod), lambda x: x[1]+desloc >= {H17} AND x[2]=2
          )) sem_cadastro_17mais,
          len(list_filter(
            list_zip(hab_s, hab_mod), lambda x: x[1]+desloc >= {H17} AND x[2]=3
          )) manuais_17mais
        FROM log
      )
      SELECT a.*, a.bio+a.sem_cadastro+a.manual_apos_falha classificados,
        a.habilitados-a.bio-a.sem_cadastro-a.manual_apos_falha desconhecidos,
        coalesce(i.votos_apos_17h, 0) votos_apos17,
        CAST(coalesce(i.votos_apos_17h, 0) > 0 AS INTEGER) tardia
      FROM agg a JOIN
        (SELECT {KEY}, votos_apos_17h FROM '{indicadores}'
          WHERE turno = {turno} AND uf <> 'ZZ') i USING ({KEY})
    """)
    n, distinct = con.execute(f"""
      SELECT count(*), count(DISTINCT ({KEY})) FROM s{year}_{turno}
    """).fetchone()
    if n != distinct:
        raise AssertionError(f"Chaves duplicadas no log {year}/{turno}: {n-distinct}")
    anomalies = con.execute(f"""
      SELECT count(*) FROM s{year}_{turno}
      WHERE classificados < 0 OR desconhecidos < 0 OR habilitacoes_17mais > habilitados
        OR manuais_17mais > manual_apos_falha
    """).fetchone()[0]
    if anomalies:
        raise AssertionError(f"Modalidades ou horários inconsistentes {year}/{turno}: {anomalies}")


def _locations(con: duckdb.DuckDBPyConnection) -> None:
    for year in (2022, 2026):
        fonte = (PROCESSADOS / "secoes_bu_2022.parquet" if year == 2022
                 else PROCESSADOS / "secoes_oficiais_2026_2t.parquet")
        if not fonte.exists():
            raise FileNotFoundError(f"Falta tabela oficial: {fonte}")
        con.execute(f"""
          CREATE OR REPLACE TABLE loc{year} AS
          SELECT {KEY}, nr_local_votacao,
                 qt_aptos aptos, qt_comparecimento comparecimento
          FROM '{fonte}' WHERE turno=2 AND uf <> 'ZZ'
        """)
        dup = con.execute(f"""
          SELECT count(*)-count(DISTINCT ({KEY})) FROM loc{year}
        """).fetchone()[0]
        if dup:
            raise AssertionError(f"Localizações repetidas em {year}: {dup}")
    # BU: "com biometria, não habilitado por biometria"; difere de "sem
    # cadastro biométrico". Mantê-lo separado da modalidade registrada no log.
    for year in (2022, 2026):
        for turno in (1, 2):
            con.execute(f"""
              CREATE OR REPLACE TABLE bu{year}_{turno} AS
              SELECT {KEY}, qt_eleitores_biometria_nh
                     bu_biometria_nao_habilitados
              FROM '{PROCESSADOS}/secoes_bu_{year}.parquet'
              WHERE turno={turno} AND uf <> 'ZZ'
            """)


def _sumarizar(con: duckdb.DuckDBPyConnection, src: str, dims: str) -> pd.DataFrame:
    # Dois universos: todos os dados e Brasil (agregação real), nunca médias de percentuais UF.
    sel = f"""
      count(*) secoes, sum(habilitados) habilitados, sum(classificados) classificados,
      sum(bio) bio, sum(sem_cadastro) sem_cadastro,
      sum(manual_apos_falha) manual_apos_falha, sum(desconhecidos) desconhecidos,
      sum(habilitacoes_17mais) habilitacoes_17mais,
      sum(manuais_17mais) manuais_17mais, sum(bio_17mais) bio_17mais,
      sum(sem_cadastro_17mais) sem_cadastro_17mais,
      sum(votos_apos17) votos_apos17,
      sum(bu_biometria_nao_habilitados) bu_biometria_nao_habilitados
    """
    d = con.execute(f"""
       SELECT {dims}, {sel} FROM {src} GROUP BY ALL
       UNION ALL
       SELECT {dims.replace("uf,", "'BR' AS uf,")}, {sel}
       FROM {src} GROUP BY ALL
    """).df()
    # Denominadores de habilitação, não de votos de candidatos.
    d["pct_manual"] = (100*d.manual_apos_falha / d.classificados.replace(0, np.nan)).round(4)
    d["pct_sem_cadastro"] = (100*d.sem_cadastro / d.classificados.replace(0, np.nan)).round(4)
    d["pct_biometrica"] = (100*d.bio / d.classificados.replace(0, np.nan)).round(4)
    d["pct_manual_17mais"] = (100*d.manuais_17mais /
                             (d.manuais_17mais + d.bio_17mais + d.sem_cadastro_17mais)
                             .replace(0, np.nan)).round(4)
    return d


def _coortes(con: duckdb.DuckDBPyConnection) -> tuple[pd.DataFrame, pd.DataFrame]:
    # Grupo "tardia" é definido exclusivamente por VOTO COMPUTADO depois das
    # 17h no segundo turno. A modalidade biométrica é avaliada separadamente.
    frames = []
    for year in (2022, 2026):
        for turno in (1, 2):
            con.execute(f"""
              CREATE OR REPLACE VIEW e{year}_{turno} AS
              SELECT b.*, g.tardia tardia_2t,
                     coalesce(bu.bu_biometria_nao_habilitados, NULL::BIGINT)
                         bu_biometria_nao_habilitados
              FROM s{year}_{turno} b
              JOIN s{year}_2 g USING ({KEY})
              LEFT JOIN bu{year}_{turno} bu USING ({KEY})
            """)
            src = f"(SELECT {year} ano, {turno} turno, uf, tardia_2t, " + ", ".join(METRICS[1:]) + f" FROM e{year}_{turno})"
            # normaliza 'secoes' não é coluna de linha, agregado só
            d = _sumarizar(con, src, "ano, turno, uf, tardia_2t")
            frames.append(d)
    return pd.concat(frames, ignore_index=True), _matched(con)


def _matched(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    # Correspondência conservadora, replicando criterio de horario_historico.py
    con.execute(f"""
      CREATE OR REPLACE TABLE matches AS SELECT a.{KEY.replace(', ', ', a.')},
         a.tardia tarde22, b.tardia tarde26, d.nr_local_votacao local,
         o.nr_local_votacao local_2022, d.aptos aptos26, o.aptos aptos22,
         d.comparecimento comp26
      FROM s2022_2 a JOIN s2026_2 b USING ({KEY})
      JOIN loc2022 o USING ({KEY}) JOIN loc2026 d USING ({KEY})
      WHERE o.aptos > 0 AND d.aptos > 0
        AND o.nr_local_votacao=d.nr_local_votacao
        AND abs(o.aptos-d.aptos)*1.0/o.aptos <= 0.10
    """)
    data=[]
    for year in (2022,2026):
        for turno in (1,2):
            src=f"""(SELECT {year} ano, {turno} turno, s.*, m.tarde22, m.tarde26,
                      m.tarde22::VARCHAR || '_' || m.tarde26::VARCHAR transicao,
                      coalesce(bu.bu_biometria_nao_habilitados, NULL::BIGINT)
                         bu_biometria_nao_habilitados
                   FROM matches m JOIN s{year}_{turno} s USING ({KEY})
                   LEFT JOIN bu{year}_{turno} bu USING ({KEY}))"""
            d=_sumarizar(con,src,"ano, turno, uf, transicao")
            data.append(d)
    return pd.concat(data,ignore_index=True)


def _regressao(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    saida=[]
    for year in (2022,2026):
        d=con.execute(f"""
          SELECT b.{KEY.replace(', ', ', b.')}, o.nr_local_votacao,
            b.tardia AS grupo, b.habilitados, b.classificados AS peso,
            100.0*b.manual_apos_falha/nullif(b.classificados,0) y,
            100.0*b.sem_cadastro/nullif(b.classificados,0) sem_cad_pct,
            100.0*p.manual_apos_falha/nullif(p.classificados,0) manual_1t,
            100.0*o.comparecimento/nullif(o.aptos,0) comp_pct,
            ln(o.aptos) log_aptos
          FROM s{year}_2 b JOIN s{year}_1 p USING ({KEY})
          JOIN loc{year} o USING ({KEY})
          WHERE b.classificados > 0 AND p.classificados > 0 AND o.aptos > 0
            AND o.nr_local_votacao IS NOT NULL
        """).df()
        for name,loc in (("mesmo_local", LOCAL),("mesmo_municipio",["uf","cd_municipio"])):
            for controles in ([],["manual_1t","sem_cad_pct","comp_pct","log_aptos"]):
                cols=["grupo","y","peso",*controles]
                valid=d[np.isfinite(d[cols].to_numpy(dtype=float)).all(axis=1)].copy()
                if valid.empty:
                    continue
                res=_wls_fe(valid,"grupo","y","peso",loc,controles)
                if res:
                    saida.append({"analise":"ano_individual","ano":year,"comparacao":name,
                                  "controles":",".join(controles) or "nenhum",**res})
    # Evolução de taxa manual, nas mesmas seções e locais, segundo grupo de
    # voto após 17h de 2022 e de 2026. Não identifica eleitores individuais.
    d=con.execute(f"""
      SELECT m.uf, m.cd_municipio, m.nr_zona, m.nr_secao,
        m.local AS nr_local_votacao, m.tarde22, m.tarde26,
        100.0*a.manual_apos_falha/nullif(a.classificados,0) manual22,
        100.0*b.manual_apos_falha/nullif(b.classificados,0) manual26,
        100.0*b.sem_cadastro/nullif(b.classificados,0) sem_cad_pct,
        100.0*m.comp26/nullif(m.aptos26,0) comp_pct,
        ln(m.aptos26) log_aptos,
        least(a.classificados,b.classificados) peso
      FROM matches m
      JOIN s2022_2 a USING ({KEY})
      JOIN s2026_2 b USING ({KEY})
      WHERE a.classificados > 0 AND b.classificados > 0
    """).df()
    d["mudanca"]=d.manual26-d.manual22
    for grupo in ("tarde22","tarde26"):
        for controles in ([],["manual22","sem_cad_pct","comp_pct","log_aptos"]):
            cs=["mudanca","peso",grupo,*controles]
            valid=d[np.isfinite(d[cs].to_numpy(dtype=float)).all(axis=1)].copy()
            res=_wls_fe(valid,grupo,"mudanca","peso",LOCAL,controles) if len(valid) else None
            if res:
                saida.append({"analise":"evolucao_mesma_secao_2022_2026","ano":"2022_2026",
                              "grupo_referencia":grupo, "comparacao":"mesmo_local",
                              "controles":",".join(controles) or "nenhum",**res})
    return pd.DataFrame(saida)



def _faixas_votos(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Votos de TODA a seção, por faixa de falha biométrica — nunca voto individual.

    Faixas nacionais fixas (0–5, 5–10, 10–15, 15–20, >=20%);
    separa seções com voto após 17h no segundo turno das demais.
    Em 1º turno, %13 e %22 referem-se a todos os válidos, incluindo terceiros.
    """
    linhas = []
    for year in (2022, 2026):
        for turno in (1, 2):
            fonte = (PROCESSADOS / f"secoes_bu_{year}.parquet"
                     if year == 2022 or turno == 1
                     else PROCESSADOS / "secoes_oficiais_2026_2t.parquet")
            if not fonte.exists():
                raise FileNotFoundError(f"Resultados da seção ausentes: {fonte}")
            con.execute(f"""
              CREATE OR REPLACE TEMP TABLE f{year}_{turno} AS
              SELECT s.uf, s.tardia_2t,
                CASE
                  WHEN 100.0*s.manual_apos_falha/s.classificados < 5 THEN '00-05%'
                  WHEN 100.0*s.manual_apos_falha/s.classificados < 10 THEN '05-10%'
                  WHEN 100.0*s.manual_apos_falha/s.classificados < 15 THEN '10-15%'
                  WHEN 100.0*s.manual_apos_falha/s.classificados < 20 THEN '15-20%'
                  ELSE '20%+'
                END faixa_manual, s.classificados, s.manual_apos_falha,
                s.sem_cadastro, s.bio, o.votos_nominais validos,
                coalesce(o.votos_candidato[13],0) votos13,
                coalesce(o.votos_candidato[22],0) votos22
              FROM (SELECT a.*, b.tardia tardia_2t
                    FROM s{year}_{turno} a
                    JOIN s{year}_2 b USING ({KEY})) s
              JOIN (SELECT {KEY}, votos_nominais, votos_candidato
                    FROM '{fonte}' WHERE turno={turno} AND uf<>'ZZ') o USING ({KEY})
              WHERE s.classificados>0 AND o.votos_nominais>0
            """)
            campos = """count(*) secoes, sum(classificados) habilitacoes_classificadas,
                sum(manual_apos_falha) manuais_apos_falha, sum(sem_cadastro) sem_cadastro,
                sum(bio) biometrica, sum(validos) votos_validos_dia,
                sum(votos13) votos13_dia, sum(votos22) votos22_dia"""
            d = con.execute(f"""
              SELECT {year} ano, {turno} turno, uf, tardia_2t, faixa_manual, {campos}
              FROM f{year}_{turno} GROUP BY ALL
              UNION ALL
              SELECT {year} ano, {turno} turno, 'BR' uf, tardia_2t, faixa_manual, {campos}
              FROM f{year}_{turno} GROUP BY ALL
            """).df()
            linhas.append(d)
    tabela = pd.concat(linhas, ignore_index=True)
    tabela["pct_manual_efetiva"] = (
        100*tabela.manuais_apos_falha/tabela.habilitacoes_classificadas).round(4)
    tabela["pct13_validos_secao"] = (100*tabela.votos13_dia/tabela.votos_validos_dia).round(4)
    tabela["pct22_validos_secao"] = (100*tabela.votos22_dia/tabela.votos_validos_dia).round(4)
    tabela["interpretacao"] = "Resultados de seções inteiras; não de eleitores sem biometria"
    return tabela.sort_values(["ano","turno","uf","tardia_2t","faixa_manual"]).reset_index(drop=True)


def executar() -> dict:
    SAIDA.mkdir(parents=True,exist_ok=True)
    con=duckdb.connect()
    con.execute("SET memory_limit='6GB'")
    con.execute(f"SET temp_directory='{PROCESSADOS}/duckdb_tmp'")
    for year in (2022,2026):
        for turno in (1,2):
            _prepare(con,year,turno)
    # Os grupos devem bater exatamente com a auditoria de horários já publicada.
    for year,expected in ((2022,34455),(2026,29609)):
        n=con.execute(f"SELECT count(*) FROM s{year}_2 WHERE tardia=1").fetchone()[0]
        if n!=expected:
            raise AssertionError(f"Grupo tardio {year}: esperado {expected}, obtido {n}")
    _locations(con)
    resumo,matched=_coortes(con)
    pareado=_regressao(con)
    faixas=_faixas_votos(con)
    con.close()
    # Metadados e taxas agregadas apenas; nunca publicar eventos identificáveis
    # nem um ranking de seções sem contextualização.
    resumo.to_csv(SAIDA/"biometria_secoes_tardias_por_uf.csv",index=False)
    matched.to_csv(SAIDA/"biometria_secoes_tardias_mesmas_secoes.csv",index=False)
    pareado.to_csv(SAIDA/"biometria_secoes_tardias_pareado.csv",index=False)
    faixas.to_csv(SAIDA/"biometria_secoes_tardias_faixas_votos.csv",index=False)
    print("Análise de biometria tardia concluída:",len(resumo),"linhas de coorte,",
          len(matched),"linhas históricas,",len(pareado),"testes controlados,",
          len(faixas),"faixas de votação por seção")
    return {"resumo":resumo,"historico":matched,"pareado":pareado,"faixas":faixas}


if __name__=="__main__":
    executar()
