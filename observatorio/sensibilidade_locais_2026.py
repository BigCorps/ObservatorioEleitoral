"""Análise de sensibilidade: código do local do BU-CSV versus Detalhe por seção.

Refaz as comparações no mesmo local para 2026 e a correspondência 2022×2026
com ambas as codificações, sem modificar os arquivos de entrada.
Uso: python -m observatorio.sensibilidade_locais_2026
"""
from __future__ import annotations

from pathlib import Path
import duckdb
import pandas as pd

from .config import PROCESSADOS, RESULTADOS
from .horario_historico import (
    carregar, _base_regressao, _wls_fe, _historico_mesmas_secoes, LOCAL
)

ANTERIOR = (PROCESSADOS / "historico" / "antes_consolidado_2026-10-29"
            / "secoes_oficiais_2026_2t.parquet")
SAIDA = RESULTADOS / "2026" / "consolidado_2t"


def executar() -> pd.DataFrame:
    if not ANTERIOR.exists():
        raise FileNotFoundError(
            f"Falta cópia histórica do Detalhe por seção: {ANTERIOR}. "
            "Não refazer download sem conferir o backup."
        )
    con = duckdb.connect()
    con.execute("SET memory_limit='6GB'")
    for ano in (2022, 2026):
        carregar(con, ano)
    con.execute("CREATE TABLE b2026_original AS SELECT * FROM b2026")
    n_original = con.execute("SELECT count(*) FROM b2026_original").fetchone()[0]
    con.execute(f"""CREATE TABLE tabela_local_detalhe AS SELECT uf, cd_municipio, nr_zona, nr_secao,
                 nr_local_votacao
                 FROM '{ANTERIOR}' WHERE uf <> 'ZZ'""")
    originais_detalhe = con.execute("""SELECT
        count(*) n, count(DISTINCT (uf, cd_municipio, nr_zona, nr_secao)) n_dist
        FROM tabela_local_detalhe""").fetchone()
    if originais_detalhe[0] != originais_detalhe[1]:
        raise AssertionError("Detalhe por seção possui chaves duplicadas")
    contagem = con.execute("""SELECT count(*),
       count(*) FILTER (b.nr_local_votacao IS DISTINCT FROM d.nr_local_votacao)
       FROM b2026_original b JOIN tabela_local_detalhe d
       USING (uf, cd_municipio, nr_zona, nr_secao)""").fetchone()
    if contagem[0] != n_original:
        raise AssertionError("Amostra de seções mudou no pareamento dos metadados")
    diferem = int(contagem[1])
    saida = []
    for fonte in ("BU_CSV", "DETALHE_SECAO"):
        if fonte == "DETALHE_SECAO":
            con.execute("""CREATE OR REPLACE TABLE b2026 AS SELECT
                b.* EXCLUDE (nr_local_votacao),
                d.nr_local_votacao AS nr_local_votacao
                FROM b2026_original b JOIN tabela_local_detalhe d
                USING (uf, cd_municipio, nr_zona, nr_secao)""")
        else:
            con.execute("CREATE OR REPLACE TABLE b2026 AS SELECT * FROM b2026_original")
        df = _base_regressao(con, 2026)
        for controles in ([], ["s13_1t", "comp_pct", "log_aptos"]):
            r = _wls_fe(df, "late17", "s13", "validos", LOCAL, controles)
            if r is None:
                raise AssertionError("Nenhum local comparável identificado")
            saida.append({
                "fonte_codigo_local": fonte, "teste": "efeito_2026_mesmo_local",
                "controles": ",".join(controles) or "nenhum",
                "codigos_divergentes_brasil": diferem, **r
            })
        pares, deltas = _historico_mesmas_secoes(con)
        pares_total = int(pares.secoes.sum())
        for _, d in deltas[
            (deltas.comparacao == "mesmo_local") &
            (deltas.controles != "nenhum")
        ].iterrows():
            saida.append({
                "fonte_codigo_local": fonte,
                "teste": "evolucao_2022_2026_" + d.grupo_tardio,
                "controles": d.controles,
                "codigos_divergentes_brasil": diferem,
                "secoes_correspondentes": pares_total,
                "locais_comparaveis": int(d.locais_comparaveis),
                "secoes": int(d.secoes),
                "secoes_tardias": int(d.secoes_tardias),
                "efeito_pp": d.efeito_pp,
                "erro_padrao_pp": d.erro_padrao_pp,
                "ic95_inf": d.ic95_inf,
                "ic95_sup": d.ic95_sup,
            })
    con.close()
    resultado = pd.DataFrame(saida)
    SAIDA.mkdir(parents=True, exist_ok=True)
    destino = SAIDA / "sensibilidade_codigo_local.csv"
    resultado.to_csv(destino, index=False)
    print("Códigos divergentes entre fontes no Brasil:", diferem)
    print(resultado.to_string(index=False))
    return resultado


if __name__ == "__main__":
    executar()
