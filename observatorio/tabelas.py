"""Conversão dos CSVs oficiais do TSE (dentro de ZIPs) para Parquet.

Todos os campos são lidos como texto (all_varchar) para não haver conversão
silenciosa: valores especiais do TSE ("#NULO#", "#NE#", -1, -3) são tratados
explicitamente nas consultas, e um campo ausente NUNCA vira zero.
"""
from __future__ import annotations

import fnmatch
import shutil
import tempfile
import zipfile
from pathlib import Path

import duckdb

from .config import DADOS, PROCESSADOS


def csv_zip_para_parquet(zip_path: Path, saida: Path, padrao: str = "*.csv",
                         filtro_sql: str | None = None, colunas: str = "*",
                         agrupar: str | None = None, prefiltro: bytes | None = None) -> int:
    """Extrai os CSVs que casam com `padrao` e grava um Parquet. Retorna nº de linhas.

    `prefiltro`: se informado, só são copiadas para o disco a linha de cabeçalho e as
    linhas que contêm esses bytes (economia de disco em CSVs de dezenas de GB). O
    filtro exato continua sendo `filtro_sql`, aplicado depois pelo DuckDB.
    """
    saida.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(dir=DADOS))
    try:
        arquivos = []
        with zipfile.ZipFile(zip_path) as z:
            for n in z.namelist():
                if fnmatch.fnmatch(Path(n).name, padrao) and "/" not in n.strip("/"):
                    destino = tmp / Path(n).name
                    with z.open(n) as src, destino.open("wb") as dst:
                        if prefiltro is None:
                            shutil.copyfileobj(src, dst, 1 << 22)
                        else:
                            dst.write(src.readline())
                            for linha in src:
                                if prefiltro in linha:
                                    dst.write(linha)
                    arquivos.append(str(destino))
        if not arquivos:
            raise FileNotFoundError(f"nenhum CSV '{padrao}' em {zip_path}")
        con = duckdb.connect()
        con.execute("SET preserve_insertion_order=false")
        con.execute("SET enable_progress_bar=false")
        lista = "[" + ",".join(f"'{a}'" for a in arquivos) + "]"
        where = f"WHERE {filtro_sql}" if filtro_sql else ""
        if agrupar:
            where += f" GROUP BY {agrupar}"
        con.execute(f"""
            COPY (SELECT {colunas} FROM read_csv({lista}, delim=';', header=true, quote='"',
                         encoding='latin-1', all_varchar=true, union_by_name=true,
                         filename=true) {where})
            TO '{saida}' (FORMAT parquet, COMPRESSION zstd)""")
        n = con.execute(f"SELECT count(*) FROM '{saida}'").fetchone()[0]
        con.close()
        return n
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def parquet(nome: str) -> Path:
    return PROCESSADOS / "tabelas" / f"{nome}.parquet"
