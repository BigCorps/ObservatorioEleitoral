"""Download retomável com verificação de integridade e registro em manifesto.

- Retoma downloads parciais (arquivo .part + cabeçalho Range).
- Confere tamanho com Content-Length e, quando o TSE publica, o hash SHA-512
  oficial (arquivo .sha512 ao lado do .zip). Sempre calcula SHA-256 próprio.
- Testa a integridade do ZIP (CRC de todos os membros) antes de aceitar.
- Registra cada tentativa (sucesso ou erro real) em manifestos/downloads.csv.
- Não baixa de novo um arquivo já verificado cuja versão (ETag) não mudou.
"""
from __future__ import annotations

import csv
import threading
import hashlib
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import requests

from .config import BRUTOS, MANIFESTOS

REGISTRO = MANIFESTOS / "downloads.csv"
_TRAVA = threading.Lock()
CAMPOS = ["url", "arquivo_local", "etag", "last_modified", "tamanho_bytes", "sha256",
          "sha512", "sha512_oficial", "hash_oficial_confere", "zip_ok", "membros_zip",
          "status", "erro", "baixado_em"]


def _ler_registro() -> dict[str, dict]:
    if not REGISTRO.exists():
        return {}
    with REGISTRO.open(encoding="utf-8") as f:
        return {r["url"]: r for r in csv.DictReader(f)}


def _gravar_registro(reg: dict[str, dict]) -> None:
    REGISTRO.parent.mkdir(parents=True, exist_ok=True)
    tmp = REGISTRO.with_suffix(".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS, extrasaction="ignore")
        w.writeheader()
        for k in sorted(reg):
            w.writerow(reg[k])
    tmp.replace(REGISTRO)


def caminho_local(url: str) -> Path:
    rel = url.split("cdn.tse.jus.br/", 1)[-1]
    return BRUTOS / rel


def hashes(caminho: Path) -> tuple[str, str]:
    h256, h512 = hashlib.sha256(), hashlib.sha512()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 22), b""):
            h256.update(bloco)
            h512.update(bloco)
    return h256.hexdigest(), h512.hexdigest()


def testar_zip(caminho: Path) -> tuple[bool, int, str]:
    """Verifica CRC de todos os membros e nomes inseguros (path traversal)."""
    try:
        with zipfile.ZipFile(caminho) as z:
            nomes = z.namelist()
            for n in nomes:
                if n.startswith("/") or ".." in Path(n).parts:
                    return False, len(nomes), f"membro com caminho inseguro: {n}"
            if len(set(nomes)) != len(nomes):
                return False, len(nomes), "membros duplicados no ZIP"
            ruim = z.testzip()
            if ruim:
                return False, len(nomes), f"CRC inválido em {ruim}"
            return True, len(nomes), ""
    except zipfile.BadZipFile as e:
        return False, 0, f"BadZipFile: {e}"


def baixar(url: str, sess: requests.Session | None = None, forcar: bool = False,
           testar: bool = True) -> dict:
    sess = sess or requests.Session()
    reg = _ler_registro()
    destino = caminho_local(url)
    destino.parent.mkdir(parents=True, exist_ok=True)
    h = sess.head(url, timeout=60, allow_redirects=True)
    etag = h.headers.get("ETag", "").strip('"')
    total = int(h.headers.get("Content-Length", 0) or 0)
    anterior = reg.get(url)
    if (not forcar and anterior and anterior.get("status") == "ok" and anterior.get("etag") == etag
            and destino.exists() and destino.stat().st_size == total):
        return anterior

    linha = {"url": url, "arquivo_local": str(destino.relative_to(BRUTOS)), "etag": etag,
             "last_modified": h.headers.get("Last-Modified", ""), "tamanho_bytes": total,
             "baixado_em": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    parcial = destino.with_name(destino.name + ".part")
    erro = ""
    for tentativa in range(5):
        try:
            ja = parcial.stat().st_size if parcial.exists() else 0
            if total and ja > total:
                parcial.unlink(); ja = 0
            if total and ja == total:
                break
            cab = {"Range": f"bytes={ja}-"} if ja else {}
            if etag:
                cab["If-Range"] = f'"{etag}"'
            with sess.get(url, headers=cab, stream=True, timeout=120) as r:
                if ja and r.status_code == 200:  # servidor ignorou Range: recomeça
                    ja = 0
                    modo = "wb"
                elif r.status_code in (200, 206):
                    modo = "ab" if ja else "wb"
                else:
                    raise RuntimeError(f"HTTP {r.status_code}")
                with parcial.open(modo) as f:
                    for bloco in r.iter_content(1 << 20):
                        f.write(bloco)
            if not total or parcial.stat().st_size == total:
                break
        except Exception as e:  # registra e tenta de novo com espera exponencial
            erro = repr(e)
            time.sleep(2 ** (tentativa + 1))
    tam = parcial.stat().st_size if parcial.exists() else 0
    if total and tam != total:
        linha.update(status="incompleto", erro=f"{tam}/{total} bytes; último erro: {erro}")
        with _TRAVA:
            reg = _ler_registro()
            reg[url] = linha
            _gravar_registro(reg)
        return linha
    parcial.replace(destino)
    s256, s512 = hashes(destino)
    linha.update(sha256=s256, sha512=s512)
    # hash oficial publicado pelo TSE (quando existe)
    try:
        r = sess.get(url + ".sha512", timeout=60)
        if r.status_code == 200 and r.text.strip():
            oficial = r.text.split()[0].strip().lower()
            linha["sha512_oficial"] = oficial
            linha["hash_oficial_confere"] = str(oficial == s512)
        else:
            linha["hash_oficial_confere"] = "sem hash publicado"
    except requests.RequestException as e:
        linha["hash_oficial_confere"] = f"erro ao obter hash: {e!r}"
    if testar and destino.suffix == ".zip":
        ok, n, msg = testar_zip(destino)
        linha.update(zip_ok=str(ok), membros_zip=n, erro=msg)
    status_ok = linha.get("hash_oficial_confere") in ("True", "sem hash publicado") and linha.get("zip_ok", "True") == "True"
    linha["status"] = "ok" if status_ok else "falha_integridade"
    with _TRAVA:
        reg = _ler_registro()
        reg[url] = linha
        _gravar_registro(reg)
    return linha
