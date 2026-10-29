# 2º turno de 2026 — votação por horário de voto e de encerramento da seção

_Gerado por `observatorio/horario_encerramento.py` (`python -c "from observatorio import horario_encerramento as H; H.executar()"`),
a partir de Parquets locais, sem novo download. Nenhuma alteração nos cálculos existentes._

## Fontes e cruzamento

| dado | arquivo | origem |
|---|---|---|
| horários (voto, encerramento, BU) e votos após 17h/19h | `dados/processados/indicadores_temporais_2026.parquet` (turno 2) | log de cada urna, coletado seção a seção no Portal de Resultados com hash conferido |
| aptos, comparecimento, votos 13/22, brancos, nulos | `dados/processados/secoes_oficiais_2026_2t.parquet` | Detalhe + Votação por seção (TSE) |
| resultado do 1º turno nas mesmas seções | `dados/processados/secoes_turnos_2026.parquet` | BU em CSV do 1º turno |
| votos por recorte de horário | `dados/processados/logs/2026_2t_*.parquet` (`votos_s`) | log da urna |

Chave: UF, município, zona e seção. Brasil em hora de Brasília (conversão pelo fuso legal de cada município);
exterior (ZZ) em hora local, apresentado separadamente. Ficam fora 30 seções sem log (29 do exterior apuradas pelo
Sistema de Apuração e 1 em SP sem log publicado): 497.896 seções no Brasil e 1.281 no exterior.

## Definição dos grupos

| grupo | critério | campo |
|---|---|---|
| A | pelo menos um voto após 17h00:00 | `votos_apos_17h > 0` (voto com hora > 61.200 s) |
| B | pelo menos um voto após 19h00:00 | `votos_apos_19h > 0` (> 68.400 s) |
| C | primeiro "Inicio do Encerramento" após 17h00:00 | `encerramento_brt > 61.200` |
| D | primeiro "Inicio do Encerramento" após 19h00:00 | `encerramento_brt > 68.400` |

Último voto (`ultimo_voto_brt`), início do encerramento (`encerramento_brt`) e geração do BU (`gera_bu_brt`) são
registros distintos do log; só o início do encerramento define C e D.

**Atenção ao grupo C:** a urna não aceita o encerramento antes das 17h (mensagem "Encerramento só pode ser solicitado
após as 17h"), por isso C reúne **497.891 das 497.896 seções** do Brasil — praticamente o total — e não separa seções
"tardias" de "cedo". Para comparações usamos A, D e, como auxiliar, encerramento após 17h15.

## Resultados — Brasil (hora de Brasília)

| | A: voto após 17h | B: voto após 19h | C: encerramento após 17h | D: encerramento após 19h | todas as seções |
|---|---|---|---|---|---|
| seções | 29.609 | 11 | 497.891 | 6.766 | 497.896 |
| aptos | 10.058.548 | 4.302 | 157.826.779 | 2.463.073 | 157.828.469 |
| comparecimento (dia todo) | 8.123.964 | 3.398 | 127.853.012 | 1.984.670 | 127.854.363 |
| votos no 13 | 4.236.980 | 1.957 | 64.055.492 | 1.051.828 | 64.055.943 |
| votos no 22 | 3.607.087 | 1.316 | 59.653.559 | 861.378 | 59.654.419 |
| brancos + nulos | 279.897 | 125 | 4.143.961 | 71.464 | 4.144.001 |
| % válidos 13 / 22 | 54,02 / 45,98 | 59,79 / 40,21 | 51,78 / 48,22 | 54,98 / 45,02 | 51,78 / 48,22 |
| % válidos 13 / 22 no **1º turno**, mesmas seções | 46,74 / 45,18 | 51,80 / 39,35 | 45,15 / 47,04 | 47,35 / 44,20 | 45,15 / 47,04 |
| votos registrados após 17h | **34.050** | 25 | 34.050 | 4.693 | 34.050 |
| votos registrados após 19h | 11 | **11** | 11 | 11 | 11 |

Exterior (hora local): A = 252 seções (416 votos após 17h; 13: 57,45%), C = 1.280 seções, B e D = 0.
Por UF: `resultados/2026/horario_grupos_uf.csv`. Nacional: `horario_grupos_nacional.csv` e `horario_todas_secoes.csv`.

Leitura: a grande maioria do comparecimento dessas seções ocorreu antes das 17h. No grupo A, os votos registrados após
17h são 34.050 de 8.123.964 (0,42%); no grupo D, o encerramento após 19h decorre da prorrogação determinada pelo STF,
mas só 11 votos foram registrados depois das 19h. Os percentuais de 13 e 22 são do **resultado da seção inteira**,
não dos votos dados depois das 17h — o sigilo do voto impede saber em quem votou quem votou tarde.

## Votos por recorte de horário (todas as seções)

Segundos desde a meia-noite, hora de Brasília, fim inclusivo; recortes por minuto, contíguos.

| recorte | limites | Brasil | exterior (hora local) |
|---|---|---|---|
| até 17h | 0 – 61.259 s (até 17h00:59) | 127.833.940 | 380.286 |
| 17h01–17h15 | 61.260 – 62.159 s (17h01:00–17h15:59) | 16.579 | 261 |
| 17h16–18h59 | 62.160 – 68.399 s (17h16:00–18h59:59) | 3.779 | 65 |
| a partir de 19h | ≥ 68.400 s (19h00:00 em diante) | 11 | 0 |
| total | | 127.854.309 | 380.612 |

Conciliação das convenções de "após 17h": exatamente 17h00:00 = 280 votos; 17h00:01–17h00:59 = 13.681;
**após 17h00:00 = 34.050** (13.681 + 16.579 + 3.779 + 11); **a partir de 17h00:00 = 34.330** (número publicado pela
CNN/setup.news). Arquivo: `horario_recortes_votos.csv`.

## Seções que encerraram mais tarde votaram diferente? (comparação pareada)

Diferença no % de válidos do 13 (2º turno) entre seções "tardias" e as demais **do mesmo local de votação** ou **do
mesmo município**, só em locais/municípios com os dois tipos de seção. Regressão ponderada pelos válidos com efeito
fixo do local/município; controles: % do 13 no 1º turno na mesma seção, comparecimento e tamanho (log dos aptos).
Erro-padrão agrupado pelo local/município. Arquivo: `horario_comparacao_pareada.csv`.

| grupo tardio | comparação | sem controles (p.p.) | com controles (p.p.) [IC 95%] |
|---|---|---|---|
| A (voto após 17h) | mesmo local de votação | −0,06 | +0,06 [+0,03; +0,08] |
| A (voto após 17h) | mesmo município | +0,45 | +0,18 [+0,13; +0,24] |
| D (encerramento após 19h) | mesmo local de votação | −0,07 | −0,00 [−0,11; +0,11] |
| D (encerramento após 19h) | mesmo município | −2,11 | −0,28 [−0,44; −0,13] |
| encerramento após 17h15 | mesmo local de votação | −0,03 | −0,06 [−0,12; +0,01] |
| encerramento após 17h15 | mesmo município | −1,03 | −0,22 [−0,30; −0,13] |

**Conclusão:** a diferença bruta (grupo A 54,0% para o 13 contra 51,8% no país) **não se sustenta** quando se comparam
seções do mesmo local: cai para −0,06 a +0,06 p.p. As seções com fila após 17h já davam mais votos ao 13 no 1º turno
(46,7% contra 45,2%) — a diferença é de **onde** ficam, não de **quando** encerraram. Os efeitos residuais, com
controles, ficam abaixo de 0,3 p.p., com sinais opostos entre os grupos.

## Validação

- A: 29.609 seções e 34.050 votos após 17h ✔ (extração anterior). B: 11 seções e 11 votos após 19h ✔.
- Cada seção aparece uma vez por grupo (`secoes` = `secoes_distintas`) ✔; soma das UFs = total nacional ✔.
- 13 + 22 + brancos + nulos = comparecimento oficial em todos os grupos e UFs (`residuo_soma` = 0) ✔.
- 5 seções do Brasil sem registro de início de encerramento ficam fora de C e D.

## Confronto com relatórios externos

| verificação | nossa extração | CNN/setup.news | relatório externo com recortes 17h01–17h15 / 17h16–18h59 |
|---|---|---|---|
| votos a partir de 17h00:00 (Brasil) | 34.330 | 34.330 | não disponível no repositório |
| votos 17h00–17h05 | 29.001 (extração anterior) | 29.001 | — |
| votos após 18h / após 19h | 1.993 / 11 | 1.993 / 11 | — |
| seções sem voto após 17h | 468.287 | 468.043 | — |
| votos por recorte | ver tabela acima | — | **pendente**: valores do relatório não fornecidos |

## Limitações

- **Cobertura:** 30 seções sem log ficam fora (comparecimento oficial delas não entra nos grupos). O TSE não publica
  hora de voto; os horários vêm do relógio da urna, convertido pelo fuso legal.
- **Exterior** em hora local, não comparável com Brasília.
- O grupo C não discrimina seções (quase todas encerram após 17h, por regra da urna).
- Comparações são **entre seções**; nada associa voto individual a horário ou candidato.
- Diferença estatística não é indício de irregularidade.
