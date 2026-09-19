# Inventário Autopass — V82.33 REV1

Hotfix concentrado na autenticação Mobile API.

- Centraliza a validação de credenciais em `_authenticate_user_credentials`.
- `/login` Web e `/api/mobile/v1/auth/login` passam a usar exatamente a mesma rotina.
- Username permanece case-insensitive; senha permanece case-sensitive; somente usuários ativos autenticam.
- Preserva validação de jornada, dispositivo, Bearer token, expiração/revogação, bootstrap e sincronização da V82.33.
- Adiciona diagnóstico seguro no Render para distinguir usuário não localizado de senha inválida, sem registrar a senha.
- Resposta 401 mobile inclui `code=INVALID_CREDENTIALS` para facilitar diagnóstico.

Teste pós-deploy prioritário: login web e, em seguida, POST `/api/mobile/v1/auth/login` com as mesmas credenciais válidas.
