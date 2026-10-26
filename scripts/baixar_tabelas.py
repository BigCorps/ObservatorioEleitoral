"""Baixa (com verificação) os arquivos tabulares oficiais necessários às análises.

Uso: python scripts/baixar_tabelas.py [ano ...]
Os pacotes de arquivos de urna (logs/BU binários) NÃO são baixados aqui: são
lidos seletivamente por `observatorio.arquivos_urna`.
"""
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, ".")
from observatorio.catalogo import carregar_inventario  # noqa: E402
from observatorio.download import baixar  # noqa: E402

TIPOS = ["historico_totalizacao_presidente", "detalhe_votacao_munzona", "votacao_candidato_munzona",
         "detalhe_votacao_secao", "secoes_agregadas", "transf_temporaria_secao", "perfil_eleitorado",
         "relatorio_totalizacao", "bu_csv", "votacao_secao", "perfil_eleitor_secao"]

anos = [a for a in sys.argv[1:]] or ["2022", "2026"]
inv = [l for l in carregar_inventario() if l["ano"] in anos and l["tipo"] in TIPOS]
inv.sort(key=lambda l: (TIPOS.index(l["tipo"]), int(l["tamanho_bytes"] or 0)))
print(len(inv), "arquivos", sum(int(l["tamanho_bytes"] or 0) for l in inv) / 1e9, "GB", flush=True)


def tarefa(l):
    try:
        r = baixar(l["url"])
        print(r.get("status"), r.get("hash_oficial_confere", ""), l["url"].rsplit("/", 1)[-1], flush=True)
    except Exception as e:
        print("ERRO", l["url"], repr(e), flush=True)


with ThreadPoolExecutor(4) as ex:
    list(ex.map(tarefa, inv))
