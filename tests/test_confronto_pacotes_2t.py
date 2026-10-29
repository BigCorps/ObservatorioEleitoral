import zipfile
from types import SimpleNamespace

import pandas as pd

from observatorio import confronto_pacotes_2t as cp
from observatorio.config import RESULTADOS


def test_comparar_bu_inclui_secoes_do_sistema_de_apuracao(tmp_path, monkeypatch):
    (tmp_path / "bu").mkdir()
    with zipfile.ZipFile(tmp_path / "bu" / "2026_2t_ZZ.zip", "w") as z:
        z.writestr("o03221zz2917300010494.bu", b"a" * 10)
        z.writestr("o03221zz2917300010001.bu", b"b" * 10)
    crc = {i.filename: i.CRC for i in zipfile.ZipFile(tmp_path / "bu" / "2026_2t_ZZ.zip").infolist()}
    monkeypatch.setattr(cp, "BRUTOS", tmp_path)
    membros = [SimpleNamespace(nome="o03221zz2917300010494-busa.dat", tamanho=10, crc=crc["o03221zz2917300010494.bu"]),
               SimpleNamespace(nome="o03221zz2917300010001-bu.dat", tamanho=10, crc=crc["o03221zz2917300010001.bu"]),
               SimpleNamespace(nome="o03221zz2917300010001-log.jez", tamanho=5, crc=0)]
    bu = cp.comparar_bu("ZZ", membros)
    assert (bu.situacao == "idêntico (tamanho e CRC32)").all() and len(bu) == 2


def test_bu_do_pacote_identico_em_todas_as_secoes():
    d = pd.read_csv(RESULTADOS / "2026" / "consolidado_2t" / "pacote_oficial_2t_bu_x_portal_todas_ufs.csv")
    assert len(d) == 28 and d.secoes.sum() == 499207
    assert (d["idêntico (tamanho e CRC32)"] == d.secoes).all()


def test_convencao_de_fuso_da_uf_reproduz_quadro_do_tse():
    d = pd.read_csv(RESULTADOS / "2026" / "confronto_horarios_tse_logs_detalhe_uf.csv")
    for c in ("diferenca_apos17_fuso_uf", "diferenca_18h_a_19h_fuso_uf", "diferenca_apos19_fuso_uf"):
        assert (d[c] == 0).all()
