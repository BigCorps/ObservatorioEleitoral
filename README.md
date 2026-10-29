# Observatório Eleitoral — auditoria reproduzível das eleições presidenciais 2022 e 2026

Pesquisa independente da BigCorps Tecnologia, baseada exclusivamente em arquivos oficiais do
Tribunal Superior Eleitoral (TSE). O objetivo é **descobrir o que os dados mostram** —
compatibilidades e incompatibilidades entre resultados, Boletins de Urna (BU) e registros
técnicos das urnas —, não demonstrar uma hipótese escolhida antes.

> Nenhuma diferença estatística é tratada como prova de irregularidade. Toda divergência
> entre fontes oficiais é registrada com valores, origem e tentativa de explicação.

## Onde está cada coisa

| Documento | Conteúdo |
|---|---|
| [docs/relatorio-publico.md](docs/relatorio-publico.md) | linguagem simples, com gráficos |
| [docs/auditoria-2022.md](docs/auditoria-2022.md) | resultados reproduzidos dos dois turnos de 2022 |
| [docs/auditoria-2026.md](docs/auditoria-2026.md) | resultados disponíveis de 2026 |
| [docs/auditoria-2026-2turno.md](docs/auditoria-2026-2turno.md) | auditoria final do 2º turno de 2026 (cobertura, hashes, horários, biometria, discrepâncias, estudos externos) |
| [docs/reconciliacao-consolidado-2026-2t.md](docs/reconciliacao-consolidado-2026-2t.md) | reconciliação do BU em CSV consolidado do 2º turno de 2026, cronologia de publicação e afirmações externas |
| [docs/biometria-perfil-e-abstencao-por-idade.md](docs/biometria-perfil-e-abstencao-por-idade.md) | falha de biometria × concentração de votos × idade e escolaridade; abstenção por faixa etária |
| [docs/comparativo-historico.md](docs/comparativo-historico.md) | 2022 × 2026 |
| [docs/metodologia.md](docs/metodologia.md) | fórmulas, regras de leitura, critérios |
| [docs/fontes.md](docs/fontes.md) | URLs, versões (ETag), hashes, cobertura |
| [docs/dicionario-dados.md](docs/dicionario-dados.md) | campos e diferenças entre anos |
| [docs/referencias-normativas.md](docs/referencias-normativas.md) | resoluções, fusos, especificações |
| [docs/auditoria-estudos-externos.md](docs/auditoria-estudos-externos.md) | revisão das auditorias independentes |
| [docs/limitacoes.md](docs/limitacoes.md) | pendências e questões em aberto |
| [docs/perguntas-frequentes.md](docs/perguntas-frequentes.md) | biometria, horários, abstenção, estatística |

## Estado do projeto

Veja a seção "Cobertura" no topo de cada `docs/auditoria-ANO.md` (gerada automaticamente)
e `manifestos/cobertura_arquivos_urna.csv`. Em 26–27/10/2026:

- 2022, 1º e 2º turnos: BU em CSV, tabelas oficiais e reconciliações **nacionais**
  concluídas; processamento dos logs e BUs binários por UF em andamento/concluído conforme
  a cobertura registrada.
- 2026, 1º turno: BU em CSV e tabelas oficiais processados; logs conforme cobertura.
- 2026, 2º turno (25/10/2026): BU em CSV consolidado (Dados Abertos, publicado no CKAN em 27/10/2026, SHA-512
  oficial conferido) adotado como fonte principal em 29/10/2026 e reconciliado seção a seção com os BUs binários e
  logs coletados no Portal de Resultados e com o resultado oficial por seção — ver
  [docs/reconciliacao-consolidado-2026-2t.md](docs/reconciliacao-consolidado-2026-2t.md). Os pacotes de arquivos transmitidos
  do 2º turno (no CKAN desde 28/10) foram confrontados com a coleta: BU idêntico em 499.207/499.207 seções; em PE,
  `vsc` e log idênticos em 618 seções conferidas; diferença residual com o quadro de horários do TSE explicada pelo
  fuso (0 em todas as UFs pela convenção do TSE); códigos de local sem efeito nas análises:
  [docs/verificacao-final-horarios-2026.md](docs/verificacao-final-horarios-2026.md).

## Como reproduzir

Requisitos: Python ≥ 3.11, ~30 GB livres (os pacotes de urna, ~263 GB, **não** são
baixados inteiros: são lidos seção a seção por HTTP Range).

```bash
pip install -r requirements.txt
python -c "from observatorio.catalogo import inventariar; inventariar()"   # 1. inventário (CKAN + HEAD)
python scripts/baixar_tabelas.py 2022 2026                                  # 2. tabelas e BU em CSV (com hashes)
python -c "from observatorio import bweb; [bweb.converter(2022,t,uf) for t in (1,2) for uf in __import__('observatorio.config',fromlist=['x']).UFS_COM_EXTERIOR]"
python scripts/processar_arquivos_urna.py 2022 1,2                          # 3. logs + BU binário (retomável)
python scripts/processar_arquivos_urna.py 2026 1
python scripts/processar_portal.py 2026 2                                   # 2º turno 2026: seção a seção no Portal de Resultados
python scripts/executar_analises.py 2022                                    # 4. todos os testes
python scripts/executar_analises.py 2026
python -c "from observatorio import historico; historico.executar()"        # 5. comparação histórica
python -c "from observatorio import testes_historicos as T; T.executar()"   # testes 2026 x 2022 (Holm)
python scripts/comparar_estudos_externos.py [secoes_logs_brasil.parquet]   # confronto com pesquisas independentes
python scripts/gerar_relatorios.py                                          # 6. documentos
python -m pytest -q                                                         # testes automatizados
```

Cada etapa é incremental: downloads verificados não são repetidos (ETag), pacotes de urna
já registrados em `manifestos/cobertura_arquivos_urna.csv` são pulados, e qualquer análise
pode ser refeita a partir de `dados/processados/` sem novo download.

## Estrutura

```
observatorio/   código (catálogo, download, leitura de BU/log, reconciliação, testes, relatórios)
scripts/        pontos de entrada das etapas
tests/          testes automatizados (dados sintéticos, sem dados pessoais)
manifestos/     inventário de fontes, registro de downloads, cobertura, metadados CKAN
especificacoes/ especificações ASN.1 do BU com procedência e SHA-256
resultados/     CSVs consolidados, gráficos, incompatibilidades, diagnósticos
docs/           documentação e relatórios
dados/          (fora do Git) arquivos brutos e Parquet intermediário
```

## Privacidade

Não são publicados CPFs, títulos, nomes de eleitores ou dados biométricos. Os logs das urnas
contêm números de título de mesários; essas mensagens não são extraídas e os diagnósticos
mascaram qualquer sequência com esse formato. Nenhum horário é associado a voto em
candidato. A análise pública é agregada por seção ou acima.

## Testes de verificação (resumo)

A integridade das fontes · B reconciliação de BUs · C eleitorado · D cronologia · E
intervalos · F biometria · G brancos e nulos · H mudanças entre turnos · I modelos de urna ·
J estatística adicional · K reprodutibilidade por caminhos independentes · L referências
documentais das incompatibilidades. Detalhes em `docs/metodologia.md`.
