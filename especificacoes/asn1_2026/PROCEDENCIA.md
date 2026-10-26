# Procedência das especificações ASN.1 — formato "v2" (aplicado a 2026)

Cópia publicada em alissonlinneker/DataUrnas-BR (`spec/v2`, descrita pelo projeto como
válida "de 2024 em diante"). Fonte única (não há segundo espelho independente) e o
site oficial do TSE respondeu HTTP 403 a este ambiente em 26/10/2026.

**Validação empírica:** os .bu do 1º turno de 2026 são decodificados sem erro com esta
especificação, e os totais decodificados são comparados com o BU publicado em CSV
(Teste B2 em docs/auditoria-2026.md). Mudanças relevantes em relação a 2022:
`qtdEleitoresCompareceram` obrigatório; `DetalhamentoComparecimento` (sem biometria,
habilitados por biometria, habilitados por biografia/ano de nascimento);
`qtdEleitoresAptosSecao` + `qtdEleitoresAptosTTE`; remoção de
`qtdEleitoresLibCodigo`/`qtdEleitoresCompBiometrico`.
