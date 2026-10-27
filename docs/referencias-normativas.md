# Referências técnicas e legais: auditoria dos dados abertos (Eleições 2022 e 2026)

Data de acesso de todas as fontes: **26/10/2026**.
Diretório base: `(área temporária da pesquisa)/`

Legenda de confiabilidade:
- **[VERIFICADO]**: conferido diretamente em arquivo oficial baixado (TSE/CDN, Planalto, DJE) ou em cópia fiel de texto oficial.
- **[VERIFICADO-ESPELHO]**: texto oficial obtido de cópia de terceiro (o original no tse.jus.br não pôde ser acessado).
- **[EMPÍRICO]**: inferido dos próprios dados oficiais (contagens e cruzamentos feitos nesta sessão).
- **[INCERTO]**: fonte secundária (imprensa, terceiros) ou não confirmada.

> **Limitação de acesso.** Os portais Plone da Justiça Eleitoral (`www.tse.jus.br`, `sintse.tse.jus.br`, `www.tre-*.jus.br`, `www.justicaeleitoral.jus.br`) responderam **HTTP 403** a este ambiente, tanto por curl quanto por WebFetch, e não tentei contornar o bloqueio. `cdn.tse.jus.br`, `dadosabertos.tse.jus.br` e `resultados.tse.jus.br` funcionaram normalmente. O `planalto.gov.br` só respondeu via WebFetch.

---

## 1. Especificação ASN.1 dos arquivos da urna (BU, RDV, assinatura/VSCMR)

### 1.1 Fonte oficial
- Página oficial (2022): https://www.tse.jus.br/eleicoes/eleicoes-2022/documentacao-tecnica-do-software-da-urna-eletronica (**403 neste ambiente**). Segundo o snippet do buscador, a página traz um ZIP com a "especificação ASN.1 dos arquivos de boletim de urna (BU), registro digital do voto (RDV) e assinatura digital dos arquivos gravados na mídia de resultados", com "scripts Python de exemplo". Traz também um PDF com a especificação dos arquivos de log e o ZIP de hashes SHA-512 das chaves públicas do QR Code do BU. **[INCERTO: conteúdo descrito pelo buscador, não visto]**
- O README do projeto TSEParser informa que a mesma documentação foi publicada pelo TRE-MT: https://www.tre-mt.jus.br/eleicoes/eleicoes-2022/documentacao-tecnica-do-software-da-urna-eletronica (também **403**).
- **O ZIP oficial não foi baixado.** Os arquivos abaixo vêm de **espelhos no GitHub**, obtidos por raw.githubusercontent.com.

### 1.2 Arquivos baixados (espelhos) **[VERIFICADO-ESPELHO]**
Dois espelhos independentes (danarrib/TSEParser e alissonlinneker/DataUrnas-BR `spec/v1`) têm **hashes SHA-256 idênticos** para os três arquivos da especificação de 2022:

| Arquivo | SHA-256 | Caminhos |
|---|---|---|
| bu.asn1 (2022) | `9d37fca5be4ee5a8f57302fae3e5a17c7be89adc643e8edad10e9fc4a5f8f438` | `espelho_2022_danarrib_TSEParser/spec/bu.asn1`, `espelho_alissonlinneker_v1/bu.asn1`, `espelho_2026_juliosaulo/bu.asn1` |
| rdv.asn1 (2022) | `4512b49bf7ab8a8e7f4294dda1eb3a6b47e00975270ec3f4ffe7b0738c3dc70e` | idem |
| assinatura.asn1 (2022) | `b5e2718d3657f06cec1fc0c10644a038d2db09290a73963454f6de839493e1c2` | idem |
| bu.asn1 (v2, "2024 em diante") | `e53e28e9812bb7e19cc4bcc77b6ce48f25c413f62a60369a91c4f269e19b7ed6` | `espelho_alissonlinneker_v2/bu.asn1` |
| rdv.asn1 (v2) | `282dcde0c7ba1f1bb128fe27443ad8d18f7490416c9546d033910a7ec557a465` | `espelho_alissonlinneker_v2/rdv.asn1` |
| assinatura.asn1 (v2) | `66dfa7bcb79f31b2d6a4d1427dc0e1d1b7134aba83fb62c496713a4ac2c7e083` | `espelho_alissonlinneker_v2/assinatura.asn1` |

Scripts Python de exemplo (espelho TSEParser, pasta `TSE_Docs/python`): `bu_dump.py`, `rdv_dump.py` e `assinatura_dump.py`, todos **não executados**. Usam `asn1tools`.
- Testei também `validacao.py`, `dump_bu.py` e `vscmr_dump.py`: **404** nesse espelho. Não confirmei se existem no ZIP oficial. **[INCERTO]**

URLs dos espelhos:
- https://raw.githubusercontent.com/danarrib/TSEParser/master/TSE_Docs/spec/{bu,rdv,assinatura}.asn1 e .../TSE_Docs/python/{bu_dump,rdv_dump,assinatura_dump}.py
- https://raw.githubusercontent.com/alissonlinneker/DataUrnas-BR/main/spec/{v1,v2}/{bu,rdv,assinatura}.asn1
- https://raw.githubusercontent.com/juliosaulo/como-meus-vizinhos-votam/main/coleta_2026/referencia_tse/extraido/spec/*.asn1. Apesar do nome "2026", o conteúdo é **idêntico ao de 2022**. **[INCERTO: rótulo do repositório]**

### 1.3 Conteúdo relevante (2022, `bu.asn1`, módulo `ModuloBU DEFINITIONS IMPLICIT TAGS`)
Trecho de `EntidadeBoletimUrna` (linhas 153–165):
```
dataHoraEmissao             DataHoraJE,  -- Data e hora da emissão do boletim de urna.
qtdEleitoresLibCodigo       [1] QtdEleitores OPTIONAL, -- Quantidade de eleitores que compareceram que foram habilitados manualmente.
qtdEleitoresCompBiometrico  [2] QtdEleitores OPTIONAL, -- Quantidade de eleitores que compareceram que utilizaram biometria.
```
- `dataHoraAbertura`: "Data e hora do início da aquisição do voto (Primeiro voto) ... (YYYYMMDDThhmmss)". `dataHoraEncerramento`: "Data e hora do término da aquisição do voto (Último voto)".
- `TipoUrna ::= ENUMERATED { secao(1), contingencia(3), reservaSecao(4), reservaEncerrandoSecao(6) }`. O valor 6 é a "Barriga de aluguel para seção".
- `assinatura.asn1` (2022): `ModeloUrna ::= ENUMERATED { ue2009(9), ue2010(10), ue2011(11), ue2013(13), ue2015(15), ue2020(20) }`.

Mudanças no v2 (2024 em diante, provável formato de 2026):
- `qtdEleitoresCompareceram` passa a ser campo obrigatório.
- Novo `DetalhamentoComparecimento { qtdEleitoresCompareceramSemBiometria, qtdEleitoresHabilitadosPorBiometria, qtdEleitoresHabilitadosPorBiografia }`. A última grandeza é descrita como "que tinham biometria cadastrada e que foram habilitados por ano de nascimento".
- Os campos `qtdEleitoresLibCodigo` e `qtdEleitoresCompBiometrico` foram removidos.
- O enum de modelos passa a se chamar `ModeloEquipamento` e inclui `ue2022(22)`, `tpm12` e `tpm20`.
- Novo `IdentificadorGeradorMidia`.
- `qtdEleitoresAptos = qtdEleitoresAptosSecao + qtdEleitoresAptosTTE`.

Segundo o README do DataUrnas-BR, em 2026 os arquivos de urna são `-bu.dat`/`-busa.dat` e `-vota.vsc`. Em 2022 eram `.bu`, `.rdv`, `.logjez`, `.imgbu` e `.vscmr`. **[INCERTO]**

---

## 2. Horário de votação (8h–17h, horário de Brasília) e senhas

### 2.1 Eleições 2022
**Res.-TSE nº 23.674/2021 (Calendário Eleitoral 2022), art. 2º** **[VERIFICADO-ESPELHO]**
> "Art. 2º Nas Eleições 2022, no dia da eleição, todas as unidades da federação, sem exceção, observarão o mesmo horário oficial de Brasília."

O Anexo I, em "2 de outubro – domingo", diz: "Às 8 horas – 1.3. Início da votação (Código Eleitoral, art. 144)"; "Às 17 horas – 1.4. Encerramento da votação (Código Eleitoral, arts. 144 e 153)".
- Fonte oficial: https://www.tse.jus.br/legislacao/compilada/res/2021/resolucao-no-23-674-de-16-de-dezembro-de-2021 (403).
- Cópia usada: https://portal.varzeapaulista.sp.gov.br/wp-content/uploads/2022/06/RESOLUCAO-No-23.674-2021-CALENDARIO-ELEICOES-2022-TSE.pdf (impressão do portal do TSE em 27/06/2022).
- **Observação:** a unificação de fuso está na resolução do **calendário**, e não na Res. 23.669. Busquei "Brasília" na Res. 23.669: ela só aparece no art. 98, § 1º (correspondências esperadas até as 16h) e na regra de divulgação dos resultados.

**Res.-TSE nº 23.669/2021 (atos gerais, Eleições 2022)** **[VERIFICADO-ESPELHO]**
- Cópia usada: https://www.mpce.mp.br/wp-content/uploads/2022/09/RESOLUCAO-No-23.669-DE-14-DE-DEZEMBRO-DE-2021.-%E2%80%94-Tribunal-Superior-Eleitoral.pdf (impressão do texto compilado do TSE em 19/09/2022).
- Original: https://www.tse.jus.br/legislacao/compilada/res/2021/resolucao-no-23-669-de-14-de-dezembro-de-2021

Textos:
- **Art. 109**: "O(A) presidente da mesa receptora de votos, às 8 horas, declarará iniciada a votação (Código Eleitoral, arts. 143 e 144)."
- **Art. 136**: "O recebimento dos votos terminará às 17 horas, desde que não haja eleitoras ou eleitores presentes na fila de votação da seção eleitoral (Código Eleitoral, art. 144)."
  - "§ 1º Havendo eleitoras ou eleitores na fila, a mesário ou o mesário procederá à sua identificação e entregará a respectiva senha, começando pelo último da fila, para que sejam admitidos(as) a votar (Código Eleitoral, art. 153, caput)."
  - "§ 2º A votação continuará na ordem decrescente das senhas distribuídas até a última eleitora ou eleitor votar (Código Eleitoral, art. 153, parágrafo único)."
- Atribuições da mesa: "IV - distribuir às eleitoras e aos eleitores, às 17 horas, as senhas de acesso à seção eleitoral, previamente rubricadas ou carimbadas". Material da seção: "VI - senhas a serem distribuídas às eleitoras e aos eleitores após as 17 horas".
- **Art. 143**: "As mesas receptoras de justificativas funcionarão das 8 às 17 horas do dia da eleição."
- **Art. 68**: no exterior, "será observado o horário local".

### 2.2 Eleições 2026
**Res.-TSE nº 23.751, de 26/02/2026 (atos gerais, Eleições 2026)** **[VERIFICADO-ESPELHO]**
- Texto original, conforme o DJE/TSE nº 30 de 03/03/2026, pp. 170 e seguintes. Cópia: https://static.poder360.com.br/2026/03/Atos-gerais-da-eleicao-TSE-.pdf
- A resolução foi **alterada pela Res. 23.767/2026**, de 03/08/2026, que não li. Compilada: https://www.tse.jus.br/legislacao/compilada/res/2026/resolucao-no-23-751-de-26-de-fevereiro-de-2026 (403).

Textos:
- **Art. 121**: "No dia marcado para a votação, às 7h (sete horas) do horário de Brasília, as(os) componentes da Mesa Receptora verificarão (Código Eleitoral, art. 142): ..."
- **Art. 129**: "A(O) Presidente da Mesa Receptora de Votos, às 8h (oito horas), horário de Brasília, declarará iniciada a votação (Código Eleitoral, arts. 143 e 144)."
- **Art. 160**: "O recebimento dos votos terminará às 17h (dezessete horas), horário de Brasília, desde que não haja eleitoras ou eleitores presentes na fila de votação da seção eleitoral (Código Eleitoral, art. 144)."
  - "§ 1º As 2 (duas) últimas pessoas a votar serão convidadas a acompanhar os procedimentos de encerramento da seção eleitoral e receberão o boletim de urna, ..."
  - "§ 2º Havendo eleitoras ou eleitores na fila, a mesária ou o mesário procederá à sua identificação e entregará a respectiva senha, começando pela(o) última(o) da fila, para que sejam admitidas(os) a votar (Código Eleitoral, art. 153, caput)."
  - "§ 3º A votação continuará na ordem decrescente das senhas distribuídas até que a última eleitora ou o último eleitor vote (Código Eleitoral, art. 153, parágrafo único)."
- **Art. 167**: as Mesas Receptoras de Justificativa funcionam das 8h às 17h.

**Res.-TSE nº 23.760/2026 (Calendário 2026)** **[VERIFICADO-ESPELHO]**
- Cópia do DJE: https://static.poder360.com.br/2026/03/calendario-tse.pdf
- Anexo I, dia da eleição: "A partir das 7 horas (horário de Brasília) ... Às 8 horas (horário de Brasília) 1.3. Início da votação ... Às 17 horas (horário de Brasília) 1.4. Encerramento da votação (Código Eleitoral, arts. 144 e 153)".
- Ao contrário de 2022, não há artigo autônomo de "mesmo horário oficial de Brasília": a regra vem embutida em cada horário.

**ATENÇÃO para o 2º turno de 2026 (25/10/2026)** **[INCERTO: só imprensa]**
- A imprensa noticiou que o Min. Cristiano Zanin (STF) **prorrogou a votação até as 19h** (horário de Brasília). Segundo as matérias, o alcance foi depois restrito às seções/locais com problemas de transporte, e o TSE pausou a totalização entre ~17h20 e 19h.
- Fontes: Gazeta do Povo (https://www.gazetadopovo.com.br/eleicoes/2026/tse-paralisa-apuracao-apos-zanin-prorrogar-votacao/), InfoMoney (https://www.infomoney.com.br/politica/tse-pausa-totalizacao-dos-votos-apos-zanin-prorrogar-votacao-ate-as-19h/), Exame (https://exame.com/brasil/apos-prorrogacao-tse-retoma-totalizacao-dos-votos-e-divulgacao-dos-resultados/).
- Petição do PT ao STF (Rcl, protocolo de 25/10/2026, 16:22) citando o art. 160 da Res. 23.751: https://static.poder360.com.br/uploads/2026/10/Extensao-Rcl-STF-Recibo_134182_2026.pdf
- **Não li a decisão em si.** Para auditar `DT_ENCERRAMENTO` do 2º turno de 2026, o limite das 17h **não** é válido sem antes verificar o escopo exato da decisão.

---

## 3. Habilitação sem reconhecimento biométrico

### 3.1 Eleições 2022 (Res. 23.669/2021) **[VERIFICADO-ESPELHO]**
**Art. 113**, incisos III–V:
> "III - não havendo dúvidas quanto à sua identidade, a mesário ou o mesário digitará o número do título no terminal; IV - aceito o número do título pelo sistema da urna, a mesária ou o mesário solicitará à eleitora ou ao eleitor que posicione o dedo polegar ou o indicador sobre o sensor biométrico, para habilitar a urna para a votação; V - havendo o reconhecimento da biometria, a mesário ou o mesário autorizará a eleitora ou o eleitor a votar, dispensando a assinatura no Caderno de Votação;"

> "§ 1º A leitura da biometria a que se refere o inciso IV do caput deste artigo poderá ser repetida por até 4 (quatro) vezes para cada tentativa de habilitação, observando-se as mensagens apresentadas no Terminal do Mesário."

**Art. 114**:
> "Na hipótese de não reconhecimento da biometria, após a última tentativa, o(a) presidente da mesa deverá conferir se o número do título digitado no Terminal do Mesário corresponde à inscrição da eleitora ou do eleitor e, se confirmado, indagará o ano do seu nascimento, digitando-o no Terminal do Mesário e:"
> - "I - se coincidente, autorizará a eleitora ou o eleitor a votar;"
> - "II - se não coincidente, em última tentativa, repetirá a pergunta quanto ao ano de nascimento e digitará no Terminal do Mesário;"
> - "III - se persistir a não identificação, a eleitora ou o eleitor será orientado(a) a contatar a Justiça Eleitoral para consultar sobre o ano de nascimento constante do Cadastro Eleitoral, para que proceda à nova tentativa de votação."
> - "§ 1º Comprovada a identidade, a eleitora ou o eleitor: I - assinará o Caderno de Votação ou premirá sua impressão digital, se não souber ou não puder assinar; II - será habilitado(a) a votar mediante a leitura da digital da mesária ou do mesário; e III - será orientado(a) a procurar posteriormente o cartório eleitoral para atualização de seus dados (Res.-TSE nº 23.659/2021, art. 8º, § 4º)."
> - "§ 2º As situações ocorridas neste artigo deverão ser consignadas na Ata da Mesa Receptora."

**Art. 115**:
> "A eleitora ou o eleitor que não possui dados biométricos na urna será identificado(a) conforme os incisos I a III do art. 113 desta Resolução e, aceito o número do título pelo sistema, assinará ou premirá sua digital no Caderno de Votação e será autorizado(a) a votar nos termos dos incisos VI e VII do mesmo artigo."

**Art. 178** (conteúdo do BU):
> "XII - a quantidade de eleitoras ou eleitores cuja habilitação para votar não ocorreu por reconhecimento biométrico; ... Parágrafo único. O inciso XII deste artigo aplica-se apenas às seções com biometria."

**"Código de liberação":** o termo **não aparece** no texto da Res. 23.669. O que a resolução prevê é a habilitação pelo ano de nascimento seguida da leitura da **digital do mesário**. No BU de 2022, isso corresponde a `qtdEleitoresLibCodigo` ("habilitados manualmente"). A equivalência entre esse campo e o procedimento do art. 114 é inferência minha. **[INCERTO]**

### 3.2 Eleições 2026 (Res. 23.751/2026, texto original) **[VERIFICADO-ESPELHO]**
**Art. 133**: o Presidente da Mesa digita o **CPF ou título** e confere a foto no Terminal do Mesário (incisos III–VII).
> "§ 2º A leitura da biometria ... poderá ser repetida por até 4 (quatro) vezes, observando-se as mensagens apresentadas no Terminal do Mesário."
> "§ 3º Não havendo êxito no reconhecimento da biometria, a(o) Presidente da Mesa deverá realizar nova tentativa depois de: I - conferir se o nome e o título eleitoral correspondem à pessoa, mediante nova digitação do número do CPF ou do título eleitoral; ou II - verificar, no Caderno de Votação, se a eleitora ou o eleitor foi devidamente localizado."

**Art. 134**:
> "Se a eleitora ou o eleitor não possuir biometria coletada, a habilitação para votar ocorrerá com a digitação do ano de seu nascimento, conforme informado pela própria pessoa. § 1º Caso o ano de nascimento digitado não seja aceito pela urna, a(o) Presidente da Mesa Receptora repetirá a pergunta ... § 2º Persistindo o não reconhecimento, ... contatar a Justiça Eleitoral ..."

**Art. 135**: mesmo fluxo do art. 114 de 2022, com a adição do § 2º ("impossibilidade de assinar"):
> "Na hipótese de não reconhecimento da biometria, após o procedimento descrito no § 3º do art. 133, a(o) Presidente da Mesa indagará o ano do nascimento ... § 1º Aceito o ano de nascimento pela urna, a eleitora ou o eleitor: I - assinará o Caderno de Votação ...; II - será habilitada(o) a votar mediante a leitura da digital da mesária ou do mesário; e III - será orientada(o) a procurar posteriormente o cartório eleitoral ..."

Relatório "Eleitores não Reconhecidos Biometricamente": a mesa o emite e o entrega junto com o material.

---

## 4. Dicionários de dados (leiame) **[VERIFICADO]**

### 4.1 Boletim de Urna – `bweb_<TURNO>_<UF>_<DATA_HORA_GERACAO>.zip`
- Dataset CKAN: https://dadosabertos.tse.jus.br/dataset/resultados-2022-boletim-de-urna
- Exemplo: https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2022/buweb/bweb_1t_AC_051020221321.zip. O SHA-512 bate com o arquivo `.zip.sha512` oficial.
- O leiame de 2022 é o `leiame-boletimurnaweb.pdf`, **datado de 18/11/2020**, e vem dentro do ZIP. Cópia em `dados_tse/leiames/bweb_2022_leiame.pdf` e `.txt`.

Definições literais do leiame de 2022:
- **QT_APTOS**: "Quantidade de eleitores aptos a votar naquele município, zona e seção."
- **QT_COMPARECIMENTO**: "Quantidade de eleitores que compareceram às eleições naquele município, zona e seção."
- **QT_ABSTENCOES**: "Quantidade de eleitores que não compareceram às eleições naquele município, zona e seção."
- **CD_TIPO_URNA**: "Código de identificação do tipo de urna." **DS_TIPO_URNA**: "Descrição de identificação do tipo de urna."
- **NR_URNA_EFETIVADA**: "Número da urna efetivada."
- **CD_CARGA_1_URNA_EFETIVADA** / **CD_CARGA_2_URNA_EFETIVADA**: "Código da Carga 1/2 da urna efetivada."
- **CD_FLASHCARD_URNA_EFETIVADA**: "Código do Flashcard de urna efetivada."
- **DT_CARGA_URNA_EFETIVADA**: "Data da carga da urna efetivada."
- **DT_BU_RECEBIDO**: "Data do boletim de urna recebido."
- **DT_ABERTURA**: "Data/hora de abertura da urna eletrônica para votação."
- **DT_ENCERRAMENTO**: "Data/hora de encerramento da urna eletrônica para votação."
- **QT_ELEITORES_BIOMETRIA_NH**: "Quantitativo de eleitores com biometria, mas que não foram habilitados por meio dela."
- **DT_EMISSAO_BU**: "Data/hora de emissão do boletim de urna (BU)."
- **NR_VOTAVEL**: 95 = branco, 96 = nulo, 97 = anulado e apurado em separado, 98 = anulado.
- Convenções: "#NULO" equivale a -1 e "#NE" a -3. Codificação "Latin 1", separador ";".

Leiame de 2026 (`_leiame-boletimurnaweb.pdf`, 06/10/2026):
- **CD_TIPO_URNA**: "Código do tipo de urna da urna efetivada. Pode assumir os valores: - 1: Apurada; - 2: Não apurada; - 3: Anulada e apurada em separado; - 4: Anulada; e - 5: Não instalada." Em 2022 o CSV também mostra `1`/`APURADA`. Portanto, **CD_TIPO_URNA no bweb é situação de apuração, e não modelo nem o `TipoUrna` do ASN.1**.
- **NR_URNA_EFETIVADA**: "Urna efetivada representa a urna que realmente foi utilizada na eleição ... podendo ser a urna original ou uma outra urna de contingência".
- **CD_CARGA_1_URNA_EFETIVADA**: "O conjunto dos primeiros 19 caracteres que compõe o código da carga original da urna." CD_CARGA_2: "últimos 6 caracteres".
- **QT_ELEI_BIOM_SEM_HABILITACAO** (nome novo de 2026): "Quantidade de eleitoras e eleitores com biometria, mas que não foram habilitados por meio dela."
- **DS_SECOES_AGREGADAS** substitui DS_AGREGADAS. Em 2026 as datas vêm no formato `AAAA-MM-DD hh:mm:ss`.
- **Não existe coluna `QT_ELEI_BIOM`** nos cabeçalhos de 2022 nem de 2026. Em 2022 o nome é `QT_ELEITORES_BIOMETRIA_NH`; em 2026, `QT_ELEI_BIOM_SEM_HABILITACAO`. **[VERIFICADO no cabeçalho dos CSVs]**

**Fuso dos campos de data no bweb** **[EMPÍRICO]**:
- `DT_ABERTURA`, `DT_ENCERRAMENTO` e `DT_EMISSAO_BU` estão no **horário local da urna**. No AC, por exemplo, a abertura é "02/10/2022 06:00:01", o que equivale a 08:00 em Brasília. Em Fernando de Noronha, 09:00:01.
- `DT_BU_RECEBIDO` está no **horário de Brasília**. Ele coincide exatamente com `DT_RECEBIMENTO_BU_HOR_TSE` ("Hora TSE") do detalhe_votacao_secao: seção AC 1392/1/3, 18:45:30.
- O leiame não declara nenhuma das duas coisas; trata-se de inferência.

### 4.2 detalhe_votacao_secao (2022)
- Fonte: https://cdn.tse.jus.br/estatistica/sead/odsele/detalhe_votacao_secao/detalhe_votacao_secao_2022.zip (leiame de 30/07/2026; CSVs regerados em 31/07/2026).
- Leiame salvo em `dados_tse/leiames/detalhe_votacao_secao_2022_leiame.txt`.
- QT_APTOS, QT_COMPARECIMENTO e QT_ABSTENCOES: definições iguais às do bweb, com redação inclusiva.
- **QT_VOTOS_ANULADOS_APU_SEP**: "Esse quantitativo reflete os votos oriundos de alguma urna que está sub judice."
- **DT_RECEBIMENTO_BU_HOR_TSE**: "Data e hora do recebimento do Boletim de Urna (Hora TSE)". **DT_PRIM_TOT_PARCIAL_HOR_TSE**: "Data e hora da primeira totalização parcial ... (Hora TSE)".
- **DS_ORIGEM_VOTO**: "U - Urna Eletrônica, T - Totalização, C - Sistema de apuração, R - BU gerado por RED em urna de seção e B - BU gerado por RED em urna de contingência. **RED - Recuperador de dados."
- **ST_SECAO_INSTALADA**, **ST_SECAO_ANULADA** (S/N).
- **CD_MODELO_URNA**: "Código do modelo da urna." **DS_MODELO_URNA**: "Descrição do modelo da urna." Valores: 2009/2010/2011/2013/2015/2020, ou -1.

### 4.3 votacao_secao (2022)
- Fonte: https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_secao/votacao_secao_2022_AC.zip (leiame de 22/06/2026). Salvo em `dados_tse/leiames/votacao_secao_2022_AC_leiame.txt`.
- Campos por votável: CD_CARGO, NR_VOTAVEL, NM_VOTAVEL e QT_VOTOS ("Quantidade de votos recebidos pelo votável naquele ...").
- **Não tem campos de biometria nem de horário.**

---

## 5. Fusos horários

### 5.1 Base legal **[VERIFICADO via WebFetch do planalto.gov.br]**
Decreto nº 2.784/1913, na redação da **Lei nº 12.876/2013**:
- **(a)** "o primeiro fuso, caracterizado pela hora de Greenwich 'menos duas horas', comprehende o archipelago Fernando de Noronha e a ilha da Trindade". Logo, **Fernando de Noronha (PE) está em UTC-2**.
- **(b)** UTC-3: DF e os estados enumerados (RS ... AP).
- **(c)** "o terceiro fuso, caracterizado pela hora de Greenwich 'menos quatro horas', compreende os Estados de Mato Grosso, de Mato Grosso do Sul, de Rondônia e de Roraima e a parte do Estado do Amazonas que fica a leste da linha que, partindo do Município de Tabatinga, no Estado do Amazonas, segue até o Município de Porto Acre, no Estado do Acre".
- **(e)** "o quarto fuso, caracterizado pela hora de Greenwich 'menos cinco horas', compreende: 1. o Estado do Acre; 2. a parte do Estado do Amazonas que fica a oeste da linha fixada na alínea 'c'".

Fontes:
- https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2013/lei/l12876.htm
- https://www.planalto.gov.br/ccivil_03/decreto/historicos/dpl/dpl2784-1913.htm

A lei define a fronteira por uma **linha geográfica**, e não por uma lista de municípios.

**Horário de verão:** o Decreto nº 9.772/2019, art. 1º, diz "Fica encerrada a hora de verão no território nacional" (https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2019/decreto/D9772.htm). Portanto, **não houve horário de verão em 2022**. **[VERIFICADO]**
- Para 2026, o JB de 05/10/2026 (https://www.jb.com.br/editorias/2026/10/05/horario-de-verao-2026.html) informa que o MME mantém o horário de verão suspenso para 2026/2027. **[INCERTO]**
- Indício empírico para 2026: no 1º turno, o AC abriu às 06:00:01 locais (bweb 2026), o que é consistente com UTC-5 contra UTC-3 em Brasília, sem horário de verão. **[EMPÍRICO]**

### 5.2 Municípios do AM em UTC-5 (votação das 6h às 15h locais)
A lista vem do TRE-AM (via imprensa) e foi **confirmada empiricamente** no bweb do 1º turno de 2022: são exatamente estes 11 municípios que têm DT_ABERTURA às 06h locais. Todos os outros 51 municípios do AM abriram às 07h. **[EMPÍRICO + INCERTO quanto à fonte primária]**

| Município (nome TSE) | CD_MUNICIPIO (TSE) |
|---|---|
| Amaturá | 02917 |
| Atalaia do Norte | 02054 |
| Benjamin Constant | 02135 |
| Eirunepé | 02291 |
| Envira | 02313 |
| Guajará | 02020 |
| Ipixuna | 02399 |
| Itamarati | 98370 |
| Jutaí | 02496 |
| São Paulo de Olivença | 02755 |
| Tabatinga | 98477 |

- Fontes: https://ac24horas.com/2026/09/26/eleicoes-2026-11-municipios-do-amazonas-terao-votacao-no-mesmo-horario-do-acre/ (cita Marcelo Sussuarana, TRE-AM) e https://aam.org.br/confira-os-horarios-de-votacao-nos-municipios-do-amazonas/ (02/10/2026).
- **Códigos IBGE não verificados** nesta sessão (o bweb traz apenas o código TSE).
- **Divergência com o IANA tzdata** (https://raw.githubusercontent.com/eggert/tz/main/southamerica):
  - O tzdata lista como "west Amazonas (America/Eirunepe)" Atalaia do Norte, Boca do Maoco, Benjamin Constant, Eirunepé, Envira e Ipixuna.
  - Lista como "east (America/Manaus)" Boca do Acre, **Jutaí**, Manaus e Floriano Peixoto.
  - Os dados da urna mostram Jutaí em UTC-5 e Boca do Acre, Pauini e Lábrea em UTC-4.
  - **Para a auditoria, use a lista acima, e não a zona IANA.**
- Demais UFs: **AC = UTC-5**. **RO, RR, MT, MS e o restante do AM = UTC-4**. Demais UFs e DF = UTC-3. **Fernando de Noronha = UTC-2**: o bweb PE 2022 mostra o município 30015 abrindo às 09:00 locais.

---

## 6. Totais nacionais – Presidente **[VERIFICADO]**

### 6.1 2022
Fontes:
- Histórico de totalização, linha final: https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2022/Historico_Totalizacao_Presidente_BR_1T_2022.zip e `..._2T_2022.zip`.
- Conferido com a soma de `detalhe_votacao_munzona_2022_BR.csv`: https://cdn.tse.jus.br/estatistica/sead/odsele/detalhe_votacao_munzona/detalhe_votacao_munzona_2022.zip

| | 1º turno (02/10/2022) | 2º turno (30/10/2022) |
|---|---:|---:|
| Eleitorado apto | 156.454.011 | 156.454.011 |
| Comparecimento | 123.682.372 | 124.252.796 |
| Abstenção (aptos − comparecimento) | 32.771.639 | 32.201.215 |
| Abstenção (campo QT_ABSTENCOES do munzona) | 32.770.982 | 32.200.558 |
| Votos válidos | 118.229.719 | 118.552.353 |
| Brancos | 1.964.779 | 1.769.678 |
| Nulos | 3.487.874 | 3.930.765 |
| Lula (13) | 57.259.504 (48,43%) | 60.345.999 (50,90%) |
| Jair Bolsonaro (22) | 51.072.345 (43,20%) | 58.206.354 (49,10%) |

- A diferença de 657 na abstenção corresponde a `QT_ELEITORES_SECOES_NAO_INSTALADAS` (47 seções não instaladas).
- Seções: 472.075 principais e 24.163 agregadas.
- Última totalização: 1º turno em 04/10/2022 10:27:34; 2º turno em 31/10/2022 00:18:04.
- Conferência: válidos + brancos + nulos = comparecimento nos dois turnos.

### 6.2 2026 – 1º turno (04/10/2026)
Fontes:
- Relatório Resultado da Totalização (SISTOT, "Oficial", emitido em 07/10/2026 16:37): https://cdn.tse.jus.br/estatistica/sead/odsele/relatorio_resultado_totalizacao/Relatorio_Resultado_Totalizacao_2026_BR.zip
- JSON https://resultados.tse.jus.br/oficial/ele2026/6257/dados/br/br-c0001-e006257-u.json
- Soma do detalhe_votacao_munzona_2026: valores idênticos.

Resumo:
- Aptos: **158.745.502**.
- Comparecimento: **125.275.835** (78,92%).
- Abstenção: **33.469.244** (21,08%).
- Válidos: **119.300.788**.
- Brancos: **2.300.798**.
- Nulos: **3.674.249**, sendo 3.669.003 na urna e **5.246 nulos técnicos**.
- Seções: 499.207 principais funcionaram (499.176 em urna eletrônica e 31 pelo Sistema de Apuração) e 41 não foram instaladas.

| Candidato | Votos | % válidos | Situação |
|---|---:|---:|---|
| 22 Flávio Nantes Bolsonaro (PL) | 56.104.503 | 47,03 | 2º turno |
| 13 Luiz Inácio Lula da Silva (PT) | 53.879.538 | 45,16 | 2º turno |
| 70 Augusto Jorge Cury | 3.448.569 | 2,89 | Não eleito |
| 14 Renan Antonio Ferreira dos Santos | 2.675.887 | 2,24 | Não eleito |
| 55 Ronaldo Ramos Caiado (PSD) | 2.605.148 | 2,18 | Não eleito |
| 30 Romeu Zema Neto | 326.488 | 0,27 | Não eleito |
| 80 Samara Martins da Silva Feitosa | 122.911 | 0,10 | Não eleito |
| 16 Hertz da Conceição Dias | 43.103 | 0,04 | Não eleito |
| 27 Clariana Zacarkim Barão | 40.043 | 0,03 | Não eleito |
| 21 Edmilson Silva Costa | 22.693 | 0,02 | Não eleito |
| 35 Wilson Grassi Junior | 16.881 | 0,01 | Não eleito |
| 29 Rui Costa Pimenta | 15.024 | 0,01 | Não eleito |

A soma dos candidatos dá 119.300.788, igual ao total de válidos.

### 6.3 2026 – 2º turno (25/10/2026)
Fonte: https://resultados.tse.jus.br/oficial/ele2026/6258/dados/br/br-c0001-e006258-u.json. Campos: `"f":"o"` (oficial), `"tf":"s"` (totalização finalizada), gerado em 25/10/2026 23:27:02.
- Seções totalizadas: 499.248/499.248 (100%).
- Aptos: 158.745.502.
- Comparecimento: **128.236.074** (80,78%).
- Abstenção: **30.509.005**.
- Válidos: **124.082.273**.
- Brancos: **1.430.496**.
- Nulos: **2.723.305**.
- **Lula: 64.256.232 (51,79%), "Eleito".**
- **Flávio Bolsonaro: 59.826.041 (48,21%), "Não eleito".**

Status:
- O resultado foi divulgado no portal Resultados.
- O Relatório de Totalização (PDF) do 2º turno e os bweb do 2º turno **ainda não constavam do CKAN** em 26/10/2026. O pacote `resultados-2026-boletim-de-urna` só tem o 1º turno.
- Imprensa: houve a prorrogação de horário por decisão do STF (seção 2.2), e Flávio Bolsonaro anunciou que pedirá a anulação. **[INCERTO]**
- A diplomação não foi verificada.

---

## 7. Modelos de urna e identificação no log

### 7.1 Modelos de urna 2022 (detalhe_votacao_secao_2022, cargo Presidente, por seção principal) **[VERIFICADO/EMPÍRICO]**

| Modelo | 1º turno | 2º turno |
|---|---:|---:|
| UE2009 | 46.020 | 47.011 |
| UE2010 | 93.839 | 92.840 |
| UE2011 | 27.279 | 26.440 |
| UE2013 | 24.810 | 24.300 |
| UE2015 | 85.631 | 85.314 |
| UE2020 | 192.563 | 192.499 |
| #NULO# (-1) | 1.933 | 3.671 |
| **Total** | 472.075 | 472.075 |

Origem do voto no 1º turno:

| Origem | Seções |
|---|---:|
| Urna eletrônica | 471.774 |
| Sistema de Apuração | 116 |
| RED em urna de seção | 126 |
| RED em contingência | 8 |
| Totalização | 51 |

O enum ASN.1 de 2022 (`ModeloUrna`) contém ue2009, ue2010, ue2011, ue2013, ue2015 e ue2020. O de 2024+ (`ModeloEquipamento`) acrescenta ue2022.

### 7.2 Identificação no log **[INCERTO: fonte secundária]**
Fonte: USP/UFSCar/UFPA, "Considerações sobre os logs das urnas eletrônicas brasileiras usadas nas eleições de 2022", 14/12/2022 (https://jornal.usp.br/wp-content/uploads/2022/12/Analise-Bug04030201_USPUFSCarUFPAoutros.pdf).
- Sobre o modelo: "a informação do modelo de urna pode ser obtida diretamente do próprio log da urna, buscando pelas palavras 'Identificação do Modelo de Urna'".
- Formato da linha de log: `DD/MM/AAAA hh:mm:ss NÍVEL ID_UE APLICAÇÃO Mensagem HASH`. Exemplo: `02/10/2022 11:11:22 INFO 67305985 VOTA Voto confirmado para [Deputado Estadual] ...`.
- Nos modelos anteriores à UE2020, o ID_UE aparece com o valor fixo "67305985" (0x04030201).
- **Não verifiquei o formato exato da linha** (por exemplo, "Identificação do Modelo de Urna: UE2020" ou "UEN..."). Não havia log de 2022 acessível: os caminhos antigos do resultados.tse.jus.br retornam 404, e não há ferramenta 7z neste ambiente.
- O **catálogo oficial de mensagens de log** (PDF "especificação dos arquivos de log", na mesma página de documentação técnica de 2022) **não foi obtido** (403).

---

## 8. Inventário de arquivos baixados
Diretório base: `(área temporária da pesquisa)/`

- `espelho_2022_danarrib_TSEParser/spec/{bu,rdv,assinatura}.asn1` e `python/{bu_dump,rdv_dump,assinatura_dump}.py` (não executados)
- `espelho_alissonlinneker_v1/` (= 2022) e `espelho_alissonlinneker_v2/` (2024+)
- `espelho_2026_juliosaulo/` (idêntico a 2022)
- `dados_tse/*.zip`:
  - bweb AC/AM/PE 1T 2022 e bweb AC 1T 2026, com SHA-512 conferido contra os `.sha512` oficiais para AC22, AM22 e AC26
  - detalhe_votacao_secao_2022, detalhe_votacao_munzona_2022/2026, votacao_secao_2022_AC
  - Historico_Totalizacao_Presidente_BR_1T/2T_2022
  - Relatorio_Resultado_Totalizacao_2026_BR
- `dados_tse/leiames/*.pdf|.txt` (leiames extraídos e relatório PDF de 2026)
- `dados_tse/br-c0001-e006257-u.json`, `dados_tse/br-c0001-e006258-u.json`
- Textos legais (fora de tsedocs), em `(área temporária da pesquisa)/leg/`: `res23669.txt`, `res23674.txt`, `res23751_poder360.txt`, `calendario2026_poder360.txt` e `poder360_rcl.txt`
