"""Normalização de horários para o horário de Brasília (UTC-3).

Os logs e os BUs registram o relógio interno da urna, ajustado à hora LOCAL.
Em 2022 (Res.-TSE 23.674/2021, art. 2º) e 2026 (Res.-TSE 23.751/2026, arts. 129 e
160) a votação ocorre das 8h às 17h de Brasília em todo o país; no exterior vale o
horário local (Res. 23.669/2021, art. 68).

- Fuso aplicado = fuso legal: exceção municipal (config.FUSO_MUNICIPIO) ou padrão da UF.
- Validação: fuso empírico por município = hora local da mediana do primeiro voto − 11
  (mediana entre 8h e 9h locais => UTC-3; 7h-8h => UTC-4; 6h-7h => UTC-5; 9h-10h => UTC-2).
  Divergências entre legal e empírico são registradas como achados (Teste D).
- Exterior (ZZ): analisado em hora local; não há conversão para Brasília.
- Conversão: hora_Brasília = hora_local + (−3 − fuso).
"""
from __future__ import annotations

from .config import FUSO_MUNICIPIO, FUSO_UF


def fuso(uf: str, cd_municipio: int) -> int | None:
    if uf == "ZZ":
        return None
    return FUSO_MUNICIPIO.get(int(cd_municipio), FUSO_UF.get(uf))


def sql_fuso(col_uf: str = "uf", col_mun: str = "cd_municipio") -> str:
    """Expressão SQL (DuckDB) do fuso legal; NULL para o exterior."""
    mun = " ".join(f"WHEN {k} THEN {v}" for k, v in FUSO_MUNICIPIO.items())
    ufs = " ".join(f"WHEN '{k}' THEN {v}" for k, v in FUSO_UF.items())
    return (f"(CASE WHEN {col_uf} = 'ZZ' THEN NULL ELSE coalesce(CASE {col_mun} {mun} END, "
            f"CASE {col_uf} {ufs} END) END)")


def sql_desloc_brt(col_uf: str = "uf", col_mun: str = "cd_municipio") -> str:
    """Segundos a somar à hora local para obter a hora de Brasília (0 no exterior: hora local)."""
    return f"coalesce((-3 - {sql_fuso(col_uf, col_mun)}) * 3600, 0)"
