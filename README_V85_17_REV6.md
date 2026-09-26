# V85.17 REV6 — correção estrutural do Monitoramento

- Parte da V85.17 REV5.
- Remove integralmente o identificador problemático `v8517BulkState`.
- O estado de seleção e as funções de seleção/exclusão passam a ser declarados antes de `render()`, `apply()` e `load()`.
- Usa uma única função `v8517UpdateBulkUI()` para sincronizar checkbox, contador e botão de exclusão.
- Mantém exclusão lógica/auditada e preservação de ATM, programação recorrente, R0050 e dados-fonte.
- Cache-busting atualizado para 85.17.6.
