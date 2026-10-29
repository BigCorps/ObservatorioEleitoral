# Auditoria 2026 — Presidente

_Gerado automaticamente por `scripts/gerar_relatorios.py` em 29/10/2026 14:37 UTC. Todos os números vêm de `resultados/2026/`. Ver método em `docs/metodologia.md`._

## Cobertura dos arquivos de urna (logs e BU binário)

- 1º turno: 28 de 28 pacotes (27 UFs + exterior) processados; 499.207 seções lidas, 0 com falha de leitura, 31 sem log no pacote.
- 2º turno: 28 de 28 pacotes (27 UFs + exterior) processados; 499.207 seções lidas, 0 com falha de leitura, 30 sem log no pacote.

## 1. Totais nacionais reproduzidos a partir das seções

| turno | seções | aptos | comparecimento | abstenções | válidos | brancos | nulos | % abstenção | % brancos | % nulos |
|---|---|---|---|---|---|---|---|---|---|---|
| 1º | 499.206 | 158.745.007 | 125.275.835 | 33.469.172 | 119.306.034 | 2.300.798 | 3.669.003 | 21,084 | 1,837 | 2,929 |
| 2º | 499.205 | 158.744.977 | 128.236.074 | 30.508.903 | 124.082.273 | 1.430.496 | 2.723.305 | 19,219 | 1,115 | 2,124 |


Os totais nacionais publicados pelo TSE (histórico de totalização e detalhe por município/zona) são reproduzidos pela soma das seções; a única diferença em *aptos* corresponde a eleitores de seções não instaladas, que não têm BU (ver B5 abaixo).

### Mudança entre turnos: comparecimento, brancos, nulos e válidos

**Classificação:** Conferido

- **O que verificamos?** Se a variação dos votos válidos entre os turnos é exatamente a variação do comparecimento menos a variação de brancos e nulos, em cada seção, zona, município, UF e no Brasil.
- **O que os números mostram?** Brasil: comparecimento 2.960.239; brancos+nulos -1.816.000; válidos 4.776.239; resíduo da identidade 0. Abstenção variou -1,865 p.p. (de 21,08% para 19,22% dos aptos); brancos -0,721 p.p.; nulos -0,805 p.p. (sobre o comparecimento). Lula (13) variou 10.376.694 votos e Bolsonaro (22) 3.721.538.
- **O que significa?** As contas fecham em todos os níveis. Os aumentos de votos de cada candidato são variações LÍQUIDAS: não dizem quem trocou de voto, quem deixou de votar ou quem passou a votar.
- **Existe explicação conhecida?** Candidatos eliminados no 1º turno deixam de receber votos; eleitores podem mudar de voto, abster-se ou voltar a votar.
- **O que ainda não sabemos?** Transferências individuais de voto não são observáveis (voto secreto). Qualquer estimativa de transferência exigiria inferência ecológica, com incerteza grande e hipóteses fortes; não foi feita.
- **Como conferir?** `resultados/2026/resultados_brasil.csv`, `resultados_uf.csv`, `resultados_municipio.csv`, `resultados_zona.csv`; código `observatorio/resultados_eleitorais.py`.

## 2. Reconciliação entre fontes oficiais (Testes A, B, C, K)

| teste | campo | fonte_a | fonte_b | registros_comparados | divergencias | explicadas | não_explicadas |
|---|---|---|---|---|---|---|---|
| A2 | presenca | BWEB | BUBIN | 998.414 | 3 | 2 | 1 |
| A3 | presenca | DSEC | BWEB | 998.496 | 85 | 85 | 0 |
| B1 | comparecimento_vs_soma_votos | BWEB | BWEB | 998.411 | 0 | 0 | 0 |
| B2 | aptos | BWEB | BUBIN | 998.411 | 0 | 0 | 0 |
| B2 | biometria_nh_vs_lib_codigo | BWEB | BUBIN | 998.411 | 2.619 | 2.617 | 2 |
| B2 | brancos | BWEB | BUBIN | 998.411 | 0 | 0 | 0 |
| B2 | comparecimento | BWEB | BUBIN | 998.411 | 0 | 0 | 0 |
| B2 | nulos | BWEB | BUBIN | 998.411 | 0 | 0 | 0 |
| B2 | votos_nominais | BWEB | BUBIN | 998.411 | 0 | 0 | 0 |
| B2 | votos_por_candidato_soma_dif_abs | BWEB | BUBIN | 998.411 | 0 | 0 | 0 |
| B2c | votos_extra_no_bu | BUBIN | BWEB | 998.411 | 0 | 0 | 0 |
| B3 | abstencoes | BWEB | DSEC | 998.411 | 0 | 0 | 0 |
| B3 | aptos | BWEB | DSEC | 998.411 | 0 | 0 | 0 |
| B3 | brancos | BWEB | DSEC | 998.411 | 0 | 0 | 0 |
| B3 | comparecimento | BWEB | DSEC | 998.411 | 0 | 0 | 0 |
| B3 | nulos | BWEB | DSEC | 998.411 | 0 | 0 | 0 |
| B3 | votos_nominais | BWEB | DSEC | 998.411 | 0 | 0 | 0 |
| B4 | votos_candidato_zona | BWEB | CMZ | 74.888 | 2.148 | 2.148 | 0 |
| B5 | abstencoes | BWEB | DMZ | 12.584 | 83 | 83 | 0 |
| B5 | aptos | BWEB | DMZ | 12.584 | 83 | 83 | 0 |
| B5 | brancos | BWEB | DMZ | 12.584 | 83 | 83 | 0 |
| B5 | comparecimento | BWEB | DMZ | 12.584 | 83 | 83 | 0 |
| B5 | nulos | BWEB | DMZ | 12.584 | 2.231 | 2.231 | 0 |
| B5 | validos | BWEB | DMZ | 12.584 | 2.231 | 2.231 | 0 |
| B6 | biometria_nh_vs_liberacao_manual_no_log | BWEB | LOG | 998.353 | 6 | 0 | 6 |
| B6 | comparecimento_vs_votos_computados | BWEB | LOG | 998.353 | 15 | 0 | 15 |
| B6 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | BWEB | LOG | 998.353 | 207 | 196 | 11 |
| B8 | habilitados_por_biografia_vs_manual_apos_falha | BUBIN | LOG | 995.791 | 6 | 0 | 6 |
| B8 | habilitados_por_biometria | BUBIN | LOG | 995.791 | 8.346 | 8.330 | 16 |
| B8 | sem_biometria_cadastrada | BUBIN | LOG | 995.791 | 3 | 0 | 3 |
| C1 | aptos_vs_comp_mais_abst | BWEB | BWEB | 998.411 | 0 | 0 | 0 |
| K1 | votos_votavel | BWEB | VSEC | 5.731.614 | 0 | 0 | 0 |
| K2 | brancos | DSEC | VSEC | 998.414 | 0 | 0 | 0 |
| K2 | nulos | DSEC | VSEC | 998.414 | 0 | 0 | 0 |
| K2 | votos_nominais | DSEC | VSEC | 998.414 | 0 | 0 | 0 |


Legenda: BWEB = BU publicado em CSV; BUBIN = arquivo .bu transmitido pela urna; LOG = log da urna; DSEC = detalhe da apuração por seção; VSEC = votação por seção; CMZ = votação nominal por município/zona; DMZ = detalhe por município/zona. A lista completa, caso a caso, está em `resultados/2026/incompatibilidades.csv`.

### Boletins de Urna, arquivos da urna e tabelas oficiais

**Classificação:** Conferido (com diferenças explicadas e incompatibilidades listadas)

- **O que verificamos?** Se o mesmo número aparece igual em todas as publicações oficiais que deveriam coincidir, seção a seção (BU em CSV, BU binário, detalhe por seção, votação por seção) e na soma por zona.
- **O que os números mostram?** 19 de 35 comparações sem nenhuma divergência; 60 divergências ainda sem explicação documental (listadas abaixo).
- **O que significa?** Os votos publicados por seção são os mesmos do arquivo binário assinado gerado pela urna e das demais tabelas do TSE.
- **Existe explicação conhecida?** As divergências explicadas decorrem de seções não instaladas, seções apuradas pelo Sistema de Apuração (cédulas), campos opcionais omitidos no exterior e eleitores de seções não instaladas incluídos nos aptos por zona.
- **O que ainda não sabemos?** A verificação criptográfica das assinaturas dos arquivos (.vscmr) não foi feita nesta etapa.
- **Como conferir?** `resultados/2026/reconciliacao_resumo.csv` e `incompatibilidades.csv`; código `observatorio/reconciliacao.py`.

#### Incompatibilidades documentais ainda não explicadas

| teste | turno | uf | cd_municipio | nr_zona | nr_secao | campo | valor_a | fonte_a | valor_b | fonte_b |
|---|---|---|---|---|---|---|---|---|---|---|
| A2 | 1 | ZZ | 29.564 | 1 | 91 | presenca | — | BWEB | 1 | BUBIN |
| B2 | 1 | MG | 41.238 | 39 | 168 | biometria_nh_vs_lib_codigo | 0 | BWEB | — | BUBIN |
| B2 | 1 | MG | 50.075 | 47 | 41 | biometria_nh_vs_lib_codigo | 0 | BWEB | — | BUBIN |
| B6 | 1 | BA | 39.934 | 183 | 175 | biometria_nh_vs_liberacao_manual_no_log | 17 | BWEB | 16 | LOG |
| B6 | 1 | RJ | 60.011 | 8 | 61 | biometria_nh_vs_liberacao_manual_no_log | 38 | BWEB | 37 | LOG |
| B6 | 1 | SP | 71.072 | 2 | 35 | biometria_nh_vs_liberacao_manual_no_log | 18 | BWEB | 16 | LOG |
| B6 | 2 | BA | 35.653 | 173 | 235 | biometria_nh_vs_liberacao_manual_no_log | 33 | BWEB | 21 | LOG |
| B6 | 2 | MA | 8.893 | 47 | 609 | biometria_nh_vs_liberacao_manual_no_log | 19 | BWEB | 15 | LOG |
| B6 | 2 | RS | 89.060 | 17 | 191 | biometria_nh_vs_liberacao_manual_no_log | 12 | BWEB | 11 | LOG |
| B6 | 1 | BA | 39.934 | 183 | 175 | comparecimento_vs_votos_computados | 272 | BWEB | 236 | LOG |
| B6 | 1 | ES | 56.995 | 53 | 211 | comparecimento_vs_votos_computados | 265 | BWEB | 264 | LOG |
| B6 | 1 | RJ | 58.971 | 87 | 184 | comparecimento_vs_votos_computados | 258 | BWEB | 256 | LOG |
| B6 | 1 | RN | 16.039 | 29 | 28 | comparecimento_vs_votos_computados | 242 | BWEB | 241 | LOG |
| B6 | 1 | RS | 89.036 | 83 | 44 | comparecimento_vs_votos_computados | 279 | BWEB | 278 | LOG |
| B6 | 1 | SP | 63.614 | 227 | 305 | comparecimento_vs_votos_computados | 290 | BWEB | 289 | LOG |
| B6 | 1 | SP | 64.254 | 291 | 346 | comparecimento_vs_votos_computados | 278 | BWEB | 277 | LOG |
| B6 | 1 | SP | 71.072 | 2 | 35 | comparecimento_vs_votos_computados | 247 | BWEB | 232 | LOG |
| B6 | 1 | SP | 71.072 | 260 | 37 | comparecimento_vs_votos_computados | 285 | BWEB | 284 | LOG |
| B6 | 2 | BA | 34.711 | 21 | 178 | comparecimento_vs_votos_computados | 234 | BWEB | 233 | LOG |
| B6 | 2 | BA | 35.653 | 173 | 235 | comparecimento_vs_votos_computados | 217 | BWEB | 204 | LOG |
| B6 | 2 | MA | 8.893 | 47 | 609 | comparecimento_vs_votos_computados | 224 | BWEB | 188 | LOG |
| B6 | 2 | PB | 21.750 | 2 | 254 | comparecimento_vs_votos_computados | 304 | BWEB | 303 | LOG |
| B6 | 2 | PI | 11.533 | 3 | 216 | comparecimento_vs_votos_computados | 259 | BWEB | 258 | LOG |
| B6 | 2 | RS | 89.060 | 17 | 191 | comparecimento_vs_votos_computados | 92 | BWEB | 90 | LOG |
| B6 | 1 | BA | 39.934 | 183 | 175 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 272 | BWEB | 236 | LOG |
| B6 | 1 | RJ | 58.971 | 87 | 184 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 258 | BWEB | 256 | LOG |
| B6 | 1 | RJ | 60.011 | 8 | 61 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 311 | BWEB | 309 | LOG |
| B6 | 1 | RS | 89.036 | 83 | 44 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 279 | BWEB | 278 | LOG |
| B6 | 1 | SP | 70.971 | 268 | 43 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 219 | BWEB | 220 | LOG |
| B6 | 1 | SP | 71.072 | 2 | 35 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 247 | BWEB | 232 | LOG |
| B6 | 2 | BA | 33.634 | 75 | 137 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 235 | BWEB | 237 | LOG |
| B6 | 2 | BA | 35.653 | 173 | 235 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 217 | BWEB | 204 | LOG |
| B6 | 2 | BA | 37.850 | 51 | 146 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 283 | BWEB | 286 | LOG |
| B6 | 2 | MA | 8.893 | 47 | 609 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 224 | BWEB | 188 | LOG |
| B6 | 2 | RS | 89.060 | 17 | 191 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 92 | BWEB | 91 | LOG |
| B8 | 1 | BA | 39.934 | 183 | 175 | habilitados_por_biografia_vs_manual_apos_falha | 17 | BUBIN | 16 | LOG |
| B8 | 1 | RJ | 60.011 | 8 | 61 | habilitados_por_biografia_vs_manual_apos_falha | 38 | BUBIN | 37 | LOG |
| B8 | 1 | SP | 71.072 | 2 | 35 | habilitados_por_biografia_vs_manual_apos_falha | 18 | BUBIN | 16 | LOG |
| B8 | 2 | BA | 35.653 | 173 | 235 | habilitados_por_biografia_vs_manual_apos_falha | 33 | BUBIN | 21 | LOG |
| B8 | 2 | MA | 8.893 | 47 | 609 | habilitados_por_biografia_vs_manual_apos_falha | 19 | BUBIN | 15 | LOG |
| B8 | 2 | RS | 89.060 | 17 | 191 | habilitados_por_biografia_vs_manual_apos_falha | 12 | BUBIN | 11 | LOG |
| B8 | 1 | BA | 39.934 | 183 | 175 | habilitados_por_biometria | 231 | BUBIN | 200 | LOG |
| B8 | 1 | ES | 56.995 | 53 | 211 | habilitados_por_biometria | 98 | BUBIN | 97 | LOG |
| B8 | 1 | MG | 44.458 | 103 | 221 | habilitados_por_biometria | 222 | BUBIN | 221 | LOG |
| B8 | 1 | RJ | 58.971 | 87 | 184 | habilitados_por_biometria | 243 | BUBIN | 242 | LOG |
| B8 | 1 | RJ | 60.011 | 8 | 61 | habilitados_por_biometria | 252 | BUBIN | 251 | LOG |
| B8 | 1 | RN | 16.039 | 29 | 28 | habilitados_por_biometria | 205 | BUBIN | 204 | LOG |
| B8 | 1 | RS | 89.036 | 83 | 44 | habilitados_por_biometria | 238 | BUBIN | 237 | LOG |
| B8 | 1 | SP | 63.614 | 227 | 305 | habilitados_por_biometria | 262 | BUBIN | 261 | LOG |
| B8 | 1 | SP | 64.254 | 291 | 346 | habilitados_por_biometria | 252 | BUBIN | 251 | LOG |
| B8 | 1 | SP | 71.072 | 2 | 35 | habilitados_por_biometria | 219 | BUBIN | 206 | LOG |
| B8 | 1 | SP | 71.072 | 260 | 37 | habilitados_por_biometria | 253 | BUBIN | 252 | LOG |
| B8 | 2 | BA | 35.653 | 173 | 235 | habilitados_por_biometria | 159 | BUBIN | 158 | LOG |
| B8 | 2 | MA | 8.893 | 47 | 609 | habilitados_por_biometria | 205 | BUBIN | 173 | LOG |
| B8 | 2 | PB | 21.750 | 2 | 254 | habilitados_por_biometria | 263 | BUBIN | 262 | LOG |
| B8 | 2 | PI | 11.533 | 3 | 216 | habilitados_por_biometria | 238 | BUBIN | 237 | LOG |
| B8 | 2 | RS | 89.060 | 17 | 191 | habilitados_por_biometria | 78 | BUBIN | 77 | LOG |
| B8 | 1 | BA | 39.934 | 183 | 175 | sem_biometria_cadastrada | 24 | BUBIN | 20 | LOG |
| B8 | 1 | RJ | 58.971 | 87 | 184 | sem_biometria_cadastrada | 6 | BUBIN | 5 | LOG |
| B8 | 2 | BA | 34.711 | 21 | 178 | sem_biometria_cadastrada | 78 | BUBIN | 77 | LOG |


Diagnóstico individual de cada caso (estrutura do log: arquivos, urnas, eventos de contingência) em `resultados/2026/diagnosticos/`.

## 3. Horários de votação (Testes D e E)

### 1º turno: votos antes das 8h e depois das 17h (horário de Brasília)

**Classificação:** Conferido (distribuição descrita)

- **O que verificamos?** Quantos votos concluídos o log registra fora do horário regular, após converter o relógio de cada urna para o horário de Brasília pelo fuso legal do município.
- **O que os números mostram?** Em 497.895 seções com log (124.933.451 votos): 0 votos antes das 8h em 0 seções; 3.723.678 votos após as 17h (2,981%) em 221.609 seções; 779.454 após 18h; 131.143 após 19h.
- **O que significa?** Votos depois das 17h são previstos em lei para quem estava na fila. Votos antes das 8h, se existirem, precisam ser examinados um a um (relógio, fuso, troca de urna).
- **Existe explicação conhecida?** Fila às 17h (Res. 23.669/2021, art. 136, §§ 1º–2º). A distribuição por UF acompanha o tamanho das seções e o volume do 1º turno (5 cargos).
- **O que ainda não sabemos?** O log não registra a senha distribuída às 17h, portanto não é possível confirmar, eleitor a eleitor, que quem votou depois das 17h estava na fila.
- **Como conferir?** `resultados/2026/temporal_por_uf.csv`, `secoes_horarios_atipicos.csv`, `votos_por_15min.csv`; gráfico `resultados/{ano}/graficos/votos_por_15min.png`.

### 2º turno: votos antes das 8h e depois das 17h (horário de Brasília)

**Classificação:** Conferido (distribuição descrita)

- **O que verificamos?** Quantos votos concluídos o log registra fora do horário regular, após converter o relógio de cada urna para o horário de Brasília pelo fuso legal do município.
- **O que os números mostram?** Em 497.896 seções com log (127.854.309 votos): 0 votos antes das 8h em 0 seções; 34.050 votos após as 17h (0,027%) em 29.609 seções; 1.993 após 18h; 11 após 19h.
- **O que significa?** Votos depois das 17h são previstos em lei para quem estava na fila. Votos antes das 8h, se existirem, precisam ser examinados um a um (relógio, fuso, troca de urna).
- **Existe explicação conhecida?** Fila às 17h (Res. 23.669/2021, art. 136, §§ 1º–2º). A distribuição por UF acompanha o tamanho das seções e o volume do 1º turno (5 cargos).
- **O que ainda não sabemos?** O log não registra a senha distribuída às 17h, portanto não é possível confirmar, eleitor a eleitor, que quem votou depois das 17h estava na fila.
- **Como conferir?** `resultados/2026/temporal_por_uf.csv`, `secoes_horarios_atipicos.csv`, `votos_por_15min.csv`; gráfico `resultados/{ano}/graficos/votos_por_15min.png`.

### Validação dos fusos horários

**Classificação:** Pendente

- **O que verificamos?** Se o fuso legal atribuído a cada município é coerente com o horário local do primeiro voto.
- **O que os números mostram?** 11.142 combinações município×turno avaliadas; 3 divergentes.
- **O que significa?** Sem divergências, os horários convertidos são confiáveis; divergências indicariam erro de fuso ou relógio.
- **Existe explicação conhecida?** Lista legal de municípios do oeste do AM em UTC-5 e Fernando de Noronha em UTC-2.
- **O que ainda não sabemos?** Relógios individuais de urnas podem diferir do município; isso aparece como retrocesso de relógio ou horário atípico na seção.
- **Como conferir?** `resultados/2026/validacao_fusos_municipio.csv`.

### Intervalos muito curtos entre votos ("rajadas")

| turno | limiar_s | min_votos | sequencias | votos_em_sequencias | secoes |
|---|---|---|---|---|---|
| 1 | 6 | 5 | 0 | 0 | 0 |
| 1 | 10 | 5 | 0 | 0 | 0 |
| 1 | 20 | 3 | 0 | 0 | 0 |
| 1 | 20 | 5 | 0 | 0 | 0 |
| 1 | 30 | 3 | 122 | 382 | 80 |
| 1 | 30 | 5 | 3 | 15 | 3 |
| 2 | 6 | 5 | 0 | 0 | 0 |
| 2 | 10 | 5 | 0 | 0 | 0 |
| 2 | 20 | 3 | 1 | 3 | 1 |
| 2 | 20 | 5 | 0 | 0 | 0 |
| 2 | 30 | 3 | 125601 | 402851 | 60275 |
| 2 | 30 | 5 | 4378 | 23569 | 3689 |


Intervalo = tempo entre dois registros consecutivos de voto concluído na mesma urna. Grade de sensibilidade com limiares de 6 a 30 s e mínimo de 3 ou 5 votos. Versão com intervalos entre habilitações em `resultados/2026/rajadas_sensibilidade_habilitacoes.csv`.

## 4. Identificação biométrica e alternativa (Teste F)

### 1º turno: quem votou sem reconhecimento biométrico

**Classificação:** Conferido

- **O que verificamos?** Quantos eleitores com biometria cadastrada votaram após liberação manual (sem reconhecimento da digital) e se o log confirma o número do BU.
- **O que os números mostram?** BU: 8.342.249 eleitores (6,68% do comparecimento) com biometria e não habilitados por ela. Nos logs processados: 109.646.855 votantes por biometria, 8.342.245 liberados manualmente após falha e 6.940.329 sem biometria cadastrada.
- **O que significa?** A liberação manual é o procedimento previsto quando a digital não é reconhecida; o número no BU e no log coincide (Teste B6).
- **Existe explicação conhecida?** Res.-TSE 23.669/2021, arts. 113–115 (até 4 leituras; depois ano de nascimento e digital do mesário).
- **O que ainda não sabemos?** O log de 2022 não identifica o motivo da falha (sujeira, desgaste, leitor); o modelo de urna influencia a taxa (ver Teste I).
- **Como conferir?** `resultados/2026/biometria_por_uf.csv`, `biometria_modalidade_por_hora.csv`, `biometria_duracao_por_modalidade_modelo.csv`.

### 2º turno: quem votou sem reconhecimento biométrico

**Classificação:** Conferido

- **O que verificamos?** Quantos eleitores com biometria cadastrada votaram após liberação manual (sem reconhecimento da digital) e se o log confirma o número do BU.
- **O que os números mostram?** BU: 8.632.488 eleitores (6,75% do comparecimento) com biometria e não habilitados por ela. Nos logs processados: 111.965.700 votantes por biometria, 8.632.445 liberados manualmente após falha e 7.251.808 sem biometria cadastrada.
- **O que significa?** A liberação manual é o procedimento previsto quando a digital não é reconhecida; o número no BU e no log coincide (Teste B6).
- **Existe explicação conhecida?** Res.-TSE 23.669/2021, arts. 113–115 (até 4 leituras; depois ano de nascimento e digital do mesário).
- **O que ainda não sabemos?** O log de 2022 não identifica o motivo da falha (sujeira, desgaste, leitor); o modelo de urna influencia a taxa (ver Teste I).
- **Como conferir?** `resultados/2026/biometria_por_uf.csv`, `biometria_modalidade_por_hora.csv`, `biometria_duracao_por_modalidade_modelo.csv`.

## 5. Modelos de urna (Teste I)

| turno | controle | indicador | diferenca_ingenua_pp | diferenca_controlada_pp | ic95_inf | ic95_sup | grupos_comparaveis | secoes_ref | secoes_outras |
|---|---|---|---|---|---|---|---|---|---|
| 1 | mesmo_local | pct_validos_22 | 0,489 | -0,016 | -0,116 | 0,078 | 5.243 | 22.416 | 21.726 |
| 1 | mesmo_local | pct_validos_13 | -0,284 | 0,027 | -0,070 | 0,128 | 5.243 | 22.416 | 21.726 |
| 1 | mesmo_local | pct_comparecimento | -0,172 | 0,120 | 0,029 | 0,219 | 5.243 | 22.416 | 21.726 |
| 1 | mesmo_local | pct_brancos_nulos | 0,012 | 0,012 | -0,025 | 0,049 | 5.243 | 22.416 | 21.726 |
| 1 | mesmo_local | pct_biometria_nh | -1,213 | -0,026 | -0,086 | 0,033 | 5.243 | 22.416 | 21.726 |
| 1 | mesma_zona | pct_validos_22 | 0,489 | -0,055 | -0,398 | 0,293 | 1.048 | 63.329 | 84.411 |
| 1 | mesma_zona | pct_validos_13 | -0,284 | -0,023 | -0,425 | 0,344 | 1.048 | 63.329 | 84.411 |
| 1 | mesma_zona | pct_comparecimento | -0,172 | 0,080 | -0,062 | 0,221 | 1.048 | 63.329 | 84.411 |
| 1 | mesma_zona | pct_brancos_nulos | 0,012 | 0,014 | -0,047 | 0,076 | 1.048 | 63.329 | 84.411 |
| 1 | mesma_zona | pct_biometria_nh | -1,213 | -0,821 | -0,922 | -0,717 | 1.048 | 63.329 | 84.411 |
| 1 | mesmo_municipio | pct_validos_22 | 0,489 | 0,266 | -0,355 | 0,931 | 879 | 76.226 | 110.528 |
| 1 | mesmo_municipio | pct_validos_13 | -0,284 | -0,312 | -0,979 | 0,380 | 879 | 76.226 | 110.528 |
| 1 | mesmo_municipio | pct_comparecimento | -0,172 | 0,146 | -0,046 | 0,309 | 879 | 76.226 | 110.528 |
| 1 | mesmo_municipio | pct_brancos_nulos | 0,012 | -0,042 | -0,129 | 0,050 | 879 | 76.226 | 110.528 |
| 1 | mesmo_municipio | pct_biometria_nh | -1,213 | -1,068 | -1,536 | -0,663 | 879 | 76.226 | 110.528 |
| 2 | mesmo_local | pct_validos_22 | 0,422 | 0,011 | -0,084 | 0,104 | 5.398 | 23.124 | 22.731 |
| 2 | mesmo_local | pct_validos_13 | -0,422 | -0,011 | -0,106 | 0,083 | 5.398 | 23.124 | 22.731 |
| 2 | mesmo_local | pct_comparecimento | -0,193 | 0,070 | -0,023 | 0,159 | 5.398 | 23.124 | 22.731 |
| 2 | mesmo_local | pct_brancos_nulos | -0,047 | 0,007 | -0,025 | 0,037 | 5.398 | 23.124 | 22.731 |
| 2 | mesmo_local | pct_biometria_nh | -1,226 | -0,057 | -0,114 | 0,002 | 5.398 | 23.124 | 22.731 |
| 2 | mesma_zona | pct_validos_22 | 0,422 | -0,150 | -0,498 | 0,203 | 1.078 | 63.943 | 87.847 |
| 2 | mesma_zona | pct_validos_13 | -0,422 | 0,150 | -0,201 | 0,489 | 1.078 | 63.943 | 87.847 |
| 2 | mesma_zona | pct_comparecimento | -0,193 | -0,004 | -0,141 | 0,133 | 1.078 | 63.943 | 87.847 |
| 2 | mesma_zona | pct_brancos_nulos | -0,047 | 0,023 | -0,014 | 0,059 | 1.078 | 63.943 | 87.847 |
| 2 | mesma_zona | pct_biometria_nh | -1,226 | -0,770 | -0,878 | -0,659 | 1.078 | 63.943 | 87.847 |
| 2 | mesmo_municipio | pct_validos_22 | 0,422 | 0,064 | -0,641 | 0,816 | 902 | 78.264 | 116.479 |
| 2 | mesmo_municipio | pct_validos_13 | -0,422 | -0,064 | -0,825 | 0,675 | 902 | 78.264 | 116.479 |
| 2 | mesmo_municipio | pct_comparecimento | -0,193 | -0,194 | -0,962 | 0,218 | 902 | 78.264 | 116.479 |
| 2 | mesmo_municipio | pct_brancos_nulos | -0,047 | -0,024 | -0,124 | 0,063 | 902 | 78.264 | 116.479 |
| 2 | mesmo_municipio | pct_biometria_nh | -1,226 | -0,728 | -1,467 | 0,199 | 902 | 78.264 | 116.479 |

### UE2020 × demais modelos: proporção de votos do nº 22

**Classificação:** Diferença estatística (controles fracos) / Conferido sem diferença (mesmo local)

- **O que verificamos?** Se seções com urna modelo 2020 têm resultado diferente de seções com outros modelos, comparando seções próximas (mesmo local de votação, mesma zona, mesmo município).
- **O que os números mostram?** Sem controle geográfico a diferença é grande (1º t.: 0,49 p.p., 2º t.: 0,42 p.p.). No mesmo local: 1º t. -0,02 p.p. (IC95% -0,12 a 0,08); 2º t. 0,01 p.p. (IC95% -0,08 a 0,10). Na mesma zona: 1º t. -0,06 p.p. (IC95% -0,40 a 0,29); 2º t. -0,15 p.p. (IC95% -0,50 a 0,20).
- **O que significa?** A maior parte da diferença bruta é geográfica. No controle mais forte (mesmo local) o intervalo inclui zero; com controles mais fracos (zona, município) resta diferença de cerca de 1 p.p., que pode refletir diferenças entre bairros/locais dentro da zona.
- **Existe explicação conhecida?** A distribuição dos modelos não é aleatória (logística do TSE por zona/local). O modelo 2020 tem leitor biométrico mais novo: a taxa de liberação manual é ~5 p.p. menor nas mesmas localidades, diferença técnica esperada.
- **O que ainda não sabemos?** Sem covariáveis anteriores à eleição por seção (ex.: resultado de 2018 na mesma seção), não é possível separar efeito do modelo de efeito de localização. Diferença estatística ≠ causalidade.
- **Como conferir?** `resultados/2026/modelos_efeito_controlado.csv`, `modelos_medias_ingenuas.csv`; gráfico `resultados/2026/graficos/modelos_efeito_22.png`.

## 6. Testes estatísticos de dígitos e distribuição (Teste J)

| teste | testes | rejeitados_holm_1pct | cramer_v_mediano | maior_desvio_pp_mediano |
|---|---|---|---|---|
| segundo_digito_benford_descritivo | 116 | 105 | 0,062 | 3,158 |
| segundo_digito_vs_simulacao_binomial_zona | 116 | 65 | 0,021 | 1,103 |
| ultimo_digito_uniforme | 116 | 13 | 0,011 | 0,642 |
| ultimo_digito_vs_simulacao_binomial_zona | 116 | 0 | 0,010 | 0,535 |

### Dígitos das contagens por seção

**Classificação:** Diferença estatística (sem relevância prática) — não é evidência de irregularidade

- **O que verificamos?** Se o último e o segundo dígito dos votos por seção de Lula (13) e Bolsonaro (22) seguem o esperado.
- **O que os números mostram?** Contra a referência teórica (uniforme / Benford) há rejeições, com efeitos pequenos. Contra a referência simulada (binomial com o tamanho real das seções e a proporção da zona), o último dígito não é rejeitado em nenhum caso, e o desvio do 2º dígito cai para frações de ponto percentual.
- **O que significa?** As rejeições contra Benford vêm da premissa errada (seções têm tamanho limitado), não dos votos.
- **Existe explicação conhecida?** Literatura: Mebane (2006); Deckert, Myagkov & Ordeshook (2011) — testes de dígitos não detectam fraude de forma confiável.
- **O que ainda não sabemos?** O modelo simulado ignora a heterogeneidade entre seções de uma zona (sobredispersão), o que explica o pequeno desvio residual no 2º dígito.
- **Como conferir?** `resultados/2026/estatistica_testes_digitos.csv`.

### Seções com 100% dos votos válidos para um único candidato

| turno | faixa_validos | secoes | secoes_100pct_um_candidato |
|---|---|---|---|
| 1 | 100+ | 493.592 | 13 |
| 1 | 50-99 | 4.892 | 16 |
| 1 | <50 | 722 | 11 |
| 2 | 100+ | 493.803 | 65 |
| 2 | 50-99 | 4.725 | 26 |
| 2 | <50 | 677 | 19 |

