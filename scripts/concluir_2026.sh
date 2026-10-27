#!/bin/bash
# Etapas finais de 2026 + comparação histórica + relatórios.
cd "$(dirname "$0")/.."
while pgrep -f "^python3 scripts/processar_arquivos_urna.py" >/dev/null; do sleep 10; done
python3 scripts/executar_analises.py 2026 --sem-oficiais
python3 -c "from observatorio import historico; historico.executar(); print('historico ok')"
python3 scripts/gerar_relatorios.py
echo FIM2026
