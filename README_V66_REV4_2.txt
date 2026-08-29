V66 REV4.2 — Performance 2.0

Objetivo
- Consolidar a correção de desempenho antes da V67.

Alterações
1. EMV legado /api/emv-chip-swaps/ deixa de redirecionar e passa a responder diretamente com payload SLIM, sem fotos/evidências.
2. Rota canônica permanece /api/emv-chip-swaps.
3. Cache-busting atualizado para manager.js e emv_chip_swap.js.
4. Namespace do Service Worker atualizado para forçar descarte de cache estático antigo.
5. Resumo TopDesk sem filtros usa status operacional para evitar processamento textual desnecessário.
6. Release atualizado para V66 REV4.2.

Validação após deploy
- Abrir EMV atividade e dashboard.
- Abrir TopDesk dashboard.
- Atualizar Telemetria após alguns minutos de uso.
- Verificar P95, /api/emv-chip-swaps/, /api/emv-chip-swaps e /api/topdesk/dashboard.
