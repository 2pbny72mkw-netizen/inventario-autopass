# V79 — Coleta de Valores

- Base soberana: 602 ATMs do cadastro oficial (`atm_official_082026.json`).
- Universo monitorado: 256 ATMs cujo cadastro complementar indica DINHEIRO + CARTÃO.
- Programação inicial: 256 regras importadas da planilha `Acompanhamento e auditoria - TBForte (2).xlsx`.
- Histórico inicial: valores declarados/apurados disponíveis na aba Monitoramento, importados sem duplicar terminal+data.
- Abas: Monitoramento e Programação de Coletas.
- Regra financeira única: Diferença = Apurado - Declarado.
- Programação semanal e por dias do mês; feriado desloca para o próximo dia operacional (terça a sexta).
- Alertas: sem programação, não realizada, aguardando apuração, divergência e coleta extra.
- Big Numbers clicáveis, drill-down por ATM e exportação Excel respeitando filtros.
