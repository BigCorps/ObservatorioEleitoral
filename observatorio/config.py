"""Caminhos, constantes e tabelas de referência."""
from __future__ import annotations

import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DADOS = Path(os.environ.get("OBS_DADOS", RAIZ / "dados"))
BRUTOS = DADOS / "brutos"          # arquivos baixados (fora do Git)
PROCESSADOS = DADOS / "processados"  # parquet intermediário (fora do Git)
MANIFESTOS = RAIZ / "manifestos"    # inventários e registros de download (no Git)
RESULTADOS = RAIZ / "resultados"    # CSVs pequenos e gráficos (no Git)
DOCS = RAIZ / "docs"

CKAN_API = "https://dadosabertos.tse.jus.br/api/3/action"

UFS = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA",
    "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
]
UFS_COM_EXTERIOR = UFS + ["ZZ"]

# Conjuntos do Portal de Dados Abertos do TSE examinados.
DATASETS = {
    2022: [
        "resultados-2022-boletim-de-urna",
        "resultados-2022-arquivos-transmitidos-para-totalizacao",
        "resultados-2022",
        "eleitorado-2022",
    ],
    2026: [
        "resultados-2026-boletim-de-urna",
        "resultados-2026-arquivos-transmitidos-para-totalizacao",
        "resultados-2026",
        "eleitorado-2026",
    ],
}

# Fuso horário legal (horas em relação a UTC) por UF, sem horário de verão
# (extinto pelo Decreto 9.772/2019). Exceções municipais em FUSO_MUNICIPIO.
FUSO_UF = {uf: -3 for uf in UFS}
FUSO_UF.update({"AM": -4, "RR": -4, "RO": -4, "MT": -4, "MS": -4, "AC": -5})

# Exceções por código TSE de município (CD_MUNICIPIO).
# Preenchido em observatorio/fusos.py a partir dos nomes oficiais.
FUSO_MUNICIPIO: dict[int, int] = {}

# Horário oficial de votação em 2022 e 2026: 8h às 17h no horário de Brasília (UTC-3)
# em todo o território nacional (ver docs/metodologia.md para a base normativa).
INICIO_VOTACAO_BRT = 8
FIM_VOTACAO_BRT = 17
