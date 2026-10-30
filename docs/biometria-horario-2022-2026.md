# Biometria nas seções com votos após 17h — quatro turnos (2022 e 2026)

Esta nota registra um resultado **já reproduzível com os CSVs por hora** do Observatório e descreve o cruzamento por seção preparado, mas ainda **não executado neste ambiente**. Não atribui votos individuais a candidatos.

Fontes: `resultados/2022/biometria_modalidade_por_hora.csv`, `resultados/2026/biometria_modalidade_por_hora.csv`, `observatorio/logs.py`, `observatorio/biometria.py`.

| Ano | Turno | Falha biométrica antes de 17h (% das modalidades classificadas) | A partir de 17h (%) | Diferença p.p. | Manuais a partir de 17h | Total habilitações a partir de 17h |
|---|---:|---:|---:|---:|---:|---:|
| 2022 | 1º | 8,8113 | 9,0166 | +0,2053 | 379.701 | 4.213.509 |
| 2022 | 2º | 8,1478 | 9,7163 | +1,5685 | 3.415 | 35.380 |
| 2026 | 1º | 6,7249 | 5,1669 | −1,5580 | 186.082 | 3.601.534 |
| 2026 | 2º | 6,7521 | 8,0894 | +1,3374 | 2.507 | 30.991 |

**Definição:** modalidade 1 = reconhecimento biométrico; 2 = sem biometria cadastrada; 3 = liberação manual após falha; 0 = não classificada. O denominador da porcentagem inclui somente 1+2+3; o total de habilitações pode incluir modalidade 0. O período é da **habilitação**, que pode anteceder o voto computado. Dados do Brasil, sem exterior, fuso legal de cada município para horário de Brasília.

**Limitação importante:** as porcentagens acima agregam todas as urnas por horário, não apenas as seções com voto após 17h. Não se pode usá-las para concluir que as seções tardias tinham taxas diferentes das vizinhas. Ademais, a codificação e a cobertura de biometria evoluíram entre 2022 e 2026.

## Teste por seção que falta executar

O código `observatorio/biometria_secoes_tardias.py` usa os Parquets locais já processados e gera:

- `resultados/comparativo/biometria_secoes_tardias_por_uf.csv`: taxas ponderadas de biometria, falha e ausência de cadastro nas seções tardias versus não tardias, por UF e turno; marca tardia se houve ao menos **um voto computado estritamente após 17:00:00 no segundo turno daquele ano**.
- `resultados/comparativo/biometria_secoes_tardias_mesmas_secoes.csv`: quatro turnos nas correspondências conservadoras 2022×2026, com as quatro transições de presença de voto tardio.
- `resultados/comparativo/biometria_secoes_tardias_pareado.csv`: comparação ponderada dentro do mesmo local/município, com e sem controles (taxa manual no primeiro turno daquela seção, ausência de cadastro, comparecimento e aptos), incluindo mudança 2022→2026 nas seções correspondentes.
- `resultados/comparativo/biometria_secoes_tardias_faixas_votos.csv`: resultados por seção em faixas fixas da proporção de liberação manual (0–5%, 5–10%, 10–15%, 15–20%, 20%+), separados por presença de voto após 17h, UF e cada um dos quatro turnos. **A porcentagem por candidato refere-se à seção inteira, jamais somente às pessoas liberadas manualmente.**

Os totais nacionais de seções com voto após 17h são validados contra a auditoria anterior: **34.455 (2022, 2º turno) e 29.609 (2026, 2º turno)**. Toda diferença persistente precisa ser comparada com tamanho e cobertura da amostra; a regressão é observacional e não prova causalidade.

Para executar **sem novos downloads**:

```bash
python -m observatorio.biometria_secoes_tardias
```

O BU com biometria não habilitada é lido do **turno correto**, inclusive quando a seção do 1º turno é associada ao grupo tardio definido pelo 2º turno.

Depois, revisar a integridade e a cobertura dos logs nas seções do grupo, verificar o alinhamento entre modalidade e horário de habilitação, conferir os totais do BU em CSV e comparar resultados com e sem seções incompletas. Excluir grupos do exterior do teste em horário de Brasília e relatar separadamente. **Só atualizar o painel depois de calcular e validar os novos CSVs.**

No âmbito jurídico, voto não depende exclusivamente da leitura biométrica: há conferência de documento, ano de nascimento e procedimentos alternativos; vide Resolução TSE 23.751/2026, arts. 133 a 135.
