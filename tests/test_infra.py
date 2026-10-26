import io
import zipfile

from observatorio.catalogo import classificar
from observatorio.download import testar_zip as verificar_zip
from observatorio.fusos import fuso, sql_desloc_brt
from observatorio.remotezip import Membro, extrair_de_bloco


def test_classificar_urls_tse():
    assert classificar("https://x/bweb_2t_SP_311020221535.zip") == {"tipo": "bu_csv", "uf": "SP", "turno": "2"}
    assert classificar("https://x/bu_imgbu_logjez_rdv_vscmr_2022_1t_ZZ.zip")["tipo"] == "arquivos_urna"
    assert classificar("https://x/detalhe_votacao_secao_2022.zip")["tipo"] == "detalhe_votacao_secao"


def test_fusos_legais():
    assert fuso("SP", 71072) == -3
    assert fuso("AC", 1392) == -5
    assert fuso("AM", 2496) == -5 and fuso("AM", 2550) == -4   # Jutaí (oeste) x Manaus
    assert fuso("PE", 30015) == -2                              # Fernando de Noronha
    assert fuso("ZZ", 29297) is None


def test_desloc_sql():
    import duckdb
    r = duckdb.sql(f"SELECT {sql_desloc_brt()} FROM (VALUES ('AC', 1392), ('ZZ', 1), ('RJ', 60011)) t(uf, cd_municipio)").fetchall()
    assert [x[0] for x in r] == [7200, 0, 0]


def _zip_bytes():
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("a.bu", b"conteudo-bu" * 10)
        z.writestr("a.logjez", b"conteudo-log")
    return b.getvalue()


def test_extrair_de_bloco_confere_crc():
    dados = _zip_bytes()
    z = zipfile.ZipFile(io.BytesIO(dados))
    i = z.getinfo("a.bu")
    m = Membro(i.filename, i.header_offset, i.compress_size, i.file_size, i.CRC, i.compress_type)
    assert extrair_de_bloco(dados, 0, m) == b"conteudo-bu" * 10
    m_ruim = Membro(i.filename, i.header_offset, i.compress_size, i.file_size, i.CRC ^ 1, i.compress_type)
    try:
        extrair_de_bloco(dados, 0, m_ruim)
        assert False, "CRC inválido deveria falhar"
    except ValueError:
        pass


def test_testar_zip(tmp_path):
    p = tmp_path / "ok.zip"
    p.write_bytes(_zip_bytes())
    assert verificar_zip(p)[0] is True
    q = tmp_path / "ruim.zip"
    q.write_bytes(_zip_bytes()[:50])
    assert verificar_zip(q)[0] is False
