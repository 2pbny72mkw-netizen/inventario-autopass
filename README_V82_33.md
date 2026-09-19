# Inventário Autopass — V82.33

Evolução da fundação mobile iniciada na V82.32. Foco: autenticação e sessão próprias para o futuro cliente Android A0.1, preservando a plataforma web e a Matriz de Permissões.

## Entregas
- Mantém integralmente a fundação V82.32: bootstrap, sincronização idempotente, GPS offline e registro de dispositivo.
- Nova autenticação mobile por `POST /api/mobile/v1/auth/login`.
- Token Bearer aleatório por usuário/dispositivo; o banco armazena somente SHA-256 do token.
- Expiração de sessão mobile em 30 dias e revogação no logout.
- Novo `GET /api/mobile/v1/auth/me` para validar sessão, usuário e permissões.
- Endpoints `bootstrap`, `sync/events` e `sync/status` passam a aceitar autenticação mobile Bearer, mantendo compatibilidade com sessão web/PWA.
- Jornada continua sendo validada no login mobile; usuário controlado fora da jornada recebe `OUTSIDE_JOURNEY`.
- Permissões continuam vindo da mesma Matriz de Permissões; nenhuma regra fixa por perfil foi adicionada.
- Vínculo de dispositivo permanece exclusivo por usuário.
- Migração `V82.33-001` cria somente a tabela `mobile_session_tokens`, sem alteração destrutiva de dados existentes.

## Fora do escopo desta versão
- APK final e distribuição em loja.
- Edição completa de atividades offline.
- Resolução avançada de conflitos de edição.

Esses itens permanecem para as próximas etapas do cliente Android.
