# Perguntas frequentes

## Horários

**Por que algumas urnas do Acre registram votos às 6h?**
O relógio da urna marca a hora local. Em 2022 e 2026 a votação foi das 8h às 17h *de
Brasília* em todo o país. No Acre (e em 11 municípios do oeste do Amazonas), 8h de Brasília
são 6h locais. Depois da conversão para o horário de Brasília, esses votos estão dentro do
horário. Quem não faz essa conversão "encontra" votos antes das 8h que não existem.

**Votar depois das 17h é irregular?**
Não. Quem está na fila às 17h recebe senha e vota (Resolução TSE 23.669/2021, art. 136).
Seções grandes, com muitos cargos (5 no 1º turno de 2022) e filas longas terminam mais
tarde. O log não registra quem recebeu senha, então não dá para conferir eleitor a eleitor;
o que se pode verificar é a distribuição e os casos extremos (listados em
`resultados/ANO/secoes_horarios_atipicos.csv`).

**O que é um "intervalo muito curto" entre votos?**
É o tempo entre dois registros de "voto computado" seguidos na mesma urna. Não existe um
mínimo universal: depende do número de cargos, da identificação e do eleitor. Publicamos a
distribuição completa e uma grade de limiares, em vez de escolher um corte arbitrário.

## Biometria

**Votar sem reconhecimento biométrico é irregular?**
Não. Se a digital não é reconhecida após até 4 tentativas, o presidente da mesa confere o
eleitor, pergunta o ano de nascimento e libera o voto com a digital de um mesário (Res.
23.669/2021, arts. 113–114). Eleitores sem biometria cadastrada votam pelo procedimento
tradicional (art. 115). No exterior, as urnas não fazem identificação biométrica.

**O BU e o log concordam sobre isso?**
Sim, na verificação seção a seção: o campo do BU "eleitores com biometria não habilitados
por ela" coincide com a contagem de liberações manuais no log, exceto nos casos listados em
`resultados/ANO/incompatibilidades.csv` (teste B6), cada um com diagnóstico.

## Abstenção, brancos e nulos

**Como se calcula a abstenção?**
Abstenção = eleitores aptos − comparecimento. Percentual sobre os aptos. Brancos e nulos são
calculados sobre o comparecimento. Votos válidos = votos nominais em candidatos.

**Por que o número de aptos de uma seção muda entre os turnos?**
Porque eleitores podem votar temporariamente em outra seção (voto em trânsito, mesários,
presos provisórios, militares), e isso pode valer para um turno só. O total nacional não
muda. Mais de 96% dos casos são explicados exatamente pelo arquivo oficial de transferências
temporárias (ver auditoria 2022).

## Estatística

**Um valor-p pequeno prova fraude?**
Não. Com centenas de milhares de seções, diferenças minúsculas ficam "estatisticamente
significantes". Por isso publicamos sempre o tamanho do efeito e uma referência realista.

**E a Lei de Benford?**
A lei supõe números que variam em várias ordens de grandeza. Votos por seção têm teto (as
seções têm poucas centenas de eleitores), então o desvio é esperado mesmo sem qualquer
problema. Comparando com uma simulação que respeita o tamanho real das seções, o desvio
praticamente desaparece.

**A diferença de votos por modelo de urna significa algo?**
Comparando seções do mesmo local de votação, não há diferença estatisticamente
significativa. Diferenças aparecem em comparações mais grosseiras (mesma zona ou município),
onde as seções comparadas são de bairros diferentes. Correlação não é causa.

**É possível saber em quem cada pessoa votou a partir do horário?**
Não. O log não registra o candidato, e o Registro Digital do Voto embaralha a ordem dos
votos por desenho. Este projeto não tenta fazer essa associação.
