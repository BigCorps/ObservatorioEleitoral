"""Comparação auditável com o quadro por UF publicado pelo TSE em 27/10/2026.

Fonte: https://www.tse.jus.br/comunicacao/noticias/arquivos/total-de-votos-apos-17h
O quadro oficial descreve início de encerramento e horários sob critérios que
podem diferir da extração de eventos 'O voto do eleitor foi computado' do log.

Uso: python -m observatorio.confronto_horarios_tse
Requer apenas os Parquets de logs locais já processados; não baixa nada.
"""
from __future__ import annotations

from pathlib import Path
import duckdb
import pandas as pd

from .config import FUSO_UF, PROCESSADOS, RESULTADOS
from .fusos import sql_desloc_brt

FONTE = RESULTADOS / "2026" / "confronto_horarios_tse_uf.csv"
SAIDA = RESULTADOS / "2026" / "confronto_horarios_tse_logs_detalhe_uf.csv"
H17, H18, H19 = 17 * 3600, 18 * 3600, 19 * 3600


def executar() -> pd.DataFrame:
    referencia = pd.read_csv(FONTE)
    assert referencia.uf.nunique() == 27, "O quadro oficial deve conter 27 UFs"
    assert referencia.tse_apos17.sum() == 34393 and referencia.tse_apos19.sum() == 13
    caminhos = sorted(
        str(p) for p in (PROCESSADOS / "logs").glob("2026_2t_*.parquet")
        if "_amostra" not in p.name
    )
    if not caminhos:
        raise FileNotFoundError("Parquets de log de 2026, 2º turno, não encontrados")
    con = duckdb.connect()
    con.execute("SET memory_limit='6GB'")
    # Repete exatamente a conversão de fuso e o evento que a auditoria anterior usou.
    # Duas convenções de fuso: a legal por município (Noronha UTC-2; oeste do AM UTC-5), confirmada pela
    # mediana do primeiro voto, e a da UF inteira — que reproduz o quadro do TSE.
    fuso_uf = "CASE uf " + " ".join(f"WHEN '{k}' THEN {(-3 - v) * 3600}" for k, v in FUSO_UF.items()) + " END"
    con.execute(f"""CREATE TEMPORARY TABLE eventos AS SELECT uf, cd_municipio,
      unnest(votos_s) + {sql_desloc_brt()} AS instante, unnest(votos_s) + {fuso_uf} AS instante_fuso_uf
      FROM read_parquet({caminhos}, union_by_name=true)
      WHERE tem_log AND uf <> 'ZZ'""")
    contagem = con.execute(f"""SELECT uf,
        count(*) FILTER (instante = {H17}) exatamente_17h,
        count(*) FILTER (instante >= {H17}) desde_17h,
        count(*) FILTER (instante > {H17}) estritamente_depois_17h,
        count(*) FILTER (instante >= {H18} AND instante < {H19}) de_18h_a_19h,
        count(*) FILTER (instante = {H19}) exatamente_19h,
        count(*) FILTER (instante > {H19}) estritamente_depois_19h,
        count(*) FILTER (instante >= {H19}) desde_19h,
        count(*) FILTER (instante_fuso_uf >= {H17}) desde_17h_fuso_uf,
        count(*) FILTER (instante_fuso_uf >= {H18} AND instante_fuso_uf < {H19}) de_18h_a_19h_fuso_uf,
        count(*) FILTER (instante_fuso_uf > {H19}) depois_19h_fuso_uf
      FROM eventos GROUP BY uf ORDER BY uf""").df()
    con.close()
    if len(contagem) != 27:
        raise AssertionError(f"Esperadas 27 UFs com logs, recebidas {len(contagem)}")
    resultado = referencia.merge(contagem, on="uf", how="left", validate="one_to_one")
    resultado["diferenca_apos17_apos_incluir_limite"] = (
        resultado.tse_apos17 - resultado.desde_17h
    )
    resultado["diferenca_apos19_estrita"] = (
        resultado.tse_apos19 - resultado.estritamente_depois_19h
    )
    resultado["diferenca_apos19_inclusiva"] = (
        resultado.tse_apos19 - resultado.desde_19h
    )
    resultado["diferenca_18h_a_19h"] = (
        resultado.tse_18_19 - resultado.de_18h_a_19h
    )
    resultado["diferenca_apos17_fuso_uf"] = resultado.tse_apos17 - resultado.desde_17h_fuso_uf
    resultado["diferenca_18h_a_19h_fuso_uf"] = resultado.tse_18_19 - resultado.de_18h_a_19h_fuso_uf
    resultado["diferenca_apos19_fuso_uf"] = resultado.tse_apos19 - resultado.depois_19h_fuso_uf
    resultado.to_csv(SAIDA, index=False)
    print("Totais TSE: depois 17h =", int(resultado.tse_apos17.sum()),
          "; após 19h =", int(resultado.tse_apos19.sum()))
    print("Totais logs: desde 17h =", int(resultado.desde_17h.sum()),
          "; após 19h =", int(resultado.estritamente_depois_19h.sum()))
    print("Diferença residual 17h =", int(resultado.diferenca_apos17_apos_incluir_limite.sum()),
          "; diferença residual 19h =", int(resultado.diferenca_apos19_estrita.sum()))
    print("Com o fuso único da UF (convenção do quadro do TSE): diferenças 17h / 18-19h / 19h =",
          int(resultado.diferenca_apos17_fuso_uf.abs().sum()), int(resultado.diferenca_18h_a_19h_fuso_uf.abs().sum()),
          int(resultado.diferenca_apos19_fuso_uf.abs().sum()))
    return resultado


if __name__ == "__main__":
    executar()
