# V85.18 — Gestão + TB Forte

Base: V85.17 REV7 homologada.

- Preview do reporte diário classifica a causa da não coleta e mostra o fluxo de acompanhamento.
- Seleção explícita do responsável pelas atividades antes da importação.
- Criação idempotente: ATM + data programada não duplica tarefa em reimportações.
- Kanban: filtro de origem e indicador de não coletas TB Forte em aberto.
- Ocorrência TB Forte só pode ser concluída com desfecho e observação obrigatórios; o desfecho fica registrado na descrição e em evento auditável.
- Sem alteração nos cálculos financeiros, programação recorrente, R0050 ou regras de exclusão homologadas na REV7.
