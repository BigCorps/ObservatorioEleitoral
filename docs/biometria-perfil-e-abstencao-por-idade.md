# Falha de biometria, perfil do eleitorado e abstenção por idade

_Análise descritiva com dados oficiais do TSE. Nenhuma diferença aqui é indício de irregularidade._

Reprodução:

    python scripts/baixar_perfil_idade_secao.py 2022 2026     # perfil do eleitorado por seção (~3,6 GB, apagado após agregar)
    python scripts/baixar_comparecimento_idade.py              # comparecimento e abstenção por faixa etária (~430 MB)
    python -c "from observatorio import biometria_perfil as B; B.executar(); B.abstencao_idade()"

## 1. Biometria nas seções com mais de 80% para um candidato

Grupos: seções em que **o mesmo candidato** teve mais de 80% dos votos válidos no 1º **e** no 2º turno
(13 ou 22); demais seções. Taxas do log da urna no 2º turno, sem o exterior. "Falha" = eleitor liberado
manualmente após a biometria não ser reconhecida.

Arquivos: `resultados/comparativo/biometria_concentracao_perfil.csv`,
`biometria_gradiente_idade_escolaridade.csv`, `biometria_concentracao_padronizada.csv`.

| ano | grupo | seções | 60+ | 70+ | baixa escolaridade¹ | falha (liberação manual) |
|---|---|---|---|---|---|---|
| 2022 | mais de 80% para o 13 | 30.227 | 20,1% | 10,1% | 59,4% | 12,81% |
| 2022 | mais de 80% para o 22 | 1.321 | 21,1% | 9,0% | 38,0% | 11,01% |
| 2022 | demais | 439.111 | 21,1% | 9,5% | 32,7% | 7,80% |
| 2026 | mais de 80% para o 13 | 20.623 | 21,9% | 10,6% | 56,0% | 8,75% |
| 2026 | mais de 80% para o 22 | 3.588 | 24,4% | 10,8% | 34,5% | 8,08% |
| 2026 | demais | 473.296 | 23,7% | 10,9% | 29,8% | 6,67% |

¹ Analfabeto, lê e escreve ou fundamental incompleto.

A falha cresce com a proporção de idosos e com a baixa escolaridade em todas as seções (2026: de 5,1% no
quinto mais jovem a 9,0% no mais idoso; de 5,9% a 8,4% por escolaridade). Comparando cada grupo com as demais
seções **do mesmo município, com idade e escolaridade semelhantes** (padronização direta), o excesso cai para
**+0,26 e +0,57 p.p. (2022)** e **+0,35 e +0,38 p.p. (2026)** para os grupos do 13 e do 22 — simétrico entre
os candidatos. A comparação mais estrita cobre 61%–72% das seções concentradas (células de referência com
pelo menos 300 habilitados).

## 2. Abstenção dos eleitores com 80 anos ou mais (voto facultativo)

Fonte: "Perfil do comparecimento e abstenção" (Dados Abertos do TSE). Arquivo:
`resultados/comparativo/abstencao_faixa_etaria.csv` (Brasil e UF; grupos e faixas originais).

**Limitação:** em 28/10/2026, o arquivo de 2026 publicado pelo TSE (Last-Modified 21/10/2026, gerado em
13/10/2026) contém **somente o 1º turno**. A abstenção por idade no 2º turno de 2026 ainda não é observável.

| ano | turno | 80+ aptos | 80+ abstenção | % | total de abstenções |
|---|---|---|---|---|---|
| 2022 | 1º | 5.149.578 | 4.226.604 | 82,08% | 32.739.676 |
| 2022 | 2º | 5.149.578 | 4.049.766 | 78,64% | 32.186.397 |
| 2026 | 1º | 5.516.165 | 4.033.023 | 73,11% | 33.468.233 |
| 2026 | 2º | — | não publicado | — | 30.509.005² |

² Total do Detalhe da apuração por seção (2º turno de 2026).

- **2022 (medido):** as abstenções caíram 553.279 entre os turnos; os eleitores com 80+ responderam por
  **176.838** (32%) e os de 70–79 por 437.461, enquanto 18–69 tiveram 62.345 abstenções **a mais**.
- **2026 (não medido):** as abstenções caíram **2.960.167** entre os turnos. A única informação demonstrável é o
  teto: no 1º turno, 4.033.023 eleitores com 80+ se abstiveram. **Cenário** (não é medida): se a abstenção dos
  80+ tivesse caído como em 2022 (−3,43 p.p. sobre os aptos, ou 4,18% de quem se absteve no 1º turno), seriam
  cerca de **169 mil a 189 mil** votos, ~6% da queda total. O número real só poderá ser calculado quando o TSE
  publicar o 2º turno no mesmo conjunto.
