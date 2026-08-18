V39.7 — pacote enxuto

Nova atividade: Troca de Chips — Validadores de Recarga
- Nova aba superior Troca de Chips.
- GPS identifica/sugere a localidade mais próxima com referência cadastrada.
- Lista somente Validadores de Recarga da base associados à estação.
- Evidência por foto; ao menos uma foto conclui automaticamente o equipamento.
- Status: PENDENTE, EM ANDAMENTO e CONCLUÍDA.
- Registro de técnico, data/hora, GPS, equipamento, observação e evidência.
- Auditoria CHIP_SWAP_UPDATE.

Dashboard
- Nova aba lateral Troca de Chips.
- Indicadores: total previsto, concluídos, em andamento, pendentes e percentual.
- Filtros por empresa, linha e localidade.
- Progresso por localidade e produtividade por técnico.

Banco de dados
- As tabelas chip_swaps e chip_swap_photos são criadas automaticamente pelo db.create_all().

Pacote incremental sobre a V39.6.
