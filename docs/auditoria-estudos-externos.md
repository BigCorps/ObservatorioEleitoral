# Revisão de projetos externos: auditorias das eleições de 2022 (dados abertos do TSE)

Revisão factual de três projetos públicos de terceiros, feita para apoiar uma auditoria independente, neutra e reprodutível. **Não adotamos as conclusões deles.** Separamos sempre:

- **[ALEGAM]**: o que o projeto afirma (texto, número ou rótulo publicado por ele).
- **[VERIFICADO]**: o que esta revisão conferiu diretamente (HTTP, código-fonte, arquivos de dados publicados, consistência interna). Nenhum número foi recalculado a partir dos arquivos brutos do TSE. "Verificado" quer dizer "confere no material publicado por eles" e não "confere com o TSE".
- **[OBSERVAÇÃO]**: problema de método ou inconsistência que identificamos.

Acesso: 26/10/2026, 23:12 a 23:30 UTC, via `curl` através do proxy de saída deste ambiente. Nenhum código dos projetos foi executado. O repositório foi apenas clonado e lido, e os Parquet que ele distribui foram consultados com DuckDB (leitura de dados).

Arquivos brutos baixados nesta revisão: `(arquivos brutos não versionados; reobteníveis pelas URLs abaixo)` (HTML, JS e JSON dos sites) e `(clone local, commit 12f0433)` (clone).

> **Natureza deste documento.** Revisão documental dos três projetos indicados na missão
> (seção 7). Tudo marcado [ALEGAM] é afirmação dos autores, **não** cálculo nosso. A
> comparação com os nossos próprios cálculos, feitos a partir dos arquivos do TSE, está na
> seção final "Reprodução independente", gerada por `scripts/gerar_relatorios.py`.

---

## Contexto normativo usado como régua

- Em 2022 a votação foi das 8h às 17h **de Brasília** no país inteiro. A urna grava **hora local** no log. No Acre (UTC-5) a janela aparece como 6h–15h; em AM, MT, MS, RO e RR (UTC-4), como 7h–16h. Alguns municípios do oeste do Amazonas seguem UTC-5, e Fernando de Noronha (PE) segue UTC-2.
- Voto depois das 17h é legal para o eleitor que já estava na fila. Voto depois de 17h **não** é, por si só, anomalia.
- O log do 2º turno de 2022 **acumula** os eventos do 1º turno da mesma urna. É preciso filtrar pela data.
- Benford (1º dígito) em votos por seção é um teste fraco ou inadequado, porque o tamanho das seções é limitado. O 2º dígito e o último dígito também sofrem efeitos de números pequenos.

---

# 1. https://auditoriaeleicoes.com/relatorio/

## 1.1 Acessibilidade e autoria [VERIFICADO]

| Item | Resultado |
|---|---|
| HTTP | `200` (nginx/1.24.0 Ubuntu), 11.749 bytes, `last-modified: Sun, 25 Oct 2026 14:41:10 GMT` |
| Data de acesso | 26/10/2026 23:12 UTC |
| Precisa de JS? | **Sim.** O HTML é uma casca. O conteúdo vem de `app.js?v=16` (vanilla) + `vendor/plotly.min.js` e de `data/*.json`. Sem JS, só aparecem títulos de seção e a metodologia resumida. |
| Banner "Dados de demonstração" | Está no HTML estático. O JS o esconde quando `summary.json` traz o campo `gerado`, que hoje vale `2026-10-10T07:52:30`. Com JS, portanto, o banner não aparece; sem JS, ele aparece e engana. |
| Eleição padrão | Seletor com `2022_1t`, `2022_2t` e `2026_1t` (selecionado por padrão). `summary.json` também tem `2024_1t` e `2024_2t`. |
| Autoria | Rodapé: "Análise gerada com inteligência agentica da UPX AI Cybersecurity" / "Bruno Prado". Não há outra identificação. |
| Código | **Não publicado.** O texto diz "scripts em Python (pandas) listados no rodapé", mas não há nenhum link para scripts no HTML nem no JS. |
| Resultados | Publicados como JSON agregados (todos HTTP 200): `summary.json` (315 KB), `comparecimento_share.json`, `pos17.json`, `fila.json`, `ritmo.json`, `abstencao.json`, `mesario.json`, `casos.json`, `resumo_2022_2t.json`, `pareado_irmas.json`, `painel_inventario.json`, `tentativas_uf.csv` etc. Por seção: `data/secoes/2022_2t_<UF>.json` e `2026_1t_<UF>.json` (`2022_1t_AC.json` → 404). Arquivo citado e ausente: `1f_padroes2.json` → 404. |

## 1.2 Fontes de dados [ALEGAM, parcialmente VERIFICADO]

- **[ALEGAM]** "Baixamos 100% dos arquivos públicos de urna do TSE": BU, log, RDV e "dados de transmissão", de dadosabertos.tse.jus.br e resultados.tse.jus.br.
- **[VERIFICADO]** `summary.json.fontes.zips` lista ZIPs com tamanho (GB) e SHA-256, no padrão `bu_imgbu_logjez_rdv_vscmr_2022_{1t,2t}_<UF>.zip`. É o mesmo pacote que o DataUrnas-BR documenta em `https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2022/arqurnatot/bu_imgbu_logjez_rdv_vscmr_2022_<turno>t_<UF>.zip`.
- Universo declarado para 2022 (`summary.json`):
  - **1T**: 471.853 seções, 123.639.727 votos (BU), 156.351.448 aptos, 28 "UFs" (27 + ZZ), 95.958.570 habilitações no log.
  - **2T**: 471.983 seções, 124.248.306 votos, 96.513.389 habilitações no log.
- **[OBSERVAÇÃO] Cobertura dos logs em 2022 exclui SP nos dois turnos.** As métricas de log usam 370.662 urnas no 1T e 370.820 no 2T (`estados`, `pos17`, `mesario`, `ritmo`), sem SP, enquanto as métricas de BU incluem SP. Eles atribuem isso a "SP sem log de 2022-2T no ZIP do TSE" e declaram "pendente SP 2022-1T". **[VERIFICADO no DataUrnas-BR]**: a base do DataUrnas tem logs de SP nos dois turnos (1T: 99.526 de 101.071 seções com `votos_log>0`), obtidos pela API de resultados. Os logs de SP existiram publicamente. Não conferimos se o ZIP atual do CDN os contém.

## 1.3 Testes e análises (todos os que se aplicam a 2022)

A página define 14 "teses" (array `TESES` em `app.js`), uma seção "Forense", uma "Linha do tempo", "Casos" e uma longa "Contraprova" (itens 1–15). O número "14 testes / 0 com evidência de manipulação" do topo é **constante no código** (`const nTestes = 14` e o texto literal `"${nTestes} / 0"`). Não é calculado. **[VERIFICADO]**

Para cada teste: pergunta, método e regras, insumo, números [ALEGAM] e interpretação deles [ALEGAM], seguidos das nossas observações.

### A1. "Urnas votaram antes das 8h"
- **Método**: contar habilitações (votos) com horário BRT < 08:00. A conversão BRT é por UF: AC +2h; AM, RR, RO, MT e MS +1h. A janela vai de 00:00 do dia até 06:00 do dia seguinte. Insumo: log (`logd.dat`). Também há um histograma da hora (BRT) do primeiro voto por seção.
- **Números [ALEGAM]**: 1T **8.185 votos** antes das 8h; 484 seções com primeiro voto às 7h BRT. 2T **19.408 votos**; 487 seções às 7h.
- **Interpretação [ALEGAM]**, texto fixo: "Nenhuma seção abriu antes do horário legal". O veredito é dinâmico ("Para olhar individualmente" quando o valor não é 0).
- **[OBSERVAÇÃO] Artefato de fuso.** Pelo `summary.json.estados`, 100% desses votos estão no **AM** (1T: 8.207; 2T: 19.408). Isso é compatível com os municípios do oeste do AM em UTC-5 (votação 6h–15h local) convertidos com +1h em vez de +2h. O texto fixo contradiz o número exibido.

### A2. "Votos em rajada = mesário votando"
- **Método**: sequências de ≥5 votos consecutivos, todos com intervalo < limite entre habilitações. O limite é 20 s com 5 cargos (1T) e **6 s** com 1 cargo (2T e exterior). Na contraprova há uma sensibilidade com 20 s/≥3, 30 s/≥3 e 30 s/≥5. Insumo: log.
- **Números [ALEGAM]**:
  - 1T: 1.504 sequências, **10.184 votos**, 319 urnas, `pct_votos` = 8,2×10⁻⁵ (sobre 123,6 M). Margem 6.182.336.
  - 2T: 777 sequências, **4.296 votos**, 589 urnas. Margem 2.139.667.
  - Sensibilidade 1T (sobre 95,96 M votos de log): 30 s/≥3 = 87.939 votos (0,092%), 30 s/≥5 = 18.398, 20 s/≥3 = 24.318.
  - Sensibilidade 2T: 30 s/≥3 = 7.398.580 votos (7,7%, "ritmo normal do 2T").
  - No `resumo_2022_2t.json` há outra definição, "≥10 votos com gap < 20 s em 10 min": 0 rajadas.
- **Interpretação [ALEGAM]**: "Explicado": fila grande e eleitores rápidos; o tempo de habilitação continua normal.
- **[OBSERVAÇÃO]**:
  - A "escala" exibe `pct_votos` (fração dos votos) com o rótulo "% da margem" e sem ×100. O rótulo e a escala estão errados.
  - Os denominadores mudam entre arquivos (123,6 M em um, 95,96 M sem SP em outro).
  - Há três definições diferentes de "rajada" no mesmo site.

### A3. "Urna totalizada antes de fechar"
- **Método declarado**: horário de totalização do BU anterior ao encerramento. O campo usado no código é `integridade.t_hab_gt_t_comp`, que pelo nome é "hora da habilitação > hora do cômputo". O nome do campo não corresponde à descrição.
- **Números [ALEGAM]**: 0 (1T e 2T). `ordem_dup` = 0.
- **[OBSERVAÇÃO]**: a métrica realmente calculada é ambígua. Sem código, não dá para saber.

### A4. "Modelo UE2020 favoreceu um candidato"
- **Método**: share 13/22 por modelo de urna (modelo extraído do log ou do vscmr), bruto e "ajustado pela média do município" (desvio da seção em relação à média municipal, agregado por modelo). Há ainda um bootstrap (2.000 réplicas, reamostrando municípios) da diferença de share 22 entre UE2020 e os demais, restrito aos municípios com os dois tipos.
- **Números [ALEGAM]**:
  - 1T bruto: UE2020 share22 = 44,61% contra 40,8–43,5% nos outros modelos.
  - 1T ajustado: entre −0,28 e +0,12 p.p.
  - 1T bootstrap: **+1,00 p.p., IC95 [0,59; 1,58]**, 310 municípios.
  - 2T bootstrap: **+1,17 p.p., IC95 [0,72; 1,80]**, 311 municípios.
- **Interpretação [ALEGAM]**: "Não encontrado": "a tese morre no ajuste geográfico".
- **[OBSERVAÇÃO]**: o veredito "Não encontrado" é fixo no código. O próprio bootstrap publicado dá IC95 que **exclui zero** nos dois turnos, e o site não discute isso. A amostra de 310 municípios é seletiva (apenas os que têm UE2020 e outros modelos).

### A5. "Benford prova fraude" (2º dígito)
- **Método**: 2º dígito dos votos por seção de cada candidato (13 e 22) contra Benford-2. A medida é o MAD, comparado a uma faixa nula simulada por binomial com o share real do município e os mesmos tamanhos de seção. A nota diz que o 1º dígito "sempre falha" e não é usado.
- **Números [ALEGAM]**:

  | Turno | Candidato | MAD real | Faixa nula (p05–p95) | p empírico | n seções |
  |---|---|---|---|---|---|
  | 1T | 13 | 0,0104 | 0,0147–0,0150 | 1,0 | 471.714 |
  | 1T | 22 | 0,0118 | 0,0135–0,0139 | 1,0 | 467.258 |
  | 2T | 13 | 0,0103 | 0,0118–0,0121 | 1,0 | — |
  | 2T | 22 | 0,0065 | 0,0086–0,0089 | 1,0 | — |

- **Interpretação [ALEGAM]**: "desvio dentro da faixa do acaso".
- **[OBSERVAÇÃO]**: o MAD real fica **abaixo** de toda a faixa nula, não dentro dela. Isso indica que o nulo binomial está mal especificado. De qualquer forma, o teste não discrimina fraude. Benford em contagens por seção é teste fraco.

### A6. "Seções com 100% para um candidato"
- **Método**: seções em que um candidato tem 100% dos votos válidos (BU).
- **Números [ALEGAM]**: 1T **18**; 2T **29** (`bu.secoes_100pct_cand`). O "painel independente" listava 55 (1T) e 132 (2T), com outro critério (nominais).
- **[OBSERVAÇÃO]**: o texto fixo diz "não ocorreu nos dados auditados", mas o número exibido é 18 ou 29. O texto contradiz o dado.

### A7. "Mesário operou várias seções"
- **Método**: identificador do mesário (título, quando o log o registra) aparecendo em mais de uma seção no mesmo dia.
- **Números [ALEGAM]**: 1T **66**; 2T **43** títulos. `total_mesarios` = null.
- **[ALEGAM]**: "Em 2022-1T o log não nomeia o mesário na liberação manual; os testes por mesário só existem para 2026."
- **[OBSERVAÇÃO]**: sem denominador. A cobertura de 2022 é parcial e não documentada.

### A8. "Eleitor 'já votou' é voto roubado"
- **Método**: linhas do tipo "O eleitor identificado já votou" e verificação de se houve voto computado depois.
- **Números [ALEGAM]**: nacional 2022 = **0 tentativas, 0 computadas** (1T e 2T).
- **[OBSERVAÇÃO] Inconsistência interna.** A soma por UF em `summary.json.estados` dá **107.934** tentativas (1T) e **187.884** (2T); só o AC, por exemplo, tem 826. O adendo diz que "em 2022 a mesma linha existe (AL 1T: 68 em 80,5 mil votos)". Ainda assim, o texto do card afirma que "toda tentativa marcada 'já votou' foi recusada". O total nacional parece ser bug de agregação.

### A9. "Urnas fecharam de madrugada" (hora do último voto)
- **Método**: histograma da hora BRT do último voto por seção.
- **Números [ALEGAM]**:
  - 1T, último voto por hora: 15h 854; 16h 191.601; 17h 136.463; 18h 30.890; 19h 8.121; 20h 1.953; **21h 457**; 22h 104; 23h 40. Mais `apos_meia_noite` = 241. Último voto mais tarde: PI mun 10766 z15 s79, 03/10 03:07:05.
  - 2T: 15h 1.545; 16h 342.760; 17h 26.249; 18h 17; 19h 2. Último: MG 45551 z120 s99, 19:22:42.
- **Interpretação [ALEGAM]**: "Explicado": fila, contingência, zona rural.
- **[OBSERVAÇÃO]**:
  - Três "casos" de 2022-1T mostram último voto às 23:59:xx com encerramento às 00:40–01:53 e log < BU (331 vs 367; 371 vs 414; 225 vs 243). Isso sugere corte à meia-noite no cálculo por seção, contrariando a janela até 06:00 declarada.
  - O texto do caso diz "Log e boletim batem" mesmo quando não batem (template fixo).

### A10. "Comparecimento maior que aptos"
- **Números [ALEGAM]**: 0 (1T e 2T). Há também `comp_100` (comparecimento = 100% dos aptos): 9 no 1T e 4 no 2T.

### A11. "BU não bate com a apuração"
- **Método declarado**: soma de votos do BU ≠ comparecimento declarado (consistência interna).
- **Números [ALEGAM]**: 0 inconsistentes.
- Para 2026 há também a comparação entre a soma dos BUs e o resultado oficial por UF (fora do escopo de 2022).
- **[VERIFICADO]**, somas deles para 2022-2T: 13 = 60.343.850 e 22 = 58.204.183; margem 2.139.667. Eles próprios dizem que o oficial é 2.139.645 (22 votos de diferença, atribuídos a seções ausentes).

### A12. "Apuração rápida demais"
- **Números**: `transmissao` = null em 2022 (1T e 2T). **Não há dados para 2022.**

### A13. "Votos ultrarrápidos"
- **Método**: duração entre habilitação e confirmação, com percentuais < 40 s e < 20 s, mediana e percentis por hora e por tipo de habilitação.
- **Números [ALEGAM]**:
  - 1T: mediana 52 s (p10 34, p90 106); <40 s **22,08%**; <20 s **0,37%**; >300 s 0,54%; mediana da habilitação 15 s. Habilitação: biometria 75,5%, sem biometria 14,1%, manual 8,96%. Mediana do voto: 51 s (bio) e 66 s (manual).
  - 2T: mediana 13 s; <20 s 79,2%.
  - Teto de impacto 1T: 22.837 votos "sinalizados" = 0,37% da margem.
- **Interpretação [ALEGAM]**: eleitor que já sabia os números.
- **[OBSERVAÇÃO]**: o teto soma categorias heterogêneas, com valores fixos de 300 votos por "urna manual-rápida" e 73 por "mesário outlier".

### A14. "Contingência / recuperador de dados"
- **Números [ALEGAM]**:
  - 1T: 7.990 urnas com contingência; **368.437 urnas com desligamento**; 48.270 suspensões (1.059 após 17h); 8.709 com encerramento ≥19h; 341.589 habilitações manuais após 17h.
  - 2T: 14.775 contingências; 369.966 com desligamento; 5.657 suspensões.
- **[OBSERVAÇÃO]**: "desligamento" em ~99% das urnas indica que a regra conta o desligamento normal (fim do dia e véspera). A métrica não é útil como está. Os critérios de log não são publicados.

### A15. Forense: Klimek (comparecimento × share)
- **Método**: heatmap 50×50 de comparecimento × share por seção, correlação de Pearson e `canto_pct` (fração no canto de alto comparecimento e alto share; o limiar não é publicado).
- **Números [ALEGAM]**: 1T corr = −0,034 (13) e +0,023 (22); canto 0,74% e 0,02%. 2T: −0,089 e +0,083; canto 0,74% e 0,06%.
- **Interpretação [ALEGAM]**: correlação negativa é o padrão sem fraude.

### A16. Forense: último dígito
- **Método**: frequência do último dígito do total de votos por seção (13 e 22), qui-quadrado de uniformidade.
- **Números [ALEGAM]**: 1T p = **0,0** (13, n = 300.728) e p = **0,0** (22, n = 273.822); desvio máximo de 0,65 e 0,69 p.p. 2T também p = 0,0.
- **[OBSERVAÇÃO] Contradição.** O texto fixo da página diz "(uniformidade não rejeitada)", mas o p publicado é 0,0. As frequências caem monotonicamente de 0 a 9, um efeito conhecido de números pequenos ou truncamento. O teste é fraco.

### A17. Linha do tempo: habilitações a cada 15 min
- **Método**: contagem por faixa de 15 min, separada em biometria, sem biometria e manual, com marcas em 08:00 e 17:00 BRT.
- **Números [ALEGAM]**, 1T: biometria 72.490.340, sem biometria 13.550.104, manual 8.595.411.

### C1. Contraprova 1: votos depois de 17h, 18h e 19h, por UF e região
- **Números [ALEGAM]** (logs sem SP):
  - 1T: **4,18%** dos votos após 17h (4.013.479 de 95.958.806); 1,07% após 18h; 0,25% após 19h.
  - NE 6,54% após 17h; N 5,95%; SE 3,10%; CO 2,00%; S 1,37%. Topo por UF: AL 9,19%, PA 7,98%, MA 7,73%, BA 7,38%.
  - 2T: **0,033%** após 17h (31.567 votos).
- **Interpretação [ALEGAM]**: padrão geográfico, ligado a fila e tamanho de seção.

### C2. Contraprova 3: "Só presidente" (1T 2022)
- **Critério**: ≥90% de voto nominal para presidente e ≥50% de branco+nulo em todos os outros cargos, mínimo de 50 eleitores.
- **Números [ALEGAM]**: **0** de 370.782 seções. 3.831 seções com gap ≥30 p.p.

### C3. Contraprova 4: votos pós-17h × tamanho da urna
- **Números [ALEGAM]**, 1T:
  - Urnas com voto pós-17h: 178.034 (média de 283 votos, 360 aptos).
  - Urnas sem voto pós-17h: 192.629 (média de 236 votos, 298 aptos).
  - Mediana de segundos por voto: 53 contra 52. Biometria: 75,9% contra 74,1%.
  - O mesmo vale dentro da BA, do NE e do S.
- **Interpretação [ALEGAM]**: a urna que atrasa é a urna cheia (fila).

### C4. Contraprova 5: fila como hipótese falsificável (2022-1T)
- **Números [ALEGAM]**:
  - Mediana de ocupação com habilitação na última hora antes das 17h: 77%.
  - Gap entre o último voto antes das 17h e o primeiro depois: mediana 120 s. 3,3% das urnas com gap >15 min.
  - Ritmo: 32 votos/h das 16h às 17h, 36,8 votos/h depois das 17h.
  - 54% das urnas tinham eleitor habilitado antes das 17:00 que votou depois.
  - Mediana de 14 votos após 17h por urna.
  - "Suspeitas": 182 (gap >15 min e ≥20 votos tardios) + 666 (ociosa antes das 17h e ≥20 votos tardios); 469 com ritmo pós-17h acima de 2× o anterior.
- **[ALEGAM]**: as suspeitas, lidas uma a uma, têm desligamento ou contingência no log.

### C5. Contraprova 7: ritmo do mesário por hora (2022-1T)
- **Números [ALEGAM]**: habilitações por urna e hora, de 22,5 (8h) a 30,4 (11h) e 24,0 (16h), caindo para 7,9 (17h). Ociosidade mediana entre CONFIRMA e a próxima habilitação: 38–53 s. Duração da habilitação: 14–19 s. CV horário por urna, mediana 0,22.

### C6. Contraprova 8: abstenção no NE
- **Números [ALEGAM]**, 1T:
  - Abstenção nacional 20,92%. NE 19,53%, S 19,34%, SE 21,95%, CO 21,34%, N 20,94%, ZZ 55,7%.
  - Dentro do município, share22 nas seções com abstenção acima da mediana: 42,58%; abaixo: 43,70%.
  - 2T: nacional 20,58%.

### C7. Contraprova 9: "mesário votando por ausentes" (liberação manual pós-17h, 2022-1T)
- **Números [ALEGAM]** (aqui "manual" inclui sem biometria + manual):
  - Manual antes das 17h: 24,6%. Depois das 17h: 21,9%.
  - Urnas com ≥20 manuais pós-17h: 8.665 (256.848 votos); desvio mediano de share22 contra o município: −0,68 p.p.
  - Urnas com ≥5 manuais consecutivos pós-17h: 7.758.
  - Correlação manual × desvio: BR −0,037; BA −0,054; CE −0,065.
  - ZZ: 100% manual (sem biometria no exterior).
- **[OBSERVAÇÃO]**: "manual" aqui tem definição diferente do `pct_manual` = 8,96% do `summary`. São dois conceitos com o mesmo nome.

### C8. Itens 14–15 e adendos com números de 2022
- **Caso × irmã**: seção que dispara um padrão contra as outras seções do mesmo local, no mesmo pleito. **[ALEGAM]** 2022-1T: seções com share13 ≥90% → 5.333 casos, +11,6 p.p. contra as irmãs. Arquivo `pareado_irmas.json` publicado.
- **2022-2T** (`resumo_2022_2t.json`): manual 8,4% (8.107.441 de 96.513.389); 267 seções com ≥50% manual, share22 nelas −7,36 p.p. contra o município; 19 seções com último voto após 18h BRT (−13,3 p.p.); 8.620 seções com share13 ≥90% e 180 com share22 ≥90% (mínimo de 100 votos); 14.688 urnas de contingência de 370.820 (3,96%), share22 −0,85 p.p.; 43 títulos de mesário em ≥2 seções.
- **Urnas após 18h** (2026, comparado com 2022): em 2022-1T, 9,1% das seções "tardias"; share22 nas tardias 34,8% contra 46,6% (mesma escola).
- **Abstenção NE e horário** (2022-1T): votos após 16h por faixa de abstenção relativa (≤−10 p.p.: 12,3%; normal: 16,0%; >+10: 13,6%).
- **Títulos expostos no log**: "já existia em 2022 (136 seções no 1T, 273 no 2T)".
- **Reanálise de um "painel independente"** (`painel_inventario.json`): eles inventariam 22 métricas de um painel de terceiros, não identificado, com valores de 2022, por exemplo ">90%": 1T 5.947 e 2T 9.606; "lenta 20h+": 1T 11.467. Classificação deles: 12 replicadas, 5 pendentes, 5 erradas.

### C9. Por seção ("Consulte sua seção")
- **[OBSERVAÇÃO][VERIFICADO]**: em `data/secoes/2022_2t_AC.json`, o campo `primeiro_brt` é **negativo** (≈ −39.836 min, ou seja, 02/10) em **2.076 de 2.124** seções. O "1º voto" do 2T mostrado ao usuário vem do 1º turno (log cumulativo não filtrado neste campo). O caso AP 6050 z2 s750 (2T) mostra "179 votos depois do encerramento", enquanto o resumo nacional diz 0. É o mesmo artefato (encerramento do 1T no log do 2T), que eles reconhecem no resumo, mas não no card.

## 1.4 Avaliação geral do alvo 1

- O site descreve o método em prosa e publica agregados ricos, mas **não publica código**. Vários vereditos e textos são **fixos no JS** e contradizem os números publicados (A1, A4, A6, A8, A16).
- Há bugs de agregação ("já votou"), um artefato de fuso (oeste do AM) e um log cumulativo não filtrado em campos por seção do 2T.
- A cobertura de log de 2022 exclui SP.
- Mesmo assim, os nomes de mensagens de log e os critérios que eles documentam são úteis para especificar a reprodução.

---

# 2. https://github.com/alissonlinneker/DataUrnas-BR

## 2.1 Acessibilidade e autoria [VERIFICADO]

| Item | Resultado |
|---|---|
| Acesso | `git clone --depth 1` via HTTPS funcionou (235 arquivos). |
| Commit lido | `12f0433bd20882d305dd7b9e4987d6dcf3b321a9`, 2026-10-15 03:19:51 −0700, "Merge pull request #10 … release-v0.2.2" |
| Autor | Alisson Linneker (git: alissonlinneker@gmail.com); `CITATION.cff` presente |
| Licença | MIT |
| Código, método e resultados | **Tudo publicado**: código Python (`src/dataurnas`), metodologia (`docs/metodologia.md`), resultados em Parquet ZSTD (`data/parquet/`, ~183 MB para 2022), relatório de integridade (`docs/integridade-2022.md`), CI e testes. Painel Streamlit no Hugging Face Spaces (não acessado). |

## 2.2 Fontes de dados [VERIFICADO no código e nos docs]

- **2022 (base de análise)**: API hierárquica de resultados do TSE (config da eleição → config da UF → `aux.json` por seção → arquivos `.bu`, `.rdv`, `.logjez`, `.imgbu`, `.vscmr`). Pleitos 406 (1T, 02/10/2022) e 407 (2T, 30/10/2022). Presidente. **27 UFs, sem o exterior (ZZ)**. **[VERIFICADO no Parquet]**: 1T 470.986 seções, 2T 471.001, 27 UFs; `fuso_offset` −2 em 2.124 seções, −1 em ~27.480, 0 no resto.
- **2022 (integridade, à parte)**: ZIPs do CDN `https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2022/arqurnatot/bu_imgbu_logjez_rdv_vscmr_2022_<turno>t_<UF>.zip`, lidos por faixas de bytes. Segundo os docs, a API "não serve mais os arquivos de 2022 (HTTP 404)".
- 2026 (1T) também é coberto. Fora do escopo aqui, salvo o módulo de tempo de log, que só se aplica a 2026.

## 2.3 Regras de parsing de log (lidas em `src/dataurnas/parsers/log.py` e `analyzer/log_analyzer.py`)

- **Formato da linha** (regex): `^(\d{2}/\d{2}/\d{4}) (\d{2}:\d{2}:\d{2})\t(\w+)\t(\d+)\t(\w+)\t(.+?)\t([A-Fa-f0-9]+)\s*$`, que corresponde a data, hora, severidade, id da urna, aplicativo, descrição e hash/MAC. Linhas fora do padrão são descartadas silenciosamente. A decodificação é latin-1.
- **Extração 2022 (`.logjez` em 7z)**: lê **apenas o primeiro arquivo do pacote em ordem alfabética** (`alvo = sorted(i.filename for i in infos)[0]`). Para 2026 (ZIP), lê os logs aninhados de urnas substituídas e deduplica linhas.
- **Filtro por turno**: só entram linhas com `data == data do turno` (02/10/2022 ou 30/10/2022).
- **Eventos (substring ou regex na descrição)**:

  | Evento | Regra |
  |---|---|
  | Voto | `"O voto do eleitor foi computado"` (contagem de `votos_computados`) |
  | Abertura | **primeira** `"Urna pronta para receber votos"` do dia |
  | Encerramento | **última** `"Início do Encerramento"` (regex `In[ií]cio do Encerramento`); também `"Procedimento de encerramento confirmado"` |
  | Reinício (C06) | nº de `"Urna pronta para receber votos"` no dia − 1 |
  | Ligada/desligada | `"Urna ligada em (.+)"` (primeira), `"Urna desligada"` |
  | Carga/contingência | `"Modo de carga da UE"`; substituição: regex `(substitui\|contingencia\|conting[eê]ncia)` (case-insensitive) |
  | Erro | regex `(ERRO\|ERROR\|FALHA\|FAIL)` (case-insensitive) em qualquer descrição |
  | Ajuste de hora | regex `(ajust\|acert).*(hora\|relogio\|rel[oó]gio)` |
  | Alerta de mesário | `"Mesário indagado"` |
  | Modelo | `(Modelo de [Uu]rna\|Modelo UE\|UE)[\s:]*(\d{4})` ou `avusrlibue(\d{4})\.vst` |
  | logd | `"Início das operações do logd"` (definido, mas não usado nas regras) |

- **Habilitação, biometria e manual**: **não** são extraídas do log. Biometria vem do **BU**: `qtdEleitoresLibCodigo` (liberado por código) e `qtdEleitoresCompBiometrico` (spec v1, 2022). Taxa = lib_codigo / (lib_codigo + comp_biometrico). Os eleitores sem biometria cadastrada ficam fora do denominador.
- **Intervalos e histogramas de hora**: **não há para 2022.** A única métrica de tempo é a duração da abertura ao encerramento (minutos). Existe um módulo para **2026** (`analyzer/rdv_recontagem.py::analisar_log_tempo`, `data_eleicao="04/10/2026"`) que:
  - conta "O voto do eleitor foi computado" do dia;
  - mede intervalos entre votos consecutivos **da mesma urna**, com faixas [0,1), [1,2), [2,3), [3,5), [5,10), [10,15), [15,20), [20,30), [30,45), [45,60), [60,120), [120,300), [300,600), [600,3600), ≥3600 s;
  - aplica as flags `<10 s` (rajada), `>3600 s` (lacuna) e voto antes das 8h BRT (convertido em hora local);
  - marca voto fora de sequência (antes de "Urna pronta" ou depois de "Inicio do Encerramento" da mesma urna), voto em outra data e relógio invertido.
- **Fuso** (`analyzer/timezones.py`): AC −2; AM, MT, MS, RO e RR −1; exceções municipais AM UTC-5 (códigos TSE 2054 Atalaia do Norte, 2135 Benjamin Constant, 2291 Eirunepé, 2313 Envira, 2020 Guajará, 2399 Ipixuna, 98477 Tabatinga) e Noronha (pe, 30015) +1. **[ALEGAM]** "A base de 2022 distribuída foi compilada antes dessas exceções e usa o fuso da UF".
- **Limites (BRT convertido em hora local)**:

  | Código | Regra |
  |---|---|
  | M01 | abertura antes das 7h |
  | A04 | abertura depois das 8h30 |
  | A05 | encerramento antes das 17h |
  | M02 | encerramento depois das 22h |
  | M03 | log com mais de 100 linhas e sem abertura |
  | M04 | mais de 10 "erros" |
  | M05 | qualquer ajuste de hora |
  | I01 | qualquer substituição |
  | I02 | mais de 20 alertas de mesário |
  | A03 | \|votos_log − max(comparecimento do BU)\| > 2 |
  | E03 | duração negativa |

## 2.4 Testes e análises (com números de 2022)

Números marcados **[VERIFICADO-Parquet]** foram contados por nós em `data/parquet/issues.parquet` e `secoes.parquet`, a base que eles distribuem. Isso confere com o que eles publicam, não com o TSE.

| # | Teste | Método e limiar | Insumo | 1T | 2T |
|---|---|---|---|---|---|
| D1 | C05 votos > aptos | votos de um cargo > aptos (sem TTE) | BU | 0 | 0 |
| D2 | A02 votos > comparecimento | por cargo | BU | 0 | 0 |
| D3 | A06 comparecimento difere entre cargos | — | BU | 0 | 0 |
| D4 | A01 aptos diferentes entre eleições do mesmo BU | desconto de trânsito (só a partir da v0.2) | BU | 19.155 | 11.417 |
| D5 | A03 log ≠ BU | \|votos_log − comparecimento\| > 2 | log + BU | 3.356 | 1.691 |
| D6 | C06 reinício | "Urna pronta…" > 1 vez no dia | log | 73.089 seções | 63.840 |
| D7 | A04 abertura > 8h30 | hora local ajustada pela UF | log | 5.813 | 2.391 |
| D8 | A05 encerramento < 17h | — | log | 251 | 440 |
| D9 | M02 encerramento > 22h | — | log | 141 | 0 |
| D10 | M01 abertura < 7h | — | log | 0 | 0 |
| D11 | M03 sem abertura | >100 linhas | log | 41 | 26 |
| D12 | M04 >10 erros | regex ERRO/FALHA | log | 161 | 104 |
| D13 | M05 ajuste de hora | regex | log | 120 | 33 |
| D14 | I01 substituição/contingência | regex | log | 5.269 | 2.932 |
| D15 | I02 >20 alertas de mesário | "Mesário indagado" | log | 2.934 | 59 |
| D16 | M06 >30% liberados por código | lib_codigo/(lib+bio) | BU | 2.011 | 1.210 |
| D17 | I03 nulos >15% (por cargo) | — | BU | 49.002 ocorrências | 265 |
| D18 | I04 brancos >10% (por cargo) | — | BU | 229.633 | 540 |
| D19 | I05 abstenção >40% | — | BU | 3.800 | 3.389 |
| D20 | I06 urna de reserva / tipo ≠ seção | `tipoUrna` | BU | 10.077 | 17.931 |
| D21 | Benford 1º dígito | χ², V de Cramér (conforme se V < 0,05) | BU | só no painel | — |
| D22 | Benford 2º dígito | χ² + KS + V de Cramér; "conforme" = p > 0,05 e V < 0,10 | BU | só no painel | — |
| D23 | Outliers por z-score | \|z\| > 3 nacional e por UF (abstenção, % biometria, duração; nulos, brancos e share por UF) | BU/log | só no painel | — |
| D24 | Reinício × voto | χ² de independência (grupo com/sem reboot × candidato), V de Cramér, por UF e modelo | BU + log | só no painel | — |
| D25 | Biometria × voto | quartis de % biometria contra share 13/22 | BU | só no painel | — |
| D26 | Duração × voto, modelo × voto, reserva × normal, substituição × resultado | agregações descritivas | BU + log | só no painel | — |
| D27 | Entre turnos | variação do comparecimento por UF, "migração" de votos, seções presentes em um turno só | BU | só no painel | — |
| D28 | Índice de confiança 0–100 | média ponderada: hash 25, C05 20, Benford 15, reinícios 15, turnos 10, biometria 10, outliers 5 | derivado | só no painel | — |
| D29 | Integridade 2022 (à parte) | SHA-512 de cada arquivo contra o hash assinado no `.vscmr`; assinatura ECDSA P-521/Ed521; cadeia até a AC intermediária em amostra de 5% | ZIP CDN | ver abaixo | — |
| D30 | Votos de presidente do BU assinado = base | — | ZIP + base | 470.819 conferem, 0 divergem | 470.834 / 0 |

- Outros números **[ALEGAM e VERIFICADO-Parquet]**:
  - 511.121 ocorrências no total (alta 70.231, média 115.059, informativa 325.831).
  - Soma 13 e 22 da base (sem ZZ): 1T 57.094.611 / 50.938.437; 2T 60.168.088 / 58.049.729.
- **Integridade 2022 [ALEGAM, docs/integridade-2022.md]**:
  - 944.051 seções (472.024 no 1T e 472.027 no 2T, **incluindo ZIPs com ZZ**).
  - 3.776.042 SHA-512 conferem, **0 divergentes**; 944.051 assinaturas válidas, 0 inválidas.
  - 173 arquivos assinados ausentes do pacote, em 64 seções.
  - 2.064 seções fora do banco de 2022.
  - Assinatura de software CEPESC não verificada.
- **Interpretação [ALEGAM]**: três grupos de leitura. Grupo 1 (C01, C05, A02, A06) seria indício direto de adulteração, e há 0. Grupo 2 tem explicações conhecidas (A03: troca de urna divide o log). Grupo 3 é operacional ou estatístico. Benford e outliers "têm alta taxa de falso positivo". Os arquivos públicos não detectam manipulação dentro da urna antes da assinatura.

## 2.5 Observações de método sobre o DataUrnas-BR

1. **A03 é viesado pela extração.** **[VERIFICADO-Parquet]** Todas as 3.356 (1T) e 1.691 (2T) ocorrências A03 têm `votos_log < comparecimento` (mediana −81 e −117), nunca o contrário. Isso é compatível com duas regras do código:
   - para 2022, só o primeiro arquivo do 7z é lido, então logs de urnas substituídas ficam de fora;
   - o filtro `data == data do turno` descarta votos depois da meia-noite (1T 2022: centenas de seções votaram depois das 00h, segundo o outro alvo).
   Na soma geral, 1T: `votos_log` 121.207.532 contra comparecimento 123.373.129.
2. **Fuso por UF na base distribuída**: o oeste do AM (UTC-5) recebe −1. A04/A05/M01 nessas seções podem ser artefatos. Também não há tratamento empírico (por exemplo, pela abertura modal do município).
3. **"Reinício" = repetições de "Urna pronta para receber votos"**: não separa religamento por falta de energia, troca de urna e reinício do aplicativo. 15,5% das seções do 1T aparecem com C06.
4. **Regex amplos**: `ERRO|FALHA` e `substitui|contingencia` casam qualquer descrição que contenha a substring. Por isso as contagens M04 e I01 são ruidosas.
5. **Benford**:
   - inclui o 1º dígito e pondera Benford em 15% do índice de confiança, apesar da ressalva textual dos próprios autores;
   - aplica o KS a dados discretos (p-valor inválido);
   - usa χ² com n ≈ 470 mil, que rejeita qualquer desvio;
   - os cortes do V de Cramér (0,05/0,10/0,20) são arbitrários.
6. **z-score com |z| > 3** em distribuições assimétricas (abstenção, biometria) produz muitos falsos positivos. Os próprios autores reconhecem isso.
7. **Exterior (ZZ) fora da base de 2022.**
8. **Para 2022 não há métricas de ritmo voto a voto** (intervalos, rajadas, histograma por hora, habilitação biométrica, biográfica ou manual pelo log). Esses testes só existem para 2026.

---

# 3. https://brasil.arvor.co/politizese.html

## 3.1 Acessibilidade e autoria [VERIFICADO]

| Item | Resultado |
|---|---|
| HTTP | `200`, 15.776 bytes, servido por **GitHub Pages** (`server: GitHub.com`), `last-modified: Mon, 26 Oct 2026 23:13:15 GMT` |
| Precisa de JS? | **Sim.** Busca por seção, CEP, cidade ou geolocalização via `assets/politize_se/app.js`, que lê `assets/politize_se/dados/indice.json` (639 KB, `gerado_em` 2026-10-26T22:38:21Z) e `dados/zona/<UF>/<zona>.json.gz`. Sem JS, só aparecem o formulário e o texto de método. Tem Google Analytics (gtag). Usa Supabase para receber relatos e BUs (função `receber-bu`). |
| Autoria | "Arvor Intelligence · brasil.arvor.co". Sem pessoa nomeada na página. Num contrato de método aparece "Pedido do Leonardo" (sem sobrenome). |
| Código e método | Repositório público citado em páginas irmãs: **https://github.com/ArvorCo/PNAD**. Baixamos `analysis/politize_se/CONTRATO.md` (HTTP 200, 33 KB) e `analysis/apuracao_2t_2026/CONTRATO_ANOMALIA.md` (200, 18 KB). O código do pipeline (`scripts/…`) é citado; não o lemos. |
| Páginas irmãs | `logs_urnas_2026.html` 200; `apuracao_2T_2026.html` 200 (6,3 MB); `mudancas_secoes_abstencoes.html` 200; `politizese_mapa.html` 200; `politize.html` 404. |

## 3.2 Escopo e fontes

- **[VERIFICADO] A página trata da eleição de 2026 (1º e 2º turnos), não de 2022.** Candidatos "Flávio" e "Lula"; 1T em 04/10/2026, 2T em 25/10/2026. Nem `app.js` nem `indice.json` contêm dados de 2022.
- Fontes declaradas (`indice.json.fontes`): bancos SQLite de BUs do 1T (8,55 GB) e do 2T ("em coleta"), régua do 1T, logs do 1T e do 2T (`logs_urnas_2t_2026.sqlite`, 4,35 GB), clima (ERA5, CEMADEN, ECMWF IFS) e anomalia ML. Há SHA-256 de alguns arquivos.
- Cobertura de BUs do 2T: 499.207 de 499.248 seções (99,99%; ZZ 1.310 de 1.351).

## 3.3 Testes e análises (2026)

- **P1. Seis "sinais da régua da casa"** (por seção, 2T contra 1T e contra o município):
  - `delta`: comparecimento ≥5 p.p. acima do 1T;
  - `sem_bio`: ≥10% sem digital cadastrada **e** pelo menos o dobro do município;
  - `ano_nasc`: ≥10% liberados pelo ano de nascimento **e** pelo menos o dobro do município;
  - `salto_bio`: parcela sem digital reconhecida ≥5 p.p. acima do 1T;
  - `tardia`: último voto depois das 19h ou ≥30 min depois do 1T;
  - `papel`: BU do Sistema de Apuração (cédula).
  - O escore vai de 0 a 6. Seções com menos de 30 aptos não mostram votos.
  - Explicações automáticas: perto das 19h (prorrogação), fila (<18h55), seção agregada, aptos mudaram mais de 10%, contingência ou mais de uma carga, cédula, seção com menos de 100 aptos, salto no mesmo local, zona ou seção com biometria baixa no 1T, comparecimento do 1T baixo, alta acompanha o município ou a UF.
  - **[ALEGAM]**, por UF: por exemplo BA `secoes_sinal` 10.669, `secoes_sinal2` 1.360, escore máximo 5.
- **P2. Horário**: minutos desde a meia-noite de Brasília, com fuso da UF **mais correção por município pela abertura modal às 8h**; exterior em hora local. É uma abordagem empírica que evitaria o artefato do oeste do AM.
- **P3. Troca de urna entre turnos**: número interno da urna e carga nos dois BUs. Categorias: mesma; mesma com recarga; reserva/contingência; nova; outra seção da zona; outro município.
- **P4. Nível de atenção do log (0–3)**: famílias energia, identificação, ritmo, pausas e arquivo. Os 27 critérios estão publicados em `logs_urnas_2026.html`, com regras explícitas. Exemplos:
  - referência = mediana de pares da mesma UF, modelo e número de cargos (≥30 seções);
  - corte em ±4 "escalas robustas" (1,4826 × MAD, com pisos) **e** um excesso mínimo;
  - "intervalo ≥1.800 s entre cômputos consecutivos";
  - "bateria durante a votação com ≥5 outras seções do município a até 60 s";
  - "ERRO/FATAL no dia (ALERTA excluído)";
  - "contagem de 'voto computado' ≠ comparecimento do BU".
  - **[ALEGAM]**, 1T 2026: 499.176 logs; mediana do processo do identificador ao cômputo 74 s; 10 seções com contagem log ≠ BU; 0 seções com processo, cadência ou trecho "rápido demais"; 17.350 com intervalo ≥30 min; 117.016 com bateria.
  - Mensagens citadas: "Eleitor foi habilitado", "Batimento de digitais retornou o score", partida do VOTA, LOGD "urna ligada".
- **P5. Anomalia por mistura gaussiana**:
  - 9 frações do eleitorado (lula1, flavio1, outros1, brancos1, nulos1, lula2, flavio2, brancos2, nulos2), padronizadas;
  - `GaussianMixture(full)`, k escolhido pelo "joelho" do BIC (k = 8), sem o exterior;
  - grupo 5 = "atípico": **10.850 de 497.796 seções**.
  - **[ALEGAM]** "atipicidade não é irregularidade".
- **P6.** Mudança de local entre turnos, clima (chuva ≥20 mm, rajada ≥50 km/h) e uma "régua de fiscalização" com níveis de prioridade.

## 3.4 Observações

- Não serve como insumo direto para 2022. É útil como **referência de desenho de regras**: comparação com pares (UF, modelo, cargos), escalas robustas, correção empírica de fuso por município, exigência de ciclo completo e reconstrução de logs com vários fragmentos.
- A mistura gaussiana sobre frações de voto marca seções com perfil de voto atípico (geografia ou demografia), não irregularidade operacional. Os próprios autores dizem isso.

---

# 4. Classificação de reprodutibilidade (para 2022)

Legenda:
- **(a)** reprodutível com os dados abertos do TSE (BU e log);
- **(b)** reprodutível só parcialmente (método incompleto, critério ambíguo ou dado faltante);
- **(c)** não reprodutível.

| ID | Teste | Fonte | Classe | Motivo |
|---|---|---|---|---|
| A1 | Votos antes das 8h BRT | auditoria | **a** | regra clara; corrigir o fuso |
| A2 | Rajadas (≥5 votos com intervalo < 20 s no 1T; < 6 s no 2T) | auditoria | **a** | não dizem se o intervalo é entre habilitações ou entre cômputos; definir explicitamente |
| A3 | "Totalizada antes de fechar" | auditoria | b | campo usado ≠ descrição |
| A4 | Modelo de urna × share (bruto, ajustado por município, bootstrap) | auditoria | **a** | modelo vem do log/vscmr |
| A5 | Benford 2º dígito com nulo binomial | auditoria | b | detalhes da simulação não publicados; teste fraco |
| A6 | 100% para um candidato | auditoria | **a** | — |
| A7 | Mesário em várias seções | auditoria | b/c | 2022 não nomeia o mesário em todas as linhas |
| A8 | "Já votou" | auditoria | **a** | com a string; o total deles tem bug |
| A9 | Hora do último voto | auditoria | **a** | — |
| A10, A11 | Comparecimento > aptos; consistência do BU | ambos | **a** | — |
| A12 | Velocidade da apuração | auditoria | c | sem dado de transmissão em 2022 |
| A13 | Duração do voto (<40 s, <20 s) | auditoria | **a** | — |
| A14 | Contingência, desligamentos, suspensões | ambos | b | strings não publicadas pela auditoria; o DataUrnas usa regex ampla |
| A15 | Klimek | auditoria | **a** | o limiar do "canto" não é publicado |
| A16 | Último dígito | auditoria | **a** | teste fraco |
| A17 | Habilitações a cada 15 min por tipo | auditoria | **a** | precisa do vocabulário de habilitação de 2022 |
| C1, C3, C4, C5 | Votos pós-17h/18h/19h, × tamanho, fila, ritmo | auditoria | **a** | incluir SP (logs existem via API) |
| C2 | "Só presidente" | auditoria | **a** | — |
| C6 | Abstenção × share | auditoria | **a** | só BU |
| C7 | Manual pós-17h | auditoria | **a** | definir "manual" explicitamente |
| C8 | Caso × irmã | auditoria | **a** | precisa do local de votação (cadastro de locais do TSE) |
| — | Teto de impacto | auditoria | c | pesos fixos arbitrários |
| D1–D3, D4 | C05/A02/A06/A01 | DataUrnas | **a** | código publicado |
| D5 | A03 log × BU | DataUrnas | **a** | ler todos os fragmentos e votos depois da meia-noite |
| D6–D15 | Horários, reinícios, erros, alertas | DataUrnas | **a** | código publicado; revisar regex |
| D16–D20 | Biometria pelo BU, nulos, brancos, abstenção, reserva | DataUrnas | **a** | — |
| D21–D27 | Benford, z-score, χ² reinício × voto, quartis, entre turnos | DataUrnas | **a** | métodos fracos, mas publicados |
| D28 | Índice de confiança | DataUrnas | b | pesos arbitrários |
| D29–D30 | Integridade SHA-512 e assinatura | DataUrnas | **a** | exceto CEPESC (c) e cadeia até a raiz (c) |
| P1–P6 | Arvor | Arvor | n/a para 2022 | eleição de 2026; regras (P2, P4) transportáveis |

## 4.1 Especificações de reprodução para os itens (a)

### Insumos comuns
- **Pacote**: `https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2022/arqurnatot/bu_imgbu_logjez_rdv_vscmr_2022_{1t,2t}_{UF}.zip`, 27 UFs + ZZ. Guardar o SHA-256 de cada ZIP.
- Dentro do pacote, por seção: `.bu` (ASN.1/BER; specs em `DataUrnas-BR/spec/v1/bu.asn1`), `.logjez` (7z; abrir **todos** os membros, incluindo logs de urnas substituídas, e deduplicar linhas idênticas), `.vscmr` (assinatura; modelo e hashes), `.rdv` e `.imgbu`.
- Linha do log: `DD/MM/AAAA HH:MM:SS<TAB>SEV<TAB>ID_URNA<TAB>APLICATIVO<TAB>DESCRIÇÃO<TAB>HASH`, latin-1.
- **Vocabulário**: antes de qualquer contagem, gerar a tabela de frequência das `DESCRIÇÃO` normalizadas (sem números) por turno, para confirmar as strings de 2022. As strings citadas pelas fontes são:
  - `"O voto do eleitor foi computado"`
  - `"Urna pronta para receber votos"`
  - `"Início do Encerramento"` / `"Inicio do Encerramento"`
  - `"Procedimento de encerramento confirmado"`
  - `"Urna ligada em"`, `"Urna desligada"`
  - `"Modo de carga da UE"` (variante "- Urna de contingência")
  - `"Mesário indagado"`
  - `"O eleitor identificado já votou"`
  - `"Solicita digital. Tentativa [n] de [4]"`
  - `"Solicitação de dado pessoal do eleitor para habilitação manual"`
  - `"Eleitor foi habilitado"`
  - `"Batimento de digitais retornou o score"`
  - Atenção: segundo a auditoria, várias mensagens de mesário e de CPF só existem em 2026.
- **Hora BRT**: `t_BRT = t_local − offset`, com offset AC −2; AM, MT, MS, RO e RR −1; oeste do AM −2 (lista oficial de municípios em UTC-5, a conferir com a lei); Noronha +1. **Validar empiricamente**: a moda de "Urna pronta para receber votos" por município deve cair em 08:00 BRT; reportar os municípios que não caem. ZZ em hora local.
- **Janela do dia**: data do turno de 00:00 até D+1 06:00. No 2T, **descartar eventos com data < 30/10/2022** (log cumulativo).

### Especificações por teste
1. **Votos antes das 8h e depois das 17h, 18h e 19h** (A1, C1): eventos "O voto do eleitor foi computado" na janela, em BRT. Contar `<08:00` e `≥17:00/18:00/19:00` por UF e região. Denominador: total de votos do log. Reportar quantos votos depois das 17h tiveram habilitação (o "Eleitor foi habilitado" anterior da mesma urna) antes das 17:00.
2. **Hora do primeiro e do último voto** (A9): min/max de "voto computado" por seção; histograma por hora BRT. Seções com último voto depois da meia-noite são contadas à parte.
3. **Duração do voto e da habilitação** (A13, A17): ciclo = habilitação → "voto computado" na mesma urna. Classificar o tipo de habilitação (biométrica, por código/manual, sem biometria) pelas mensagens do ciclo. Calcular mediana, p10, p90, % < 40 s e % < 20 s, histograma em faixas de 10 s e série a cada 15 min por tipo. Conferir os totais por tipo com `qtdEleitoresCompBiometrico` e `qtdEleitoresLibCodigo` do BU.
4. **Rajadas** (A2): intervalos entre "voto computado" consecutivos **da mesma urna** (sem atravessar reinícios). Contar sequências de ≥5 intervalos abaixo do limiar (20 s no 1T; 6 s no 2T e no ZZ) e a sensibilidade 20/30 s × ≥3/≥5. Reportar votos, urnas e % dos votos do log.
5. **Log × BU** (A03, A11): nº de "voto computado" (todos os fragmentos, toda a janela) contra o `comparecimento` do BU. Reportar a distribuição da diferença com sinal.
6. **Consistência do BU** (C05, A02, A06, A10, 100%): votos por cargo ≤ aptos (sem TTE) e ≤ comparecimento; comparecimento igual entre cargos; seções com 100% para um candidato (válidos e nominais, os dois critérios).
7. **"Já votou"** (A8): linhas "O eleitor identificado já votou" por seção. Verificar se a linha seguinte da mesma urna é habilitação ou voto computado para o mesmo eleitor (no 2022 o log não traz o título; usar a sequência).
8. **Contingência e reinícios** (A14, C06): seções com mais de um ID_URNA de votação, "Modo de carga da UE - Urna de contingência", ou mais de uma "Urna pronta para receber votos" no dia. Reportar separadamente.
9. **Modelo × share** (A4): modelo via `.vscmr` ou `avusrlibueNNNN.vst` no log; share 13/22 bruto e desvio contra a média do município; bootstrap por município (2.000 réplicas) nos municípios com os dois tipos de modelo; publicar o IC.
10. **Klimek, último dígito, Benford-2** (A15, A16, A5): só BU. Publicar como descritivo e com o nulo simulado explícito; não usar como prova.
11. **Pós-17h × tamanho, fila e ritmo** (C3, C4, C5): por urna, votos totais e aptos; ocupação na última hora antes das 17h; gap entre o último voto antes das 17h e o primeiro depois; ritmo em votos por hora antes e depois.
12. **Manual pós-17h e caso × irmã** (C7, C8): % de habilitação manual antes e depois das 17h, por UF. Comparar share e comparecimento da seção contra as outras seções do mesmo local (cadastro de locais de votação do TSE) e contra o município.
13. **Integridade** (D29): SHA-512 de cada arquivo contra a lista assinada no `.vscmr`; verificação ECDSA P-521/Ed521. A cadeia só vai até a AC intermediária.

## Reprodução independente (cálculo próprio a partir dos arquivos do TSE)

_Gerado por `scripts/gerar_relatorios.py`. Os valores da coluna "alegado" são de terceiros e não foram adotados; a coluna seguinte é calculada por este projeto, com a cobertura informada em `docs/auditoria-2022.md`. Divergências de definição estão indicadas._

| id | fonte | verificação | turno | alegado (terceiros) | cálculo próprio (TSE) |
|---|---|---|---|---|---|
| A1 | auditoriaeleicoes.com | Votos antes das 8h (Brasília) | 1º | 8.185 (todos no AM) | 0 (em 18.785 seções com log) |
| A1 | auditoriaeleicoes.com | Votos antes das 8h (Brasília) | 2º | 19.408 (todos no AM) | 0 (em 13.287 seções com log) |
| C1 | auditoriaeleicoes.com | % dos votos após 17h (Brasília), sem SP | 1º | 4,18% | 2,548% (com SP); 2,548% (sem SP) |
| C1 | auditoriaeleicoes.com | % dos votos após 17h (Brasília), sem SP | 2º | 0,033% | 0,047% (com SP); 0,047% (sem SP) |
| A2 | auditoriaeleicoes.com | Rajadas: ≥5 votos com intervalos <20 s (1º t.) / <6 s (2º t.) | 1º | 10.184 votos em 1.504 sequências | pendente (AttributeError) |
| A2 | auditoriaeleicoes.com | Rajadas: ≥5 votos com intervalos <20 s (1º t.) / <6 s (2º t.) | 2º | 4.296 votos em 777 sequências | pendente (AttributeError) |
| A6 | auditoriaeleicoes.com | Seções com 100% dos válidos para um candidato | 1º | 18 | 62 (todas as faixas); 17 com ≥100 válidos |
| A6 | auditoriaeleicoes.com | Seções com 100% dos válidos para um candidato | 2º | 29 | 147 (todas as faixas); 63 com ≥100 válidos |
| A4 | auditoriaeleicoes.com | UE2020 − demais, % do nº 22, mesmo município (bootstrap) | 1º | +1,00 p.p. [0,59; 1,58] | 0,65 p.p. [0,09; 1,23] (município); 0,42 [-0,22; 1,08] (mesmo local) |
| A4 | auditoriaeleicoes.com | UE2020 − demais, % do nº 22, mesmo município (bootstrap) | 2º | +1,17 p.p. [0,72; 1,80] | 0,78 p.p. [0,14; 1,40] (município); 0,37 [-0,25; 1,02] (mesmo local) |
| A16 | auditoriaeleicoes.com | Último dígito uniforme (13 e 22) | 1º | p = 0,0 (rejeita) | uniforme: p_holm 4.6e-07, 1.1e-15 (efeito máx. 0,29 p.p.); vs. simulação: p_holm 1.00, 1.00 |
| A13 | auditoriaeleicoes.com | Mediana habilitação→voto (s) | 1º | 52 s | 54 s |
| A13 | auditoriaeleicoes.com | Mediana habilitação→voto (s) | 2º | 13 s | 13 s |
| D5 | DataUrnas-BR | Seções com |votos no log − comparecimento| > 2 | 1º | 3.356 (todas com log < BU) | 5 seções (todos os arquivos de log da seção, janela até o dia seguinte); 12 com qualquer diferença |
| D5 | DataUrnas-BR | Seções com |votos no log − comparecimento| > 2 | 2º | 1.691 | 0 seções (todos os arquivos de log da seção, janela até o dia seguinte); 3 com qualquer diferença |

Notas: (1) A1 — a conversão por UF aplica −1 h a todo o AM; o oeste do AM está em UTC−5, de modo que o voto das 6h locais nesses municípios (= 8h de Brasília) vira 7h com a conversão de +1 h e é classificado como "antes das 8h". (2) D5 — o DataUrnas-BR lê só o primeiro arquivo do pacote 7z e descarta votos após a meia-noite, o que produz contagens de log menores que o BU. (3) A2 — com intervalos medidos entre registros de voto computado, a definição publicada não reproduz a contagem alegada; o critério exato dos autores não é público.
