# Auditoria do 2º turno de 2026 (25/10/2026) — Presidente

_Gerado por `scripts/gerar_relatorios.py`. Fonte dos arquivos de urna: Portal de Resultados do TSE, seção a seção (`observatorio/arquivos_secao.py`), com verificação de hash. Os números de terceiros aparecem só como afirmações a verificar._

## 1–3. Cobertura e integridade

- Seções esperadas (resultado oficial por seção): 499.207; processadas: 499.207 (**100,00%**); falhas de download: 0.
- Hash publicado = SHA-256 do `vota.vsc`: 499.178 seções; SHA-512 do BU listado no `vsc`: 499.178; SHA-512 do log listado no `vsc`: 499.177. Nenhuma falha de hash.
- Sem log: 30 seções — 29 do exterior apuradas pelo Sistema de Apuração (sem urna eletrônica: arquivos `busa`/`logsa`, sem `vsc`) e 1 em SP (64777/395/298) cujo `aux.json` oficial lista apenas `bu`, `rdv` e `vota` (log não publicado; BU com hash conferido).
- Assinaturas digitais do `vsc` não foram verificadas (exigem as chaves públicas do TSE); a verificação é de consistência entre hash publicado, `vsc` e arquivos.

| uf | seções esperadas | secoes_processadas | secoes_sem_log | integridade_vsc_ok | integridade_log_ok | integridade_bu_ok |
|---|---|---|---|---|---|---|
| AC | 2.270 | 2.270 | 0 | 2.270 | 2.270 | 2.270 |
| AL | 7.101 | 7.101 | 0 | 7.101 | 7.101 | 7.101 |
| AM | 8.157 | 8.157 | 0 | 8.157 | 8.157 | 8.157 |
| AP | 1.914 | 1.914 | 0 | 1.914 | 1.914 | 1.914 |
| BA | 35.476 | 35.476 | 0 | 35.476 | 35.476 | 35.476 |
| CE | 23.765 | 23.765 | 0 | 23.765 | 23.765 | 23.765 |
| DF | 6.969 | 6.969 | 0 | 6.969 | 6.969 | 6.969 |
| ES | 9.844 | 9.844 | 0 | 9.844 | 9.844 | 9.844 |
| GO | 15.686 | 15.686 | 0 | 15.686 | 15.686 | 15.686 |
| MA | 18.093 | 18.093 | 0 | 18.093 | 18.093 | 18.093 |
| MG | 52.062 | 52.062 | 0 | 52.062 | 52.062 | 52.062 |
| MS | 7.106 | 7.106 | 0 | 7.106 | 7.106 | 7.106 |
| MT | 8.287 | 8.287 | 0 | 8.287 | 8.287 | 8.287 |
| PA | 20.827 | 20.827 | 0 | 20.827 | 20.827 | 20.827 |
| PB | 10.712 | 10.712 | 0 | 10.712 | 10.712 | 10.712 |
| PE | 21.418 | 21.418 | 0 | 21.418 | 21.418 | 21.418 |
| PI | 10.225 | 10.225 | 0 | 10.225 | 10.225 | 10.225 |
| PR | 27.142 | 27.142 | 0 | 27.142 | 27.142 | 27.142 |
| RJ | 37.675 | 37.675 | 0 | 37.675 | 37.675 | 37.675 |
| RN | 8.115 | 8.115 | 0 | 8.115 | 8.115 | 8.115 |
| RO | 4.698 | 4.698 | 0 | 4.698 | 4.698 | 4.698 |
| RR | 1.519 | 1.519 | 0 | 1.519 | 1.519 | 1.519 |
| RS | 27.547 | 27.547 | 0 | 27.547 | 27.547 | 27.547 |
| SC | 17.326 | 17.326 | 0 | 17.326 | 17.326 | 17.326 |
| SE | 5.923 | 5.923 | 0 | 5.923 | 5.923 | 5.923 |
| SP | 103.656 | 103.656 | 1 | 103.656 | 103.655 | 103.656 |
| TO | 4.384 | 4.384 | 0 | 4.384 | 4.384 | 4.384 |
| ZZ | 1.310 | 1.310 | 29 | 1.281 | 1.281 | 1.281 |


## 6–7. Horários: votos após 17h e primeiro/último voto por UF

Brasil (sem exterior, hora de Brasília): 127.854.309 votos no log de 497.896 seções; antes das 8h: 0; após 17h: **34.050** (0.0266%) em 29.609 seções; após 18h: 1.993; após 19h: 11. Parte das seções teve a votação prorrogada até 19h por decisão do STF (liminar às 17h03; orientação às 17h49 de manter abertas até 19h as seções ainda não encerradas).

| uf | secoes_com_log | votos | votos_apos_17h | pct_votos_apos_17h | votos_apos_18h | votos_apos_19h | mediana_primeiro_voto | mediana_ultimo_voto | ultimo_voto_maximo | secoes_com_contingencia |
|---|---|---|---|---|---|---|---|---|---|---|
| AC | 2.270 | 453.654 | 157 | 0,035 | 0 | 0 | 08:02:00 | 16:51:12 | 17:06:31 | 4 |
| AL | 7.101 | 1.951.632 | 640 | 0,033 | 0 | 0 | 08:01:47 | 16:51:12 | 17:59:48 | 30 |
| AM | 8.157 | 2.192.059 | 999 | 0,046 | 0 | 0 | 08:02:18 | 16:52:31 | 17:42:54 | 23 |
| AP | 1.914 | 429.975 | 140 | 0,033 | 0 | 0 | 08:01:58 | 16:51:38 | 17:05:00 | 4 |
| BA | 35.476 | 9.422.033 | 4.167 | 0,044 | 287 | 2 | 08:01:57 | 16:50:56 | 19:01:48 | 207 |
| CE | 23.765 | 6.024.843 | 1.069 | 0,018 | 1 | 0 | 08:01:33 | 16:48:05 | 18:13:09 | 84 |
| DF | 6.969 | 1.868.280 | 976 | 0,052 | 2 | 0 | 08:03:19 | 16:52:14 | 18:28:51 | 15 |
| ES | 9.844 | 2.409.214 | 289 | 0,012 | 0 | 0 | 08:02:08 | 16:47:21 | 17:47:40 | 51 |
| GO | 15.686 | 4.047.280 | 725 | 0,018 | 0 | 0 | 08:01:48 | 16:50:10 | 17:56:26 | 44 |
| MA | 18.093 | 4.127.735 | 915 | 0,022 | 10 | 0 | 08:01:50 | 16:47:12 | 18:49:57 | 78 |
| MG | 52.062 | 13.044.203 | 2.228 | 0,017 | 0 | 0 | 08:01:47 | 16:49:28 | 17:55:23 | 158 |
| MS | 7.106 | 1.594.460 | 419 | 0,026 | 0 | 0 | 08:01:42 | 16:50:50 | 17:16:28 | 19 |
| MT | 8.287 | 2.085.334 | 896 | 0,043 | 1 | 0 | 08:02:04 | 16:52:34 | 18:18:47 | 31 |
| PA | 20.827 | 4.989.573 | 1.299 | 0,026 | 4 | 0 | 08:02:02 | 16:49:39 | 18:53:19 | 65 |
| PB | 10.712 | 2.743.559 | 465 | 0,017 | 41 | 0 | 08:01:32 | 16:47:44 | 18:53:48 | 53 |
| PE | 21.418 | 6.126.467 | 1.625 | 0,027 | 113 | 0 | 08:01:22 | 16:50:20 | 18:55:21 | 83 |
| PI | 10.225 | 2.239.829 | 334 | 0,015 | 1 | 0 | 08:01:56 | 16:46:32 | 18:13:17 | 35 |
| PR | 27.142 | 7.059.339 | 909 | 0,013 | 0 | 0 | 08:01:27 | 16:49:14 | 17:33:36 | 135 |
| RJ | 37.675 | 10.077.449 | 4.126 | 0,041 | 883 | 4 | 08:02:02 | 16:50:44 | 19:01:56 | 185 |
| RN | 8.115 | 2.232.823 | 412 | 0,018 | 2 | 0 | 08:01:39 | 16:48:56 | 18:36:45 | 28 |
| RO | 4.698 | 988.489 | 552 | 0,056 | 0 | 0 | 08:02:06 | 16:52:26 | 17:09:50 | 12 |
| RR | 1.519 | 308.597 | 143 | 0,046 | 0 | 0 | 08:02:08 | 16:52:13 | 17:08:44 | 4 |
| RS | 27.547 | 6.889.636 | 819 | 0,012 | 0 | 0 | 08:01:34 | 16:49:37 | 17:50:07 | 100 |
| SC | 17.326 | 4.762.303 | 454 | 0,010 | 0 | 0 | 08:01:23 | 16:48:48 | 17:22:59 | 92 |
| SE | 5.923 | 1.466.659 | 284 | 0,019 | 7 | 0 | 08:01:34 | 16:49:21 | 18:56:42 | 43 |
| SP | 103.655 | 27.364.121 | 8.787 | 0,032 | 641 | 5 | 08:02:05 | 16:51:24 | 19:06:21 | 382 |
| TO | 4.384 | 954.763 | 221 | 0,023 | 0 | 0 | 08:02:11 | 16:49:19 | 17:11:29 | 4 |
| ZZ | 1.281 | 380.612 | 416 | 0,109 | 0 | 0 | 08:02:32 | 16:54:17 | 17:58:55 | 4 |


Por faixa de 15 minutos: `resultados/2026/votos_por_15min.csv` (Brasil e exterior), `votos_por_15min_uf.csv`, `votos_por_15min_municipio.csv.gz`, `votos_por_15min_zona.csv.gz`; por seção em `dados/processados/temporal/votos_por_15min_secao_2026.parquet` (reproduzível; fora do Git pelo tamanho).


## 5. Biometria (2026, sem exterior)

| turno | log_votantes_biometria | log_votantes_manual_apos_falha | log_votantes_sem_biometria_cadastrada | bu_bin_habilitados_biometria | bu_bin_habilitados_biografia | bu_bin_sem_biometria_cadastrada |
|---|---|---|---|---|---|---|
| 1 | 109.646.855 | 8.342.245 | 6.940.329 | 109.650.927 | 8.342.249 | 6.940.334 |
| 2 | 111.965.700 | 8.632.445 | 7.251.808 | 111.970.333 | 8.632.488 | 7.251.810 |


A série de quatro turnos (2022 e 2026) está em `docs/comparativo-historico.md` (indicadores `pct_hab_biometrica_log`, `pct_hab_manual_apos_falha_log`, `pct_hab_sem_biometria_log`).


## 8–10. Incompatibilidades do 2º turno

Testes executáveis sem o BU em CSV (ainda não publicado nos Dados Abertos): A2o (seção oficial × pacote), B7 (resultado oficial por seção × BU binário: aptos, comparecimento, nominais, brancos, nulos e votos por candidato), B6o (resultado oficial × log), B8 (BU binário por forma de habilitação × log) e K2.

- B7 e A2o: **0 divergências** em — seções — o BU de cada urna reproduz exatamente o resultado oficial por seção, voto a voto por candidato.

| teste | campo | divergencias | explicadas | nao_explicadas | soma_abs_diferencas_nao_explicadas |
|---|---|---|---|---|---|
| A2 | presenca | 2 | 2 | 0 | — |
| A3 | presenca | 43 | 43 | 0 | — |
| B2 | biometria_nh_vs_lib_codigo | 1.308 | 1.308 | 0 | — |
| B5 | abstencoes | 42 | 42 | 0 | — |
| B5 | aptos | 42 | 42 | 0 | — |
| B5 | brancos | 42 | 42 | 0 | — |
| B5 | comparecimento | 42 | 42 | 0 | — |
| B5 | nulos | 42 | 42 | 0 | — |
| B5 | validos | 42 | 42 | 0 | — |
| B6 | biometria_nh_vs_liberacao_manual_no_log | 3 | 0 | 3 | 17 |
| B6 | comparecimento_vs_votos_computados | 6 | 0 | 6 | 54 |
| B6 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | 53 | 48 | 5 | 55 |
| B8 | habilitados_por_biografia_vs_manual_apos_falha | 3 | 0 | 3 | 17 |
| B8 | habilitados_por_biometria | 4.338 | 4.333 | 5 | 36 |
| B8 | sem_biometria_cadastrada | 1 | 0 | 1 | 1 |


Diagnóstico das seções do 2º turno com comparecimento oficial maior que os votos computados no log
(B6o, sem explicação documental), conferido arquivo a arquivo no pacote publicado de cada seção:

| seção | oficial | log | o que o pacote mostra |
|---|---|---|---|
| MA 8893/47/609 | 224 | 188 | Urna substituída por contingência às 10h49–10h51 (1º voto no log: 10h58). A contingência anexa "o log da ME" (`-01.jez`), mas o arquivo anexado é de **outra urna, carregada para a seção 445**: em 25/10 só registra tentativas de inicialização das 10h25 às 10h35 com "GAP erro 72 – dados da mídia de votação não correspondem" e nenhum voto. O log da urna que registrou os 36 primeiros votos da seção 609 não está no pacote. |
| BA 35653/173/235 | 217 | 204 | Contingência às 10h03–10h05 (1º voto no log: 10h12). Arquivos anexados: um da seção 83 (sem votos) e um da seção 235 com votos só de 04/10 (1º turno). 13 votos de 25/10 sem log publicado. |
| RS 89060/17/191 | 92 | 90 | Log original anexado com 15 votos até 9h02 e log da contingência com 75 votos a partir de 10h03; 2 votos sem registro de voto computado. |
| BA 34711/21/178, PB 21750/2/254 | — | −1 | Habilitados = comparecimento oficial; um voto a menos com a mensagem "O voto do eleitor foi computado". |
| PI 11533/3/216 | 259 | 258 | 260 habilitações, 1 votação suspensa e 6 inicializações da urna. |

Em todas, o BU binário (com hash conferido) e o resultado oficial coincidem; a lacuna é de **registro no log**. Nas
três primeiras, o mecanismo é a substituição da urna: o resultado oficial inclui os votos recuperados da memória de
votação, mas o log publicado da urna original está ausente ou é de outra urna/turno. Classificação: **Incompatibilidade
documental pendente** — a confirmação depende da ata da mesa receptora e do relatório de contingência do cartório, não
publicados.


B8 (habilitados por biometria no BU um a mais que no log): a diferença é igual ao número de habilitações em que o log registra a captura da digital e a habilitação sem a mensagem de tipo "[biométrica]"; padrão conferido em cinco seções e aplicado como explicação somente quando a igualdade é exata.


## Quadro de discrepâncias (2º turno)

| categoria | itens | apontamentos | votos |
|---|---|---|---|
| Conferido sem diferença | 20 | 0 | 0 |
| Diferença estatística | 28 | 33 | 0 |
| Diferença explicada | 11 | 5.986 | 0 |
| Incompatibilidade documental pendente | 6 | 23 | 54 |


Votos só são contados quando a diferença é contagem de votos registrados entre duas fontes (B6/B6o); nos demais testes a coluna fica vazia. Detalhe: `resultados/quadro_discrepancias.csv`.


## 11. Comparação com pesquisas independentes

| Verificação | Fonte | Nossa extração | Pesquisa independente | Diferença | Nota |
|---|---|---|---|---|---|
| Seções com log processadas (sem exterior) | CNN/setup.news | 497.896 | 497.895 | 1 | — |
| Seções com log processadas (sem exterior) | Agnoletto | 497.896 | 497.896 | 0 | — |
| Votos após 17h de Brasília (sem exterior) | CNN/setup.news | 34.050 | 34.330 | -280 | CNN não informa fuso nem se 17:00:00 conta; a partir de 17:00:00 = 34330 |
| Votos a partir de 17:00:00 de Brasília (sem exterior) | CNN/setup.news | 34.330 | 34.330 | 0 | mesma definição que reproduz o número da CNN (inclui o segundo 17:00:00) |
| Votos após o encerramento previsto (17h Brasília) | Agnoletto | 34.050 | 31.060 | 2.990 | Agnoletto usa o horário local previsto por seção |
| Votos entre 17h00 e 17h05 | CNN/setup.news | 29.001 | 29.001 | 0 | — |
| Votos após 18h de Brasília | CNN/setup.news | 1.993 | 1.993 | 0 | inclui seções prorrogadas até 19h por decisão do STF |
| Votos após 19h de Brasília | CNN/setup.news | 11 | 11 | 0 | — |
| Seções sem voto após 17h | CNN/setup.news | 468.287 | 468.043 | 244 | — |
| Votos manuais após 17h (seções com modalidade alinhada) | Agnoletto | 2.746 | 2.512 | 234 | 497896 seções com modalidade por voto alinhada |
| Seções com início de encerramento a partir de 18h55 | Agnoletto | 6.864 | 7.577 | -713 | — |
| Mediana da duração do voto (s) | Agnoletto | 11 | 10 | 1 | — |
| % habilitação manual após falha biométrica · UE2013 | Agnoletto | 10,800 | 11 | -0,200 | — |
| % habilitação manual após falha biométrica · UE2015 | Agnoletto | 9,600 | 9,800 | -0,200 | — |
| % habilitação manual após falha biométrica · UE2020 | Agnoletto | 6 | 6,200 | -0,200 | — |
| % habilitação manual após falha biométrica · UE2022 | Agnoletto | 6 | 6,200 | -0,200 | — |
| Arquivos e resultados publicados | kakaroto.dev | — | — | — | não reproduzido: site fora do ar (HTTP 530 em 26–27/10/2026) e sem código público |


Seção a seção com a base de André Agnoletto e explicação das diferenças: `docs/auditoria-estudos-externos.md`.


## Conclusão sobre a pergunta da missão

O 2º turno de 2026 **não apresentou incompatibilidade documental de resultado**: o BU de cada uma das 499.207 seções, com hash conferido, reproduz o resultado oficial por seção (0 divergências), e os votos do log coincidem com o comparecimento oficial em 499.171 das 499.177 seções com log. As pendências documentais são de **registro no log** em 6 seções (54 votos sem registro de voto computado no log publicado, 3 casos ligados a substituição de urna) e de classificação da forma de habilitação (poucas seções), além de 1 seção com log não publicado.

Houve **diferenças estatísticas** em relação a 2022: brancos e nulos para Presidente caíram do 1º para o 2º turno (em 2022 subiram), com concentração em PB, PA, CE e SE; a abstenção caiu mais que em 2022. Não há explicação documental para isso nas tabelas oficiais — são mudanças de comportamento do eleitorado e não indicam, por si, irregularidade. Votos após 17h ficaram no nível de 2022 (0,027% contra 0,033%).

**O que ainda precisa ser investigado:** atas e relatórios de contingência das seções MA 8893/47/609, BA 35653/173/235 e RS 89060/17/191; o log da seção SP 64777/395/298; o BU em CSV do 2º turno (quando publicado) para executar B1–B5 e K1; as 11 + 5 seções pendentes de B8.

