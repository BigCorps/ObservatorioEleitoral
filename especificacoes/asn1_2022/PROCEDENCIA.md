# Procedência das especificações ASN.1 (BU, RDV, assinatura) — 2022

A página oficial de documentação técnica do TSE (www.tse.jus.br) respondeu HTTP 403
ao ambiente desta pesquisa em 26/10/2026, de modo que o pacote oficial não pôde ser
baixado diretamente. Foram usadas cópias publicadas em dois repositórios
independentes no GitHub, cujos arquivos `bu.asn1`, `rdv.asn1` e `assinatura.asn1`
são **byte a byte idênticos** (mesmo SHA-256, ver `SHA256SUMS`):

- danarrib/TSEParser (pasta `spec/`)
- alissonlinneker/DataUrnas-BR (especificação v1, aplicável a 2022)

O mesmo `bu.asn1` também aparece num espelho de 2026 (juliosaulo), indicando que
a especificação do BU não mudou para 2026.

**Validação empírica:** a especificação é considerada adequada porque decodifica
todos os .bu processados sem erro e os totais decodificados conferem com os BUs
publicados em CSV (ver Teste B em docs/auditoria-2022.md). Pendência: conferir o
SHA-256 contra o pacote oficial do TSE quando o acesso for possível.
