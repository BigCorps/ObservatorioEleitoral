from observatorio.horario_encerramento import GRUPOS, H17, H19, RECORTES


def test_recortes_contiguos_sem_lacuna():
    fins = [r[2] for r in RECORTES[:-1]]
    inicios = [r[1] for r in RECORTES[1:]]
    assert all(i == f + 1 for f, i in zip(fins, inicios))
    assert RECORTES[0][1] is None and RECORTES[-1][2] is None
    assert RECORTES[-1][1] == H19 == 19 * 3600


def test_grupos_usam_campos_distintos():
    assert "votos_apos_17h" in GRUPOS["A"][0] and "votos_apos_19h" in GRUPOS["B"][0]
    assert f"encerramento_brt > {H17}" == GRUPOS["C"][0]
    assert f"encerramento_brt > {H19}" == GRUPOS["D"][0]
    # o último voto e a geração do BU não definem nenhum grupo
    assert not any("ultimo_voto" in c or "gera_bu" in c for c, _ in GRUPOS.values())
