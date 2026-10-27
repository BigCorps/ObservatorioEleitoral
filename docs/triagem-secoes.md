# Triagem exploratória por seção — metodologia e limites

## Objetivo

Localizar **padrões que merecem conferência** em resultados presidenciais oficiais, não atribuir fraude a eleitor, mesário, seção, equipamento, partido ou candidato. O destaque é **descritivo**, não uma acusação nem uma probabilidade de irregularidade.

Os testes operam em seções agregadas do TSE (BU-CSV, preferencial; na ausência do BU do turno, Detalhe por Seção + Votação por Seção — DSEC+VSEC). O ano e o turno são registrados no manifesto. O código lê Parquets já preparados pelo Observatório, sem baixar arquivos, sem depender de logs e sem acessar votos individuais.

### Comandos

    python scripts/gerar_triagem_secoes.py --ano 2022 --ano 2026
    python -m pytest -q tests/test_triagem_secoes.py

Caso faltem arquivos locais, o processo para com erro explícito (não converte ausência em zero). Antes, execute os conversores existentes para preparar os Parquets das seções.

**Não rodar processamento pesado dentro do GitHub Pages ou no deploy.** Gerar, revisar e versionar apenas resultados consolidados.

## Testes de triagem

| Teste | Critério | Limite de interpretação |
|---|---|---|
| Concentração 90% | Um candidato recebeu ≥90% dos válidos, com ≥100 válidos na seção | Não é probabilidade matemática nem prova de fraude |
| Concentração 95% | Mesmo critério com ≥95% | Subconjunto do teste acima |
| Unanimidade | Um candidato recebeu 100% dos válidos | Inclui seções pequenas; contextualizar tamanho |
| Diferença entre seções pares | 13 ou 22 difere ≥25 pontos percentuais dos demais votos do mesmo local (≥2 seções pares e ≥200 válidos); usar zona se faltarem pares (≥5 pares e ≥1.000 válidos) | A própria seção é retirada da média dos pares. Explicitar se a comparação é local ou zonal |
| Mudança 20/30/40 p.p. | Mudança do percentual do 13 ou 22 entre turnos em seção comparável, com ≥100 válidos em cada turno | Mudança líquida, não transferência identificável de eleitores |
| Inversão 13×22 | Inversão da liderança relativa dos dois números no mesmo local e seção | Não equivale necessariamente à mudança do vencedor geral no primeiro turno |
| Comparecimento | Mudança ≥20 p.p. sobre aptos entre turnos | Pode decorrer de mudanças de composição e transferências temporárias |
| Brancos + nulos | Mudança ≥15 p.p. sobre comparecimento | Não identifica votos de indivíduos |
| Múltiplos indicadores | Pelo menos dois grupos distintos de indicadores | Apenas triagem prioritária, sem escore de fraude |
| União | Seções distintas com pelo menos um indicador | Não somar as outras linhas, que se sobrepõem |

**Critério de comparabilidade entre turnos:** mesmo identificador de seção, mesmo local e eleitorado apto com variação não superior a 10 eleitores ou 5%, além de ≥100 válidos nos dois turnos. É uma salvaguarda heurística, não garantia de que as pessoas são as mesmas. Não comparar o mesmo número de seção entre 2022 e 2026 como se fosse o mesmo eleitorado. Entre anos, comparar taxas dos agregados territoriais e registrar diferenças de composição.

## Como ler a dimensão

- **Seções sinalizadas:** número de seções que satisfazem o teste; uma seção pode entrar em vários testes.
- **Seções elegíveis:** seções com dados suficientes para cada teste. Percentual de seções usa esta base.
- **Votos válidos em seções sinalizadas:** *todos* os votos válidos dessas seções, **não** votos suspeitos, irregulares ou afetados.
- **Percentual de votos nas seções sinalizadas:** soma dos válidos dessas seções dividida pelo total de válidos no recorte.
- **Brasil:** 27 UFs + exterior (ZZ). Exterior mantém consulta separada. Os testes de pares no exterior são locais e exigem contexto.
- **Exemplos exibidos:** os 15 mais extremos por teste/UF e no Brasil, não uma listagem exaustiva nem amostra representativa.

Não interpretar ausência de resultados como zero. Mudanças estatísticas não demonstram causa; p-valores requerem modelo e correção para múltiplas comparações.

## Artefatos gerados por ano

1. resultados/ANO/triagem_secoes_resumo.csv — totais por UF (e Brasil), turno e teste.
2. resultados/ANO/triagem_secoes_exemplos.csv — exemplos selecionados com município, zona, local, seção, contagens, percentuais e referências.
3. resultados/ANO/triagem_secoes_metadados.json — geração, origem dos arquivos e cobertura processada.

Intermediários Parquet ficam fora do Git. Não publicar nomes de eleitores, CPF, título, biometria individual ou ligação entre registro temporal e voto.

## Antes de publicar

Conferir cobertura real, seção única por turno, reconciliação com dados oficiais, denominadores, tamanho mínimo, mudança de local e aptos. Validar amostras dos extremos contra os arquivos originais. Se o 2º turno de 2026 vier de DSEC+VSEC, declarar isso até chegar o BU consolidado. Fazer integração apenas após concluir o processamento concorrente do Codex.

## Leitura do painel após integração do segundo turno de 2026

A seleção inicial é **concentração de 90% ou mais**, pois o teste `qualquer` é dominado em alguns segundos turnos por inversões de liderança relativa entre 13 e 22. A inversão entre esses dois números pode decorrer da redistribuição dos votos destinados a outros candidatos no primeiro turno; por isso é um teste **descritivo separado**, não uma irregularidade.

Os números oficiais consolidados do recorte Brasil para o segundo turno são: 2022 — 8.800 seções com concentração ≥90% e 2.079 ≥95%; 2026 — 6.615 ≥90% e 1.539 ≥95%. A união de indicadores contém inversões e sobreposições: 30.819 de 472.027 seções elegíveis (6,53%) em 2022 e 39.178 de 499.205 (7,85%) em 2026, e **não representa 6,53% ou 7,85% de votos irregulares**. A lista de exemplos apresenta "marcações" quando uma seção atende vários limiares sobrepostos, não o número de causas independentes.

Para os testes que dependem da comparação entre turnos, o 1º turno mostra **não aplicável**; bases com zero seções elegíveis mostram **sem base elegível**, não porcentagem zero.
