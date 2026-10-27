"""Gera todos os documentos de resultados a partir de resultados/ e manifestos/."""
import sys

sys.path.insert(0, ".")
from observatorio.relatorios import escrever_tudo  # noqa: E402

print(escrever_tudo())
