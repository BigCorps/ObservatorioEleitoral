"""Gera um diagnóstico do log para cada seção com incompatibilidade log × BU não explicada.

Uso: python scripts/diagnosticar_incompatibilidades.py ANO
Saída: resultados/ANO/diagnosticos/<arquivo>.txt (sem dados pessoais).
"""
import subprocess
import sys

import duckdb

sys.path.insert(0, ".")
from observatorio.config import PROCESSADOS, RESULTADOS  # noqa: E402

ano = sys.argv[1]
pasta = RESULTADOS / ano / "diagnosticos"
pasta.mkdir(parents=True, exist_ok=True)
casos = duckdb.sql(f"""
  SELECT DISTINCT i.turno, i.uf, l.arquivo FROM read_csv('{RESULTADOS}/{ano}/incompatibilidades.csv') i
  JOIN read_parquet('{PROCESSADOS}/logs/{ano}_*.parquet', union_by_name=true) l
    ON l.turno=i.turno AND l.uf=i.uf AND l.cd_municipio=i.cd_municipio AND l.nr_zona=i.nr_zona AND l.nr_secao=i.nr_secao
  WHERE i.teste='B6' AND i.classificacao <> 'Diferença explicada'
    AND i.campo IN ('comparecimento_vs_votos_computados', 'biometria_nh_vs_liberacao_manual_no_log')""").fetchall()
for turno, uf, arq in casos:
    saida = pasta / f"{turno}t_{uf}_{arq}.txt"
    if saida.exists():
        continue
    r = subprocess.run([sys.executable, "scripts/diagnosticar_secao.py", ano, str(turno), uf, arq],
                       capture_output=True, text=True)
    saida.write_text(r.stdout + (("\nERRO: " + r.stderr[-500:]) if r.returncode else ""), encoding="utf-8")
    print(saida.name, flush=True)
