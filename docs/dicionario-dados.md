# Dicionário de dados e diferenças entre anos

Definições literais dos leiames do TSE estão em `docs/referencias-normativas.md`
(seção 4). Aqui ficam (1) os campos usados, (2) o que muda entre 2022 e 2026 e (3) as
colunas produzidas pelo Observatório.

## 1. Campos de origem usados

### BU em CSV (`bweb_<turno>_<UF>_<geração>.zip`, latin-1, `;`)

| Campo | 2022 | 2026 | Uso |
|---|---|---|---|
| Cargo | `CD_CARGO_PERGUNTA` = 1 | igual | filtro Presidente |
| Aptos / comparecimento / abstenções | `QT_APTOS`, `QT_COMPARECIMENTO`, `QT_ABSTENCOES` | igual | B1, C1, G |
| Votos | `DS_TIPO_VOTAVEL` (Nominal/Branco/Nulo), `NR_VOTAVEL`, `QT_VOTOS` | igual | B1, H, J |
| Situação da urna | `CD_TIPO_URNA`/`DS_TIPO_URNA` (APURADA, ANULADA…) | "Apurada"… | **não é o modelo da urna** |
| Biometria não usada | `QT_ELEITORES_BIOMETRIA_NH` | `QT_ELEI_BIOM_SEM_HABILITACAO` | F, B2, B6 |
| Seções agregadas | `DS_AGREGADAS` | `DS_SECOES_AGREGADAS` | |
| Horários | `DT_ABERTURA`, `DT_ENCERRAMENTO`, `DT_EMISSAO_BU` em **hora local da urna**, formato `dd/mm/aaaa hh:mm:ss` | mesmos campos, formato `aaaa-mm-dd hh:mm:ss` | D |
| Recebimento | `DT_BU_RECEBIDO` em **hora de Brasília** (coincide com "Hora TSE" do detalhe por seção) | igual | D |
| Urna | `NR_URNA_EFETIVADA`, `CD_CARGA_1/2_URNA_EFETIVADA`, `CD_FLASHCARD_URNA_EFETIVADA` | igual | substituições |

Convenções: `#NULO`/`#NULO#` = −1, `#NE` = −3; valores negativos nunca são somados como
quantidade.

### BU binário (ASN.1)

| Conceito | 2022 (`bu.asn1` v1) | 2026 (`bu.asn1` v2) |
|---|---|---|
| comparecimento | `qtdComparecimento` por cargo | `qtdEleitoresCompareceram` + por cargo |
| identificação | `qtdEleitoresLibCodigo` ("habilitados manualmente"), `qtdEleitoresCompBiometrico` | `DetalhamentoComparecimento`: sem biometria cadastrada / habilitados por biometria / habilitados por biografia (tinham biometria e foram habilitados pelo ano de nascimento) |
| aptos | `qtdEleitoresAptos` | `qtdEleitoresAptos` = `AptosSecao` + `AptosTTE` |
| abertura/encerramento | `dadosSecao.dataHoraAbertura` = **primeiro voto**, `dataHoraEncerramento` = **último voto** (comentários da especificação) | igual |

`qtdEleitoresLibCodigo` (2022) e `qtdEleitoresHabilitadosPorBiografia` (2026) medem a
mesma coisa *conceitualmente* (eleitor com biometria cadastrada que votou sem
reconhecimento), mas o procedimento de 2026 inclui a identificação por CPF e a foto;
comparações entre anos levam isso em conta.

### Pacotes de arquivos de urna

| | 2022 | 2026 |
|---|---|---|
| nome | `o00406-MMMMMZZZZSSSS.bu`, `.logjez`, `.imgbu`, `.rdv`, `.vscmr` | `o03220ufMMMMMZZZZSSSS-bu.dat`, `-log.jez`, `-imgbu.dat`, `-rdv.dat`, `-vota.vsc` |
| log | 7z com `logd.dat` (+ `.jez` aninhados) | ZIP com `logd.dat` |
| identificação do eleitor no log | `Título digitado pelo mesário` | `Identificador do eleitor digitado pelo mesário` (título **ou CPF**) |
| sem biometria cadastrada | `O eleitor não possui biometria` | `Ano de nascimento digitado é igual ao do cadastro` (sem falha prévia) |
| cargos no 1º turno | 5 (DF, DE, SEN, GOV, PRES) | 6 votos (2 vagas de Senador) |

### Outras tabelas

- *Detalhe da apuração por seção*: `ST_SECAO_INSTALADA`, `ST_SECAO_ANULADA`,
  `DS_ORIGEM_VOTO` (Urna Eletrônica, Sistema de apuração, Totalização, BU gerado por RED),
  `DS_MODELO_URNA` (fonte do modelo para o Teste I).
- *Perfil do eleitorado por seção*: `QT_ELEITORES_PERFIL`, `QT_ELEITORES_BIOMETRIA`
  (cadastro; data de geração própria, não é o dia da eleição).
- *Transferência temporária por seção*: origem → destino, por turno e tipo (voto em
  trânsito, mesários/ofício, presos provisórios, militares, acessibilidade…).

## 2. Colunas produzidas (principais)

`dados/processados/logs/{ano}_{t}t_{UF}.parquet` — uma linha por seção:

| Coluna | Significado |
|---|---|
| `n_votos_computados` | nº de `O voto do eleitor foi computado` nos logs da seção |
| `n_habilitados` | nº de `Eleitor foi habilitado` |
| `hab_biometrica`, `hab_sem_biometria`, `hab_manual_apos_falha`, `hab_indeterminada` | habilitações por modalidade (indeterminada = sem etapa biométrica, ex. exterior) |
| `votos_s`, `hab_s` | segundos desde 00:00 (hora local) de cada voto/habilitação; +86400 para o dia seguinte |
| `dur_voto`, `dur_voto_mod` | duração habilitação→voto e modalidade do eleitor |
| `t_*_primeiro`, `t_*_ultimo` | primeiro/último horário de cada evento (hora local) |
| `log_modelos`, `log_versoes`, `log_n_ids_urna` | modelo(s), versão do software e identificadores no log |
| `log_arquivos_outras_secoes` | logs presentes no pacote que declaram outra seção |
| `log_retrocessos_relogio` | vezes em que o horário recua dentro do mesmo arquivo |

`resultados/{ano}/*.csv` — ver `README.md`, seção "Resultados".
