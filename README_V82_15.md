# Inventário Autopass — V82.15 ENXUTA

## Reprogramação de coletas — estratégia agressiva
- Mantém o gatilho individual exclusivamente pela média do **Valor Apurado** das últimas 2 ou 3 coletas válidas.
- Se ao menos uma ATM de uma localidade superar o valor de referência e gerar uma segunda visita semanal, **todas as demais ATMs elegíveis da mesma localidade acompanham essa segunda coleta**.
- ATM que gerou o gatilho mantém o motivo `Média das últimas N coletas acima de R$ X`.
- ATM abaixo da referência incluída na segunda visita recebe o motivo `Aproveitamento de coleta na mesma localidade`.
- A média apurada original é preservada; inclusão logística não transforma ATM em gatilho financeiro.
- Tela/carga diária, proposta salva, ativação e exportação usam os dois dias do `terminal_plan`.
- O total de ATMs únicas não é duplicado; aumentam apenas as ocorrências semanais.
- Linha 17/Ouro permanece com a regra específica de 2x/mês e não participa da propagação semanal.

## Continuidade
Preserva as correções e funcionalidades da V82.14.
