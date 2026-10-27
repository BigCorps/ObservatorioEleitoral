#!/bin/bash
# Etapas finais após a coleta do 2º turno de 2026 pelo Portal de Resultados.
# Uso: bash scripts/concluir_2t2026.sh [caminho/secoes_logs_brasil.parquet do Agnoletto]
set -e
cd "$(dirname "$0")/.."
while pgrep -f "scripts/processar_portal.py" >/dev/null; do sleep 20; done
n=$(python3 -c "import csv;print(len({r['uf'] for r in csv.DictReader(open('manifestos/cobertura_arquivos_urna.csv')) if r['ano']=='2026' and r['turno']=='2'}))")
echo "UFs do 2º turno de 2026 na cobertura: $n"
[ "$n" = 28 ] || { echo "cobertura incompleta: não prosseguir"; exit 1; }
python3 scripts/decodificar_bus.py
python3 scripts/executar_analises.py 2026 --sem-oficiais
python3 scripts/comparar_estudos_externos.py "$1"
python3 -c "from observatorio import historico; historico.executar(); print('historico ok')"
python3 -c "from observatorio import testes_historicos as T; print(T.executar())"
python3 scripts/gerar_relatorios.py
echo FIM2T2026
