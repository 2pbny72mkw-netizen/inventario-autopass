V56-A.2 — hotfix de estabilidade e polling

- Elimina tempestade de chamadas em /api/topdesk/import/active.
- Polling singleton: 10s somente durante importação ativa; 60s quando ocioso; suspenso/reduzido com aba em background.
- Impede múltiplos timers concorrentes na mesma aba e chamadas simultâneas (inflight guard).
- Backfill TopDesk mais gentil com PostgreSQL/Render: lotes de 250 e pausa de 200ms entre commits.
- Ajusta exibição de bloqueios EMV manuais: Terminal a definir e validação contra placeholders.
- Mantém dados existentes e não requer nova importação TopDesk.
