# Inventário Autopass — V82.30 REV3

Revisão funcional sobre a V82.30 REV2.1, preservando o hotfix do Monitoramento de Coletas e os ajustes da REV1.

## Arrow — planejamento x execução
- Planejamento separado da execução do técnico.
- Edição do planejamento: usuário com `arrow.edit` ou criador da atividade; técnico atribuído não recebe edição apenas por ser o responsável.
- API passa a informar `can_execute` separadamente de `can_edit`.
- Técnico responsável pode executar a própria atividade sem alterar Observações ou demais campos do planejamento.
- `Iniciar`: PLANEJADA -> EM ANDAMENTO, com registro em `arrow_activity_executions`.
- `Registrar impedimento`: exige texto e cria evento histórico sem substituir o status operacional.
- `Concluir`: encerra a atividade e registra usuário/data-hora/observação.
- Atividade CONCLUÍDA/CANCELADA fica sem ações operacionais para o técnico.
- Nova API `GET /api/arrow/activities/<id>/execucoes` para linha do tempo.
- Modal mostra histórico de execução e mantém Observações somente leitura quando não houver permissão de planejamento.
- Calendário suporta múltiplas atividades no mesmo dia com rolagem vertical dentro do dia.
- Criação mantém repetição por quantidade de dias e opção de somente dias úteis.

## Itens preservados da V82.30
- RH/APT com container e rolagem horizontal dedicada.
- Bobinas: novo estoque/localidade, editar e exclusão lógica auditada.
- PowerPoint do Mapeamento ATM com fotos em proporção preservada.
- Monitoramento de Coletas com cache fail-safe da REV2.1.

Release: `V82.30 REV3`
