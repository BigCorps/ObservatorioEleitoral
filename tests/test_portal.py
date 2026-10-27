import base64
import hashlib

from observatorio.arquivos_secao import hash_publicado


def test_hash_publicado_base64_com_traco():
    dig = hashlib.sha256(b"vota.vsc sintetico").digest()
    texto = base64.b64encode(dig).decode().replace("/", "-")
    assert hash_publicado(texto.encode().hex()) == dig


def test_hash_publicado_exemplo_real():
    # aux.json da seção DF 97012/0001/0001, 2º turno de 2026 (texto contém "-")
    h = "436858652d35384167714e6f65684166662b417164726b4759494c333578744b4f577961485153544c70453d"
    assert len(hash_publicado(h)) == 32
