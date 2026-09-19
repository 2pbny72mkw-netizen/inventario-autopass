# Inventário Autopass — V82.34

Versão de fechamento da fundação Mobile API antes do primeiro cliente Android.

## Alteração principal
- Isola integralmente a autenticação de `/api/mobile/v1/*` da sessão Web.
- Endpoints Mobile passam a aceitar exclusivamente `Authorization: Bearer <token>` válido.
- Cookie/sessão Web não é mais usado como fallback na API Mobile.
- Token revogado, expirado, ausente ou de usuário inativo retorna HTTP 401 mesmo quando o navegador estiver autenticado no sistema Web.

## Preservado da V82.33 REV1
- Mesma validação de credenciais para login Web e Mobile.
- Username case-insensitive e senha case-sensitive.
- Validação de jornada.
- Token por dispositivo, expiração e revogação.
- Bootstrap com usuário, permissões, jornada e atividades Arrow.
- Sincronização offline com `device_id`, `event_id` e idempotência.
- GPS offline preservando `captured_at`.

## Teste pós-deploy prioritário
1. Fazer login Mobile e confirmar `/api/mobile/v1/auth/me` = 200.
2. Executar `/api/mobile/v1/auth/logout` = 200.
3. Reutilizar o mesmo Bearer token em `/api/mobile/v1/auth/me`, mesmo com a sessão Web aberta: deve retornar 401.
