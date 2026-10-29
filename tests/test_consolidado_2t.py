import inspect

from observatorio import bweb
from observatorio.cronologia import _geracao


def test_geracao_no_nome_do_arquivo():
    assert _geracao("https://x/bweb_2t_AC_261020260742.zip") == "2026-10-26 07:42"
    assert _geracao("https://x/bweb_2t_AC_311020221535.zip") == "2022-10-31 15:35"
    assert _geracao("https://x/votacao_secao_2026_AC.zip") is None


def test_conversao_mantem_secao_sem_votantes_apenas_com_comparecimento_zero():
    fonte = inspect.getsource(bweb.converter)
    assert "CD_CARGO_PERGUNTA = '1'" in fonte
    assert "CD_CARGO_PERGUNTA = '-1' AND QT_COMPARECIMENTO = '0'" in fonte
    assert '#NULO#' in fonte


def test_mapa_de_candidatos_vazio_nunca_nulo():
    assert "map([]::INT[], []::INT[])" in inspect.getsource(bweb.consolidar)
