# V80 REV11.1 — Hotfix de layout do Monitoramento

Base: V80 REV11.

## Correção
- Remove a técnica de centralização por `50vw/translateX` que fazia o Monitoramento ficar cortado/deslocado para a esquerda.
- Em `monitor_mode`, o `main.wrap` passa a usar 100% da largura disponível do viewport com padding lateral mínimo de 10 px.
- Filtros, botões, Big Numbers e tabela permanecem dentro da área útil, sem ficar escondidos sob a borda/lateral.
- A tabela continua full-width e mantém scroll horizontal apenas quando realmente necessário.
- Demais telas permanecem com o layout anterior.

Pacote ENXUTO: sobrepor ao projeto completo em produção.
