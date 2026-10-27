# Auditoria 2022 — Presidente

_Gerado automaticamente por `scripts/gerar_relatorios.py` em 27/10/2026 00:32 UTC. Todos os números vêm de `resultados/2022/`. Ver método em `docs/metodologia.md`._

## Cobertura dos arquivos de urna (logs e BU binário)

- 1º turno: 20 de 28 pacotes (27 UFs + exterior) processados; 156.188 seções lidas, 0 com falha de leitura, 158 sem log no pacote.
- 2º turno: 16 de 28 pacotes (27 UFs + exterior) processados; 90.671 seções lidas, 0 com falha de leitura, 33 sem log no pacote.

**Pacotes ainda não processados** — 1º turno: BA, CE, MG, PE, PR, RJ, RS, SP; 2º turno: BA, CE, GO, MA, MG, PA, PE, PR, RJ, RS, SC, SP. Indicadores de log abaixo valem apenas para a cobertura indicada.

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
| A2 | presenca | BWEB | BUBIN | 47.768 | 138 | 138 | 0 |
| A3 | presenca | DSEC | BWEB | 944.150 | 94 | 94 | 0 |
| B1 | comparecimento_vs_soma_votos | BWEB | BWEB | 944.056 | 0 | 0 | 0 |
| B2 | aptos | BWEB | BUBIN | 47.630 | 0 | 0 | 0 |
| B2 | biometria_nh_vs_lib_codigo | BWEB | BUBIN | 47.630 | 1.899 | 1.899 | 0 |
| B2 | brancos | BWEB | BUBIN | 47.630 | 0 | 0 | 0 |
| B2 | comparecimento | BWEB | BUBIN | 47.630 | 0 | 0 | 0 |
| B2 | nulos | BWEB | BUBIN | 47.630 | 0 | 0 | 0 |
| B2 | votos_nominais | BWEB | BUBIN | 47.630 | 0 | 0 | 0 |
| B2 | votos_por_candidato_soma_dif_abs | BWEB | BUBIN | 47.630 | 0 | 0 | 0 |
| B2c | votos_extra_no_bu | BUBIN | BWEB | 47.630 | 0 | 0 | 0 |
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
| B6 | biometria_nh_vs_liberacao_manual_no_log | BWEB | LOG | 114.337 | 7 | 4 | 3 |
| B6 | comparecimento_vs_votos_computados | BWEB | LOG | 114.337 | 15 | 3 | 12 |
| B6 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | BWEB | LOG | 114.337 | 72 | 67 | 5 |
| C1 | aptos_vs_comp_mais_abst | BWEB | BWEB | 944.056 | 0 | 0 | 0 |
| K1 | votos_votavel | BWEB | VSEC | 5.380.733 | 0 | 0 | 0 |


Legenda: BWEB = BU publicado em CSV; BUBIN = arquivo .bu transmitido pela urna; LOG = log da urna; DSEC = detalhe da apuração por seção; VSEC = votação por seção; CMZ = votação nominal por município/zona; DMZ = detalhe por município/zona. A lista completa, caso a caso, está em `resultados/2022/incompatibilidades.csv`.

### Boletins de Urna, arquivos da urna e tabelas oficiais

**Classificação:** Conferido (com diferenças explicadas e incompatibilidades listadas)

- **O que verificamos?** Se o mesmo número aparece igual em todas as publicações oficiais que deveriam coincidir, seção a seção (BU em CSV, BU binário, detalhe por seção, votação por seção) e na soma por zona.
- **O que os números mostram?** 17 de 29 comparações sem nenhuma divergência; 20 divergências ainda sem explicação documental (listadas abaixo).
- **O que significa?** Os votos publicados por seção são os mesmos do arquivo binário assinado gerado pela urna e das demais tabelas do TSE.
- **Existe explicação conhecida?** As divergências explicadas decorrem de seções não instaladas, seções apuradas pelo Sistema de Apuração (cédulas), campos opcionais omitidos no exterior e eleitores de seções não instaladas incluídos nos aptos por zona.
- **O que ainda não sabemos?** A verificação criptográfica das assinaturas dos arquivos (.vscmr) não foi feita nesta etapa.
- **Como conferir?** `resultados/2022/reconciliacao_resumo.csv` e `incompatibilidades.csv`; código `observatorio/reconciliacao.py`.

#### Incompatibilidades documentais ainda não explicadas

| teste | turno | uf | cd_municipio | nr_zona | nr_secao | campo | valor_a | fonte_a | valor_b | fonte_b |
|---|---|---|---|---|---|---|---|---|---|---|
| B6 | 1 | DF | 97.012 | 17 | 90 | biometria_nh_vs_liberacao_manual_no_log | 49 | BWEB | 37 | LOG |
| B6 | 1 | MS | 98.035 | 38 | 8 | biometria_nh_vs_liberacao_manual_no_log | 38 | BWEB | 36 | LOG |
| B6 | 1 | SE | 31.690 | 12 | 77 | biometria_nh_vs_liberacao_manual_no_log | 52 | BWEB | 51 | LOG |
| B6 | 1 | AL | 27.219 | 9 | 5 | comparecimento_vs_votos_computados | 242 | BWEB | 241 | LOG |
| B6 | 1 | DF | 97.012 | 17 | 90 | comparecimento_vs_votos_computados | 274 | BWEB | 261 | LOG |
| B6 | 1 | ES | 56.189 | 41 | 226 | comparecimento_vs_votos_computados | 230 | BWEB | 229 | LOG |
| B6 | 1 | ES | 56.251 | 54 | 126 | comparecimento_vs_votos_computados | 251 | BWEB | 250 | LOG |
| B6 | 1 | ES | 56.251 | 54 | 511 | comparecimento_vs_votos_computados | 289 | BWEB | 288 | LOG |
| B6 | 1 | MS | 98.035 | 38 | 8 | comparecimento_vs_votos_computados | 193 | BWEB | 120 | LOG |
| B6 | 1 | RN | 16.977 | 68 | 66 | comparecimento_vs_votos_computados | 270 | BWEB | 271 | LOG |
| B6 | 1 | RN | 18.139 | 65 | 32 | comparecimento_vs_votos_computados | 249 | BWEB | 259 | LOG |
| B6 | 1 | RN | 18.953 | 7 | 123 | comparecimento_vs_votos_computados | 267 | BWEB | 266 | LOG |
| B6 | 1 | SE | 31.690 | 12 | 77 | comparecimento_vs_votos_computados | 209 | BWEB | 208 | LOG |
| B6 | 2 | DF | 97.012 | 6 | 44 | comparecimento_vs_votos_computados | 259 | BWEB | 258 | LOG |
| B6 | 2 | TO | 73.440 | 29 | 229 | comparecimento_vs_votos_computados | 270 | BWEB | 269 | LOG |
| B6 | 1 | DF | 97.012 | 17 | 90 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 274 | BWEB | 261 | LOG |
| B6 | 1 | MS | 98.035 | 38 | 8 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 193 | BWEB | 120 | LOG |
| B6 | 1 | RN | 16.330 | 5 | 173 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 260 | BWEB | 262 | LOG |
| B6 | 1 | RN | 16.977 | 68 | 66 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 270 | BWEB | 271 | LOG |
| B6 | 1 | RN | 18.139 | 65 | 32 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 249 | BWEB | 259 | LOG |


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
- **O que os números mostram?** Em 18.785 seções com log (4.387.404 votos): 0 votos antes das 8h em 0 seções; 111.797 votos após as 17h (2,548%) em 6.896 seções; 22.823 após 18h; 3.856 após 19h.
- **O que significa?** Votos depois das 17h são previstos em lei para quem estava na fila. Votos antes das 8h, se existirem, precisam ser examinados um a um (relógio, fuso, troca de urna).
- **Existe explicação conhecida?** Fila às 17h (Res. 23.669/2021, art. 136, §§ 1º–2º). A distribuição por UF acompanha o tamanho das seções e o volume do 1º turno (5 cargos).
- **O que ainda não sabemos?** O log não registra a senha distribuída às 17h, portanto não é possível confirmar, eleitor a eleitor, que quem votou depois das 17h estava na fila.
- **Como conferir?** `resultados/2022/temporal_por_uf.csv`, `secoes_horarios_atipicos.csv`, `votos_por_15min.csv`; gráfico `resultados/{ano}/graficos/votos_por_15min.png`.

### 2º turno: votos antes das 8h e depois das 17h (horário de Brasília)

**Classificação:** Conferido (distribuição descrita)

- **O que verificamos?** Quantos votos concluídos o log registra fora do horário regular, após converter o relógio de cada urna para o horário de Brasília pelo fuso legal do município.
- **O que os números mostram?** Em 13.287 seções com log (2.905.466 votos): 0 votos antes das 8h em 0 seções; 1.355 votos após as 17h (0,047%) em 1.157 seções; 0 após 18h; 0 após 19h.
- **O que significa?** Votos depois das 17h são previstos em lei para quem estava na fila. Votos antes das 8h, se existirem, precisam ser examinados um a um (relógio, fuso, troca de urna).
- **Existe explicação conhecida?** Fila às 17h (Res. 23.669/2021, art. 136, §§ 1º–2º). A distribuição por UF acompanha o tamanho das seções e o volume do 1º turno (5 cargos).
- **O que ainda não sabemos?** O log não registra a senha distribuída às 17h, portanto não é possível confirmar, eleitor a eleitor, que quem votou depois das 17h estava na fila.
- **Como conferir?** `resultados/2022/temporal_por_uf.csv`, `secoes_horarios_atipicos.csv`, `votos_por_15min.csv`; gráfico `resultados/{ano}/graficos/votos_por_15min.png`.

### Validação dos fusos horários

**Classificação:** Conferido

- **O que verificamos?** Se o fuso legal atribuído a cada município é coerente com o horário local do primeiro voto.
- **O que os números mostram?** 563 combinações município×turno avaliadas; 0 divergentes.
- **O que significa?** Sem divergências, os horários convertidos são confiáveis; divergências indicariam erro de fuso ou relógio.
- **Existe explicação conhecida?** Lista legal de municípios do oeste do AM em UTC-5 e Fernando de Noronha em UTC-2.
- **O que ainda não sabemos?** Relógios individuais de urnas podem diferir do município; isso aparece como retrocesso de relógio ou horário atípico na seção.
- **Como conferir?** `resultados/2022/validacao_fusos_municipio.csv`.

## 4. Identificação biométrica e alternativa (Teste F)

### 1º turno: quem votou sem reconhecimento biométrico

**Classificação:** Conferido

- **O que verificamos?** Quantos eleitores com biometria cadastrada votaram após liberação manual (sem reconhecimento da digital) e se o log confirma o número do BU.
- **O que os números mostram?** BU: 10.780.979 eleitores (8,74% do comparecimento) com biometria e não habilitados por ela. Nos logs processados: 3.673.665 votantes por biometria, 398.621 liberados manualmente após falha e 314.861 sem biometria cadastrada.
- **O que significa?** A liberação manual é o procedimento previsto quando a digital não é reconhecida; o número no BU e no log coincide (Teste B6).
- **Existe explicação conhecida?** Res.-TSE 23.669/2021, arts. 113–115 (até 4 leituras; depois ano de nascimento e digital do mesário).
- **O que ainda não sabemos?** O log de 2022 não identifica o motivo da falha (sujeira, desgaste, leitor); o modelo de urna influencia a taxa (ver Teste I).
- **Como conferir?** `resultados/2022/biometria_por_uf.csv`, `biometria_modalidade_por_hora.csv`, `biometria_duracao_por_modalidade_modelo.csv`.

### 2º turno: quem votou sem reconhecimento biométrico

**Classificação:** Conferido

- **O que verificamos?** Quantos eleitores com biometria cadastrada votaram após liberação manual (sem reconhecimento da digital) e se o log confirma o número do BU.
- **O que os números mostram?** BU: 10.011.347 eleitores (8,08% do comparecimento) com biometria e não habilitados por ela. Nos logs processados: 3.600.307 votantes por biometria, 359.839 liberados manualmente após falha e 300.786 sem biometria cadastrada.
- **O que significa?** A liberação manual é o procedimento previsto quando a digital não é reconhecida; o número no BU e no log coincide (Teste B6).
- **Existe explicação conhecida?** Res.-TSE 23.669/2021, arts. 113–115 (até 4 leituras; depois ano de nascimento e digital do mesário).
- **O que ainda não sabemos?** O log de 2022 não identifica o motivo da falha (sujeira, desgaste, leitor); o modelo de urna influencia a taxa (ver Teste I).
- **Como conferir?** `resultados/2022/biometria_por_uf.csv`, `biometria_modalidade_por_hora.csv`, `biometria_duracao_por_modalidade_modelo.csv`.

## 5. Modelos de urna (Teste I)

| turno | controle | indicador | diferenca_ingenua_pp | diferenca_controlada_pp | ic95_inf | ic95_sup | grupos_comparaveis | secoes_ref | secoes_outras |
|---|---|---|---|---|---|---|---|---|---|
| 1 | mesmo_local | pct_validos_22 | 2,461 | 0,420 | -0,223 | 1,076 | 133 | 690 | 660 |
| 1 | mesmo_local | pct_validos_13 | -4,328 | -0,486 | -1,159 | 0,163 | 133 | 690 | 660 |
| 1 | mesmo_local | pct_comparecimento | 1,878 | -0,242 | -1,129 | 0,641 | 133 | 690 | 660 |
| 1 | mesmo_local | pct_brancos_nulos | 0,123 | 0,101 | -0,098 | 0,298 | 133 | 690 | 660 |
| 1 | mesmo_local | pct_biometria_nh | -6,872 | -4,958 | -5,641 | -4,336 | 133 | 690 | 660 |
| 1 | mesma_zona | pct_validos_22 | 2,461 | 1,165 | 0,653 | 1,689 | 460 | 46.556 | 56.149 |
| 1 | mesma_zona | pct_validos_13 | -4,328 | -1,713 | -2,377 | -1,098 | 460 | 46.556 | 56.149 |
| 1 | mesma_zona | pct_comparecimento | 1,878 | -0,184 | -0,392 | 0,025 | 460 | 46.556 | 56.149 |
| 1 | mesma_zona | pct_brancos_nulos | 0,123 | -0,265 | -0,354 | -0,173 | 460 | 46.556 | 56.149 |
| 1 | mesma_zona | pct_biometria_nh | -6,872 | -4,663 | -4,834 | -4,502 | 460 | 46.556 | 56.149 |
| 1 | mesmo_municipio | pct_validos_22 | 2,461 | 0,654 | 0,093 | 1,234 | 310 | 52.757 | 58.965 |
| 1 | mesmo_municipio | pct_validos_13 | -4,328 | -1,195 | -1,833 | -0,508 | 310 | 52.757 | 58.965 |
| 1 | mesmo_municipio | pct_comparecimento | 1,878 | -0,025 | -0,358 | 0,318 | 310 | 52.757 | 58.965 |
| 1 | mesmo_municipio | pct_brancos_nulos | 0,123 | -0,267 | -0,371 | -0,170 | 310 | 52.757 | 58.965 |
| 1 | mesmo_municipio | pct_biometria_nh | -6,872 | -4,506 | -4,839 | -4,101 | 310 | 52.757 | 58.965 |
| 2 | mesmo_local | pct_validos_22 | 3,395 | 0,374 | -0,251 | 1,024 | 161 | 737 | 979 |
| 2 | mesmo_local | pct_validos_13 | -3,395 | -0,374 | -1,003 | 0,267 | 161 | 737 | 979 |
| 2 | mesmo_local | pct_comparecimento | 1,905 | -0,290 | -0,952 | 0,440 | 161 | 737 | 979 |
| 2 | mesmo_local | pct_brancos_nulos | 0,259 | 0,097 | -0,125 | 0,313 | 161 | 737 | 979 |
| 2 | mesmo_local | pct_biometria_nh | -6,387 | -4,606 | -5,202 | -4,064 | 161 | 737 | 979 |
| 2 | mesma_zona | pct_validos_22 | 3,395 | 1,336 | 0,771 | 1,926 | 461 | 46.601 | 56.116 |
| 2 | mesma_zona | pct_validos_13 | -3,395 | -1,336 | -1,928 | -0,805 | 461 | 46.601 | 56.116 |
| 2 | mesma_zona | pct_comparecimento | 1,905 | -0,253 | -0,488 | -0,017 | 461 | 46.601 | 56.116 |
| 2 | mesma_zona | pct_brancos_nulos | 0,259 | -0,075 | -0,132 | -0,020 | 461 | 46.601 | 56.116 |
| 2 | mesma_zona | pct_biometria_nh | -6,387 | -4,454 | -4,594 | -4,317 | 461 | 46.601 | 56.116 |
| 2 | mesmo_municipio | pct_validos_22 | 3,395 | 0,780 | 0,140 | 1,402 | 311 | 52.802 | 58.932 |
| 2 | mesmo_municipio | pct_validos_13 | -3,395 | -0,780 | -1,371 | -0,153 | 311 | 52.802 | 58.932 |
| 2 | mesmo_municipio | pct_comparecimento | 1,905 | -0,151 | -0,442 | 0,164 | 311 | 52.802 | 58.932 |
| 2 | mesmo_municipio | pct_brancos_nulos | 0,259 | -0,071 | -0,136 | -0,020 | 311 | 52.802 | 58.932 |
| 2 | mesmo_municipio | pct_biometria_nh | -6,387 | -4,302 | -4,607 | -3,888 | 311 | 52.802 | 58.932 |

### UE2020 × demais modelos: proporção de votos do nº 22

**Classificação:** Diferença estatística (controles fracos) / Conferido sem diferença (mesmo local)

- **O que verificamos?** Se seções com urna modelo 2020 têm resultado diferente de seções com outros modelos, comparando seções próximas (mesmo local de votação, mesma zona, mesmo município).
- **O que os números mostram?** Sem controle geográfico a diferença é grande (1º t.: 2,46 p.p., 2º t.: 3,39 p.p.). No mesmo local: 1º t. 0,42 p.p. (IC95% -0,22 a 1,08); 2º t. 0,37 p.p. (IC95% -0,25 a 1,02). Na mesma zona: 1º t. 1,17 p.p. (IC95% 0,65 a 1,69); 2º t. 1,34 p.p. (IC95% 0,77 a 1,93).
- **O que significa?** A maior parte da diferença bruta é geográfica. No controle mais forte (mesmo local) o intervalo inclui zero; com controles mais fracos (zona, município) resta diferença de cerca de 1 p.p., que pode refletir diferenças entre bairros/locais dentro da zona.
- **Existe explicação conhecida?** A distribuição dos modelos não é aleatória (logística do TSE por zona/local). O modelo 2020 tem leitor biométrico mais novo: a taxa de liberação manual é ~5 p.p. menor nas mesmas localidades, diferença técnica esperada.
- **O que ainda não sabemos?** Sem covariáveis anteriores à eleição por seção (ex.: resultado de 2018 na mesma seção), não é possível separar efeito do modelo de efeito de localização. Diferença estatística ≠ causalidade.
- **Como conferir?** `resultados/2022/modelos_efeito_controlado.csv`, `modelos_medias_ingenuas.csv`; gráfico `resultados/2022/graficos/modelos_efeito_22.png`.

## 6. Testes estatísticos de dígitos e distribuição (Teste J)

| teste | testes | rejeitados_holm_1pct | cramer_v_mediano | maior_desvio_pp_mediano |
|---|---|---|---|---|
| segundo_digito_benford_descritivo | 116 | 100 | 0,058 | 3,003 |
| segundo_digito_vs_simulacao_binomial_zona | 116 | 58 | 0,020 | 1,181 |
| ultimo_digito_uniforme | 116 | 12 | 0,011 | 0,635 |
| ultimo_digito_vs_simulacao_binomial_zona | 116 | 0 | 0,010 | 0,546 |

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

