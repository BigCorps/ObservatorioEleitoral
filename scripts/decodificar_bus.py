"""Decodifica os .bu binários guardados em dados/brutos/bu/*.zip para Parquet.

Uso: python scripts/decodificar_bus.py [--refazer]
Só processa ZIPs cuja cobertura já foi registrada (pacote concluído).
"""
import csv
import sys

sys.path.insert(0, ".")
from observatorio.arquivos_urna import COBERTURA  # noqa: E402
from observatorio.bu_asn1 import decodificar_zip  # noqa: E402
from observatorio.config import BRUTOS, PROCESSADOS  # noqa: E402

refazer = "--refazer" in sys.argv
with COBERTURA.open(encoding="utf-8") as f:
    concluidos = {f"{r['ano']}_{r['turno']}t_{r['uf']}" for r in csv.DictReader(f)}
for z in sorted((BRUTOS / "bu").glob("*.zip")):
    if z.stem not in concluidos:
        continue
    saida = PROCESSADOS / "bu" / f"{z.stem}.parquet"
    if saida.exists() and saida.stat().st_mtime > z.stat().st_mtime and not refazer:
        continue
    print(z.stem, decodificar_zip(z, saida), flush=True)
