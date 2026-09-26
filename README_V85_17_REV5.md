# V85.17 REV5 — Correção do estado de seleção

Base: V85.17 REV4.

## Correção
- `V8517REV1_SELECTED` foi movido para dentro do mesmo IIFE/closure que contém `V`, `$`, `render`, `apply`, `load` e todas as funções `v8517Bulk*`.
- `v8517RowKey` também foi movida para o mesmo closure.
- Isso elimina a dependência de estado top-level e garante que renderização, onchange, seleção em lote e exclusão compartilhem a mesma instância.
- Cache-busting atualizado para 85.17.5.
- Mantidas as correções REV3/REV4: summary nulo e import copy.

Sem novas funcionalidades ou alterações nas regras financeiras.
