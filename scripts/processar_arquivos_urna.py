"""Processa os pacotes de arquivos de urna (logs + BU binário) de várias UFs/turnos.

Uso: python scripts/processar_arquivos_urna.py ANO TURNOS [UFs...] [--refazer]
Ex.: python scripts/processar_arquivos_urna.py 2022 1,2
Pula UF/turno já registrados em manifestos/cobertura_arquivos_urna.csv (exceto com --refazer).
Ordem: pacotes menores primeiro. Falha de uma UF não interrompe as demais.
"""
import csv
import sys
import traceback

sys.path.insert(0, ".")
from observatorio.arquivos_urna import COBERTURA, processar  # noqa: E402
from observatorio.catalogo import carregar_inventario  # noqa: E402
from observatorio.config import UFS_COM_EXTERIOR  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith("--")]
refazer = "--refazer" in sys.argv
ano = int(args[0])
turnos = [int(t) for t in args[1].split(",")]
ufs = args[2:] or UFS_COM_EXTERIOR
feitos = set()
if COBERTURA.exists() and not refazer:
    with COBERTURA.open(encoding="utf-8") as f:
        feitos = {(r["ano"], r["turno"], r["uf"]) for r in csv.DictReader(f)}
tam = {(l["turno"], l["uf"]): int(l["tamanho_bytes"] or 0) for l in carregar_inventario()
       if l["tipo"] == "arquivos_urna" and l["ano"] == str(ano)}
fila = [(t, uf) for t in turnos for uf in ufs if (str(t), uf) in tam and (str(ano), str(t), uf) not in feitos]
fila.sort(key=lambda x: tam[(str(x[0]), x[1])])
for t, uf in fila:
    try:
        c = processar(ano, t, uf, workers=16, progresso=False)
        print("OK", ano, t, uf, c["secoes_no_pacote"], c["secoes_processadas"], c["secoes_com_falha"],
              c["duracao_s"], flush=True)
    except Exception:
        print("ERRO", ano, t, uf, traceback.format_exc()[-800:], flush=True)
