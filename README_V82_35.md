# V82.35 — Mobile Arrow (pré-homologação)

Atualiza o endpoint /api/mobile/v1/sync/events para aplicar ARROW_ACTION em atividades atribuídas ao usuário, com eventos idempotentes, captura original, registro ArrowActivityExecution e validações de jornada/permissão. O bootstrap inclui localidade e descrição.

**Não homologado para produção.** Validar em homologação: permissões, jornada, eventos em conflito, duplicidade, ordem de execução, persistência e visualização no Web. A checagem de jornada ocorre no momento da sincronização, não reconstitui autorizações históricas do instante offline. Fotos não incluídas nesta entrega parcial.
