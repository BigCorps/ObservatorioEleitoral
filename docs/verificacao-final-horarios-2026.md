# Verificação dirigida — horários do TSE e códigos de local (29/10/2026)

**Escopo:** comparação das fontes oficiais divulgadas depois da auditoria de 29/10. Esta é uma **triagem documental com dados publicados e dois programas para execução nos Parquets locais**; ainda não é a reconciliação individual concluída.

## 1. Nova disponibilidade dos pacotes do segundo turno

O Portal de Dados Abertos do TSE agora lista também recursos **"Arquivos transmitidos para totalização — Segundo turno"** para as 27 UFs e o exterior (ZZ). As páginas individuais de SP e RR indicam criação dos recursos em 28/10/2026.

Fonte: https://dadosabertos.tse.jus.br/dataset/resultados-2026-arquivos-transmitidos-para-totalizacao

Exemplos:
- SP: https://dadosabertos.tse.jus.br/dataset/resultados-2026-arquivos-transmitidos-para-totalizacao/resource/be9bf1bc-5025-45c5-a24f-730694ecd0b9
- RR: https://dadosabertos.tse.jus.br/dataset/resultados-2026-arquivos-transmitidos-para-totalizacao/resource/91bf90e8-ff77-4f25-aa10-3e7f0f05114b

**Atenção:** a disponibilidade atual não contradiz o inventário anterior — ele tinha um horário de coleta anterior. Não inferir datas de primeira publicação apenas da data de criação do recurso.

## 2. Quadro oficial TSE versus logs do Observatório

Fonte primária: TSE, "Total de votos após 17h" (quadro por UF):
https://www.tse.jus.br/comunicacao/noticias/arquivos/total-de-votos-apos-17h

| Indicador | TSE | Observatório, definição equivalente disponível | Diferença |
|---|---:|---:|---:|
| Votos após 17h | 34.393 | 34.330 (incluindo exatamente 17h00:00) | **63** |
| Votos após 19h | 13 | 11 | **2** |
| Seções com encerramento depois das 19h | 6.766 | 6.766 | **0** |

Os registros de votos **estritamente posteriores** a 17h00:00 no Observatório são 34.050; há 280 exatamente nesse segundo, totalizando 34.330 desde 17h00:00.

O quadro por UF aponta a diferença dos **dois registros após 19h para Pernambuco** (TSE: 2; Observatório: 0). Bahia (2), Rio de Janeiro (4) e São Paulo (5) coincidem nesse recorte.

Na comparação inicial de votos após 17h, antes de somar os registros exatamente às 17h00:00 de cada UF:
- PE: TSE 1.730, Observatório 1.625 (**+105**);
- SP: TSE 8.860, Observatório 8.787 (**+73**);
- AM: TSE 973, Observatório 999 (**−26**, sentido contrário!).

Esses números **não são divergências de votos em BUs**, mas diferenças entre contagens por horário/critério e cobertura. A origem ainda não foi esclarecida. **Não imputar os 63 votos a nenhuma UF até a execução do confronto por segundo**, pois os 280 votos no segundo 17h00:00 ainda precisam ser alocados por UF.

Dados reproduzíveis e tabela por UF: `resultados/2026/confronto_horarios_tse_uf.csv`.

Executar com os logs locais, sem novo download:
```bash
python -m observatorio.confronto_horarios_tse
```
Gerará `resultados/2026/confronto_horarios_tse_logs_detalhe_uf.csv`, com as diferenças residuais por UF, os votos exatamente às 17h e às 19h e os recortes entre 18h e 19h.

**Próximo passo:** localizar as seções individuais de PE e dos estados com maior diferença residual, comparar as versões dos logs originais do Portal de Resultados com os pacotes agora publicados e reproduzir exatamente o critério de evento/horário do TSE, se documentado. Não presumir erro ou manipulação de qualquer fonte.

## 3. Sensibilidade dos 7.315 códigos de local divergentes

A auditoria anterior identificou códigos de local diferentes entre o BU-CSV e o Detalhe por seção em 7.315 seções no segundo turno, com votos coincidentes. Isso pode mudar os grupos comparáveis usados nos modelos de efeitos fixos por **local**.

Executar com os Parquets que já foram preservados:
```bash
python -m observatorio.sensibilidade_locais_2026
```
Gerará `resultados/2026/consolidado_2t/sensibilidade_codigo_local.csv`, comparando:
- efeito ajustado de voto após 17h em 2026, sob cada código de local;
- correspondência conservadora de 2022 × 2026 e teste de evolução histórica sob cada código.

Comparar **amostra, locais elegíveis, efeitos ajustados e intervalos**. Uma diferença entre códigos deve ser documentada, e não corrigida silenciosamente para favorecer uma hipótese.

## 4. Pendências de logs e cronologia

Continuam documentadas no relatório principal:
`docs/reconciliacao-consolidado-2026-2t.md`.

Os recursos oficiais novos autorizam uma comparação direcionada com os pacotes consolidados (somente as seções pendentes e as diferenças temporais), sem baixar novamente o acervo inteiro. Antes da análise, registrar ETag, Last-Modified, SHA-256, versionamento e extensão real da cobertura do pacote.

**Situação no momento desta nota:** o TSE publicou novos recursos, mas os testes de sensibilidade e a comparação individual dos logs **ainda não foram executados no ambiente que guarda os Parquets**, portanto suas conclusões permanecem abertas.
