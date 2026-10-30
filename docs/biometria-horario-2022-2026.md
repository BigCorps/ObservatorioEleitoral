# Biometria nas seções com votos após 17h — quatro turnos (2022 e 2026)

Esta nota registra o resultado agregado por hora e o **cruzamento por seção executado em 30/10/2026** nos Parquets locais (sem novos downloads). Nenhum voto individual é atribuído a candidato nem a eleitor identificado sem biometria: os resultados por candidato são sempre os da **seção inteira**.

Fontes: `resultados/2022/biometria_modalidade_por_hora.csv`, `resultados/2026/biometria_modalidade_por_hora.csv`, `observatorio/logs.py`, `observatorio/biometria.py`.

| Ano | Turno | Falha biométrica antes de 17h (% das modalidades classificadas) | A partir de 17h (%) | Diferença p.p. | Manuais a partir de 17h | Total habilitações a partir de 17h |
|---|---:|---:|---:|---:|---:|---:|
| 2022 | 1º | 8,8113 | 9,0166 | +0,2053 | 379.701 | 4.213.509 |
| 2022 | 2º | 8,1478 | 9,7163 | +1,5685 | 3.415 | 35.380 |
| 2026 | 1º | 6,7249 | 5,1669 | −1,5580 | 186.082 | 3.601.534 |
| 2026 | 2º | 6,7521 | 8,0894 | +1,3374 | 2.507 | 30.991 |

**Definição:** modalidade 1 = reconhecimento biométrico; 2 = sem biometria cadastrada; 3 = liberação manual após falha; 0 = não classificada. O denominador da porcentagem inclui somente 1+2+3; o total de habilitações pode incluir modalidade 0. O período é da **habilitação**, que pode anteceder o voto computado. Dados do Brasil, sem exterior, fuso legal de cada município para horário de Brasília.

**Limitação importante:** as porcentagens acima agregam todas as urnas por horário, não apenas as seções com voto após 17h. Não se pode usá-las para concluir que as seções tardias tinham taxas diferentes das vizinhas. Ademais, a codificação e a cobertura de biometria evoluíram entre 2022 e 2026.

## Cruzamento por seção (executado em 30/10/2026)

Código: `observatorio/biometria_secoes_tardias.py`. Execução: `python -m observatorio.biometria_secoes_tardias` (3 min, sem
downloads). Arquivos em `resultados/comparativo/`:

- `biometria_secoes_tardias_por_uf.csv`: seções com voto após 17h no 2º turno × demais, por UF e turno (224 linhas);
- `biometria_secoes_tardias_mesmas_secoes.csv`: seções correspondidas 2022×2026 pelas quatro transições de voto tardio (448 linhas);
- `biometria_secoes_tardias_pareado.csv`: 12 comparações dentro do mesmo local ou município;
- `biometria_secoes_tardias_faixas_votos.csv`: votos da seção inteira por faixa de liberação manual (1.098 linhas).

**Grupo tardio:** seção com ao menos um voto computado **estritamente após 17:00:00** (horário de Brasília, fuso legal de
cada município) no 2º turno daquele ano. O mesmo grupo é usado para os dois turnos. Exterior excluído.

### Validação

| verificação | resultado |
|---|---|
| Seções tardias × auditoria de horários | **34.455 (2022) e 29.609 (2026)**, iguais às já publicadas; votos após 17h nelas: 40.698 e **34.050** |
| BR = soma das UFs | sim, em todas as colunas de contagem dos quatro CSVs |
| Manuais e habilitações a partir de 17h × tabela por hora já publicada | 2026 2º turno 2.507 / 30.991 e 2022 2º turno 3.415 / 35.380: **iguais**; 1º turno com diferença ≤ 105 habilitações (seções sem log no 2º turno) |
| Liberação manual no log × "biometria não habilitada" no BU | 2026 2º turno: 8.633.583 × 8.632.462 (diferença de 0,01%) |
| Cobertura dos logs | 2022: 470.998 (1º) e 470.999 (2º) de 471.010 seções; 2026: 497.895 (1º) e 497.896 (2º) de 497.897 |
| Votos por faixa × BU em CSV | fecham exatamente: a diferença é só das seções sem log no turno ou no 2º turno — 23, 11, 3 e 1 seções, com 4.593, 2.234, 776 e 260 votos válidos (2022 1º/2º, 2026 1º/2º) |
| Seções sem etapa biométrica | 2022: 4.184 seções no 2º turno (3.350 ES, 830 MT, 4 outras) têm log, mas nenhuma habilitação com modalidade — coincide com "sem etapa biométrica" já publicado (886.371 eleitores no ES e 184.378 no MT). Ficam numa faixa própria, e não nas taxas. |

**Correção feita na execução:** a primeira versão descartava silenciosamente essas 4.184 seções da tabela de faixas, e
as somas de 2022 não fechavam. Os votos do 2º turno de 2026 passaram a vir do BU em CSV consolidado (fonte principal);
os votos são idênticos aos do Detalhe por seção.

### Resultados — 2º turno, Brasil sem exterior

| ano | grupo | seções | habilitações classificadas | liberação manual após falha | sem cadastro biométrico |
|---|---|---:|---:|---:|---:|
| 2022 | com voto após 17h | 34.455 | 9.652.697 | **7,07%** | 17,17% |
| 2022 | demais | 436.544 | 113.236.341 | **8,24%** | 15,17% |
| 2026 | com voto após 17h | 29.609 | 8.124.280 | **6,13%** | 5,83% |
| 2026 | demais | 468.287 | 119.734.840 | **6,79%** | 5,66% |

As seções com voto após 17h têm taxa de liberação manual **menor**, e não maior, nos dois anos, e também no 1º turno
(2026: 6,04% × 6,72%; 2022: 7,58% × 8,92%). Entre as habilitações feitas a partir de 17h nessas seções, a taxa manual é
8,09% (2026) e 9,72% (2022).

**Comparação no mesmo local de votação** (mínimos quadrados ponderados por habilitações, efeitos fixos de local; em p.p.):

| ano | sem controles | com controles (taxa manual do 1º turno, sem cadastro, comparecimento, aptos) |
|---|---:|---:|
| 2022 | −0,064 [−0,106; −0,023] | −0,015 [−0,047; 0,016] |
| 2026 | −0,064 [−0,099; −0,028] | −0,027 [−0,053; −0,001] |

No mesmo município as diferenças sem controles são maiores (−0,28 e −0,33 p.p.), mas caem para −0,04 e −0,08 p.p.
com controles. **Nas mesmas seções, de 2022 para 2026** (128.507 e 109.580 seções correspondidas), a mudança da taxa
manual nas seções tardias não é maior que a das vizinhas: −0,074 p.p. com controles (grupo de 2022) e −0,027
[−0,068; 0,015] (grupo de 2026). As diferenças são de centésimos de ponto percentual e não indicam liberação manual
concentrada nas seções com votos após 17h.

**Votos da seção inteira por faixa de liberação manual — 2026, 2º turno:**

| faixa manual | seções tardias | % 13 | % 22 | demais seções | % 13 | % 22 |
|---|---:|---:|---:|---:|---:|---:|
| 0–5% | 12.410 | 53,34 | 46,66 | 161.865 | 50,96 | 49,04 |
| 5–10% | 13.689 | 54,01 | 45,99 | 224.521 | 51,32 | 48,68 |
| 10–15% | 2.836 | 55,93 | 44,07 | 63.698 | 53,45 | 46,55 |
| 15–20% | 533 | 58,82 | 41,18 | 14.183 | 55,66 | 44,34 |
| 20%+ | 141 | 63,08 | 36,92 | 4.020 | 58,05 | 41,95 |

- **Gradiente por faixa:** a participação do 13 cresce com a taxa de liberação manual nos dois grupos e nos dois anos (2022,
  seções sem voto tardio: 49,79% na faixa 0–5% e 60,84% na faixa 20%+). A taxa de falha biométrica acompanha o perfil da
  seção (região, idade e ocupação dos eleitores, ver `docs/biometria-perfil-e-abstencao-por-idade.md`).
- **Seções tardias × demais na mesma faixa:** em 2026 as seções tardias dão de 2,4 a 5,0 p.p. a mais ao 13 em todas as
  faixas. A mesma diferença já existia **no 1º turno** nessas mesmas seções (faixa 0–5%: 46,19% × 44,57%; faixa 20%+:
  59,05% × 52,08%), portanto não surge com os votos após 17h do 2º turno. Em 2022 os dois grupos ficaram próximos
  (faixa 0–5%: 49,74% × 49,79%). O efeito controlado sobre o resultado já está estimado em
  `docs/horarios-2022-2026.md` e na verificação de 29/10 (+0,056 p.p. no mesmo local). **Essas porcentagens são da seção inteira e não mostram em quem votaram os eleitores liberados manualmente**: o
sigilo do voto impede essa associação.

### Limites

- Observacional: diferenças entre grupos não provam causa.
- A codificação das modalidades mudou entre 2022 e 2026 ("sem cadastro" 15–17% em 2022 contra 6% em 2026), então só se
  comparam níveis dentro do mesmo ano; entre anos, apenas mudanças nas mesmas seções.
- O horário é o da **habilitação**, que pode anteceder o voto computado.

No âmbito jurídico, o voto não depende exclusivamente da leitura biométrica: há conferência de documento, ano de
nascimento e procedimentos alternativos; vide Resolução TSE 23.751/2026, arts. 133 a 135.
