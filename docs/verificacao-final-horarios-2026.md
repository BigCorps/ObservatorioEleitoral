# Verificação dirigida — horários do TSE, códigos de local e pacotes oficiais do 2º turno (29/10/2026)

**Escopo:** três verificações executadas nos Parquets locais já preservados (sem novo download do acervo), e o
confronto da coleta anterior com os pacotes oficiais "Arquivos transmitidos para totalização — 2º turno",
cadastrados nos Dados Abertos em 28/10/2026. Prioridade para Pernambuco. Nenhum resultado aqui é tratado como
indício de fraude, e nenhuma pendência é dada como resolvida sem documento que a explique.

Código: `observatorio/confronto_horarios_tse.py`, `observatorio/sensibilidade_locais_2026.py`,
`observatorio/confronto_pacotes_2t.py`. Saídas em `resultados/2026/` e `resultados/2026/consolidado_2t/`.

## Resumo

| verificação | resultado |
|---|---|
| Quadro TSE "Total de votos após 17h" × logs | Diferenças residuais de 63 (após 17h) e 2 (após 19h) **explicadas pela conversão de fuso**: o quadro publicado pelo TSE é reproduzido aplicando o fuso **da UF** a cada urna; o Observatório usa o fuso legal de cada **município** (Fernando de Noronha UTC−2; 11 municípios do oeste do AM UTC−5). Com essa convenção alternativa, a diferença é **0 em todas as 27 UFs** nos três recortes. O TSE não publicou nesta fonte o algoritmo interno de normalização; sua adoção exata pelo órgão é inferência, não fato documental confirmado. |
| 7.315 códigos de local divergentes | Efeitos estatísticos praticamente iguais sob o código do BU em CSV e o do Detalhe por seção (diferenças ≤ 0,002 p.p., muito menores que o erro padrão). Nenhuma conclusão muda. |
| BU do pacote oficial × BU coletado no Portal | **499.207 de 499.207 seções com tamanho e CRC32 coincidentes** (não verificação criptográfica dos 499.207 conteúdos), nas 28 UFs. |
| PE: vsc e log do pacote × coleta anterior | 618 seções conferidas, **618 idênticas**: SHA-256 do `vsc` = hash publicado no Portal; SHA-512 do log consta do `vsc`; log reinterpretado = indicadores já publicados. |
| Pendências em outras UFs | 14 seções conferidas; logs do pacote **idênticos** aos do Portal; SP 64777/395/298 **também sem log no pacote**. |

## 1. Quadro oficial TSE × logs — diferença residual por UF

Fonte primária: TSE, "Total de votos após 17h" (quadro por UF),
https://www.tse.jus.br/comunicacao/noticias/arquivos/total-de-votos-apos-17h —
`resultados/2026/confronto_horarios_tse_uf.csv`.
Execução: `python -m observatorio.confronto_horarios_tse` →
`resultados/2026/confronto_horarios_tse_logs_detalhe_uf.csv`.

Todos os recortes estão em horário de Brasília (desde 2022 a votação vai das 8h às 17h de Brasília em todo o país).

| indicador | TSE | logs, fuso legal de cada município | diferença | logs, fuso da UF para todos os municípios | diferença |
|---|---:|---:|---:|---:|---:|
| Votos a partir de 17h | 34.393 | 34.330 | 63 | 34.393 | **0** |
| Votos entre 18h e 19h | 1.981 | 1.982 | −1 | 1.981 | **0** |
| Votos após 19h | 13 | 11 | 2 | 13 | **0** |

- Contando os votos registrados exatamente às 17:00:00 (280 no total), a diferença em 25 UFs já era zero. Restavam
  **PE +94** e **AM −31**.
- **PE +94 (e +2 após 19h):** Fernando de Noronha (município 30015) usa UTC−2, uma hora à frente de Recife. Os 94 votos
  marcados entre 17h e 18h no relógio local de Noronha ocorreram entre 16h e 17h de Brasília, ainda no horário normal.
  Convertidos pelo fuso de PE, eles aparecem como "após 17h". Os 2 "após 19h" são votos de 19h49 no relógio de Noronha
  (18h49 de Brasília), na seção 4/372.
- **AM −31:** os 11 municípios do oeste do Amazonas usam UTC−5, duas horas atrás de Brasília. Os 31 votos marcados
  entre 15h e 16h no relógio local ocorreram entre 17h e 18h de Brasília. Convertidos pelo fuso de Manaus (UTC−4),
  eles aparecem como 16h–17h e ficam fora do quadro.
- **Nenhum voto falta ou sobra.** As duas contagens diferem só na régua de conversão. O fuso legal por município, que
  foi confirmado empiricamente (mediana do primeiro voto às 9h03 locais em Noronha e às 6h03 locais no oeste do AM),
  continua sendo o usado nas análises do Observatório.

## 2. Sensibilidade dos 7.315 códigos de local divergentes

Execução: `python -m observatorio.sensibilidade_locais_2026` →
`resultados/2026/consolidado_2t/sensibilidade_codigo_local.csv`.

**Correção feita antes de executar:** a versão anterior do programa comparava o código do Detalhe por seção com ele
mesmo (a base carregada já usa o Detalhe). Agora o código "BU_CSV" vem de `secoes_bu_2026.parquet`, e há uma verificação
de que as 7.315 divergências estão de fato presentes.

| teste (efeitos fixos por local, controles completos) | código do BU em CSV | código do Detalhe por seção |
|---|---:|---:|
| Efeito de voto após 17h em 2026 (p.p.) | +0,0558 [0,0294; 0,0822] | +0,0556 [0,0292; 0,0821] |
| Evolução 2022→2026, seções tardias em 2026 | +0,0139 [−0,0149; 0,0428] | +0,0123 [−0,0167; 0,0413] |
| Evolução 2022→2026, seções tardias em 2022 | −0,0075 [−0,0333; 0,0184] | −0,0058 [−0,0318; 0,0202] |
| Seções correspondentes 2022 × 2026 | 322.703 | 318.674 |

Sem controles, o efeito em 2026 é −0,0523 (BU em CSV) e −0,0545 (Detalhe). A correspondência entre anos muda em **4.029 seções** (cerca de 1,26% do conjunto com código do Detalhe). **Apesar da mudança de amostra, a escolha do código do local não altera as conclusões dos modelos avaliados.** As análises continuam usando o Detalhe por seção.

## 3. Pacotes oficiais do 2º turno × coleta anterior

### 3.1 Publicação

Os 28 pacotes (27 UFs e exterior, 124,1 GB) estão cadastrados no CKAN desde **28/10/2026 14:07–14:11 UTC**, com
Last-Modified no CDN de **26/10 18:03–21:31 UTC**. São 3,6 dias da eleição ao CKAN (1,8 dia até o arquivo no
servidor), contra 3,9 dias em 2022. Ficam corrigidas duas afirmações do relatório de reconciliação:

- os pacotes **não** saíram depois do intervalo de 2022;
- a consulta `package_show` do CKAN devolveu uma versão desatualizada do conjunto (sem esses recursos), o que levou ao
  registro "não publicado". O catálogo agora confere cada recurso também por `resource_show` e pela página do conjunto
  (`observatorio/catalogo.py`).

**BU em CSV de RR:** o recurso está cadastrado no CKAN (27/10 19:12 UTC), mas aponta para o arquivo `.sha512`, e não
para o `.zip`. Trata-se de um erro de cadastro, e não de ausência. O `.zip` foi obtido no CDN pelo padrão oficial, e o
SHA-512 publicado confere. Duas respostas de `resource_show` chegaram a mostrar a URL corrigida, mas 40 consultas
seguintes voltaram ao cadastro antigo (`manifestos/historico/ckan_amostragem_recurso_RR_2026-10-29.csv`).

### 3.2 BU — todas as UFs

Sem baixar os pacotes: lemos apenas o diretório de cada ZIP (HTTP Range) e comparamos o tamanho e o CRC32 de cada BU
com o BU coletado no Portal de Resultados em 27/10
(`resultados/2026/consolidado_2t/pacote_oficial_2t_bu_x_portal_todas_ufs.csv`).

**Resultado: 499.207 seções, todas com tamanho e CRC32 correspondentes; nenhuma só no pacote ou só no Portal.** Essa checagem dos diretórios ZIP não prova, isoladamente, igualdade byte a byte nem valida assinaturas digitais das 499.207 seções. As 29 seções do exterior
apuradas pelo Sistema de Apuração aparecem no pacote como `-busa.dat` (com `-sa.vsc` e `-logsa.jez`). Elas também apresentam tamanho e CRC32 coincidentes.

### 3.3 Pernambuco

`pacote_oficial_2t_PE_resumo.csv`, `pacote_oficial_2t_PE_bu_x_portal.csv`, `pacote_oficial_2t_PE_secoes_conferidas.csv`.

- Pacote: 107.095 membros. **BU com tamanho e CRC32 coincidentes nas 21.418 seções.**
- 618 seções baixadas (somente `vsc` e log): todas as 446 com versão "Recebido" em 26–27/10, as 106 com voto após 18h,
  as 10 de Fernando de Noronha, as 2 pendências E1 e 60 seções de controle sorteadas (semente 20261029).
- **618/618:** SHA-256 do `vsc` = hash publicado no Portal; SHA-512 do log consta do `vsc`; o log reinterpretado dá os
  mesmos votos computados, habilitações, primeiro e último voto, encerramento e identificação das urnas; 0 erros.

**As duas pendências E1 de PE** (abertura no BU em CSV × primeiro voto no log):

| seção | o que o log (completo, idêntico no pacote) mostra | situação |
|---|---|---|
| 23370/35/45 | urna ligada às 07:02, zerésima às 07:09; reinícios às 08:04 e 08:27; "Bateria interna com carga crítica" às 08:07; "Erro de leitura da mídia de resultado" às 08:09; urna pronta às 08:42; primeiro voto às 08:44 | **parcialmente esclarecida** |
| 23515/54/3 | zerésima às 07:15; reinício às 08:17; urna pronta às 08:29; primeiro voto às 08:30 | **parcialmente esclarecida** |

- **Esclarecido:** o log não está truncado. O atraso do primeiro voto tem causa registrada na própria urna (reinícios,
  bateria, erro de mídia).
- **Continua pendente:** o BU em CSV registra `DT_ABERTURA` 08:00:01 nas duas seções. Esse valor aparece em 432.947
  das 499.207 seções, o que indica que o campo não acompanha atrasos reais de início. A semântica do campo não está
  documentada pelo TSE, e não há ata da seção publicada.

### 3.4 Pendências das demais UFs

`resultados/2026/consolidado_2t/pacote_oficial_2t_pendencias_outras_ufs.csv` — mesmo procedimento:

| grupo | seções | resultado no pacote | situação |
|---|---|---|---|
| E1/E2 não explicadas (RJ, CE ×2, SP, MG, SC, ZZ, RS) | 8 | `vsc` = hash do Portal; log idêntico | **pendente** (o pacote não traz informação nova) |
| Log com menos "voto computado" que o BU (MA 609, BA 235, BA 178, PB 254, PI 216, RS 191) | 6 | idem | **pendente**: a lacuna está no próprio log oficial |
| SP 64777/395/298 sem log no Portal | 1 | `vsc` = hash do Portal; **pacote também sem log** (só `vsc`, `bu`, `rdv`, `imgbu`) | **pendente**: o log não foi publicado em nenhuma das duas fontes |

## 4. O que continua pendente

- **E1/E2:** 2 seções em PE (causa operacional registrada; falta a semântica de `DT_ABERTURA`) e 8 nas demais UFs.
- **Lacunas de "voto computado":** 6 seções e 54 votos, presentes no BU e ausentes do log oficial.
- **SP 64777/395/298:** log ausente no Portal e no pacote.
- **Documentos necessários para fechar essas pendências:** atas de seção, relatórios de contingência e substituição de
  urna, e a documentação dos campos do BU em CSV.

Nenhuma pendência envolve divergência de votos: em todas as seções, BU do pacote = BU do Portal = BU em CSV =
resultado oficial.

## Reprodução

```bash
python -m observatorio.confronto_horarios_tse
python -m observatorio.sensibilidade_locais_2026
python -m observatorio.confronto_pacotes_2t PE
python -c "from observatorio.confronto_pacotes_2t import bu_todas_ufs, pendencias_outras_ufs; bu_todas_ufs(); pendencias_outras_ufs()"
```
