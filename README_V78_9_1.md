# V78.9.1 — Correção de permissões

Base: V78.9 recebida em 09/09/2026.

Correções pontuais:
- `/usuarios`: exige `users.view`, sem exigir cumulativamente `users.config.view`.
- criação de usuário: exige `users.create`, sem exigir cumulativamente `users.config.manage`.
- edição de usuário: exige `users.edit`, sem exigir cumulativamente `users.config.manage`.
- Dashboard ATM: removida restrição hardcoded por `role=technician`; permanece protegido pelo `dashboard_required` e pela Matriz de Permissões.
- ADM/manager continua superusuário via `_has_access`.
- Regras explícitas de governança existentes não foram removidas.

Escopo deliberadamente corretivo; nenhuma funcionalidade da linha V78 foi substituída por arquivos V77.
