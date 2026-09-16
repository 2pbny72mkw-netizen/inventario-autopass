# Inventário Autopass — V82.1

## Financeiro — importação TBForte
- Reforçada a idempotência por `source_hash`: registros já existentes são ignorados sem interromper a carga.
- Registros repetidos dentro do próprio arquivo/lote são deduplicados antes do INSERT.
- PostgreSQL continua usando `ON CONFLICT DO NOTHING` sobre `source_hash`, mantendo a restrição UNIQUE como proteção final.
- Campos monetários vazios na fonte passam a permanecer `NULL`; `0,00` somente é gravado quando zero foi efetivamente informado.
- Nenhum registro financeiro existente é removido ou sobrescrito por esta correção.

## Base
- Mantidas integralmente as evoluções da V82, incluindo Mapeamento ATM e Desempenho de Bobinas.
