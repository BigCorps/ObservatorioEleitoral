"""Descoberta dos recursos nos catálogos CKAN do TSE e inventário com metadados HTTP.

Para cada recurso registra: conjunto, nome, URL, ano, tipo, UF, turno, data de
criação/modificação no catálogo e, via HTTP HEAD, tamanho, Last-Modified e ETag.
O ETag/Last-Modified identifica a *versão* publicada: se o TSE republicar um
arquivo, o inventário seguinte mostrará a diferença.
"""
from __future__ import annotations

import csv
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import requests

from .config import CKAN_API, DATASETS, MANIFESTOS

CAMPOS = [
    "conjunto", "nome", "url", "formato", "ano", "tipo", "uf", "turno",
    "ckan_created", "ckan_modified", "http_status", "tamanho_bytes",
    "last_modified", "etag", "hash_publicado_url", "consultado_em",
]


def classificar(url: str) -> dict:
    """Extrai tipo, UF e turno a partir do padrão de nome dos arquivos do TSE."""
    nome = url.rsplit("/", 1)[-1]
    out = {"tipo": "outro", "uf": "", "turno": ""}
    m = re.match(r"bweb_(\d)t_([A-Z]{2})_\d+\.zip(\.sha512)?$", nome)
    if m:
        out.update(tipo="bu_csv_hash" if m.group(3) else "bu_csv", uf=m.group(2), turno=m.group(1))
        return out
    m = re.match(r"bu_imgbu_logjez_rdv_vscmr_(\d{4})_(\d)t_([A-Z]{2})\.zip$", nome)
    if m:
        out.update(tipo="arquivos_urna", uf=m.group(3), turno=m.group(2))
        return out
    m = re.match(r"votacao_secao_(\d{4})_([A-Z]{2})\.zip$", nome)
    if m:
        out.update(tipo="votacao_secao", uf=m.group(2))
        return out
    m = re.match(r"perfil_eleitor_secao_(\w+?)_([A-Z]{2})\.zip$", nome)
    if m:
        out.update(tipo="perfil_eleitor_secao", uf=m.group(2))
        return out
    m = re.match(r"Relatorio_Resultado_Totalizacao_\d{4}_([A-Z]{2})\.zip$", nome)
    if m:
        out.update(tipo="relatorio_totalizacao", uf=m.group(1))
        return out
    m = re.match(r"Historico_Totalizacao_Presidente_BR_(\d)T_\d{4}\.zip$", nome)
    if m:
        out.update(tipo="historico_totalizacao_presidente", uf="BR", turno=m.group(1))
        return out
    for chave in ("detalhe_votacao_secao", "detalhe_votacao_munzona", "votacao_candidato_munzona",
                  "votacao_partido_munzona", "perfil_eleitorado", "eleitorado_local_votacao",
                  "secoes_agregadas", "transf_temporaria_secao", "transferencia_temporaria",
                  "perfil_eleitor_deficiencia"):
        if nome.startswith(chave):
            out["tipo"] = chave
            return out
    return out


def baixar_catalogo(conjunto: str, sess: requests.Session) -> dict:
    r = sess.get(f"{CKAN_API}/package_show", params={"id": conjunto}, timeout=60)
    r.raise_for_status()
    dados = r.json()
    if not dados.get("success"):
        raise RuntimeError(f"CKAN sem sucesso para {conjunto}")
    destino = MANIFESTOS / "ckan" / f"{conjunto}.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(dados["result"], ensure_ascii=False, indent=1, sort_keys=True))
    return dados["result"]


def head(url: str, sess: requests.Session) -> dict:
    for tentativa in range(4):
        try:
            r = sess.head(url, timeout=60, allow_redirects=True)
            return {
                "http_status": r.status_code,
                "tamanho_bytes": r.headers.get("Content-Length", ""),
                "last_modified": r.headers.get("Last-Modified", ""),
                "etag": r.headers.get("ETag", "").strip('"'),
            }
        except requests.RequestException as e:  # registra o erro real
            erro = repr(e)
            time.sleep(2 ** (tentativa + 1))
    return {"http_status": f"ERRO {erro}", "tamanho_bytes": "", "last_modified": "", "etag": ""}


def inventariar(anos=(2022, 2026), com_head: bool = True) -> list[dict]:
    sess = requests.Session()
    linhas = []
    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for ano in anos:
        for conjunto in DATASETS[ano]:
            try:
                res = baixar_catalogo(conjunto, sess)
            except Exception as e:  # conjunto ausente: registrar e seguir
                linhas.append({"conjunto": conjunto, "nome": f"ERRO CATÁLOGO: {e!r}", "ano": ano,
                               "consultado_em": agora})
                continue
            urls = {x["url"] for x in res["resources"]}
            for x in res["resources"]:
                url = x["url"]
                if url.endswith(".sha512"):
                    continue  # registrado como hash do arquivo principal
                c = classificar(url)
                linhas.append({
                    "conjunto": conjunto, "nome": x["name"].strip(), "url": url,
                    "formato": x.get("format", ""), "ano": ano, **c,
                    "ckan_created": x.get("created", ""), "ckan_modified": x.get("last_modified") or "",
                    "hash_publicado_url": url + ".sha512" if url + ".sha512" in urls else "",
                    "consultado_em": agora,
                })
    if com_head:
        with ThreadPoolExecutor(8) as ex:
            heads = list(ex.map(lambda l: head(l["url"], sess) if l.get("url") else {}, linhas))
        for l, h in zip(linhas, heads):
            l.update(h)
    destino = MANIFESTOS / "inventario_fontes.csv"
    with destino.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS, extrasaction="ignore")
        w.writeheader()
        for l in linhas:
            w.writerow(l)
    return linhas


def carregar_inventario() -> list[dict]:
    with (MANIFESTOS / "inventario_fontes.csv").open(encoding="utf-8") as f:
        return list(csv.DictReader(f))
