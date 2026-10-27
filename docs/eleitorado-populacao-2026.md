# Eleitorado cadastrado versus população residente — Bahia (2026)

Em 26 de julho de 2026, reportagem do UOL informou 23 municípios da Bahia com mais eleitores do que habitantes, comparando o eleitorado TSE de 2026 com estimativas do IBGE para 2025. Um levantamento de terceiros atualizado em 14 de outubro de 2026 informa 24 municípios, usando a estimativa populacional de 2026.

A recontagem exata dos 24 municípios com os arquivos originais do TSE e do IBGE NÃO foi executada nesta entrega. A página identifica a procedência secundária e a limitação, e traz exemplos divulgados pela fonte.

As definições são distintas: eleitorado cadastrado inclui pessoas com domicílio eleitoral por vínculos residenciais, familiares, afetivos e profissionais; a estimativa de habitantes corresponde a residentes. Razão acima de 100% não é prova de fraude nem indica que comparecimento ou votos excederam habitantes.

## Procedimento para investigação direta
1. Obter o eleitorado TSE 2026 por município e a referência do cadastro.
2. Obter o IBGE estimativa para 01/07/2026 e, separadamente, para 2025.
3. Conciliar os 417 municípios baianos pelos códigos oficiais, e não apenas pelo nome.
4. Calcular as diferenças e investigar as possíveis variações territoriais, o domicílio eleitoral e as datas de referência; distinguir eleitorado apto, comparecimento e votos apurados.
5. Publicar CSV com proveniência e comparação 2022/2024/2026. Esta etapa permanece pendente.

## Simulador
O simulador no fim da página usa os valores nacionais publicados em resultados/2026/resultados_brasil.csv: saldo de brancos/nulos e abstenções entre turnos, votos de candidatos diferentes dos números 13 e 22 no 1º turno, e total de votos iniciais de 22. O modelo recalcula duas variáveis com uma regra arbitrária que preserva proporção das contribuições anteriores, para reproduzir exatamente o crescimento líquido do 13. Isso não é uma estimativa de fluxos de eleitores.

## Fontes
- UOL, 26/07/2026: https://noticias.uol.com.br/colunas/carlos-madeiro/2026/07/26/brasil-tem-um-em-cada-8-municipios-com-mais-eleitores-em-2026-que-moradores.htm
- Levantamento 2026: https://notop10.com.br/ba/cidades-com-mais-eleitores-que-habitantes
- IBGE 2026: https://www.ibge.gov.br/estatisticas/sociais/populacao/9103-estimativas-de-populacao.html
- TSE Eleitorado 2026: https://dadosabertos.tse.jus.br/dataset/eleitorado-2026
- TSE Domicílio eleitoral: https://www.tse.jus.br/servicos-eleitorais/titulo-eleitoral/titulo-eleitoral-faq
