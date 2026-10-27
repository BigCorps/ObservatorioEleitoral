"""Integração mínima com Parquet sintético: jamais usar arquivos de eleição real."""
import csv
import json

import duckdb

from observatorio.triagem_secoes import executar


def _gravar(con, path, turnos):
    partes=[]
    for turno in turnos:
        for secao, v13 in [(1,190 if turno == 2 else 110),(2,110),(3,110)]:
            partes.append(
                f"({turno},'AC',1,'Cidade teste',1,1,{secao},260,200,200,0,0,"
                f"map([13,22],[{v13},{200-v13}]))")
    sql="""COPY (SELECT * FROM (VALUES """+",".join(partes)+""") AS s(
      turno,uf,cd_municipio,nm_municipio,nr_zona,nr_local_votacao,nr_secao,
      qt_aptos,qt_comparecimento,votos_nominais,votos_brancos,votos_nulos,
      votos_candidato)) TO '"""+str(path)+"""' (FORMAT PARQUET)"""
    con.execute(sql)


def test_geracao_csv_e_meta_sem_baixar_arquivos(tmp_path):
    proc=tmp_path/"processados"
    output=tmp_path/"resultados"
    proc.mkdir()
    con=duckdb.connect()
    _gravar(con,proc/"secoes_bu_2022.parquet",(1,2))
    con.close()
    meta=executar(2022,processados=proc,resultados=output)
    assert meta["secoes_incluidas"]==6
    assert meta["secoes_excluidas_por_inconsistencia"]==0
    assert "ZZ" in meta["ufs_ausentes"]
    with (output/"2022"/"triagem_secoes_resumo.csv").open(encoding="utf-8") as f:
        resumo=list(csv.DictReader(f))
    row=next(r for r in resumo if r["uf"]=="BR" and r["turno"]=="2"
             and r["teste"]=="concentracao90")
    assert row["secoes_sinalizadas"]=="1"
    assert row["secoes_elegiveis"]=="3"
    assert row["votos_validos_em_secoes_sinalizadas"]=="200"
    with (output/"2022"/"triagem_secoes_exemplos.csv").open(encoding="utf-8") as f:
        exemplos=list(csv.DictReader(f))
    assert any(r["teste"]=="concentracao90" and r["secao"]=="1" for r in exemplos)


def test_2026_segundo_turno_oficial_sem_bu(tmp_path):
    proc=tmp_path/"processados"
    output=tmp_path/"resultados"
    proc.mkdir()
    con=duckdb.connect()
    _gravar(con,proc/"secoes_bu_2026.parquet",(1,))
    _gravar(con,proc/"secoes_oficiais_2026_2t.parquet",(2,))
    con.close()
    meta=executar(2026,processados=proc,resultados=output)
    assert meta["fontes_por_turno"]=={"1":"BU-CSV","2":"DSEC+VSEC"}
    with (output/"2026"/"triagem_secoes_resumo.csv").open(encoding="utf-8") as f:
        resumo=list(csv.DictReader(f))
    row=next(r for r in resumo if r["uf"]=="AC" and r["turno"]=="2" and r["teste"]=="concentracao90")
    assert row["fonte"]=="DSEC+VSEC"
    assert row["secoes_sinalizadas"]=="1"
    with (output/"2026"/"triagem_secoes_metadados.json").open(encoding="utf-8") as f:
        assert json.load(f)["secoes_incluidas"]==6
