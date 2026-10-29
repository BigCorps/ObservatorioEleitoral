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


def _recursos_da_pagina(conjunto: str, conhecidos: set, sess: requests.Session) -> list[dict]:
    """A resposta de package_show da API pode vir desatualizada (observado em 29/10/2026: recursos do 2º turno
    de 2026 presentes na página do conjunto e em resource_show, ausentes de package_show). Completa a lista
    com os recursos da página web, consultando cada um por resource_show."""
    base = CKAN_API.rsplit("/api/", 1)[0]
    try:
        html = sess.get(f"{base}/dataset/{conjunto}", timeout=60).text
    except requests.RequestException:
        return []
    extras = []
    for rid in sorted(set(re.findall(r"/resource/([0-9a-f-]{36})", html)) - conhecidos):
        try:
            x = sess.get(f"{CKAN_API}/resource_show", params={"id": rid}, timeout=60).json()["result"]
        except Exception:
            continue
        x["_origem"] = "resource_show (ausente de package_show)"
        extras.append(x)
    return extras


def baixar_catalogo(conjunto: str, sess: requests.Session) -> dict:
    r = sess.get(f"{CKAN_API}/package_show", params={"id": conjunto}, timeout=60)
    r.raise_for_status()
    dados = r.json()
    if not dados.get("success"):
        raise RuntimeError(f"CKAN sem sucesso para {conjunto}")
    extras = _recursos_da_pagina(conjunto, {x["id"] for x in dados["result"]["resources"]}, sess)
    # Confere cada recurso de package_show com resource_show; quando divergem, adota a versão mais recente
    # e registra a divergência (observado: URL de RR corrigida em resource_show e ainda errada em package_show).
    atual, divergencias = [], []
    for x in dados["result"]["resources"]:
        try:
            y = sess.get(f"{CKAN_API}/resource_show", params={"id": x["id"]}, timeout=60).json()["result"]
        except Exception:
            atual.append(x)
            continue
        dif = {k: (x.get(k), y.get(k)) for k in ("url", "name", "created", "metadata_modified") if x.get(k) != y.get(k)}
        if dif:
            divergencias.append({"conjunto": conjunto, "id": x["id"], **{f"{k}_package_show": v[0] for k, v in dif.items()},
                                 **{f"{k}_resource_show": v[1] for k, v in dif.items()}})
            if (y.get("metadata_modified") or "") >= (x.get("metadata_modified") or ""):
                y["_origem"] = "resource_show (difere de package_show)"
                x = y
        atual.append(x)
    dados["result"]["resources"] = atual + extras
    dados["result"]["_divergencias_package_show"] = divergencias
    dados["result"]["_recursos_fora_de_package_show"] = len(extras)
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
                    "conjunto": conjunto, "nome": x["name"].strip() + (f" [{x['_origem']}]" if x.get("_origem") else ""),
                    "url": url,
                    "formato": x.get("format", ""), "ano": ano, **c,
                    "ckan_created": x.get("created", ""), "ckan_modified": x.get("last_modified") or "",
                    "hash_publicado_url": url + ".sha512" if url + ".sha512" in urls else "",
                    "consultado_em": agora,
                })
    import pandas as _pd
    div = []
    for ano in anos:
        for conjunto in DATASETS[ano]:
            f = MANIFESTOS / "ckan" / f"{conjunto}.json"
            if f.exists():
                div += json.loads(f.read_text()).get("_divergencias_package_show", [])
    if div:
        d = _pd.DataFrame(div)
        d.insert(0, "consultado_em", agora)
        destino = MANIFESTOS / "ckan_divergencias_package_show.csv"
        d.to_csv(destino, mode="a", header=not destino.exists(), index=False)
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
