"""Testes sintéticos: nenhuma seção, eleição ou voto aqui é real."""
from __future__ import annotations

from observatorio.triagem_secoes import (
    Secao, TESTES, _resumir, comparavel, dados_confiaveis,
    linhas_de_triagem, obter_pares, triagem_secao,
)


def secao(sec: int, turno=2, v13=110, v22=90, outros=0, validos=None,
          aptos=260, comparecimento=None, local=1, uf="AC", mun=1, zona=1):
    if validos is None:
        validos=v13+v22+outros
    if comparecimento is None:
        comparecimento=validos
    votos={13:v13,22:v22}
    if outros:
        votos[30]=outros
    return Secao(turno,uf,mun,"Cidade teste",zona,local,sec,aptos,
                 comparecimento,validos,comparecimento-validos,0,votos,"TESTE")


def test_participacao_90_95_e_unanimidade():
    s=secao(1,v13=190,v22=10)
    flags,ctx=triagem_secao(s,None,[],"indisponivel")
    assert "concentracao90" in flags
    assert "concentracao95" in flags
    assert "unanimidade" not in flags
    assert ctx["pct_13"]==95
    one=secao(2,v13=1,v22=0,aptos=5)
    flags,_=triagem_secao(one,None,[],"indisponivel")
    assert "unanimidade" in flags
    assert "concentracao90" not in flags  # efeito denominador pequeno


def test_valida_integridade_dos_numeros():
    assert dados_confiaveis(secao(1))
    assert not dados_confiaveis(secao(2,v13=100,v22=90,validos=200))
    assert not dados_confiaveis(secao(3,aptos=150))
    assert not dados_confiaveis(secao(4,comparecimento=190))


def test_comparacao_restrita_mesmo_local_e_aptos_estaveis():
    s=secao(1,turno=2)
    assert comparavel(s,secao(1,turno=1))
    assert not comparavel(s,secao(1,turno=1,local=9))
    assert not comparavel(s,secao(1,turno=1,aptos=400))
    assert not comparavel(secao(1,turno=1),secao(1,turno=2))
    assert not comparavel(s,None)


def test_pares_mesmo_local_com_referencia_excluindo_a_secao():
    grupo=[secao(1,v13=190,v22=10)]+[secao(i) for i in (2,3,4)]
    res,err=linhas_de_triagem(grupo)
    assert err==0
    s,flags,ctx=next(x for x in res if x[0].secao==1)
    assert "pares25" in flags
    assert ctx["referencia_pares"]=="mesmo_local"
    assert 39.9 < ctx["desvio_pares_pp"] < 40.1
    assert "pares25" not in next(x[1] for x in res if x[0].secao==2)


def test_pares_na_zona_quando_local_insuficiente():
    alvo=secao(1, v13=190, v22=10, local=77)
    outros=[secao(i,local=i,v13=90,v22=110) for i in range(2,8)]
    todos=outros+[alvo]
    local,zone={},{}
    for s in todos:
        local[(s.turno,s.uf,s.municipio,s.zona,s.local)]=[s]
    zone[(2,"AC",1,1)]=todos
    pares,origem=obter_pares(alvo,local,zone)
    assert origem=="mesma_zona" and len(pares)==6
    flags,_=triagem_secao(alvo,None,pares,origem)
    assert "pares25" in flags


def test_mudancas_e_virada_sem_inferir_votos_individuais():
    old=secao(1,turno=1,v13=70,v22=120,outros=10,comparecimento=220,aptos=260)
    now=secao(1,turno=2,v13=180,v22=20,comparecimento=240,aptos=260)
    flags,ctx=triagem_secao(now,old,[],"indisponivel")
    for test in ("mudanca20","mudanca30","mudanca40","virada13_22"):
        assert test in flags
    assert ctx["comparacao_entre_turnos_aplicavel"]
    assert abs(ctx["delta_13_pp"]-55)<0.001
    assert "combinados" not in flags  # virada e os 3 thresholds são um só grupo


def test_mudanca_aptos_invalida_comparacao_dos_turnos():
    now=secao(1,turno=2,v13=190,v22=10,aptos=450)
    old=secao(1,turno=1)
    flags,ctx=triagem_secao(now,old,[],"indisponivel")
    assert "concentracao90" in flags
    assert "mudanca20" not in flags
    assert not ctx["comparacao_entre_turnos_aplicavel"]


def test_bases_uf_e_brasil_inclui_exterior_sem_somar_percentuais():
    casos=[secao(1,uf="AC",v13=190,v22=10),
           secao(2,uf="AC",v13=100,v22=100),
           secao(1,uf="ZZ",v13=5,v22=5,aptos=20)]
    registros,err=linhas_de_triagem(casos)
    resumo,ex=_resumir(2026,registros,{2:"TESTE"},max_exemplos=3)
    linha=next(x for x in resumo if x["uf"]=="BR" and x["turno"]==2 and x["teste"]=="concentracao90")
    assert linha["secoes_com_dados"]==3
    assert linha["secoes_elegiveis"]==2
    assert linha["secoes_sinalizadas"]==1
    assert linha["votos_validos_no_recorte"]==410
    assert linha["votos_validos_em_secoes_sinalizadas"]==200
    assert linha["pct_secoes_sinalizadas"]==50
    assert linha["pct_validos_em_secoes_sinalizadas"]==round(200/410*100,4)
    assert any(x["abrangencia"]=="BR" and x["uf"]=="AC" for x in ex)


def test_grupo_qualquer_conta_secao_uma_vez():
    s=secao(1,v13=200,v22=0)
    registros,err=linhas_de_triagem([s])
    resumo,_=_resumir(2022,registros,{2:"TESTE"},5)
    geral=next(x for x in resumo if x["uf"]=="BR" and x["teste"]=="qualquer")
    assert geral["secoes_sinalizadas"]==1
    assert geral["votos_validos_em_secoes_sinalizadas"]==200


def test_duplicidade_impede_publicacao():
    import pytest
    s=secao(1)
    with pytest.raises(ValueError,match="duplicada"):
        linhas_de_triagem([s,s])


def test_sem_pares_nao_entra_denominador_de_comparacao_local():
    registros, ignoradas=linhas_de_triagem([secao(1,local=1),secao(2,local=2)])
    assert ignoradas == 0
    resumo,_=_resumir(2026,registros,{2:"TESTE"},max_exemplos=5)
    row=next(x for x in resumo if x["uf"]=="BR" and x["turno"]==2 and x["teste"]=="pares25")
    assert row["secoes_elegiveis"]==0
    assert row["secoes_sinalizadas"]==0
    assert row["pct_secoes_sinalizadas"] is None
