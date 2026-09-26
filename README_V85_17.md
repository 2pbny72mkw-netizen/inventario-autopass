# V85.17 — Gestão Visual + acompanhamento de não coleta TB Forte

## Escopo
- Kanban visual de Gestão de Tarefas, com colunas Aguardando, A fazer, Em execução, Em validação e Concluída.
- Drag-and-drop altera o status usando a API existente e respeita a Matriz de Permissões.
- Cards com prioridade, projeto, ATM, responsável, prazo e origem automática TB Forte.
- Importação do reporte diário cria tarefa automática para cada coleta `NAO_RECOLHIDO` correlacionada à base oficial.
- Idempotência da tarefa por `ATM + data prevista`; reimportar não duplica acompanhamento.
- Responsável padrão é o usuário que importou; a API aceita `followup_assigned_to` para atribuição explícita e a tarefa pode ser transferida no Kanban conforme permissão.
- Fechadura/cofre gera roteiro: fornecedor/manutenção → confirmação do reparo → nova coleta → confirmação do desfecho.
- Demais causas recebem roteiros de TB Forte, suporte, acesso, técnica ou classificação manual.
- A ocorrência principal só deve ser concluída após o desfecho da coleta.

## Segurança / dados
- Não exclui registros financeiros, reportes, fotos ou objetos R2.
- Não altera cálculos de conciliação.
- Mantém auditoria via `ManagementTaskEvent`.
