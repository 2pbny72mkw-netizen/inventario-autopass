# Inventário Autopass — V82.32

Fundação backend/API para cliente Android e operação offline.

## Entregas
- API mobile v1: `/api/mobile/v1/bootstrap`, `/api/mobile/v1/sync/events` e `/api/mobile/v1/sync/status`.
- Registro de dispositivo e envelope de evento com `event_id` único para reenvio idempotente.
- Preservação de `captured_at` (instante real no aparelho) e `received_at` (chegada ao servidor).
- GPS offline já aplicável ao histórico com `source=android_offline`.
- Permissões do mobile derivadas da mesma Matriz de Permissões do sistema.
- Pacote bootstrap com jornada e atividades Arrow atribuídas para preparação de cache local.
- Correção incorporada do exportador PowerPoint do Mapeamento ATM: timeout curto no R2, retry limitado e falha individual de foto sem abortar o book.

## Escopo
Esta versão prepara o servidor. O APK Android entra na etapa seguinte (V82.33 / Android A0.1).
