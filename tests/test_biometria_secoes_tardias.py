import pandas as pd
from observatorio.biometria_secoes_tardias import H17, _sumarizar, METRICS

def test_corte_e_modalidades():
    assert H17 == 61200
    assert {"manual_apos_falha", "sem_cadastro", "bio", "manuais_17mais"}.issubset(METRICS)

def test_tabela_resumo_agrega_nacional_por_contagens():
    import duckdb
    con=duckdb.connect()
    con.execute("""CREATE TABLE sample AS SELECT * FROM (
      VALUES (2026,2,'SP',1,10,10,7,2,1,0,2,1,1,0,3,1),
             (2026,2,'RJ',1,20,20,10,5,5,0,4,2,2,0,2,5)
    ) a(ano,turno,uf,tardia_2t,habilitados,classificados,bio,sem_cadastro,
       manual_apos_falha,desconhecidos,habilitacoes_17mais,manuais_17mais,
       bio_17mais,sem_cadastro_17mais,votos_apos17,bu_biometria_nao_habilitados)""")
    x=_sumarizar(con,"sample","ano, turno, uf, tardia_2t")
    br=x[x.uf=="BR"].iloc[0]
    assert br.secoes==2 and br.manual_apos_falha==6 and br.classificados==30
    assert abs(br.pct_manual-20.0)<1e-8
    con.close()


def test_faixas_resultados_de_secoes_inteiras(tmp_path, monkeypatch):
    import duckdb
    import observatorio.biometria_secoes_tardias as mod
    monkeypatch.setattr(mod,"PROCESSADOS",tmp_path)
    con=duckdb.connect()
    for year in (2022,2026):
        for turno in (1,2):
            con.execute(f"""CREATE TABLE s{year}_{turno} AS
              SELECT 'SP' uf, 123 cd_municipio, 1 nr_zona, 1 nr_secao,
                 10 classificados, 1 manual_apos_falha, 3 sem_cadastro,
                 6 bio, 1 tardia""")
        if year==2022:
            con.execute("""COPY (
               SELECT 2022 ano,turno,'SP' uf,123 cd_municipio,1 nr_zona,1 nr_secao,
                100 votos_nominais,map([13,22],[60,40]) votos_candidato
               FROM (VALUES (1),(2)) t(turno)
             ) TO ? (FORMAT PARQUET)""",[str(tmp_path/"secoes_bu_2022.parquet")])
        else:
            con.execute("""COPY (
               SELECT 2026 ano,turno,'SP' uf,123 cd_municipio,1 nr_zona,1 nr_secao,
                 100 votos_nominais,
                 CASE turno WHEN 1 THEN map([13,22],[55,45]) ELSE map([13,22],[58,42]) END votos_candidato
               FROM (VALUES (1),(2)) t(turno)
             ) TO ? (FORMAT PARQUET)""",[str(tmp_path/"secoes_bu_2026.parquet")])
    d=mod._faixas_votos(con)
    r=d[(d.ano==2026)&(d.turno==2)&(d.uf=="BR")].iloc[0]
    assert r.faixa_manual=="10-15%" and r.secoes==1
    assert r.pct13_validos_secao==58 and r.pct22_validos_secao==42
    assert r.manuais_apos_falha==1
    con.close()


def test_secao_sem_etapa_biometrica_fica_em_faixa_propria(tmp_path, monkeypatch):
    import duckdb
    import observatorio.biometria_secoes_tardias as mod
    monkeypatch.setattr(mod,"PROCESSADOS",tmp_path)
    con=duckdb.connect()
    for year in (2022,2026):
        for turno in (1,2):
            con.execute(f"""CREATE TABLE s{year}_{turno} AS
              SELECT 'ES' uf, 1 cd_municipio, 1 nr_zona, 1 nr_secao,
                 0 classificados, 0 manual_apos_falha, 0 sem_cadastro, 0 bio, 0 tardia""")
        con.execute(f"""COPY (SELECT {year} ano,turno,'ES' uf,1 cd_municipio,1 nr_zona,1 nr_secao,
            10 votos_nominais,map([13,22],[6,4]) votos_candidato FROM (VALUES (1),(2)) t(turno))
            TO '{tmp_path}/secoes_bu_{year}.parquet' (FORMAT PARQUET)""")
    d=mod._faixas_votos(con)
    r=d[(d.ano==2022)&(d.turno==2)&(d.uf=="BR")].iloc[0]
    assert r.faixa_manual=="sem etapa biométrica" and r.votos13_dia==6 and pd.isna(r.pct_manual_efetiva)
    con.close()
