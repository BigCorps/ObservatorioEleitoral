#!/bin/bash
cd "$(dirname "$0")/.."
python3 -c "from observatorio.reconciliacao import executar; r=executar(2026)['resumo']; r['nao']=r.divergencias-r.explicadas; print(r[r.divergencias>0][['teste','campo','divergencias','explicadas','nao']].to_string())"
python3 -c "from observatorio import estatistica; print(len(estatistica.executar(2026)))"
python3 scripts/diagnosticar_incompatibilidades.py 2026
python3 -c "from observatorio import graficos; print(graficos.gerar(2026))"
python3 -c "from observatorio import historico; historico.executar(); print('historico ok')"
python3 scripts/gerar_relatorios.py
echo FIMREFAZER
