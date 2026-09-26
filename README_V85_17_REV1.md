# V85.17 REV1 — Exclusão controlada no Monitoramento de Coletas

- Checkbox por lançamento real do Monitoramento.
- Selecionar exibidos, todos os resultados filtrados ou seleção manual.
- Exclusão lógica em lote com permissão `finance.delete`.
- Motivo obrigatório e auditoria `COLETA_VALORES_EXCLUSAO_LOTE`.
- Preserva cadastro da ATM, programação, R0050 e dados-fonte.
- Confirmação reforçada quando a seleção contém apuração, declarado ou ciclo transacional.
- Exclusão individual também exige `finance.delete`.
