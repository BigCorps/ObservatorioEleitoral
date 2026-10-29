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
