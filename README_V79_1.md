# V79.1 — Coleta de Valores

Correção/consolidação visual da V79.

## Tela Financeiro > Coleta de Valores
A tela passa a apresentar explicitamente três abas:
1. Visão Geral / Custos — preserva a visão financeira existente.
2. Monitoramento — programação x realizado, data/hora, declarado, apurado, diferença (Apurado - Declarado), status, observação e histórico por ATM.
3. Programação de Coletas — regras de agendamento vinculadas à base mestre das ATMs.

## Exportação
- Visão Geral / Custos: exportação respeita os filtros ativos da própria visão.
- Monitoramento / Programação: Exportar Excel respeita mês, operadora, linha, estação, ATM e status ativos.

## Base
A V79.1 não cria uma base paralela de ATM. Mantém a base mestre oficial do inventário e os vínculos de programação/monitoramento introduzidos na V79.
