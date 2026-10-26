"""Leitura seletiva de membros de ZIPs remotos por requisições HTTP Range.

Os pacotes "arquivos transmitidos para totalização" do TSE somam ~260 GB
(2022 1º+2º turno e 2026 1º turno). Para cada seção há 5 membros
(.bu, .imgbu, .logjez, .rdv, .vscmr). Esta classe lê o diretório central do
ZIP remoto e baixa somente os intervalos de bytes necessários, permitindo
processar o país inteiro sem armazenar os pacotes completos.

A integridade de cada membro é conferida pelo CRC-32 do próprio ZIP.
"""
from __future__ import annotations

import io
import struct
import time
import zipfile
import zlib
from dataclasses import dataclass

import requests


class ArquivoHTTP(io.RawIOBase):
    """Objeto tipo-arquivo somente leitura sobre HTTP Range (para o diretório central)."""

    def __init__(self, url: str, sess: requests.Session | None = None):
        self.url = url
        self.sess = sess or requests.Session()
        h = self.sess.head(url, timeout=60, allow_redirects=True)
        h.raise_for_status()
        self.tamanho = int(h.headers["Content-Length"])
        self.etag = h.headers.get("ETag", "").strip('"')
        self.last_modified = h.headers.get("Last-Modified", "")
        self.pos = 0
        self._cache: dict[int, bytes] = {}
        self.bytes_baixados = 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        if whence == 0:
            self.pos = off
        elif whence == 1:
            self.pos += off
        else:
            self.pos = self.tamanho + off
        return self.pos

    def faixa(self, ini: int, fim: int) -> bytes:
        """Bytes [ini, fim) com novas tentativas e espera exponencial."""
        ultimo = None
        for t in range(6):
            try:
                r = self.sess.get(self.url, headers={"Range": f"bytes={ini}-{fim - 1}"}, timeout=120)
                if r.status_code != 206:
                    raise RuntimeError(f"HTTP {r.status_code} para Range")
                b = r.content
                if len(b) != fim - ini:
                    raise RuntimeError(f"faixa incompleta {len(b)}/{fim - ini}")
                self.bytes_baixados += len(b)
                return b
            except Exception as e:
                ultimo = e
                time.sleep(min(2 ** (t + 1), 30))
        raise RuntimeError(f"falha ao ler faixa {ini}-{fim} de {self.url}: {ultimo!r}")

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.tamanho - self.pos
        n = min(n, self.tamanho - self.pos)
        if n <= 0:
            return b""
        # blocos de 1 MiB em cache (o diretório central é lido em pedaços pequenos)
        B = 1 << 20
        out = bytearray()
        p = self.pos
        while len(out) < n:
            bi = p // B
            if bi not in self._cache:
                ini = bi * B
                self._cache[bi] = self.faixa(ini, min(ini + B, self.tamanho))
            bloco = self._cache[bi]
            off = p - bi * B
            parte = bloco[off: off + (n - len(out))]
            out += parte
            p += len(parte)
        self.pos = p
        return bytes(out)

    def readinto(self, b):
        d = self.read(len(b))
        b[: len(d)] = d
        return len(d)


@dataclass
class Membro:
    nome: str
    offset_cabecalho: int
    tamanho_comprimido: int
    tamanho: int
    crc: int
    metodo: int


def listar_membros(arq: ArquivoHTTP) -> list[Membro]:
    with zipfile.ZipFile(arq) as z:
        infos = z.infolist()
    arq._cache.clear()
    return [Membro(i.filename, i.header_offset, i.compress_size, i.file_size, i.CRC, i.compress_type)
            for i in infos]


def extrair_de_bloco(bloco: bytes, base: int, m: Membro) -> bytes:
    """Extrai um membro a partir de um bloco de bytes que começa no offset `base`."""
    o = m.offset_cabecalho - base
    assin, = struct.unpack_from("<I", bloco, o)
    if assin != 0x04034B50:
        raise ValueError(f"cabeçalho local inválido para {m.nome}")
    n_nome, n_extra = struct.unpack_from("<HH", bloco, o + 26)
    ini = o + 30 + n_nome + n_extra
    dados = bloco[ini: ini + m.tamanho_comprimido]
    if m.metodo == zipfile.ZIP_DEFLATED:
        dados = zlib.decompress(dados, -15)
    elif m.metodo != zipfile.ZIP_STORED:
        raise ValueError(f"método de compressão não suportado: {m.metodo}")
    if len(dados) != m.tamanho or (zlib.crc32(dados) & 0xFFFFFFFF) != m.crc:
        raise ValueError(f"CRC/tamanho não confere para {m.nome}")
    return dados


def fim_membro(m: Membro, folga: int = 1024) -> int:
    """Limite superior do fim do membro (cabeçalho local + nome + extra + dados)."""
    return m.offset_cabecalho + 30 + len(m.nome.encode()) + folga + m.tamanho_comprimido
