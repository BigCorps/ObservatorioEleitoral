# Reconciliação do BU em CSV consolidado — 2º turno de 2026

> **Atualização posterior no dia 29/10/2026:** após o inventário abaixo, o Portal de Dados Abertos do TSE passou a exibir recursos do **2º turno de 2026 para os arquivos transmitidos para totalização**, incluindo SP e RR (recursos cadastrados em 28/10). As informações históricas deste relatório reproduzem o estado da coleta anterior e não devem ser interpretadas como status atual. O confronto individual com esses novos pacotes ainda não foi executado. Ver [verificação complementar de horários, pacotes e códigos de local](verificacao-final-horarios-2026.md).

_Executada em 29/10/2026 a partir de arquivos oficiais do TSE com hash conferido. Código:
`observatorio/consolidado_2t.py`, `observatorio/reconciliacao.py`, `observatorio/cronologia.py`. Saídas em
`resultados/2026/consolidado_2t/`. Nenhuma diferença aqui é tratada como indício de fraude; ausência de log não é
tratada como ausência de voto._

## 1. Arquivos oficiais obtidos

| conjunto (CKAN) | arquivos | situação em 29/10/2026 14:21 UTC |
|---|---|---|
| `resultados-2026-boletim-de-urna` | **28 BU em CSV do 2º turno** (27 UFs + exterior, 144,3 MB) e **28 hashes `.sha512`** | baixados; **SHA-512 oficial confere nos 28** |
| idem | BU de **RR** | **não listado no CKAN**; existe no CDN pelo padrão oficial (`bweb_2t_RR_261020260742.zip`, Last-Modified 26/10 12:01 UTC) com `.sha512` publicado, que confere |
| `resultados-2026` | Detalhe e Votação por seção (já usados antes), Votação/Detalhe por município-zona, Relatórios de totalização | munzona atualizados em 28–29/10 e baixados novamente (as versões antigas tinham só o 1º turno); por seção: versão local = versão vigente |
| `resultados-2026-arquivos-transmitidos-para-totalizacao` | só o 1º turno (28 pacotes) | **2º turno não publicado**; os arquivos do 2º turno (BU, log, RDV, VOTA) foram coletados em 27/10 no Portal de Resultados (499.207 seções, hash conferido) |

Inventário completo com URL, data de acesso, tamanho, ETag, Last-Modified, SHA-256, SHA-512 e hash oficial:
`resultados/2026/consolidado_2t/inventario_arquivos_oficiais_2026.csv` e `manifestos/inventario_fontes.csv`.

**Preservação:** o inventário, os JSON do CKAN, o registro de downloads e a cobertura anteriores estão em
`manifestos/historico/antes_consolidado_2026-10-29/` (com `SHA256SUMS`); as reconciliações anteriores em
`resultados/historico/antes_consolidado_2026-10-29/`; os Parquets substituídos e os zips munzona antigos em
`dados/…/historico/` (fora do Git, com `SHA256SUMS`).

## 2. Seção a seção (499.207 seções)

| comparação | seções | divergências de votos | observação |
|---|---|---|---|
| A. BU em CSV × BU binário coletado no Portal (assinado; hash publicado = SHA-256 do `vsc`) | 499.207 | **0** | aptos, comparecimento, abstenções, válidos, brancos, nulos, 13, 22 e votos por candidato |
| B. BU em CSV × resultado oficial por seção (Detalhe + Votação por seção) | 499.207 | **0** | mesmos campos; **local de votação difere em 7.315 seções** (metadado, ver §4) |
| B'. BU em CSV × Votação nominal e Detalhe por município/zona (B4, B5) | 6.292 zonas | **0** | B5: 40 zonas com seções não instaladas, explicadas |
| C. BU em CSV × pacotes de totalização | — | — | pacotes do 2º turno não publicados nos Dados Abertos; a comparação A usa os mesmos arquivos obtidos no Portal |
| D. BU em CSV × log (votos computados) | 499.177 com log | 6 seções (54 votos) | lacunas de registro no log, já conhecidas (§3) |

Totais do BU em CSV = totais oficiais: comparecimento 128.236.074; 13: 64.256.232; 22: 59.826.041; brancos
1.430.496; nulos 2.723.305. **Nenhuma divergência altera totalizações.**

Hashes e assinaturas: verificamos SHA-512 oficial dos 28 BU em CSV e, para os arquivos de urna, a cadeia
hash publicado → `vota.vsc` → SHA-512 do BU e do log. **Não** validamos criptograficamente as assinaturas digitais
(exigem as chaves públicas do TSE).

Arquivos: `resumo_bu_csv_x_fontes_anteriores.csv`, `divergencias_bu_csv_x_fontes_anteriores.csv` e
`divergencias_reconciliacao_2t.csv` (UF, município, zona, seção, campo, valor de cada fonte e explicação).

### Campos que só o BU em CSV traz × log da urna

| teste | resultado (499.177 seções com log) | explicadas | pendentes |
|---|---|---|---|
| E1 abertura no BU × primeira "Urna pronta" no log | 499.149 até 2 s; 11 com diferença > 60 s | 6 (urna de reserva: o log publicado é o da reserva) | 5 (RJ 60011/191/45, CE 15296/11/258, PE 23370/35/45, SP 71072/420/322, PE 23515/54/3) |
| E2 encerramento no BU × "encerramento confirmado" no log | 499.169 até 2 s | 1 (urna de reserva encerrou a seção) | 5 (MG 46256/131/46, CE 13897/82/490, SC 83593/8/143, ZZ 30961/1/3869, RS 89630/72/54) |
| E3 urna efetivada no BU entre as urnas do log | 499.176 | 1 (ES 57932/9/112, `reservaEncerrandoSecao`) | 0 |

O BU binário assinado registra o tipo de urna: `secao` 493.464, **`reservaSecao` 5.712**, `contingencia` 29,
`reservaEncerrandoSecao` 2 (`tipos_de_urna_bu_binario_2t.csv`). O BU em CSV marca todas como "Apurada".

## 3. Pendências anteriores revisitadas

| caso | com o BU consolidado |
|---|---|
| 6 seções / 54 votos sem "voto computado" no log | **inalterado**: BU em CSV = BU binário = oficial; a lacuna é do log. MA 8893/47/609: BU registra abertura 08:00:01, log publicado só a partir de 10:57 (urna de reserva `reservaSecao`; o anexo do log é de urna carregada para a seção 445). BA 35653/173/235: abertura 08:48:54 no BU, log a partir de 10:10 (reserva). Os resíduos de biometria (B6, B8) concentram-se nessas mesmas seções. |
| SP 64777/395/298 sem log | BU em CSV confirma seção normal (268 votantes, encerramento 17:03:46); **log continua não publicado** em 29/10 (aux.json lista só bu, rdv e vota). |
| 29 seções do exterior pelo Sistema de Apuração | presentes no BU em CSV, com os mesmos votos; o BU binário as classifica como `contingencia`; não há log por natureza. |
| 2 seções do exterior sem votantes (ZZ 29564/1/91 e 30686/1/443) | presentes no BU em CSV numa linha `#NULO#` (cargo −1); **corrigida a conversão**, que as descartava. No **1º turno** a seção ZZ 29564/1/91 não aparece no CSV — continua pendente. |
| Classificação biométrica (B8: 5 + 3 + 1) | inalterada; concentrada nas seções com log incompleto. |
| Substituição de urna | agora quantificada pelo BU assinado (5.712 reservas, 2 encerramentos por reserva). |

## 4. O que mudou em relação às auditorias anteriores

- Fonte principal do 2º turno: **BU em CSV consolidado** (antes: Detalhe + Votação por seção). Valores de votos
  idênticos em todas as seções; análises de horário e triagem não mudam de resultado.
- Executados os 6 testes antes "Não verificados" (B1–B5, K1): sem divergência de votos.
- Nova divergência de **metadado**: código do local de votação difere entre BU em CSV e Detalhe por seção em 7.315
  seções no 2º turno e 7.002 no 1º; no BU em CSV o local do 2º turno é igual ao do 1º em todas as seções, no Detalhe
  muda em 431. As análises por local de votação continuam usando o Detalhe por seção.
- Conversão do BU em CSV corrigida para manter seções sem votantes (+2 seções, +102 aptos no exterior).

## 5. Cronologia de publicação (2022 × 2026)

Arquivo: `resultados/comparativo/cronologia_publicacao.csv`. Datas em UTC.

| arquivo | eleição | geração (nome) | Last-Modified | criação no CKAN | dias até CKAN |
|---|---|---|---|---|---|
| BU em CSV, 2º turno 2022 | 30/10 | 31/10 15:35 | 31/10 19:06 | 01/11 18:13 | 2,8 |
| BU em CSV, 2º turno 2026 | 25/10 | 26/10 07:42 | 26/10 11:59–19:49 | 27/10 18:59 (RR fora do CKAN) | 2,8 |
| BU em CSV, 1º turno 2022 / 2026 | 02/10 / 04/10 | 05/10 / 05/10 | 05/10 / 06/10 | 05/10 / 06/10 | 3,9 / 2,8 |
| Arquivos transmitidos, 2º turno 2022 | 30/10 | — | 02/11 21:41 | 02/11 21:46 | 3,9 |
| Arquivos transmitidos, 2º turno 2026 | 25/10 | — | — | **não publicado** até 29/10 14:21 (≥ 4,6 dias) | — |
| Arquivos de urna no Portal, 2º turno 2026 | 25/10 | versões de 25/10 17:04 a 27/10 14:56 (hora do portal) | aux.json 25/10 20:04 a 27/10 17:56 | — | coletados por nós em 27/10 |

- O BU em CSV do 2º turno saiu com o **mesmo intervalo** de 2022 (2,8 dias até o CKAN; o arquivo existia no servidor
  1,5 dia após a eleição). Nosso inventário de 26/10 23:25 UTC ainda não o listava no CKAN.
- Os pacotes de arquivos transmitidos do 2º turno de 2026 **estão mais atrasados** que os de 2022; os mesmos arquivos
  estavam acessíveis seção a seção no Portal de Resultados desde a noite da eleição.
- No Portal, 10.893 seções tinham, na nossa coleta, versão "Recebido" (não "Totalizado"), 2.044 delas recebidas em
  26–27/10; seus BUs coincidem com o BU em CSV gerado em 26/10 07:42 e com o resultado oficial.
- Pacotes do 1º turno de 2026: listados no CKAN em 06/10, mas a versão vigente (a que processamos) tem
  Last-Modified de 22/10. **Não temos cópia anterior**: não é possível dizer se houve versão diferente antes.
- As tabelas por município/zona foram republicadas em 28–29/10 com o 2º turno; o **conteúdo do 1º turno é idêntico**
  ao da versão anterior preservada (6.292 e 75.504 linhas sem diferença).
- Uma consulta ao CKAN às 14:18:50 UTC retornou a versão antiga do conjunto (56 recursos, sem o 2º turno); 90
  consultas seguintes retornaram a vigente (registro em `manifestos/historico/`). Atribuído a cache, sem inferência.

Demora de publicação não é, por si, indício de irregularidade.

## 6. Afirmações externas

Arquivo: `resultados/2026/consolidado_2t/afirmacoes_externas_confronto.csv` (22 linhas, cálculos refeitos).

- **Confirmadas:** CNN/setup.news — 34.330 votos a partir das 17h, 29.001 nos 5 primeiros minutos, 1.993 após 18h,
  11 após 19h, 468.043 urnas sem voto após 17h (468.042); Agnoletto — 497.896 urnas com log e taxas de habilitação
  manual por modelo (±0,2 p.p.); destaque anterior do painel (SP, 57,12%).
- **Dependentes de definição ou cobertura:** CNN 497.895 urnas; Agnoletto 31.060 votos após encerramento previsto,
  2.512 manuais, 7.577 urnas às 19h, mediana de 10 s; painel auditoriaeleicoes.com — seções com mais de 90% e 100%
  (universo do painel é 210 seções menor) e diferença BU × oficial em MG e no exterior no 1º turno (o painel soma só
  seções com arquivo de urna).
- **Contrariada:** inconsistência entre BU e resultado oficial no 2º turno — 0 divergências em 499.207 seções.
- **Não verificáveis:** kakaroto.dev (fora do ar, sem código) e o relatório com recortes 17h01–17h15/17h16–18h59
  (valores não fornecidos).

## 7. Pendências

Logs ausentes ou incompletos (MA 609, BA 235, RS 191, BA 178, PB 254, PI 216; SP 64777/395/298), 5 + 5 seções de
E1/E2 sem substituição de urna registrada, B8 residual, seção ZZ 29564/1/91 ausente do BU em CSV do 1º turno, pacotes
de arquivos transmitidos do 2º turno e assinatura digital criptográfica — todas dependem de documentos ou arquivos
que o TSE ainda não publicou (atas, relatórios de contingência, pacotes).
