"""Coleta seção a seção (Portal de Resultados do TSE) de todas as UFs de um turno.

Uso: python scripts/processar_portal.py ANO TURNO [UFs...] [--refazer]
Pula UF/turno já registrados na cobertura; pacotes menores primeiro.
"""
import csv
import os
import sys
import traceback

sys.path.insert(0, ".")
from observatorio.arquivos_secao import processar, secoes_oficiais  # noqa: E402
from observatorio.arquivos_urna import COBERTURA  # noqa: E402
from observatorio.config import UFS_COM_EXTERIOR  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith("--")]
ano, turno = int(args[0]), int(args[1])
ufs = args[2:] or UFS_COM_EXTERIOR
feitos = set()
if COBERTURA.exists() and "--refazer" not in sys.argv:
    with COBERTURA.open(encoding="utf-8") as f:
        feitos = {r["uf"] for r in csv.DictReader(f) if r["ano"] == str(ano) and r["turno"] == str(turno)}
fila = sorted((uf for uf in ufs if uf not in feitos), key=lambda u: len(secoes_oficiais(ano, turno, u)))
for uf in fila:
    try:
        c = processar(ano, turno, uf, workers=int(os.environ.get("OBS_WORKERS", "24")))
        print("OK", ano, turno, uf, c["secoes_no_pacote"], c["secoes_processadas"], c["secoes_com_falha"],
              c["integridade_log_ok"], c["duracao_s"], flush=True)
    except Exception:
        print("ERRO", ano, turno, uf, traceback.format_exc()[-800:], flush=True)
