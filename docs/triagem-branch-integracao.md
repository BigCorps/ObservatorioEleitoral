# Handoff — feature/auditoria-secoes-extremos-2026

Esta branch foi criada enquanto o Codex processava o segundo turno de 2026 na main. **Não fazer merge antes da revisão final dos arquivos e da validação dos dados.**

## Quando o Codex concluir

1. Conferir HEAD de main, comparar com esta branch e integrar preservando as alterações de processamento, resultados e fontes feitas pelo Codex.
2. Validar esquemas dos Parquets das seções de 2022 e 2026 e, se o segundo turno ainda não possuir BU-CSV, usar as tabelas oficiais DSEC+VSEC.
3. Executar os testes sintéticos desta branch e a suíte existente. Fazer amostragem de casos extremos diretamente nos arquivos originais.
4. Executar: python scripts/gerar_triagem_secoes.py --ano 2022 --ano 2026
5. Revisar cobertura, fontes, ausência de dados, percentual dos votos em seções sinalizadas versus votos afetados, que não podem ser inferidos desta triagem.
6. Verificar a interface em celular e computador, Brasil + ZZ, UF, eleição e turno. A ausência dos CSVs deve exibir estado pendente, nunca zero.
7. Versionar os resultados validados e deixar uma única execução de GitHub Pages na main. Evitar Vercel e downloads repetidos.

Nenhuma estatística desta triagem deve ser apresentada como prova de irregularidade eleitoral.
