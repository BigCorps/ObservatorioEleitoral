# Auditoria 2022 — Presidente

_Gerado automaticamente por `scripts/gerar_relatorios.py` em 29/10/2026 14:37 UTC. Todos os números vêm de `resultados/2022/`. Ver método em `docs/metodologia.md`._

## Cobertura dos arquivos de urna (logs e BU binário)

- 1º turno: 28 de 28 pacotes (27 UFs + exterior) processados; 472.024 seções lidas, 0 com falha de leitura, 165 sem log no pacote.
- 2º turno: 28 de 28 pacotes (27 UFs + exterior) processados; 472.027 seções lidas, 0 com falha de leitura, 44 sem log no pacote.

## 1. Totais nacionais reproduzidos a partir das seções

| turno | seções | aptos | comparecimento | abstenções | válidos | brancos | nulos | % abstenção | % brancos | % nulos |
|---|---|---|---|---|---|---|---|---|---|---|
| 1º | 472.028 | 156.453.354 | 123.682.372 | 32.770.982 | 118.229.719 | 1.964.779 | 3.487.874 | 20,946 | 1,589 | 2,820 |
| 2º | 472.028 | 156.453.354 | 124.252.796 | 32.200.558 | 118.552.353 | 1.769.678 | 3.930.765 | 20,582 | 1,424 | 3,163 |


Os totais nacionais publicados pelo TSE (histórico de totalização e detalhe por município/zona) são reproduzidos pela soma das seções; a única diferença em *aptos* corresponde a eleitores de seções não instaladas, que não têm BU (ver B5 abaixo).

### Mudança entre turnos: comparecimento, brancos, nulos e válidos

**Classificação:** Conferido

- **O que verificamos?** Se a variação dos votos válidos entre os turnos é exatamente a variação do comparecimento menos a variação de brancos e nulos, em cada seção, zona, município, UF e no Brasil.
- **O que os números mostram?** Brasil: comparecimento 570.424; brancos+nulos 247.790; válidos 322.634; resíduo da identidade 0. Abstenção variou -0,365 p.p. (de 20,95% para 20,58% dos aptos); brancos -0,164 p.p.; nulos 0,344 p.p. (sobre o comparecimento). Lula (13) variou 3.086.495 votos e Bolsonaro (22) 7.134.009.
- **O que significa?** As contas fecham em todos os níveis. Os aumentos de votos de cada candidato são variações LÍQUIDAS: não dizem quem trocou de voto, quem deixou de votar ou quem passou a votar.
- **Existe explicação conhecida?** Candidatos eliminados no 1º turno deixam de receber votos; eleitores podem mudar de voto, abster-se ou voltar a votar.
- **O que ainda não sabemos?** Transferências individuais de voto não são observáveis (voto secreto). Qualquer estimativa de transferência exigiria inferência ecológica, com incerteza grande e hipóteses fortes; não foi feita.
- **Como conferir?** `resultados/2022/resultados_brasil.csv`, `resultados_uf.csv`, `resultados_municipio.csv`, `resultados_zona.csv`; código `observatorio/resultados_eleitorais.py`.

## 2. Reconciliação entre fontes oficiais (Testes A, B, C, K)

| teste | campo | fonte_a | fonte_b | registros_comparados | divergencias | explicadas | não_explicadas |
|---|---|---|---|---|---|---|---|
| A2 | presenca | BWEB | BUBIN | 944.056 | 137 | 137 | 0 |
| A3 | presenca | DSEC | BWEB | 944.150 | 94 | 94 | 0 |
| B1 | comparecimento_vs_soma_votos | BWEB | BWEB | 944.056 | 0 | 0 | 0 |
| B2 | aptos | BWEB | BUBIN | 943.919 | 0 | 0 | 0 |
| B2 | biometria_nh_vs_lib_codigo | BWEB | BUBIN | 943.919 | 10.286 | 10.261 | 25 |
| B2 | brancos | BWEB | BUBIN | 943.919 | 0 | 0 | 0 |
| B2 | comparecimento | BWEB | BUBIN | 943.919 | 0 | 0 | 0 |
| B2 | nulos | BWEB | BUBIN | 943.919 | 0 | 0 | 0 |
| B2 | votos_nominais | BWEB | BUBIN | 943.919 | 0 | 0 | 0 |
| B2 | votos_por_candidato_soma_dif_abs | BWEB | BUBIN | 943.919 | 0 | 0 | 0 |
| B2c | votos_extra_no_bu | BUBIN | BWEB | 943.919 | 0 | 0 | 0 |
| B3 | abstencoes | BWEB | DSEC | 944.056 | 0 | 0 | 0 |
| B3 | aptos | BWEB | DSEC | 944.056 | 0 | 0 | 0 |
| B3 | brancos | BWEB | DSEC | 944.056 | 0 | 0 | 0 |
| B3 | comparecimento | BWEB | DSEC | 944.056 | 0 | 0 | 0 |
| B3 | nulos | BWEB | DSEC | 944.056 | 0 | 0 | 0 |
| B3 | votos_nominais | BWEB | DSEC | 944.056 | 0 | 0 | 0 |
| B4 | votos_candidato_zona | BWEB | CMZ | 70.541 | 0 | 0 | 0 |
| B5 | abstencoes | BWEB | DMZ | 12.566 | 82 | 82 | 0 |
| B5 | aptos | BWEB | DMZ | 12.566 | 84 | 84 | 0 |
| B5 | brancos | BWEB | DMZ | 12.566 | 82 | 82 | 0 |
| B5 | comparecimento | BWEB | DMZ | 12.566 | 82 | 82 | 0 |
| B5 | nulos | BWEB | DMZ | 12.566 | 82 | 82 | 0 |
| B5 | validos | BWEB | DMZ | 12.566 | 82 | 82 | 0 |
| B6 | biometria_nh_vs_liberacao_manual_no_log | BWEB | LOG | 943.842 | 51 | 9 | 42 |
| B6 | comparecimento_vs_votos_computados | BWEB | LOG | 943.842 | 127 | 9 | 118 |
| B6 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | BWEB | LOG | 943.842 | 670 | 595 | 75 |
| C1 | aptos_vs_comp_mais_abst | BWEB | BWEB | 944.056 | 0 | 0 | 0 |
| K1 | votos_votavel | BWEB | VSEC | 5.380.733 | 0 | 0 | 0 |
| K2 | brancos | DSEC | VSEC | 944.056 | 0 | 0 | 0 |
| K2 | nulos | DSEC | VSEC | 944.056 | 0 | 0 | 0 |
| K2 | votos_nominais | DSEC | VSEC | 944.056 | 0 | 0 | 0 |


Legenda: BWEB = BU publicado em CSV; BUBIN = arquivo .bu transmitido pela urna; LOG = log da urna; DSEC = detalhe da apuração por seção; VSEC = votação por seção; CMZ = votação nominal por município/zona; DMZ = detalhe por município/zona. A lista completa, caso a caso, está em `resultados/2022/incompatibilidades.csv`.

### Boletins de Urna, arquivos da urna e tabelas oficiais

**Classificação:** Conferido (com diferenças explicadas e incompatibilidades listadas)

- **O que verificamos?** Se o mesmo número aparece igual em todas as publicações oficiais que deveriam coincidir, seção a seção (BU em CSV, BU binário, detalhe por seção, votação por seção) e na soma por zona.
- **O que os números mostram?** 20 de 32 comparações sem nenhuma divergência; 260 divergências ainda sem explicação documental (listadas abaixo).
- **O que significa?** Os votos publicados por seção são os mesmos do arquivo binário assinado gerado pela urna e das demais tabelas do TSE.
- **Existe explicação conhecida?** As divergências explicadas decorrem de seções não instaladas, seções apuradas pelo Sistema de Apuração (cédulas), campos opcionais omitidos no exterior e eleitores de seções não instaladas incluídos nos aptos por zona.
- **O que ainda não sabemos?** A verificação criptográfica das assinaturas dos arquivos (.vscmr) não foi feita nesta etapa.
- **Como conferir?** `resultados/2022/reconciliacao_resumo.csv` e `incompatibilidades.csv`; código `observatorio/reconciliacao.py`.

#### Incompatibilidades documentais ainda não explicadas

| teste | turno | uf | cd_municipio | nr_zona | nr_secao | campo | valor_a | fonte_a | valor_b | fonte_b |
|---|---|---|---|---|---|---|---|---|---|---|
| B2 | 1 | AM | 2.011 | 34 | 27 | biometria_nh_vs_lib_codigo | 0 | BWEB | — | BUBIN |
| B2 | 1 | AM | 2.259 | 8 | 116 | biometria_nh_vs_lib_codigo | 0 | BWEB | — | BUBIN |
| B2 | 1 | AM | 2.550 | 40 | 454 | biometria_nh_vs_lib_codigo | 0 | BWEB | — | BUBIN |
| B2 | 1 | AM | 2.690 | 4 | 129 | biometria_nh_vs_lib_codigo | 0 | BWEB | — | BUBIN |
| B2 | 1 | CE | 15.270 | 6 | 206 | biometria_nh_vs_lib_codigo | 0 | BWEB | — | BUBIN |
| B2 | 1 | CE | 15.873 | 89 | 181 | biometria_nh_vs_lib_codigo | 0 | BWEB | — | BUBIN |
| B2 | 1 | MG | 47.872 | 167 | 41 | biometria_nh_vs_lib_codigo | 0 | BWEB | — | BUBIN |
| B2 | 1 | MG | 49.050 | 196 | 173 | biometria_nh_vs_lib_codigo | 0 | BWEB | — | BUBIN |
| B2 | 1 | MS | 90.735 | 43 | 27 | biometria_nh_vs_lib_codigo | 0 | BWEB | — | BUBIN |
| B2 | 1 | MT | 98.191 | 27 | 126 | biometria_nh_vs_lib_codigo | 0 | BWEB | — | BUBIN |
| B2 | 1 | PE | 23.493 | 99 | 39 | biometria_nh_vs_lib_codigo | 0 | BWEB | — | BUBIN |
| B2 | 1 | PR | 74.039 | 48 | 13 | biometria_nh_vs_lib_codigo | 0 | BWEB | — | BUBIN |
| B2 | 1 | RN | 17.434 | 30 | 77 | biometria_nh_vs_lib_codigo | 0 | BWEB | — | BUBIN |
| B2 | 1 | RS | 87.378 | 62 | 35 | biometria_nh_vs_lib_codigo | 0 | BWEB | — | BUBIN |
| B2 | 1 | SP | 61.557 | 299 | 242 | biometria_nh_vs_lib_codigo | 0 | BWEB | — | BUBIN |
| B2 | 2 | BA | 37.877 | 105 | 83 | biometria_nh_vs_lib_codigo | 0 | BWEB | — | BUBIN |
| B2 | 2 | DF | 97.012 | 9 | 11 | biometria_nh_vs_lib_codigo | 0 | BWEB | — | BUBIN |
| B2 | 2 | GO | 92.886 | 26 | 131 | biometria_nh_vs_lib_codigo | 0 | BWEB | — | BUBIN |
| B2 | 2 | PA | 4.898 | 99 | 17 | biometria_nh_vs_lib_codigo | 0 | BWEB | — | BUBIN |
| B2 | 2 | PA | 4.898 | 99 | 18 | biometria_nh_vs_lib_codigo | 0 | BWEB | — | BUBIN |
| B2 | 2 | PA | 4.898 | 99 | 19 | biometria_nh_vs_lib_codigo | 0 | BWEB | — | BUBIN |
| B2 | 2 | PA | 4.898 | 99 | 55 | biometria_nh_vs_lib_codigo | 0 | BWEB | — | BUBIN |
| B2 | 2 | PE | 26.212 | 75 | 135 | biometria_nh_vs_lib_codigo | 0 | BWEB | — | BUBIN |
| B2 | 2 | RS | 89.192 | 54 | 13 | biometria_nh_vs_lib_codigo | 0 | BWEB | — | BUBIN |
| B2 | 2 | SC | 83.011 | 46 | 22 | biometria_nh_vs_lib_codigo | 0 | BWEB | — | BUBIN |
| B6 | 1 | BA | 30.007 | 205 | 210 | biometria_nh_vs_liberacao_manual_no_log | 11 | BWEB | 0 | LOG |
| B6 | 1 | BA | 34.134 | 171 | 232 | biometria_nh_vs_liberacao_manual_no_log | 13 | BWEB | 0 | LOG |
| B6 | 1 | BA | 35.696 | 168 | 142 | biometria_nh_vs_liberacao_manual_no_log | 35 | BWEB | 24 | LOG |
| B6 | 1 | BA | 38.490 | 2 | 534 | biometria_nh_vs_liberacao_manual_no_log | 1 | BWEB | 0 | LOG |
| B6 | 1 | CE | 14.192 | 40 | 50 | biometria_nh_vs_liberacao_manual_no_log | 9 | BWEB | 0 | LOG |
| B6 | 1 | DF | 97.012 | 17 | 90 | biometria_nh_vs_liberacao_manual_no_log | 49 | BWEB | 37 | LOG |
| B6 | 1 | MA | 7.064 | 107 | 157 | biometria_nh_vs_liberacao_manual_no_log | 58 | BWEB | 57 | LOG |
| B6 | 1 | MG | 44.830 | 303 | 70 | biometria_nh_vs_liberacao_manual_no_log | 10 | BWEB | 13 | LOG |
| B6 | 1 | MG | 49.735 | 213 | 36 | biometria_nh_vs_liberacao_manual_no_log | 2 | BWEB | 0 | LOG |
| B6 | 1 | MS | 98.035 | 38 | 8 | biometria_nh_vs_liberacao_manual_no_log | 38 | BWEB | 36 | LOG |
| B6 | 1 | PA | 4.774 | 105 | 24 | biometria_nh_vs_liberacao_manual_no_log | 38 | BWEB | 15 | LOG |
| B6 | 1 | PE | 23.434 | 33 | 36 | biometria_nh_vs_liberacao_manual_no_log | 45 | BWEB | 44 | LOG |
| B6 | 1 | PR | 75.370 | 119 | 16 | biometria_nh_vs_liberacao_manual_no_log | 70 | BWEB | 0 | LOG |
| B6 | 1 | PR | 75.833 | 43 | 74 | biometria_nh_vs_liberacao_manual_no_log | 46 | BWEB | 0 | LOG |
| B6 | 1 | PR | 77.275 | 167 | 100 | biometria_nh_vs_liberacao_manual_no_log | 31 | BWEB | 3 | LOG |
| B6 | 1 | PR | 78.336 | 131 | 45 | biometria_nh_vs_liberacao_manual_no_log | 48 | BWEB | 47 | LOG |
| B6 | 1 | RJ | 58.971 | 36 | 7 | biometria_nh_vs_liberacao_manual_no_log | 48 | BWEB | 37 | LOG |
| B6 | 1 | RJ | 59.013 | 186 | 147 | biometria_nh_vs_liberacao_manual_no_log | 26 | BWEB | 1 | LOG |
| B6 | 1 | RS | 87.912 | 60 | 322 | biometria_nh_vs_liberacao_manual_no_log | 27 | BWEB | 0 | LOG |
| B6 | 1 | RS | 88.013 | 2 | 199 | biometria_nh_vs_liberacao_manual_no_log | 20 | BWEB | 13 | LOG |
| B6 | 1 | RS | 88.013 | 114 | 336 | biometria_nh_vs_liberacao_manual_no_log | 27 | BWEB | 0 | LOG |
| B6 | 1 | RS | 89.192 | 54 | 9 | biometria_nh_vs_liberacao_manual_no_log | 42 | BWEB | 41 | LOG |
| B6 | 1 | SE | 31.690 | 12 | 77 | biometria_nh_vs_liberacao_manual_no_log | 52 | BWEB | 51 | LOG |
| B6 | 1 | SP | 64.734 | 197 | 122 | biometria_nh_vs_liberacao_manual_no_log | 19 | BWEB | 20 | LOG |
| B6 | 1 | SP | 66.850 | 71 | 23 | biometria_nh_vs_liberacao_manual_no_log | 18 | BWEB | 17 | LOG |
| B6 | 1 | SP | 71.072 | 417 | 95 | biometria_nh_vs_liberacao_manual_no_log | 27 | BWEB | 9 | LOG |
| B6 | 1 | SP | 71.072 | 418 | 395 | biometria_nh_vs_liberacao_manual_no_log | 32 | BWEB | 30 | LOG |
| B6 | 1 | SP | 71.811 | 140 | 216 | biometria_nh_vs_liberacao_manual_no_log | 12 | BWEB | 5 | LOG |
| B6 | 2 | AM | 2.550 | 68 | 512 | biometria_nh_vs_liberacao_manual_no_log | 10 | BWEB | 0 | LOG |
| B6 | 2 | BA | 34.134 | 171 | 232 | biometria_nh_vs_liberacao_manual_no_log | 18 | BWEB | 0 | LOG |
| B6 | 2 | MG | 40.720 | 167 | 179 | biometria_nh_vs_liberacao_manual_no_log | 20 | BWEB | 19 | LOG |
| B6 | 2 | PE | 23.973 | 91 | 99 | biometria_nh_vs_liberacao_manual_no_log | 33 | BWEB | 6 | LOG |
| B6 | 2 | PR | 78.050 | 130 | 41 | biometria_nh_vs_liberacao_manual_no_log | 88 | BWEB | 89 | LOG |
| B6 | 2 | PR | 84.670 | 147 | 417 | biometria_nh_vs_liberacao_manual_no_log | 26 | BWEB | 27 | LOG |
| B6 | 2 | RJ | 58.777 | 65 | 233 | biometria_nh_vs_liberacao_manual_no_log | 36 | BWEB | 33 | LOG |
| B6 | 2 | RS | 85.871 | 14 | 106 | biometria_nh_vs_liberacao_manual_no_log | 50 | BWEB | 51 | LOG |
| B6 | 2 | RS | 87.912 | 60 | 322 | biometria_nh_vs_liberacao_manual_no_log | 21 | BWEB | 0 | LOG |
| B6 | 2 | SP | 64.777 | 394 | 204 | biometria_nh_vs_liberacao_manual_no_log | 28 | BWEB | 26 | LOG |
| B6 | 2 | SP | 69.876 | 190 | 100 | biometria_nh_vs_liberacao_manual_no_log | 35 | BWEB | 31 | LOG |
| B6 | 2 | SP | 71.072 | 2 | 310 | biometria_nh_vs_liberacao_manual_no_log | 17 | BWEB | 2 | LOG |
| B6 | 2 | SP | 71.072 | 373 | 734 | biometria_nh_vs_liberacao_manual_no_log | 7 | BWEB | 0 | LOG |
| B6 | 2 | SP | 71.153 | 132 | 129 | biometria_nh_vs_liberacao_manual_no_log | 15 | BWEB | 13 | LOG |
| B6 | 1 | AL | 27.219 | 9 | 5 | comparecimento_vs_votos_computados | 242 | BWEB | 241 | LOG |
| B6 | 1 | BA | 30.007 | 205 | 210 | comparecimento_vs_votos_computados | 189 | BWEB | 9 | LOG |
| B6 | 1 | BA | 30.872 | 186 | 94 | comparecimento_vs_votos_computados | 318 | BWEB | 319 | LOG |
| B6 | 1 | BA | 34.134 | 171 | 232 | comparecimento_vs_votos_computados | 345 | BWEB | 0 | LOG |
| B6 | 1 | BA | 35.696 | 168 | 142 | comparecimento_vs_votos_computados | 287 | BWEB | 259 | LOG |
| B6 | 1 | BA | 36.196 | 185 | 122 | comparecimento_vs_votos_computados | 288 | BWEB | 289 | LOG |
| B6 | 1 | BA | 38.490 | 2 | 534 | comparecimento_vs_votos_computados | 342 | BWEB | 0 | LOG |
| B6 | 1 | BA | 39.594 | 120 | 24 | comparecimento_vs_votos_computados | 256 | BWEB | 255 | LOG |
| B6 | 1 | CE | 14.117 | 13 | 42 | comparecimento_vs_votos_computados | 234 | BWEB | 233 | LOG |
| B6 | 1 | CE | 14.192 | 40 | 50 | comparecimento_vs_votos_computados | 162 | BWEB | 0 | LOG |
| B6 | 1 | CE | 15.377 | 9 | 301 | comparecimento_vs_votos_computados | 253 | BWEB | 252 | LOG |
| B6 | 1 | DF | 97.012 | 17 | 90 | comparecimento_vs_votos_computados | 274 | BWEB | 261 | LOG |
| B6 | 1 | ES | 56.189 | 41 | 226 | comparecimento_vs_votos_computados | 230 | BWEB | 229 | LOG |
| B6 | 1 | ES | 56.251 | 54 | 126 | comparecimento_vs_votos_computados | 251 | BWEB | 250 | LOG |
| B6 | 1 | ES | 56.251 | 54 | 511 | comparecimento_vs_votos_computados | 289 | BWEB | 288 | LOG |
| B6 | 1 | GO | 92.916 | 20 | 107 | comparecimento_vs_votos_computados | 190 | BWEB | 189 | LOG |
| B6 | 1 | MA | 7.064 | 107 | 157 | comparecimento_vs_votos_computados | 279 | BWEB | 278 | LOG |
| B6 | 1 | MA | 7.331 | 56 | 166 | comparecimento_vs_votos_computados | 182 | BWEB | 181 | LOG |
| B6 | 1 | MA | 7.617 | 42 | 98 | comparecimento_vs_votos_computados | 301 | BWEB | 300 | LOG |
| B6 | 1 | MA | 7.714 | 14 | 21 | comparecimento_vs_votos_computados | 224 | BWEB | 223 | LOG |
| B6 | 1 | MA | 9.210 | 76 | 48 | comparecimento_vs_votos_computados | 297 | BWEB | 296 | LOG |
| B6 | 1 | MA | 9.598 | 102 | 12 | comparecimento_vs_votos_computados | 198 | BWEB | 199 | LOG |
| B6 | 1 | MG | 44.830 | 303 | 70 | comparecimento_vs_votos_computados | 122 | BWEB | 220 | LOG |
| B6 | 1 | MG | 45.136 | 100 | 231 | comparecimento_vs_votos_computados | 281 | BWEB | 252 | LOG |
| B6 | 1 | MG | 49.735 | 213 | 36 | comparecimento_vs_votos_computados | 61 | BWEB | 18 | LOG |
| B6 | 1 | MG | 50.350 | 350 | 147 | comparecimento_vs_votos_computados | 180 | BWEB | 179 | LOG |
| B6 | 1 | MS | 98.035 | 38 | 8 | comparecimento_vs_votos_computados | 193 | BWEB | 120 | LOG |
| B6 | 1 | PA | 4.154 | 72 | 12 | comparecimento_vs_votos_computados | 318 | BWEB | 317 | LOG |
| B6 | 1 | PA | 4.774 | 105 | 24 | comparecimento_vs_votos_computados | 312 | BWEB | 119 | LOG |
| B6 | 1 | PA | 5.177 | 82 | 62 | comparecimento_vs_votos_computados | 249 | BWEB | 248 | LOG |
| B6 | 1 | PE | 23.434 | 33 | 36 | comparecimento_vs_votos_computados | 239 | BWEB | 238 | LOG |
| B6 | 1 | PR | 74.071 | 171 | 41 | comparecimento_vs_votos_computados | 308 | BWEB | 309 | LOG |
| B6 | 1 | PR | 75.370 | 119 | 16 | comparecimento_vs_votos_computados | 268 | BWEB | 0 | LOG |
| B6 | 1 | PR | 75.833 | 43 | 74 | comparecimento_vs_votos_computados | 307 | BWEB | 0 | LOG |
| B6 | 1 | PR | 76.678 | 41 | 318 | comparecimento_vs_votos_computados | 236 | BWEB | 235 | LOG |
| B6 | 1 | PR | 77.275 | 167 | 100 | comparecimento_vs_votos_computados | 326 | BWEB | 23 | LOG |
| B6 | 1 | PR | 84.611 | 206 | 69 | comparecimento_vs_votos_computados | 263 | BWEB | 262 | LOG |
| B6 | 1 | RJ | 58.394 | 105 | 40 | comparecimento_vs_votos_computados | 208 | BWEB | 189 | LOG |
| B6 | 1 | RJ | 58.777 | 65 | 41 | comparecimento_vs_votos_computados | 271 | BWEB | 270 | LOG |
| B6 | 1 | RJ | 58.971 | 36 | 7 | comparecimento_vs_votos_computados | 264 | BWEB | 219 | LOG |
| B6 | 1 | RJ | 59.013 | 186 | 147 | comparecimento_vs_votos_computados | 215 | BWEB | 8 | LOG |
| B6 | 1 | RN | 16.977 | 68 | 66 | comparecimento_vs_votos_computados | 270 | BWEB | 271 | LOG |
| B6 | 1 | RN | 18.139 | 65 | 32 | comparecimento_vs_votos_computados | 249 | BWEB | 259 | LOG |
| B6 | 1 | RN | 18.953 | 7 | 123 | comparecimento_vs_votos_computados | 267 | BWEB | 266 | LOG |
| B6 | 1 | RS | 87.912 | 60 | 322 | comparecimento_vs_votos_computados | 300 | BWEB | 0 | LOG |
| B6 | 1 | RS | 88.013 | 2 | 199 | comparecimento_vs_votos_computados | 288 | BWEB | 196 | LOG |
| B6 | 1 | RS | 88.013 | 114 | 336 | comparecimento_vs_votos_computados | 259 | BWEB | 14 | LOG |
| B6 | 1 | RS | 89.052 | 132 | 63 | comparecimento_vs_votos_computados | 307 | BWEB | 305 | LOG |
| B6 | 1 | RS | 89.192 | 54 | 9 | comparecimento_vs_votos_computados | 253 | BWEB | 252 | LOG |
| B6 | 1 | SC | 81.434 | 73 | 134 | comparecimento_vs_votos_computados | 244 | BWEB | 243 | LOG |
| B6 | 1 | SC | 83.054 | 51 | 59 | comparecimento_vs_votos_computados | 259 | BWEB | 260 | LOG |
| B6 | 1 | SC | 83.275 | 84 | 22 | comparecimento_vs_votos_computados | 241 | BWEB | 240 | LOG |
| B6 | 1 | SE | 31.690 | 12 | 77 | comparecimento_vs_votos_computados | 209 | BWEB | 208 | LOG |
| B6 | 1 | SP | 61.654 | 14 | 206 | comparecimento_vs_votos_computados | 342 | BWEB | 341 | LOG |
| B6 | 1 | SP | 63.070 | 140 | 2 | comparecimento_vs_votos_computados | 278 | BWEB | 277 | LOG |
| B6 | 1 | SP | 64.270 | 367 | 18 | comparecimento_vs_votos_computados | 259 | BWEB | 253 | LOG |
| B6 | 1 | SP | 64.734 | 197 | 122 | comparecimento_vs_votos_computados | 191 | BWEB | 192 | LOG |
| B6 | 1 | SP | 64.777 | 394 | 152 | comparecimento_vs_votos_computados | 339 | BWEB | 338 | LOG |
| B6 | 1 | SP | 64.939 | 49 | 212 | comparecimento_vs_votos_computados | 266 | BWEB | 265 | LOG |
| B6 | 1 | SP | 66.230 | 223 | 23 | comparecimento_vs_votos_computados | 215 | BWEB | 216 | LOG |
| B6 | 1 | SP | 66.397 | 66 | 430 | comparecimento_vs_votos_computados | 222 | BWEB | 221 | LOG |
| B6 | 1 | SP | 66.850 | 71 | 23 | comparecimento_vs_votos_computados | 201 | BWEB | 200 | LOG |
| B6 | 1 | SP | 66.893 | 365 | 166 | comparecimento_vs_votos_computados | 270 | BWEB | 269 | LOG |
| B6 | 1 | SP | 70.335 | 187 | 58 | comparecimento_vs_votos_computados | 289 | BWEB | 288 | LOG |
| B6 | 1 | SP | 70.718 | 118 | 314 | comparecimento_vs_votos_computados | 213 | BWEB | 212 | LOG |
| B6 | 1 | SP | 70.998 | 412 | 195 | comparecimento_vs_votos_computados | 304 | BWEB | 303 | LOG |
| B6 | 1 | SP | 71.072 | 20 | 36 | comparecimento_vs_votos_computados | 255 | BWEB | 256 | LOG |
| B6 | 1 | SP | 71.072 | 350 | 33 | comparecimento_vs_votos_computados | 285 | BWEB | 284 | LOG |
| B6 | 1 | SP | 71.072 | 381 | 441 | comparecimento_vs_votos_computados | 346 | BWEB | 345 | LOG |
| B6 | 1 | SP | 71.072 | 417 | 95 | comparecimento_vs_votos_computados | 264 | BWEB | 82 | LOG |
| B6 | 1 | SP | 71.072 | 418 | 395 | comparecimento_vs_votos_computados | 271 | BWEB | 255 | LOG |
| B6 | 1 | SP | 71.811 | 140 | 216 | comparecimento_vs_votos_computados | 233 | BWEB | 120 | LOG |
| B6 | 2 | AM | 2.550 | 68 | 512 | comparecimento_vs_votos_computados | 238 | BWEB | 0 | LOG |
| B6 | 2 | BA | 34.134 | 171 | 232 | comparecimento_vs_votos_computados | 359 | BWEB | 0 | LOG |
| B6 | 2 | BA | 39.535 | 198 | 43 | comparecimento_vs_votos_computados | 252 | BWEB | 253 | LOG |
| B6 | 2 | CE | 13.404 | 108 | 42 | comparecimento_vs_votos_computados | 244 | BWEB | 243 | LOG |
| B6 | 2 | DF | 97.012 | 6 | 44 | comparecimento_vs_votos_computados | 259 | BWEB | 258 | LOG |
| B6 | 2 | ES | 56.251 | 54 | 618 | comparecimento_vs_votos_computados | 276 | BWEB | 216 | LOG |
| B6 | 2 | ES | 56.634 | 25 | 89 | comparecimento_vs_votos_computados | 311 | BWEB | 312 | LOG |
| B6 | 2 | MA | 7.005 | 12 | 149 | comparecimento_vs_votos_computados | 128 | BWEB | 129 | LOG |
| B6 | 2 | MA | 7.277 | 22 | 122 | comparecimento_vs_votos_computados | 298 | BWEB | 297 | LOG |
| B6 | 2 | MA | 7.650 | 28 | 30 | comparecimento_vs_votos_computados | 263 | BWEB | 262 | LOG |
| B6 | 2 | MA | 7.668 | 101 | 98 | comparecimento_vs_votos_computados | 191 | BWEB | 179 | LOG |
| B6 | 2 | MG | 40.720 | 167 | 179 | comparecimento_vs_votos_computados | 339 | BWEB | 338 | LOG |
| B6 | 2 | MG | 51.152 | 239 | 22 | comparecimento_vs_votos_computados | 206 | BWEB | 205 | LOG |
| B6 | 2 | PA | 4.154 | 43 | 914 | comparecimento_vs_votos_computados | 310 | BWEB | 309 | LOG |
| B6 | 2 | PE | 23.639 | 130 | 6 | comparecimento_vs_votos_computados | 237 | BWEB | 236 | LOG |
| B6 | 2 | PE | 23.973 | 91 | 99 | comparecimento_vs_votos_computados | 119 | BWEB | 32 | LOG |
| B6 | 2 | PE | 24.350 | 85 | 44 | comparecimento_vs_votos_computados | 296 | BWEB | 297 | LOG |
| B6 | 2 | PE | 25.216 | 83 | 416 | comparecimento_vs_votos_computados | 279 | BWEB | 278 | LOG |
| B6 | 2 | PR | 76.678 | 146 | 273 | comparecimento_vs_votos_computados | 278 | BWEB | 277 | LOG |
| B6 | 2 | PR | 78.050 | 130 | 41 | comparecimento_vs_votos_computados | 286 | BWEB | 287 | LOG |
| B6 | 2 | PR | 78.859 | 199 | 186 | comparecimento_vs_votos_computados | 351 | BWEB | 352 | LOG |
| B6 | 2 | PR | 84.670 | 147 | 417 | comparecimento_vs_votos_computados | 258 | BWEB | 259 | LOG |
| B6 | 2 | RJ | 58.335 | 128 | 136 | comparecimento_vs_votos_computados | 323 | BWEB | 324 | LOG |
| B6 | 2 | RJ | 58.335 | 200 | 154 | comparecimento_vs_votos_computados | 308 | BWEB | 307 | LOG |
| B6 | 2 | RJ | 58.777 | 65 | 233 | comparecimento_vs_votos_computados | 210 | BWEB | 179 | LOG |
| B6 | 2 | RJ | 60.011 | 7 | 479 | comparecimento_vs_votos_computados | 348 | BWEB | 347 | LOG |
| B6 | 2 | RS | 85.871 | 14 | 106 | comparecimento_vs_votos_computados | 256 | BWEB | 257 | LOG |
| B6 | 2 | RS | 87.912 | 60 | 322 | comparecimento_vs_votos_computados | 309 | BWEB | 0 | LOG |
| B6 | 2 | SC | 80.470 | 3 | 463 | comparecimento_vs_votos_computados | 290 | BWEB | 289 | LOG |
| B6 | 2 | SP | 64.254 | 291 | 165 | comparecimento_vs_votos_computados | 310 | BWEB | 309 | LOG |
| B6 | 2 | SP | 64.777 | 394 | 204 | comparecimento_vs_votos_computados | 306 | BWEB | 286 | LOG |
| B6 | 2 | SP | 66.192 | 65 | 451 | comparecimento_vs_votos_computados | 305 | BWEB | 304 | LOG |
| B6 | 2 | SP | 66.192 | 424 | 1 | comparecimento_vs_votos_computados | 185 | BWEB | 184 | LOG |
| B6 | 2 | SP | 67.938 | 163 | 23 | comparecimento_vs_votos_computados | 232 | BWEB | 231 | LOG |
| B6 | 2 | SP | 67.954 | 82 | 84 | comparecimento_vs_votos_computados | 234 | BWEB | 233 | LOG |
| B6 | 2 | SP | 68.535 | 295 | 177 | comparecimento_vs_votos_computados | 197 | BWEB | 196 | LOG |
| B6 | 2 | SP | 69.876 | 190 | 100 | comparecimento_vs_votos_computados | 281 | BWEB | 254 | LOG |
| B6 | 2 | SP | 70.572 | 156 | 309 | comparecimento_vs_votos_computados | 241 | BWEB | 240 | LOG |
| B6 | 2 | SP | 70.998 | 127 | 7 | comparecimento_vs_votos_computados | 172 | BWEB | 171 | LOG |
| B6 | 2 | SP | 70.998 | 127 | 546 | comparecimento_vs_votos_computados | 327 | BWEB | 326 | LOG |
| B6 | 2 | SP | 70.998 | 282 | 126 | comparecimento_vs_votos_computados | 275 | BWEB | 274 | LOG |
| B6 | 2 | SP | 71.072 | 2 | 310 | comparecimento_vs_votos_computados | 267 | BWEB | 17 | LOG |
| B6 | 2 | SP | 71.072 | 373 | 734 | comparecimento_vs_votos_computados | 322 | BWEB | 0 | LOG |
| B6 | 2 | SP | 71.072 | 374 | 478 | comparecimento_vs_votos_computados | 287 | BWEB | 286 | LOG |
| B6 | 2 | SP | 71.153 | 132 | 129 | comparecimento_vs_votos_computados | 294 | BWEB | 278 | LOG |
| B6 | 2 | TO | 73.440 | 29 | 229 | comparecimento_vs_votos_computados | 270 | BWEB | 269 | LOG |
| B6 | 1 | BA | 30.007 | 205 | 210 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 189 | BWEB | 9 | LOG |
| B6 | 1 | BA | 30.872 | 186 | 94 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 318 | BWEB | 319 | LOG |
| B6 | 1 | BA | 34.134 | 171 | 232 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 345 | BWEB | 0 | LOG |
| B6 | 1 | BA | 35.696 | 168 | 142 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 287 | BWEB | 259 | LOG |
| B6 | 1 | BA | 36.196 | 185 | 122 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 288 | BWEB | 290 | LOG |
| B6 | 1 | BA | 38.490 | 2 | 534 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 342 | BWEB | 0 | LOG |
| B6 | 1 | CE | 14.192 | 40 | 50 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 162 | BWEB | 0 | LOG |
| B6 | 1 | DF | 97.012 | 17 | 90 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 274 | BWEB | 261 | LOG |
| B6 | 1 | MA | 9.598 | 102 | 12 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 198 | BWEB | 199 | LOG |
| B6 | 1 | MG | 44.830 | 303 | 70 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 122 | BWEB | 220 | LOG |
| B6 | 1 | MG | 45.136 | 100 | 231 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 281 | BWEB | 252 | LOG |
| B6 | 1 | MG | 49.735 | 213 | 36 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 61 | BWEB | 18 | LOG |
| B6 | 1 | MS | 98.035 | 38 | 8 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 193 | BWEB | 120 | LOG |
| B6 | 1 | PA | 4.774 | 105 | 24 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 312 | BWEB | 119 | LOG |
| B6 | 1 | PE | 23.132 | 125 | 98 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 288 | BWEB | 290 | LOG |


Diagnóstico individual de cada caso (estrutura do log: arquivos, urnas, eventos de contingência) em `resultados/2022/diagnosticos/`.

### Eleitores aptos que mudam de seção entre os turnos

**Classificação:** Diferença explicada (96–97%) / Pendente (resíduo)

- **O que verificamos?** Por que algumas seções têm número de aptos diferente no 1º e no 2º turno.
- **O que os números mostram?** 49.710 de 472.028 seções mudaram de aptos; o total nacional não muda (soma das variações = 0). Em 47.998 delas (96,6%) a variação é exatamente o saldo das transferências temporárias publicadas pelo TSE; 1.782 seções ficam com resíduo (soma dos resíduos em módulo: 2.408 eleitores).
- **O que significa?** A diferença vem de eleitores que votam temporariamente em outra seção (voto em trânsito, mesários, presos provisórios, militares, acessibilidade), o que pode valer só para um turno.
- **Existe explicação conhecida?** Transferência temporária do eleitorado por seção (arquivo oficial).
- **O que ainda não sabemos?** O arquivo de transferências foi gerado pelo TSE em 2024, após as eleições; o resíduo pode refletir atualizações posteriores. Pendente de verificação documental seção a seção.
- **Como conferir?** `resultados/2022/aptos_entre_turnos_resumo.csv` e `aptos_entre_turnos_nao_explicados_por_tte.csv`.

## 3. Horários de votação (Testes D e E)

### 1º turno: votos antes das 8h e depois das 17h (horário de Brasília)

**Classificação:** Conferido (distribuição descrita)

- **O que verificamos?** Quantos votos concluídos o log registra fora do horário regular, após converter o relógio de cada urna para o horário de Brasília pelo fuso legal do município.
- **O que os números mostram?** Em 470.998 seções com log (123.372.053 votos): 0 votos antes das 8h em 0 seções; 4.325.283 votos após as 17h (3,506%) em 214.948 seções; 1.050.290 após 18h; 242.317 após 19h.
- **O que significa?** Votos depois das 17h são previstos em lei para quem estava na fila. Votos antes das 8h, se existirem, precisam ser examinados um a um (relógio, fuso, troca de urna).
- **Existe explicação conhecida?** Fila às 17h (Res. 23.669/2021, art. 136, §§ 1º–2º). A distribuição por UF acompanha o tamanho das seções e o volume do 1º turno (5 cargos).
- **O que ainda não sabemos?** O log não registra a senha distribuída às 17h, portanto não é possível confirmar, eleitor a eleitor, que quem votou depois das 17h estava na fila.
- **Como conferir?** `resultados/2022/temporal_por_uf.csv`, `secoes_horarios_atipicos.csv`, `votos_por_15min.csv`; gráfico `resultados/{ano}/graficos/votos_por_15min.png`.

### 2º turno: votos antes das 8h e depois das 17h (horário de Brasília)

**Classificação:** Conferido (distribuição descrita)

- **O que verificamos?** Quantos votos concluídos o log registra fora do horário regular, após converter o relógio de cada urna para o horário de Brasília pelo fuso legal do município.
- **O que os números mostram?** Em 470.999 seções com log (123.938.310 votos): 0 votos antes das 8h em 0 seções; 40.698 votos após as 17h (0,033%) em 34.455 seções; 187 após 18h; 12 após 19h.
- **O que significa?** Votos depois das 17h são previstos em lei para quem estava na fila. Votos antes das 8h, se existirem, precisam ser examinados um a um (relógio, fuso, troca de urna).
- **Existe explicação conhecida?** Fila às 17h (Res. 23.669/2021, art. 136, §§ 1º–2º). A distribuição por UF acompanha o tamanho das seções e o volume do 1º turno (5 cargos).
- **O que ainda não sabemos?** O log não registra a senha distribuída às 17h, portanto não é possível confirmar, eleitor a eleitor, que quem votou depois das 17h estava na fila.
- **Como conferir?** `resultados/2022/temporal_por_uf.csv`, `secoes_horarios_atipicos.csv`, `votos_por_15min.csv`; gráfico `resultados/{ano}/graficos/votos_por_15min.png`.

### Validação dos fusos horários

**Classificação:** Conferido

- **O que verificamos?** Se o fuso legal atribuído a cada município é coerente com o horário local do primeiro voto.
- **O que os números mostram?** 11.140 combinações município×turno avaliadas; 0 divergentes.
- **O que significa?** Sem divergências, os horários convertidos são confiáveis; divergências indicariam erro de fuso ou relógio.
- **Existe explicação conhecida?** Lista legal de municípios do oeste do AM em UTC-5 e Fernando de Noronha em UTC-2.
- **O que ainda não sabemos?** Relógios individuais de urnas podem diferir do município; isso aparece como retrocesso de relógio ou horário atípico na seção.
- **Como conferir?** `resultados/2022/validacao_fusos_municipio.csv`.

### Intervalos muito curtos entre votos ("rajadas")

| turno | limiar_s | min_votos | sequencias | votos_em_sequencias | secoes |
|---|---|---|---|---|---|
| 1 | 6 | 5 | 0 | 0 | 0 |
| 1 | 10 | 5 | 0 | 0 | 0 |
| 1 | 20 | 3 | 2 | 6 | 2 |
| 1 | 20 | 5 | 0 | 0 | 0 |
| 1 | 30 | 3 | 539 | 1765 | 170 |
| 1 | 30 | 5 | 33 | 174 | 21 |
| 2 | 6 | 5 | 0 | 0 | 0 |
| 2 | 10 | 5 | 0 | 0 | 0 |
| 2 | 20 | 3 | 40 | 123 | 35 |
| 2 | 20 | 5 | 1 | 5 | 1 |
| 2 | 30 | 3 | 80498 | 256475 | 37268 |
| 2 | 30 | 5 | 2404 | 13095 | 1814 |


Intervalo = tempo entre dois registros consecutivos de voto concluído na mesma urna. Grade de sensibilidade com limiares de 6 a 30 s e mínimo de 3 ou 5 votos. Versão com intervalos entre habilitações em `resultados/2022/rajadas_sensibilidade_habilitacoes.csv`.

## 4. Identificação biométrica e alternativa (Teste F)

### 1º turno: quem votou sem reconhecimento biométrico

**Classificação:** Conferido

- **O que verificamos?** Quantos eleitores com biometria cadastrada votaram após liberação manual (sem reconhecimento da digital) e se o log confirma o número do BU.
- **O que os números mostram?** BU: 10.780.979 eleitores (8,74% do comparecimento) com biometria e não habilitados por ela. Nos logs processados: 92.869.931 votantes por biometria, 10.780.635 liberados manualmente após falha e 18.653.373 sem biometria cadastrada.
- **O que significa?** A liberação manual é o procedimento previsto quando a digital não é reconhecida; o número no BU e no log coincide (Teste B6).
- **Existe explicação conhecida?** Res.-TSE 23.669/2021, arts. 113–115 (até 4 leituras; depois ano de nascimento e digital do mesário).
- **O que ainda não sabemos?** O log de 2022 não identifica o motivo da falha (sujeira, desgaste, leitor); o modelo de urna influencia a taxa (ver Teste I).
- **Como conferir?** `resultados/2022/biometria_por_uf.csv`, `biometria_modalidade_por_hora.csv`, `biometria_duracao_por_modalidade_modelo.csv`.

### 2º turno: quem votou sem reconhecimento biométrico

**Classificação:** Conferido

- **O que verificamos?** Quantos eleitores com biometria cadastrada votaram após liberação manual (sem reconhecimento da digital) e se o log confirma o número do BU.
- **O que os números mostram?** BU: 10.011.347 eleitores (8,08% do comparecimento) com biometria e não habilitados por ela. Nos logs processados: 94.031.700 votantes por biometria, 10.011.195 liberados manualmente após falha e 18.824.642 sem biometria cadastrada.
- **O que significa?** A liberação manual é o procedimento previsto quando a digital não é reconhecida; o número no BU e no log coincide (Teste B6).
- **Existe explicação conhecida?** Res.-TSE 23.669/2021, arts. 113–115 (até 4 leituras; depois ano de nascimento e digital do mesário).
- **O que ainda não sabemos?** O log de 2022 não identifica o motivo da falha (sujeira, desgaste, leitor); o modelo de urna influencia a taxa (ver Teste I).
- **Como conferir?** `resultados/2022/biometria_por_uf.csv`, `biometria_modalidade_por_hora.csv`, `biometria_duracao_por_modalidade_modelo.csv`.

## 5. Modelos de urna (Teste I)

| turno | controle | indicador | diferenca_ingenua_pp | diferenca_controlada_pp | ic95_inf | ic95_sup | grupos_comparaveis | secoes_ref | secoes_outras |
|---|---|---|---|---|---|---|---|---|---|
| 1 | mesmo_local | pct_validos_22 | 2,461 | 0,420 | -0,250 | 1,081 | 133 | 690 | 660 |
| 1 | mesmo_local | pct_validos_13 | -4,328 | -0,486 | -1,151 | 0,197 | 133 | 690 | 660 |
| 1 | mesmo_local | pct_comparecimento | 1,878 | -0,242 | -1,156 | 0,619 | 133 | 690 | 660 |
| 1 | mesmo_local | pct_brancos_nulos | 0,123 | 0,101 | -0,091 | 0,303 | 133 | 690 | 660 |
| 1 | mesmo_local | pct_biometria_nh | -6,872 | -4,958 | -5,621 | -4,337 | 133 | 690 | 660 |
| 1 | mesma_zona | pct_validos_22 | 2,461 | 1,165 | 0,634 | 1,688 | 460 | 46.556 | 56.149 |
| 1 | mesma_zona | pct_validos_13 | -4,328 | -1,713 | -2,374 | -1,063 | 460 | 46.556 | 56.149 |
| 1 | mesma_zona | pct_comparecimento | 1,878 | -0,184 | -0,392 | 0,024 | 460 | 46.556 | 56.149 |
| 1 | mesma_zona | pct_brancos_nulos | 0,123 | -0,265 | -0,354 | -0,177 | 460 | 46.556 | 56.149 |
| 1 | mesma_zona | pct_biometria_nh | -6,872 | -4,663 | -4,830 | -4,502 | 460 | 46.556 | 56.149 |
| 1 | mesmo_municipio | pct_validos_22 | 2,461 | 0,654 | 0,112 | 1,222 | 310 | 52.757 | 58.965 |
| 1 | mesmo_municipio | pct_validos_13 | -4,328 | -1,195 | -1,871 | -0,526 | 310 | 52.757 | 58.965 |
| 1 | mesmo_municipio | pct_comparecimento | 1,878 | -0,025 | -0,332 | 0,296 | 310 | 52.757 | 58.965 |
| 1 | mesmo_municipio | pct_brancos_nulos | 0,123 | -0,267 | -0,372 | -0,180 | 310 | 52.757 | 58.965 |
| 1 | mesmo_municipio | pct_biometria_nh | -6,872 | -4,506 | -4,833 | -4,120 | 310 | 52.757 | 58.965 |
| 2 | mesmo_local | pct_validos_22 | 3,395 | 0,374 | -0,272 | 1,017 | 161 | 737 | 979 |
| 2 | mesmo_local | pct_validos_13 | -3,395 | -0,374 | -1,028 | 0,262 | 161 | 737 | 979 |
| 2 | mesmo_local | pct_comparecimento | 1,905 | -0,290 | -1,013 | 0,420 | 161 | 737 | 979 |
| 2 | mesmo_local | pct_brancos_nulos | 0,259 | 0,097 | -0,118 | 0,317 | 161 | 737 | 979 |
| 2 | mesmo_local | pct_biometria_nh | -6,387 | -4,606 | -5,198 | -4,062 | 161 | 737 | 979 |
| 2 | mesma_zona | pct_validos_22 | 3,395 | 1,336 | 0,791 | 1,925 | 461 | 46.601 | 56.116 |
| 2 | mesma_zona | pct_validos_13 | -3,395 | -1,336 | -1,923 | -0,770 | 461 | 46.601 | 56.116 |
| 2 | mesma_zona | pct_comparecimento | 1,905 | -0,253 | -0,486 | -0,002 | 461 | 46.601 | 56.116 |
| 2 | mesma_zona | pct_brancos_nulos | 0,259 | -0,075 | -0,132 | -0,019 | 461 | 46.601 | 56.116 |
| 2 | mesma_zona | pct_biometria_nh | -6,387 | -4,454 | -4,587 | -4,310 | 461 | 46.601 | 56.116 |
| 2 | mesmo_municipio | pct_validos_22 | 3,395 | 0,780 | 0,136 | 1,409 | 311 | 52.802 | 58.932 |
| 2 | mesmo_municipio | pct_validos_13 | -3,395 | -0,780 | -1,395 | -0,130 | 311 | 52.802 | 58.932 |
| 2 | mesmo_municipio | pct_comparecimento | 1,905 | -0,151 | -0,444 | 0,171 | 311 | 52.802 | 58.932 |
| 2 | mesmo_municipio | pct_brancos_nulos | 0,259 | -0,071 | -0,142 | -0,020 | 311 | 52.802 | 58.932 |
| 2 | mesmo_municipio | pct_biometria_nh | -6,387 | -4,302 | -4,594 | -3,868 | 311 | 52.802 | 58.932 |

### UE2020 × demais modelos: proporção de votos do nº 22

**Classificação:** Diferença estatística (controles fracos) / Conferido sem diferença (mesmo local)

- **O que verificamos?** Se seções com urna modelo 2020 têm resultado diferente de seções com outros modelos, comparando seções próximas (mesmo local de votação, mesma zona, mesmo município).
- **O que os números mostram?** Sem controle geográfico a diferença é grande (1º t.: 2,46 p.p., 2º t.: 3,39 p.p.). No mesmo local: 1º t. 0,42 p.p. (IC95% -0,25 a 1,08); 2º t. 0,37 p.p. (IC95% -0,27 a 1,02). Na mesma zona: 1º t. 1,17 p.p. (IC95% 0,63 a 1,69); 2º t. 1,34 p.p. (IC95% 0,79 a 1,92).
- **O que significa?** A maior parte da diferença bruta é geográfica. No controle mais forte (mesmo local) o intervalo inclui zero; com controles mais fracos (zona, município) resta diferença de cerca de 1 p.p., que pode refletir diferenças entre bairros/locais dentro da zona.
- **Existe explicação conhecida?** A distribuição dos modelos não é aleatória (logística do TSE por zona/local). O modelo 2020 tem leitor biométrico mais novo: a taxa de liberação manual é ~5 p.p. menor nas mesmas localidades, diferença técnica esperada.
- **O que ainda não sabemos?** Sem covariáveis anteriores à eleição por seção (ex.: resultado de 2018 na mesma seção), não é possível separar efeito do modelo de efeito de localização. Diferença estatística ≠ causalidade.
- **Como conferir?** `resultados/2022/modelos_efeito_controlado.csv`, `modelos_medias_ingenuas.csv`; gráfico `resultados/2022/graficos/modelos_efeito_22.png`.

## 6. Testes estatísticos de dígitos e distribuição (Teste J)

| teste | testes | rejeitados_holm_1pct | cramer_v_mediano | maior_desvio_pp_mediano |
|---|---|---|---|---|
| segundo_digito_benford_descritivo | 116 | 100 | 0,058 | 3,003 |
| segundo_digito_vs_simulacao_binomial_zona | 116 | 58 | 0,020 | 1,161 |
| ultimo_digito_uniforme | 116 | 12 | 0,011 | 0,635 |
| ultimo_digito_vs_simulacao_binomial_zona | 116 | 0 | 0,010 | 0,578 |

### Dígitos das contagens por seção

**Classificação:** Diferença estatística (sem relevância prática) — não é evidência de irregularidade

- **O que verificamos?** Se o último e o segundo dígito dos votos por seção de Lula (13) e Bolsonaro (22) seguem o esperado.
- **O que os números mostram?** Contra a referência teórica (uniforme / Benford) há rejeições, com efeitos pequenos. Contra a referência simulada (binomial com o tamanho real das seções e a proporção da zona), o último dígito não é rejeitado em nenhum caso, e o desvio do 2º dígito cai para frações de ponto percentual.
- **O que significa?** As rejeições contra Benford vêm da premissa errada (seções têm tamanho limitado), não dos votos.
- **Existe explicação conhecida?** Literatura: Mebane (2006); Deckert, Myagkov & Ordeshook (2011) — testes de dígitos não detectam fraude de forma confiável.
- **O que ainda não sabemos?** O modelo simulado ignora a heterogeneidade entre seções de uma zona (sobredispersão), o que explica o pequeno desvio residual no 2º dígito.
- **Como conferir?** `resultados/2022/estatistica_testes_digitos.csv`.

### Seções com 100% dos votos válidos para um único candidato

| turno | faixa_validos | secoes | secoes_100pct_um_candidato |
|---|---|---|---|
| 1 | 100+ | 466.307 | 17 |
| 1 | 50-99 | 5.066 | 30 |
| 1 | <50 | 651 | 15 |
| 2 | 100+ | 466.146 | 63 |
| 2 | 50-99 | 5.180 | 56 |
| 2 | <50 | 701 | 28 |

