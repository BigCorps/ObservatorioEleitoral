"""Testes D e E — cronologia da votação e intervalos entre votos, a partir dos logs.

Todos os horários são convertidos para Brasília pelo fuso legal (fusos.py); no
exterior, permanecem em hora local. Votos após as 17h NÃO são classificados
como irregulares: a lei garante o voto de quem está na fila às 17h (Res.
23.669/2021, art. 136, §§ 1º-2º). O que se mede aqui é a distribuição.
"""
from __future__ import annotations

import duckdb

from .config import PROCESSADOS, RESULTADOS
from .fusos import sql_desloc_brt, sql_fuso

H8, H17, H18, H19 = 8 * 3600, 17 * 3600, 18 * 3600, 19 * 3600


def view_secoes(con: duckdb.DuckDBPyConnection, ano: int) -> None:
    """Cria a view `sec` com indicadores temporais por seção (em segundos, hora de Brasília)."""
    d = sql_desloc_brt()
    con.execute(f"""
    CREATE OR REPLACE VIEW sec_base AS
      SELECT *, {d} AS desloc, {sql_fuso()} AS fuso_legal
      FROM read_parquet('{PROCESSADOS}/logs/{ano}_*.parquet', union_by_name=true)
      WHERE tem_log;
    CREATE OR REPLACE VIEW sec AS
      SELECT ano, turno, uf, cd_municipio, nr_zona, nr_secao, arquivo, fuso_legal, desloc,
        log_modelos, log_n_ids_urna, log_retrocessos_relogio, log_maior_retrocesso_s, n_ligada, n_pronta,
        n_modo_contingencia, n_votacao_suspensa, n_desligada, n_tentativa_encerramento_antecipado,
        n_votos_computados, n_habilitados, hab_biometrica, hab_manual_apos_falha, hab_sem_biometria,
        hab_indeterminada, n_ja_votou, n_suspenso, log_linhas_dia_seguinte,
        t_ligada_primeiro + desloc AS ligada_brt,
        t_zeresima_primeiro + desloc AS zeresima_brt,
        t_pronta_primeiro + desloc AS abertura_brt,
        t_primeira_hab + desloc AS primeira_hab_brt,
        t_primeiro_voto + desloc AS primeiro_voto_brt,
        t_ultima_hab + desloc AS ultima_hab_brt,
        t_ultimo_voto + desloc AS ultimo_voto_brt,
        t_inicio_encerramento_primeiro + desloc AS encerramento_brt,
        t_gera_bu_primeiro + desloc AS gera_bu_brt,
        t_arquivo_bu_primeiro + desloc AS arquivo_bu_brt,
        len(list_filter(votos_s, lambda x: x + desloc < {H8})) AS votos_antes_8h,
        len(list_filter(votos_s, lambda x: x + desloc > {H17})) AS votos_apos_17h,
        len(list_filter(votos_s, lambda x: x + desloc > {H18})) AS votos_apos_18h,
        len(list_filter(votos_s, lambda x: x + desloc > {H19})) AS votos_apos_19h,
        len(list_filter(hab_s, lambda x: x + desloc < {H8})) AS hab_antes_8h,
        len(list_filter(hab_s, lambda x: x + desloc > {H17})) AS hab_apos_17h,
        list_filter(list_transform(list_slice(votos_s, 2, len(votos_s)), lambda x, i: x - votos_s[i]),
                    lambda y: true) AS intervalos,
        dur_voto, dur_voto_mod
      FROM sec_base
    """)


def indicadores_secao(con, ano: int):
    view_secoes(con, ano)
    con.execute(f"""
    CREATE OR REPLACE TABLE ind AS SELECT * EXCLUDE (intervalos, dur_voto, dur_voto_mod),
        list_min(intervalos) intervalo_min_s, list_median(intervalos) intervalo_mediano_s,
        list_max(intervalos) maior_intervalo_s,
        len(list_filter(intervalos, lambda x: x <= 5)) intervalos_ate_5s,
        len(list_filter(intervalos, lambda x: x <= 10)) intervalos_ate_10s,
        len(list_filter(intervalos, lambda x: x >= 1800)) pausas_30min,
        len(list_filter(intervalos, lambda x: x >= 3600)) pausas_60min,
        list_min(dur_voto) duracao_voto_min_s, list_median(dur_voto) duracao_voto_mediana_s,
        len(list_filter(dur_voto, lambda x: x < 10)) votos_duracao_menor_10s,
        len(intervalos) n_intervalos
      FROM sec""")
    out = PROCESSADOS / f"indicadores_temporais_{ano}.parquet"
    con.execute(f"COPY ind TO '{out}' (FORMAT parquet, COMPRESSION zstd)")
    return out


def tabelas(ano: int) -> dict:
    con = duckdb.connect()
    con.execute("SET enable_progress_bar=false")
    indicadores_secao(con, ano)
    o = RESULTADOS / str(ano)
    o.mkdir(parents=True, exist_ok=True)
    # Resumo por UF e turno
    con.execute(f"""COPY (
      SELECT turno, uf, count(*) secoes_com_log, sum(n_votos_computados) votos,
        sum(votos_antes_8h) votos_antes_8h, sum((votos_antes_8h > 0)::INT) secoes_com_voto_antes_8h,
        sum(votos_apos_17h) votos_apos_17h, round(100.0 * sum(votos_apos_17h) / sum(n_votos_computados), 3) pct_votos_apos_17h,
        sum((votos_apos_17h > 0)::INT) secoes_com_voto_apos_17h,
        sum(votos_apos_18h) votos_apos_18h, sum(votos_apos_19h) votos_apos_19h,
        sum(hab_antes_8h) hab_antes_8h, sum(hab_apos_17h) hab_apos_17h,
        strftime(make_timestamp(0) + to_seconds(CAST(median(primeiro_voto_brt) AS BIGINT)), '%H:%M:%S') mediana_primeiro_voto,
        strftime(make_timestamp(0) + to_seconds(CAST(median(ultimo_voto_brt) AS BIGINT)), '%H:%M:%S') mediana_ultimo_voto,
        strftime(make_timestamp(0) + to_seconds(CAST(max(ultimo_voto_brt) AS BIGINT)), '%H:%M:%S') ultimo_voto_maximo,
        round(avg(ultimo_voto_brt - primeiro_voto_brt) / 3600, 2) duracao_media_h,
        sum((n_pronta > 1)::INT) secoes_com_reabertura, sum((n_ligada > 1)::INT) secoes_urna_religada,
        sum((n_modo_contingencia > 0)::INT) secoes_com_contingencia, sum((log_n_ids_urna > 1)::INT) secoes_mais_de_um_id_urna,
        sum((log_retrocessos_relogio > 0)::INT) secoes_relogio_retrocede,
        sum(intervalos_ate_5s) intervalos_ate_5s, sum(pausas_60min) pausas_60min,
        median(duracao_voto_mediana_s) mediana_das_medianas_duracao_voto_s,
        sum(votos_duracao_menor_10s) votos_duracao_menor_10s
      FROM ind GROUP BY ALL ORDER BY turno, uf) TO '{o}/temporal_por_uf.csv' (HEADER)""")
    # Votos por faixa de 15 minutos (hora de Brasília; exterior em hora local)
    con.execute(f"""COPY (
      SELECT turno, CASE WHEN uf='ZZ' THEN 'ZZ (hora local)' ELSE 'BR (Brasília)' END abrangencia,
        CAST(floor((v + desloc) / 900) AS INT) * 15 AS minuto_do_dia,
        strftime(make_timestamp(0) + to_seconds(CAST(floor((v + desloc) / 900) * 900 AS BIGINT)), '%H:%M') faixa,
        count(*) votos
      FROM (SELECT turno, uf, desloc, unnest(votos_s) v FROM sec_base) GROUP BY ALL ORDER BY 1, 2, 3)
      TO '{o}/votos_por_15min.csv' (HEADER)""")
    # Distribuição dos intervalos entre votos consecutivos (segundos)
    con.execute(f"""COPY (
      SELECT turno, least(x, 600) AS intervalo_s_truncado_600, count(*) n
      FROM (SELECT turno, unnest(intervalos) x FROM sec) GROUP BY ALL ORDER BY 1, 2)
      TO '{o}/distribuicao_intervalos.csv' (HEADER)""")
    # Duração habilitação -> voto computado, por modalidade
    con.execute(f"""COPY (
      SELECT turno, m modalidade, least(d, 900) AS duracao_s_truncada_900, count(*) n
      FROM (SELECT turno, unnest(dur_voto) d, unnest(dur_voto_mod) m FROM sec) GROUP BY ALL ORDER BY 1, 2, 3)
      TO '{o}/distribuicao_duracao_voto.csv' (HEADER)""")
    # Validação do fuso: hora local mediana do primeiro voto por município
    con.execute(f"""COPY (
      SELECT turno, uf, cd_municipio, any_value(fuso_legal) fuso_legal, count(*) secoes,
        round(median(primeiro_voto_brt - desloc) / 3600.0, 3) mediana_primeiro_voto_hora_local,
        CAST(floor(median(primeiro_voto_brt - desloc) / 3600.0) AS INT) - 11 fuso_empirico,
        (CAST(floor(median(primeiro_voto_brt - desloc) / 3600.0) AS INT) - 11) IS DISTINCT FROM any_value(fuso_legal) diverge
      FROM ind WHERE uf <> 'ZZ' GROUP BY ALL ORDER BY diverge DESC, uf, cd_municipio)
      TO '{o}/validacao_fusos_municipio.csv' (HEADER)""")
    # Seções com voto antes das 8h ou após 19h (lista completa, para conferência documental)
    con.execute(f"""COPY (
      SELECT turno, uf, cd_municipio, nr_zona, nr_secao, arquivo, fuso_legal, votos_antes_8h, hab_antes_8h,
        votos_apos_17h, votos_apos_19h, abertura_brt, primeiro_voto_brt, ultimo_voto_brt, log_retrocessos_relogio,
        log_maior_retrocesso_s, n_ligada, n_modo_contingencia, log_modelos
      FROM ind WHERE votos_antes_8h > 0 OR votos_apos_19h > 0 OR hab_antes_8h > 0
      ORDER BY turno, uf, cd_municipio, nr_zona, nr_secao) TO '{o}/secoes_horarios_atipicos.csv' (HEADER)""")
    r = con.execute("SELECT turno, count(*), sum(n_votos_computados) FROM ind GROUP BY 1 ORDER BY 1").fetchall()
    con.close()
    return {"secoes_por_turno": r}
