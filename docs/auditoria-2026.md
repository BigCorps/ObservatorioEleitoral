# Auditoria 2026 — Presidente

_Gerado automaticamente por `scripts/gerar_relatorios.py` em 27/10/2026 00:32 UTC. Todos os números vêm de `resultados/2026/`. Ver método em `docs/metodologia.md`._

## Cobertura dos arquivos de urna (logs e BU binário)

Nenhum pacote de arquivos de urna processado.

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
| A3 | presenca | DSEC | BWEB | 499.248 | 42 | 42 | 0 |
| B1 | comparecimento_vs_soma_votos | BWEB | BWEB | 499.206 | 0 | 0 | 0 |
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
| C1 | aptos_vs_comp_mais_abst | BWEB | BWEB | 499.206 | 0 | 0 | 0 |
| K1 | votos_votavel | BWEB | VSEC | 3.800.511 | 0 | 0 | 0 |
| K2 | brancos | DSEC | VSEC | 998.414 | 0 | 0 | 0 |
| K2 | nulos | DSEC | VSEC | 998.414 | 0 | 0 | 0 |
| K2 | votos_nominais | DSEC | VSEC | 998.414 | 0 | 0 | 0 |


Legenda: BWEB = BU publicado em CSV; BUBIN = arquivo .bu transmitido pela urna; LOG = log da urna; DSEC = detalhe da apuração por seção; VSEC = votação por seção; CMZ = votação nominal por município/zona; DMZ = detalhe por município/zona. A lista completa, caso a caso, está em `resultados/2026/incompatibilidades.csv`.

### Boletins de Urna, arquivos da urna e tabelas oficiais

**Classificação:** Conferido (com diferenças explicadas e incompatibilidades listadas)

- **O que verificamos?** Se o mesmo número aparece igual em todas as publicações oficiais que deveriam coincidir, seção a seção (BU em CSV, BU binário, detalhe por seção, votação por seção) e na soma por zona.
- **O que os números mostram?** 12 de 20 comparações sem nenhuma divergência; 0 divergências ainda sem explicação documental (listadas abaixo).
- **O que significa?** Os votos publicados por seção são os mesmos do arquivo binário assinado gerado pela urna e das demais tabelas do TSE.
- **Existe explicação conhecida?** As divergências explicadas decorrem de seções não instaladas, seções apuradas pelo Sistema de Apuração (cédulas), campos opcionais omitidos no exterior e eleitores de seções não instaladas incluídos nos aptos por zona.
- **O que ainda não sabemos?** A verificação criptográfica das assinaturas dos arquivos (.vscmr) não foi feita nesta etapa.
- **Como conferir?** `resultados/2026/reconciliacao_resumo.csv` e `incompatibilidades.csv`; código `observatorio/reconciliacao.py`.

