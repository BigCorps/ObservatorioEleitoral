#!/bin/bash
# Etapas finais de 2022 (retomada após interrupção).
cd "$(dirname "$0")/.."
python3 -c "from observatorio import biometria; biometria.executar(2022); print('biometria ok')"
python3 -c "from observatorio.reconciliacao import executar; print(executar(2022)['resumo'].divergencias.sum())"
python3 scripts/diagnosticar_incompatibilidades.py 2022
python3 -c "from observatorio import graficos; print(graficos.gerar(2022))"
python3 scripts/gerar_relatorios.py
echo FIM
