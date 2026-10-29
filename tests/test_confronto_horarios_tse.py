from pathlib import Path

import pandas as pd

from observatorio.confronto_horarios_tse import FONTE, H17, H18, H19


def test_publicacao_tse_pdf_27_ufs():
    d = pd.read_csv(FONTE)
    assert len(d) == d.uf.nunique() == 27
    assert set(d.uf) >= {"BA", "PE", "RJ", "SP", "AM"}
    assert int(d.tse_apos17.sum()) == 34393
    assert int(d.tse_apos19.sum()) == 13
    assert int(d.observatorio_apos17_estrito.sum()) == 34050
    assert int(d.observatorio_apos19_estrito.sum()) == 11
    assert (d.tse_17_18 + d.tse_18_19 + d.tse_apos19).eq(d.tse_apos17).all()
    assert d.loc[d.uf == "PE", "diferenca_19"].iloc[0] == 2
    assert d.loc[d.uf == "AM", "diferenca_preliminar_17"].iloc[0] < 0


def test_cortes_de_horario_reproduziveis():
    assert [H17, H18, H19] == [61200, 64800, 68400]
