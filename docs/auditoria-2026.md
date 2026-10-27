# Auditoria 2026 — Presidente

_Gerado automaticamente por `scripts/gerar_relatorios.py` em 27/10/2026 05:02 UTC. Todos os números vêm de `resultados/2026/`. Ver método em `docs/metodologia.md`._

## Cobertura dos arquivos de urna (logs e BU binário)

- 1º turno: 28 de 28 pacotes (27 UFs + exterior) processados; 499.207 seções lidas, 0 com falha de leitura, 31 sem log no pacote.

## 1. Totais nacionais reproduzidos a partir das seções

| turno | seções | aptos | comparecimento | abstenções | válidos | brancos | nulos | % abstenção | % brancos | % nulos |
|---|---|---|---|---|---|---|---|---|---|---|
| 1º | 499.206 | 158.745.007 | 125.275.835 | 33.469.172 | 119.306.034 | 2.300.798 | 3.669.003 | 21,084 | 1,837 | 2,929 |
| 2º | 499.207 | 158.745.079 | 128.236.074 | 30.509.005 | 124.082.273 | 1.430.496 | 2.723.305 | 19,219 | 1,115 | 2,124 |


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
| A2 | presenca | BWEB | BUBIN | 499.207 | 1 | 0 | 1 |
| A3 | presenca | DSEC | BWEB | 499.248 | 42 | 42 | 0 |
| B1 | comparecimento_vs_soma_votos | BWEB | BWEB | 499.206 | 0 | 0 | 0 |
| B2 | aptos | BWEB | BUBIN | 499.206 | 0 | 0 | 0 |
| B2 | biometria_nh_vs_lib_codigo | BWEB | BUBIN | 499.206 | 499.206 | 1.309 | 497.897 |
| B2 | brancos | BWEB | BUBIN | 499.206 | 0 | 0 | 0 |
| B2 | comparecimento | BWEB | BUBIN | 499.206 | 0 | 0 | 0 |
| B2 | nulos | BWEB | BUBIN | 499.206 | 0 | 0 | 0 |
| B2 | votos_nominais | BWEB | BUBIN | 499.206 | 0 | 0 | 0 |
| B2 | votos_por_candidato_soma_dif_abs | BWEB | BUBIN | 499.206 | 0 | 0 | 0 |
| B2c | votos_extra_no_bu | BUBIN | BWEB | 499.206 | 0 | 0 | 0 |
| B3 | abstencoes | BWEB | DSEC | 499.206 | 0 | 0 | 0 |
| B3 | aptos | BWEB | DSEC | 499.206 | 0 | 0 | 0 |
| B3 | brancos | BWEB | DSEC | 499.206 | 0 | 0 | 0 |
| B3 | comparecimento | BWEB | DSEC | 499.206 | 0 | 0 | 0 |
| B3 | nulos | BWEB | DSEC | 499.206 | 0 | 0 | 0 |
| B3 | votos_nominais | BWEB | DSEC | 499.206 | 0 | 0 | 0 |
| B4 | votos_candidato_zona | BWEB | CMZ | 62.388 | 2.148 | 2.148 | 0 |
| B5 | abstencoes | BWEB | DMZ | 6.292 | 41 | 41 | 0 |
| B5 | aptos | BWEB | DMZ | 6.292 | 41 | 41 | 0 |
| B5 | brancos | BWEB | DMZ | 6.292 | 41 | 41 | 0 |
| B5 | comparecimento | BWEB | DMZ | 6.292 | 41 | 41 | 0 |
| B5 | nulos | BWEB | DMZ | 6.292 | 2.189 | 2.189 | 0 |
| B5 | validos | BWEB | DMZ | 6.292 | 2.189 | 2.189 | 0 |
| B6 | biometria_nh_vs_liberacao_manual_no_log | BWEB | LOG | 499.176 | 3 | 0 | 3 |
| B6 | comparecimento_vs_votos_computados | BWEB | LOG | 499.176 | 9 | 0 | 9 |
| B6 | comparecimento_vs_votos_presidente_mais_nulos_suspensao | BWEB | LOG | 499.176 | 154 | 148 | 6 |
| C1 | aptos_vs_comp_mais_abst | BWEB | BWEB | 499.206 | 0 | 0 | 0 |
| K1 | votos_votavel | BWEB | VSEC | 3.800.511 | 0 | 0 | 0 |
| K2 | brancos | DSEC | VSEC | 998.414 | 0 | 0 | 0 |
| K2 | nulos | DSEC | VSEC | 998.414 | 0 | 0 | 0 |
| K2 | votos_nominais | DSEC | VSEC | 998.414 | 0 | 0 | 0 |


Legenda: BWEB = BU publicado em CSV; BUBIN = arquivo .bu transmitido pela urna; LOG = log da urna; DSEC = detalhe da apuração por seção; VSEC = votação por seção; CMZ = votação nominal por município/zona; DMZ = detalhe por município/zona. A lista completa, caso a caso, está em `resultados/2026/incompatibilidades.csv`.

### Boletins de Urna, arquivos da urna e tabelas oficiais

**Classificação:** Conferido (com diferenças explicadas e incompatibilidades listadas)

- **O que verificamos?** Se o mesmo número aparece igual em todas as publicações oficiais que deveriam coincidir, seção a seção (BU em CSV, BU binário, detalhe por seção, votação por seção) e na soma por zona.
- **O que os números mostram?** 19 de 32 comparações sem nenhuma divergência; 497.916 divergências ainda sem explicação documental (listadas abaixo).
- **O que significa?** Os votos publicados por seção são os mesmos do arquivo binário assinado gerado pela urna e das demais tabelas do TSE.
- **Existe explicação conhecida?** As divergências explicadas decorrem de seções não instaladas, seções apuradas pelo Sistema de Apuração (cédulas), campos opcionais omitidos no exterior e eleitores de seções não instaladas incluídos nos aptos por zona.
- **O que ainda não sabemos?** A verificação criptográfica das assinaturas dos arquivos (.vscmr) não foi feita nesta etapa.
- **Como conferir?** `resultados/2026/reconciliacao_resumo.csv` e `incompatibilidades.csv`; código `observatorio/reconciliacao.py`.

#### Incompatibilidades documentais ainda não explicadas

| teste | turno | uf | cd_municipio | nr_zona | nr_secao | campo | valor_a | fonte_a | valor_b | fonte_b |
|---|---|---|---|---|---|---|---|---|---|---|
| A2 | 1 | ZZ | 29.564 | 1 | 91 | presenca | — | BWEB | 1 | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 1 | biometria_nh_vs_lib_codigo | 8 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 2 | biometria_nh_vs_lib_codigo | 9 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 3 | biometria_nh_vs_lib_codigo | 13 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 4 | biometria_nh_vs_lib_codigo | 13 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 5 | biometria_nh_vs_lib_codigo | 10 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 6 | biometria_nh_vs_lib_codigo | 3 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 7 | biometria_nh_vs_lib_codigo | 16 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 8 | biometria_nh_vs_lib_codigo | 15 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 9 | biometria_nh_vs_lib_codigo | 8 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 10 | biometria_nh_vs_lib_codigo | 8 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 120 | biometria_nh_vs_lib_codigo | 21 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 136 | biometria_nh_vs_lib_codigo | 11 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 137 | biometria_nh_vs_lib_codigo | 28 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 163 | biometria_nh_vs_lib_codigo | 4 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 186 | biometria_nh_vs_lib_codigo | 12 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 192 | biometria_nh_vs_lib_codigo | 23 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 200 | biometria_nh_vs_lib_codigo | 3 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 201 | biometria_nh_vs_lib_codigo | 7 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 202 | biometria_nh_vs_lib_codigo | 11 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 208 | biometria_nh_vs_lib_codigo | 8 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 212 | biometria_nh_vs_lib_codigo | 11 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 237 | biometria_nh_vs_lib_codigo | 8 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 242 | biometria_nh_vs_lib_codigo | 9 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 252 | biometria_nh_vs_lib_codigo | 9 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 304 | biometria_nh_vs_lib_codigo | 13 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 305 | biometria_nh_vs_lib_codigo | 4 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 310 | biometria_nh_vs_lib_codigo | 14 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 411 | biometria_nh_vs_lib_codigo | 5 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 412 | biometria_nh_vs_lib_codigo | 9 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 413 | biometria_nh_vs_lib_codigo | 7 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 419 | biometria_nh_vs_lib_codigo | 4 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 436 | biometria_nh_vs_lib_codigo | 12 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 437 | biometria_nh_vs_lib_codigo | 24 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 439 | biometria_nh_vs_lib_codigo | 12 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 440 | biometria_nh_vs_lib_codigo | 7 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 441 | biometria_nh_vs_lib_codigo | 15 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 442 | biometria_nh_vs_lib_codigo | 6 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 475 | biometria_nh_vs_lib_codigo | 14 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 476 | biometria_nh_vs_lib_codigo | 17 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 477 | biometria_nh_vs_lib_codigo | 7 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.007 | 9 | 479 | biometria_nh_vs_lib_codigo | 4 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 65 | biometria_nh_vs_lib_codigo | 20 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 66 | biometria_nh_vs_lib_codigo | 8 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 67 | biometria_nh_vs_lib_codigo | 18 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 68 | biometria_nh_vs_lib_codigo | 5 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 69 | biometria_nh_vs_lib_codigo | 10 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 70 | biometria_nh_vs_lib_codigo | 10 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 71 | biometria_nh_vs_lib_codigo | 9 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 72 | biometria_nh_vs_lib_codigo | 17 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 73 | biometria_nh_vs_lib_codigo | 12 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 74 | biometria_nh_vs_lib_codigo | 8 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 75 | biometria_nh_vs_lib_codigo | 13 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 77 | biometria_nh_vs_lib_codigo | 8 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 78 | biometria_nh_vs_lib_codigo | 12 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 79 | biometria_nh_vs_lib_codigo | 15 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 80 | biometria_nh_vs_lib_codigo | 9 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 81 | biometria_nh_vs_lib_codigo | 11 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 82 | biometria_nh_vs_lib_codigo | 6 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 87 | biometria_nh_vs_lib_codigo | 12 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 88 | biometria_nh_vs_lib_codigo | 13 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 89 | biometria_nh_vs_lib_codigo | 6 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 90 | biometria_nh_vs_lib_codigo | 10 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 91 | biometria_nh_vs_lib_codigo | 14 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 92 | biometria_nh_vs_lib_codigo | 9 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 93 | biometria_nh_vs_lib_codigo | 18 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 94 | biometria_nh_vs_lib_codigo | 5 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 95 | biometria_nh_vs_lib_codigo | 14 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 101 | biometria_nh_vs_lib_codigo | 4 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 102 | biometria_nh_vs_lib_codigo | 7 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 103 | biometria_nh_vs_lib_codigo | 14 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 105 | biometria_nh_vs_lib_codigo | 8 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 106 | biometria_nh_vs_lib_codigo | 10 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 107 | biometria_nh_vs_lib_codigo | 16 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 109 | biometria_nh_vs_lib_codigo | 8 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.015 | 2 | 111 | biometria_nh_vs_lib_codigo | 19 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 576 | biometria_nh_vs_lib_codigo | 17 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 577 | biometria_nh_vs_lib_codigo | 11 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 578 | biometria_nh_vs_lib_codigo | 9 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 579 | biometria_nh_vs_lib_codigo | 9 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 580 | biometria_nh_vs_lib_codigo | 9 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 581 | biometria_nh_vs_lib_codigo | 8 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 582 | biometria_nh_vs_lib_codigo | 9 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 583 | biometria_nh_vs_lib_codigo | 24 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 584 | biometria_nh_vs_lib_codigo | 7 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 585 | biometria_nh_vs_lib_codigo | 9 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 586 | biometria_nh_vs_lib_codigo | 5 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 587 | biometria_nh_vs_lib_codigo | 6 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 588 | biometria_nh_vs_lib_codigo | 13 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 589 | biometria_nh_vs_lib_codigo | 12 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 590 | biometria_nh_vs_lib_codigo | 11 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 591 | biometria_nh_vs_lib_codigo | 11 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 592 | biometria_nh_vs_lib_codigo | 5 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 593 | biometria_nh_vs_lib_codigo | 11 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 594 | biometria_nh_vs_lib_codigo | 4 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 595 | biometria_nh_vs_lib_codigo | 8 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 596 | biometria_nh_vs_lib_codigo | 19 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 597 | biometria_nh_vs_lib_codigo | 5 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 598 | biometria_nh_vs_lib_codigo | 11 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 599 | biometria_nh_vs_lib_codigo | 9 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 600 | biometria_nh_vs_lib_codigo | 9 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 601 | biometria_nh_vs_lib_codigo | 7 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 602 | biometria_nh_vs_lib_codigo | 4 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 603 | biometria_nh_vs_lib_codigo | 3 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 604 | biometria_nh_vs_lib_codigo | 10 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 605 | biometria_nh_vs_lib_codigo | 9 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 606 | biometria_nh_vs_lib_codigo | 4 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 607 | biometria_nh_vs_lib_codigo | 7 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 608 | biometria_nh_vs_lib_codigo | 2 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 609 | biometria_nh_vs_lib_codigo | 11 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 610 | biometria_nh_vs_lib_codigo | 8 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 611 | biometria_nh_vs_lib_codigo | 11 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 612 | biometria_nh_vs_lib_codigo | 6 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 613 | biometria_nh_vs_lib_codigo | 13 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 614 | biometria_nh_vs_lib_codigo | 16 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 615 | biometria_nh_vs_lib_codigo | 11 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 616 | biometria_nh_vs_lib_codigo | 13 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 617 | biometria_nh_vs_lib_codigo | 15 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 618 | biometria_nh_vs_lib_codigo | 4 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 619 | biometria_nh_vs_lib_codigo | 16 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 620 | biometria_nh_vs_lib_codigo | 9 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 621 | biometria_nh_vs_lib_codigo | 11 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 622 | biometria_nh_vs_lib_codigo | 3 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 623 | biometria_nh_vs_lib_codigo | 8 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 624 | biometria_nh_vs_lib_codigo | 12 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 625 | biometria_nh_vs_lib_codigo | 6 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 626 | biometria_nh_vs_lib_codigo | 10 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 627 | biometria_nh_vs_lib_codigo | 10 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 628 | biometria_nh_vs_lib_codigo | 9 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 629 | biometria_nh_vs_lib_codigo | 7 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 630 | biometria_nh_vs_lib_codigo | 14 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 631 | biometria_nh_vs_lib_codigo | 9 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 797 | biometria_nh_vs_lib_codigo | 21 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 799 | biometria_nh_vs_lib_codigo | 7 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 851 | biometria_nh_vs_lib_codigo | 22 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.023 | 1 | 853 | biometria_nh_vs_lib_codigo | 8 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.031 | 3 | 58 | biometria_nh_vs_lib_codigo | 20 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.031 | 3 | 60 | biometria_nh_vs_lib_codigo | 10 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.031 | 3 | 65 | biometria_nh_vs_lib_codigo | 5 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.031 | 3 | 72 | biometria_nh_vs_lib_codigo | 13 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.031 | 3 | 76 | biometria_nh_vs_lib_codigo | 13 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.031 | 3 | 77 | biometria_nh_vs_lib_codigo | 3 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.031 | 3 | 87 | biometria_nh_vs_lib_codigo | 1 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.031 | 3 | 88 | biometria_nh_vs_lib_codigo | 12 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.031 | 3 | 95 | biometria_nh_vs_lib_codigo | 7 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.031 | 3 | 96 | biometria_nh_vs_lib_codigo | 7 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.031 | 3 | 122 | biometria_nh_vs_lib_codigo | 2 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.031 | 3 | 125 | biometria_nh_vs_lib_codigo | 2 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.031 | 3 | 152 | biometria_nh_vs_lib_codigo | 6 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.031 | 3 | 157 | biometria_nh_vs_lib_codigo | 11 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.031 | 3 | 170 | biometria_nh_vs_lib_codigo | 5 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.031 | 3 | 172 | biometria_nh_vs_lib_codigo | 1 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 73 | biometria_nh_vs_lib_codigo | 13 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 74 | biometria_nh_vs_lib_codigo | 11 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 75 | biometria_nh_vs_lib_codigo | 6 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 76 | biometria_nh_vs_lib_codigo | 5 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 114 | biometria_nh_vs_lib_codigo | 4 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 140 | biometria_nh_vs_lib_codigo | 3 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 141 | biometria_nh_vs_lib_codigo | 3 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 142 | biometria_nh_vs_lib_codigo | 3 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 143 | biometria_nh_vs_lib_codigo | 13 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 160 | biometria_nh_vs_lib_codigo | 8 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 161 | biometria_nh_vs_lib_codigo | 7 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 162 | biometria_nh_vs_lib_codigo | 5 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 163 | biometria_nh_vs_lib_codigo | 20 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 182 | biometria_nh_vs_lib_codigo | 11 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 196 | biometria_nh_vs_lib_codigo | 2 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 201 | biometria_nh_vs_lib_codigo | 12 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 203 | biometria_nh_vs_lib_codigo | 6 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 223 | biometria_nh_vs_lib_codigo | 23 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 230 | biometria_nh_vs_lib_codigo | 16 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 236 | biometria_nh_vs_lib_codigo | 10 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 237 | biometria_nh_vs_lib_codigo | 6 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 251 | biometria_nh_vs_lib_codigo | 5 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 279 | biometria_nh_vs_lib_codigo | 8 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 284 | biometria_nh_vs_lib_codigo | 2 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 294 | biometria_nh_vs_lib_codigo | 1 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 318 | biometria_nh_vs_lib_codigo | 8 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 324 | biometria_nh_vs_lib_codigo | 0 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 326 | biometria_nh_vs_lib_codigo | 10 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 327 | biometria_nh_vs_lib_codigo | 4 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 331 | biometria_nh_vs_lib_codigo | 6 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 337 | biometria_nh_vs_lib_codigo | 4 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 347 | biometria_nh_vs_lib_codigo | 6 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 359 | biometria_nh_vs_lib_codigo | 3 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 375 | biometria_nh_vs_lib_codigo | 7 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 384 | biometria_nh_vs_lib_codigo | 4 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 389 | biometria_nh_vs_lib_codigo | 1 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 424 | biometria_nh_vs_lib_codigo | 3 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 434 | biometria_nh_vs_lib_codigo | 7 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 435 | biometria_nh_vs_lib_codigo | 3 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 441 | biometria_nh_vs_lib_codigo | 15 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 443 | biometria_nh_vs_lib_codigo | 6 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 444 | biometria_nh_vs_lib_codigo | 8 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 456 | biometria_nh_vs_lib_codigo | 3 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 461 | biometria_nh_vs_lib_codigo | 8 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 463 | biometria_nh_vs_lib_codigo | 7 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 504 | biometria_nh_vs_lib_codigo | 7 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.040 | 4 | 506 | biometria_nh_vs_lib_codigo | 1 | BWEB | — | BUBIN |
| B2 | 1 | AC | 1.058 | 6 | 1 | biometria_nh_vs_lib_codigo | 9 | BWEB | — | BUBIN |


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

### Validação dos fusos horários

**Classificação:** Pendente

- **O que verificamos?** Se o fuso legal atribuído a cada município é coerente com o horário local do primeiro voto.
- **O que os números mostram?** 5.571 combinações município×turno avaliadas; 3 divergentes.
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

## 5. Modelos de urna (Teste I)

| turno | controle | indicador | diferenca_ingenua_pp | diferenca_controlada_pp | ic95_inf | ic95_sup | grupos_comparaveis | secoes_ref | secoes_outras |
|---|---|---|---|---|---|---|---|---|---|
| 1 | mesmo_local | pct_validos_22 | 0,489 | -0,016 | -0,114 | 0,088 | 5.243 | 22.416 | 21.726 |
| 1 | mesmo_local | pct_validos_13 | -0,284 | 0,027 | -0,069 | 0,119 | 5.243 | 22.416 | 21.726 |
| 1 | mesmo_local | pct_comparecimento | -0,172 | 0,120 | 0,019 | 0,214 | 5.243 | 22.416 | 21.726 |
| 1 | mesmo_local | pct_brancos_nulos | 0,012 | 0,012 | -0,024 | 0,052 | 5.243 | 22.416 | 21.726 |
| 1 | mesmo_local | pct_biometria_nh | -1,213 | -0,026 | -0,086 | 0,034 | 5.243 | 22.416 | 21.726 |
| 1 | mesma_zona | pct_validos_22 | 0,489 | -0,055 | -0,386 | 0,284 | 1.048 | 63.329 | 84.411 |
| 1 | mesma_zona | pct_validos_13 | -0,284 | -0,023 | -0,391 | 0,333 | 1.048 | 63.329 | 84.411 |
| 1 | mesma_zona | pct_comparecimento | -0,172 | 0,080 | -0,071 | 0,217 | 1.048 | 63.329 | 84.411 |
| 1 | mesma_zona | pct_brancos_nulos | 0,012 | 0,014 | -0,047 | 0,076 | 1.048 | 63.329 | 84.411 |
| 1 | mesma_zona | pct_biometria_nh | -1,213 | -0,821 | -0,927 | -0,714 | 1.048 | 63.329 | 84.411 |
| 1 | mesmo_municipio | pct_validos_22 | 0,489 | 0,266 | -0,346 | 0,969 | 879 | 76.226 | 110.528 |
| 1 | mesmo_municipio | pct_validos_13 | -0,284 | -0,312 | -0,982 | 0,345 | 879 | 76.226 | 110.528 |
| 1 | mesmo_municipio | pct_comparecimento | -0,172 | 0,146 | -0,057 | 0,306 | 879 | 76.226 | 110.528 |
| 1 | mesmo_municipio | pct_brancos_nulos | 0,012 | -0,042 | -0,130 | 0,056 | 879 | 76.226 | 110.528 |
| 1 | mesmo_municipio | pct_biometria_nh | -1,213 | -1,068 | -1,547 | -0,660 | 879 | 76.226 | 110.528 |

### UE2020 × demais modelos: proporção de votos do nº 22

**Classificação:** Diferença estatística (controles fracos) / Conferido sem diferença (mesmo local)

- **O que verificamos?** Se seções com urna modelo 2020 têm resultado diferente de seções com outros modelos, comparando seções próximas (mesmo local de votação, mesma zona, mesmo município).
- **O que os números mostram?** Sem controle geográfico a diferença é grande (1º t.: 0,49 p.p.). No mesmo local: 1º t. -0,02 p.p. (IC95% -0,11 a 0,09). Na mesma zona: 1º t. -0,06 p.p. (IC95% -0,39 a 0,28).
- **O que significa?** A maior parte da diferença bruta é geográfica. No controle mais forte (mesmo local) o intervalo inclui zero; com controles mais fracos (zona, município) resta diferença de cerca de 1 p.p., que pode refletir diferenças entre bairros/locais dentro da zona.
- **Existe explicação conhecida?** A distribuição dos modelos não é aleatória (logística do TSE por zona/local). O modelo 2020 tem leitor biométrico mais novo: a taxa de liberação manual é ~5 p.p. menor nas mesmas localidades, diferença técnica esperada.
- **O que ainda não sabemos?** Sem covariáveis anteriores à eleição por seção (ex.: resultado de 2018 na mesma seção), não é possível separar efeito do modelo de efeito de localização. Diferença estatística ≠ causalidade.
- **Como conferir?** `resultados/2026/modelos_efeito_controlado.csv`, `modelos_medias_ingenuas.csv`; gráfico `resultados/2026/graficos/modelos_efeito_22.png`.

