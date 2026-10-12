# Web V85.56 REV1
Base: V85.56. Suporte ao evento offline STOCK_WITHDRAW no endpoint móvel `/api/mobile/v1/sync/events`.
- Idempotência pelo envelope existente `MobileSyncEvent.event_id`.
- Verificação de permissões; saldo de armário bloqueado via `SELECT FOR UPDATE` (PostgreSQL).
- Transação de retirada, carga do técnico e confirmação no mesmo savepoint.
- Rejeição de saldo insuficiente, sem baixar estoque negativo.
- Sem migração de banco; não modifica demais módulos.
- Requer homologação em Render antes de instalar Android REV3.2.
