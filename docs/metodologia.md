# Metodologia

Este documento descreve, de forma verificável, como cada número do Observatório é
produzido. Toda afirmação aqui corresponde a código em `observatorio/` e pode ser
reexecutada (ver `README.md`, seção "Como reproduzir").

## 1. Princípios

1. **Fonte oficial primeiro.** Somente arquivos publicados pelo TSE (portal de dados
   abertos e CDN `cdn.tse.jus.br`). Estudos de terceiros são revisados, nunca copiados
   (`docs/auditoria-estudos-externos.md`).
2. **Sem hipótese escolhida a priori.** Os testes medem compatibilidade entre fontes e
   descrevem distribuições; nenhuma diferença estatística é tratada como prova.
3. **Ausente não é zero.** Campos são lidos como texto (`all_varchar`) e convertidos
   explicitamente. A única regra de "ausência = 0" usada é estrutural e testada: o BU
   relaciona apenas os votáveis que receberam votos; a identidade *comparecimento =
   nominais + brancos + nulos* (teste B1) confirma a regra em 100% das seções.
4. **Toda divergência é registrada.** `resultados/{ano}/incompatibilidades.csv` lista
   cada caso, inclusive os explicados, com a regra de explicação aplicada.
5. **Privacidade.** Logs contêm números de título de mesários; essas linhas não são
   extraídas nem publicadas. Nenhum horário é associado a voto em candidato (o log não
   permite e o RDV embaralha a ordem por desenho).

## 2. Fontes e integridade (Teste A)

- Descoberta: API CKAN (`package_show`) dos conjuntos listados em `observatorio/config.py`.
  Cada recurso recebe HEAD HTTP (tamanho, `ETag`, `Last-Modified`) →
  `manifestos/inventario_fontes.csv`. O `ETag` identifica a **versão** publicada; o TSE
  republicou várias tabelas em 2026 (ex.: `votacao_candidato_munzona_2022` em
  24/10/2026), o que fica registrado.
- Download (`observatorio/download.py`): retomável (`Range` + `If-Range`, validação de
  `Content-Range`), SHA-256 próprio, SHA-512 oficial quando o TSE publica `.sha512`
  (Boletins de Urna em CSV), teste de CRC de todos os membros do ZIP e rejeição de
  nomes inseguros. Registro de cada tentativa em `manifestos/downloads.csv`.
- Pacotes de arquivos de urna (≈ 263 GB no total): não são baixados inteiros. O
  diretório central do ZIP é lido por HTTP Range e, para cada seção, baixa-se apenas a
  faixa de bytes que contém `.bu` e `.logjez`; cada membro é conferido pelo CRC-32 do
  próprio ZIP (`observatorio/remotezip.py`). Seções com arquivos faltantes no pacote são
  contadas em `manifestos/cobertura_arquivos_urna.csv`.

## 3. Leitura dos arquivos

| Arquivo | Leitor | Observações |
|---|---|---|
| BU em CSV (`bweb_*`) | `bweb.py` | só Presidente (`CD_CARGO_PERGUNTA = 1`); pré-filtro por texto para não gravar CSVs de dezenas de GB |
| BU binário (`.bu` 2022; `-bu.dat` 2026) | `bu_asn1.py` | ASN.1/BER; especificação por ano em `especificacoes/` (procedência documentada) |
| Log (`.logjez`) | `logs.py` | 7z (2022) ou ZIP (2026); `.jez` aninhados abertos recursivamente |
| Tabelas de resultados/eleitorado | `oficiais.py` | detalhe por seção e por município/zona, votação nominal, votação por seção (arquivo "BR"), perfil por seção, seções agregadas, transferências temporárias |

### 3.1 Interpretação do log

Linha: `data hora <TAB> nível <TAB> id <TAB> aplicação <TAB> mensagem <TAB> verificação`.
Usam-se apenas linhas da data da eleição e do dia seguinte (votação após a meia-noite).
Eventos utilizados (texto exato da mensagem):

| Evento | Mensagem |
|---|---|
| abertura | `Urna pronta para receber votos` (primeira do dia; repetições = reabertura) |
| início do atendimento a um eleitor | `Título digitado pelo mesário` (2022) / `Identificador do eleitor digitado pelo mesário` (2026) |
| habilitação | `Eleitor foi habilitado` |
| voto concluído | `O voto do eleitor foi computado` |
| modalidade biométrica | `Tipo de habilitação do eleitor [biométrica]` |
| sem biometria cadastrada | `O eleitor não possui biometria` (2022) / `Ano de nascimento digitado é igual ao do cadastro` sem falha prévia (2026) |
| liberação manual após falha | `Solicitação de dado pessoal do eleitor para habilitação manual` |
| encerramento | `Inicio do Encerramento`; BU: `Gerando relatório [BU] [INÍCIO]`, `Gerando arquivo de resultado [.bu] + [Término]` |
| contingência | `Modo de carga da UE - Urna de contingência`, `Contingência executada com sucesso` |
| suspensões | `Eleitor foi suspenso pelo mesário`, `Eleitor votou parcialmente e em seguida foi suspenso`, `Eleitor foi suspenso e não confirmou nenhum voto` |

Regras de pareamento: a modalidade é a última indicação entre o início do atendimento e
`Eleitor foi habilitado`; o voto concluído seguinte é pareado com essa habilitação. Um
eleitor suspenso sem nenhum voto não compõe o comparecimento e desfaz o pareamento.
Cancelamentos intermediários (ex.: "Habilitação cancelada durante a captura de digital
do mesário") não zeram a modalidade — o fluxo segue no mesmo atendimento (verificado em
casos reais; ver histórico de commits).

**Seleção dos logs da própria seção.** Cada log declara, ao iniciar, `Município`,
`Zona Eleitoral` e `Seção Eleitoral`. O pacote de uma seção pode conter logs de outras
seções — por exemplo, quando uma urna de contingência do cartório (seção `0000`) foi
usada para recuperar resultados de várias seções cuja mídia falhou. São mantidos os logs
que declaram a seção-alvo, os de contingência (seção 0) do mesmo município/zona e os sem
identificação; os demais são listados em `log_arquivos_outras_secoes`.

**Validação empírica do leitor.** Em todas as seções em que o resultado veio da urna, o
número de `O voto do eleitor foi computado` é comparado ao comparecimento do BU, e a
contagem de liberações manuais ao campo `QT_ELEITORES_BIOMETRIA_NH` (Teste B6). No Acre
(1º turno, 2.124 seções), ambos conferem em 100% das seções.

## 4. Horários

O relógio da urna registra **hora local**. Em 2022 (Res.-TSE 23.674/2021, art. 2º) e 2026
(Res.-TSE 23.751/2026, arts. 129 e 160) a votação ocorre das 8h às 17h **de Brasília** em
todo o país; no exterior, das 8h às 17h locais (Res. 23.669/2021, art. 68).

- Conversão: `hora_Brasília = hora_local + (−3 − fuso)`, com fuso legal por UF (AC −5;
  AM, MT, MS, RO, RR −4; demais −3) e exceções municipais: 11 municípios do oeste do AM
  em −5 e Fernando de Noronha em −2 (`config.FUSO_MUNICIPIO`; base legal e fontes em
  `docs/referencias-normativas.md`, seção 5).
- Validação: para cada município, a hora local da mediana do primeiro voto deve indicar o
  mesmo fuso (`resultados/{ano}/validacao_fusos_municipio.csv`).
- Exterior: mantido em hora local; não entra nas contagens "antes das 8h de Brasília".
- Sem horário de verão em 2022 e 2026 (Decreto 9.772/2019).
- **Votar após as 17h não é irregular**: quem está na fila recebe senha e vota (Res.
  23.669/2021, art. 136, §§ 1º–2º). Reporta-se a distribuição, não um juízo.

Indicadores por seção (`temporal.py`): abertura, primeira/última habilitação, primeiro/
último voto, início do encerramento, geração do BU, votos e habilitações antes das 8h e
após 17h/18h/19h, intervalos entre votos consecutivos (mínimo, mediana, máximo, nº ≤ 5 s,
pausas ≥ 30 e ≥ 60 min), duração habilitação→voto, reaberturas, religamentos, retrocessos
do relógio dentro do mesmo arquivo de log.

**Intervalos curtos.** Não há tempo mínimo universal fundamentado: o tempo depende do
número de cargos (5 no 1º turno de 2022; 1–2 no 2º), da forma de identificação e do
eleitor. Por isso os limiares (5 s, 10 s) são descritivos, e as distribuições completas são
publicadas.

## 5. Contas e reconciliações (Testes B, C, G, H, K)

Identidades verificadas **por seção, mesmo cargo (Presidente), mesma base**:

- B1: `comparecimento = nominais + brancos + nulos`
- C1: `aptos = comparecimento + abstenções`
- C2: variação de aptos entre turnos = variação líquida das transferências temporárias
  (arquivo oficial "Transferência temporária do eleitorado por seção")
- H: `Δválidos = Δcomparecimento − Δ(brancos + nulos)` em cada nível (seção, zona,
  município, UF, Brasil)

Comparações entre fontes (todas registradas campo a campo):

| Teste | Fonte A | Fonte B | Nível |
|---|---|---|---|
| B2 | BU em CSV | BU binário transmitido pela urna | seção |
| B3 | BU em CSV | Detalhe da apuração por seção | seção |
| B4 | soma das seções | Votação nominal por município e zona | zona × candidato |
| B5 | soma das seções | Detalhe por município e zona | zona |
| B6 | BU em CSV | log da urna | seção |
| K1 | BU em CSV | Votação por seção (arquivo independente) | seção × votável |
| A2/A3 | presença da seção em cada fonte | | seção |

Uma divergência só é reclassificada como **Diferença explicada** quando há regra objetiva
e fonte (ex.: seção com `DS_ORIGEM_VOTO = Sistema de apuração`, seção não instalada,
campo opcional omitido no exterior por norma). As regras estão em
`reconciliacao.explicar()`.

## 6. Testes estatísticos (I, J)

- **Modelos de urna (I):** diferença entre seções UE2020 e demais, dentro do mesmo local
  de votação (controle mais forte), da mesma zona e do mesmo município; média ponderada
  por votos válidos; IC 95% por bootstrap de grupos (2.000 réplicas). Diferença
  controlada ≠ causa: a alocação de modelos não é aleatória.
- **Dígitos (J):** último dígito (contagens ≥ 50) e segundo dígito (≥ 10), contra (i) a
  referência teórica e (ii) uma referência **simulada** (binomial com o tamanho real da
  seção e a proporção do candidato na zona). Correção de Holm-Bonferroni sobre todos os
  testes; tamanho de efeito (V de Cramér e maior desvio em p.p.) sempre reportado.
  Benford de 2º dígito é apresentado apenas como descrição: seções têm tamanho limitado,
  o que viola a premissa da lei (Mebane 2006; Deckert et al. 2011).
- **Impressão digital** (Klimek et al. 2012): histograma 2D comparecimento × proporção
  do candidato, para inspeção visual.

Um valor-p pequeno, por si só, não é evidência de fraude.

## 7. Classificação das verificações

| Categoria | Uso |
|---|---|
| Conferido | cálculo reproduzido e igual às fontes examinadas |
| Diferença explicada | divergência com explicação documental verificável (regra + fonte) |
| Diferença estatística | afastamento de uma referência, sem incompatibilidade documental |
| Incompatibilidade documental | fontes que deveriam coincidir diferem, sem explicação ainda |
| Pendente | dados insuficientes ou processamento incompleto |
| Não reproduzido | teste de terceiros que não pôde ser reproduzido |

Nenhuma categoria equivale a prova de irregularidade.

## 8. Comparação 2022 × 2026

- Seções são pareadas por (UF, município, zona, seção) **e** classificadas: mesmo local
  de votação e aptos semelhantes (±10%) → "correspondência provável"; local diferente ou
  aptos muito diferentes → "mudou"; sem par → "sem correspondência". O mesmo número de
  seção não implica o mesmo eleitorado.
- Indicadores só são comparados quando têm a mesma definição nos dois anos; diferenças de
  definição estão em `docs/dicionario-dados.md`.
