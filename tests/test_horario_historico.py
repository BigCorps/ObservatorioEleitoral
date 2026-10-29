from observatorio.horario_historico import H17, H19, _fonte_urna, CHAVES, LOCAL


def test_limites_historicos():
    assert (H17, H19) == (17 * 3600, 19 * 3600)


def test_fontes_historicas_independentes():
    assert _fonte_urna(2022).name == "secoes_bu_2022.parquet"
    assert _fonte_urna(2026).name == "secoes_oficiais_2026_2t.parquet"


def test_chaves_mesma_secao_e_mesmo_local():
    assert CHAVES == ["uf", "cd_municipio", "nr_zona", "nr_secao"]
    assert LOCAL == ["uf", "cd_municipio", "nr_zona", "nr_local_votacao"]
