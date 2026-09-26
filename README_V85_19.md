# V85.19 — Evidências + Performance

Base: V85.18 homologada.

- Simulação de retenção 30/60/90 dias preservada.
- Execução controlada liberada inicialmente para Troca de Chips Recarga e EMV concluídas.
- Fluxo: simular -> revisar quantidade/espaço -> confirmação explícita `EXCLUIR EVIDENCIAS` -> excluir objetos R2 elegíveis -> remover somente metadados de foto -> preservar atividade/histórico -> AuditEvent.
- Nenhuma limpeza automática de objetos órfãos.
- Visão Panorâmica, Relatórios de Visita e Bobinas permanecem fora da execução desta versão.
- Diagnóstico de performance PostgreSQL permanece somente leitura; nenhum índice/DDL é criado automaticamente.
