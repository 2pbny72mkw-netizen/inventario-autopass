# V71.4 HOTFIX1 — Correção de loop de redirecionamento

## Correção
- Remove a canonicalização global de URLs adicionada na V71.4.
- Mantém `/gerencial` como URL oficial dos dashboards.
- `/dashboard` continua somente como alias legado.
- Remove uso de redirect 308 nos aliases internos para evitar conflitos com proxy/Flask.
- Mantém a rota canônica `/api/emv-chip-swaps`.
- Mantém o alias `/api/emv-chip-swaps/` apenas como compatibilidade explícita.
- Atualiza cache/Service Worker para `v71-4-hf1`.
- Sem migração de banco.

## URL oficial
`https://inventario-autopass.onrender.com/gerencial`
