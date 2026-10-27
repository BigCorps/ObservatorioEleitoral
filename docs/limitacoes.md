# Limitações e pendências

_Atualizado em 27/10/2026 00:06 UTC._

## Cobertura do processamento dos arquivos de urna (logs + BU binário)

- 2022, 1º turno: 15/28 pacotes processados; faltam: BA, CE, GO, MA, MG, PA, PB, PE, PR, RJ, RS, SC, SP.
- 2022, 2º turno: 9/28 pacotes processados; faltam: AL, AM, BA, CE, ES, GO, MA, MG, MT, PA, PB, PE, PI, PR, RJ, RN, RS, SC, SP.
- 2026, 1º turno: 0/28 pacotes processados; faltam: AC, AL, AM, AP, BA, CE, DF, ES, GO, MA, MG, MS, MT, PA, PB, PE, PI, PR, RJ, RN, RO, RR, RS, SC, SE, SP, TO, ZZ.

Enquanto houver pacotes faltando, os indicadores baseados em log (horários, intervalos,
modalidade de habilitação, B6) **não são nacionais**: valem para as UFs processadas. Os
indicadores baseados no BU em CSV e nas tabelas oficiais são nacionais (todas as seções).

## Dados não publicados ou indisponíveis

- **2º turno de 2026** (25/10/2026): BU, arquivos de urna e tabelas ainda não estavam no Portal de
  Dados Abertos em 27/10/2026. Totais oficiais conhecidos apenas pelo portal de resultados.
- **Especificação ASN.1 oficial e catálogo de mensagens do log**: a página de documentação técnica
  do TSE respondeu HTTP 403 a este ambiente; usaram-se espelhos (procedência em `especificacoes/`),
  validados pela decodificação e pela concordância com o BU publicado.
- **Atas das mesas receptoras e cadernos de votação**: não são publicados como dados abertos; são o
  documento necessário para esclarecer as incompatibilidades log × BU remanescentes.
- **Senhas distribuídas às 17h**: não registradas no log; votos após 17h não podem ser conferidos
  eleitor a eleitor.

## Downloads com problema registrado

Nenhum.

## Divergência de versões no CDN do TSE

Em 26–27/10/2026 o CDN respondeu a HEAD com uma versão de alguns arquivos e a GET com outra
(ETag e tamanho diferentes), indicando republicação em curso. Os casos estão registrados
(coluna `aviso_versao` de `manifestos/downloads.csv`); adotou-se a versão efetivamente baixada,
identificada pelo SHA-256.

| url | aviso_versao |
|---|---|
| https://cdn.tse.jus.br/estatistica/sead/odsele/detalhe_votacao_secao/detalhe_votacao_secao_2026.zip | HEAD: ETag a8ba227-65d465412458b, 176923175 bytes; GET: ETag df80409-65ec014ca87c2, 234357769 bytes (versão do GET adotada) |
| https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_secao/votacao_secao_2026_BR.zip | HEAD: ETag 9a21287-65d30ec9f3a44, 161616519 bytes; GET: ETag e6af70f-65ec1dac721b7, 241891087 bytes (versão do GET adotada) |
| https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_secao/votacao_secao_2026_GO.zip | HEAD: ETag 4dc8d22-65d30ebff8bef, 81562914 bytes; GET: ETag 4fef003-65ec1d0c35182, 83816451 bytes (versão do GET adotada) |
| https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_secao/votacao_secao_2026_PE.zip | HEAD: ETag 6501e0d-65ec1d6be5651, 105913869 bytes; GET: ETag 60e2a37-65d4672092753, 101591607 bytes (versão do GET adotada) |
| https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_secao/votacao_secao_2026_PR.zip | HEAD: ETag 915df32-65ec1cf9faa4e, 152428338 bytes; GET: ETag 8b503f8-65d30ec1cb894, 146080760 bytes (versão do GET adotada) |
| https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_secao/votacao_secao_2026_RR.zip | HEAD: ETag 5355c4-65ec1d196c99b, 5461444 bytes; GET: ETag 52472e-65d30ec5c2a8a, 5392174 bytes (versão do GET adotada) |
| https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_secao/votacao_secao_2026_RS.zip | HEAD: ETag 8ee4166-65ec1f234f8e7, 149832038 bytes; GET: ETag 89df2ab-65d30ebb7b1aa, 144569003 bytes (versão do GET adotada) |
| https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_secao/votacao_secao_2026_TO.zip | HEAD: ETag d12896-65ec1d1dbd52f, 13707414 bytes; GET: ETag c1e591-65d30ec395c82, 12707217 bytes (versão do GET adotada) |


## Questões metodológicas em aberto

- **Assinaturas digitais** (`.vscmr`/`-vota.vsc`) não foram verificadas criptograficamente nesta etapa.
- **Ajustes de relógio**: o log registra a aplicação "AJUSTE DE DATA E HORA"; a contagem sistemática
  ainda não foi incorporada ao leitor (identificado em diagnóstico de caso, RN 18139/65/32).
- **Transferências temporárias**: ~3% das seções com variação de aptos entre turnos não são
  explicadas pelo arquivo de TTE (gerado em 2024); verificação documental pendente.
- **Modelos de urna**: sem covariáveis anteriores por seção, efeito de modelo e de localização não se
  separam totalmente.
- **Inferência de transferência de votos entre turnos**: não realizada (inferência ecológica).
- **Exterior**: horários em hora local de cada país; sem biometria; não entra em indicadores de Brasília.
