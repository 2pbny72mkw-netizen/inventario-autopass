# Inventário Autopass V56-A.4 — atualização enxuta

Aplicar sobre a V56-A.3 HOTFIX2.

Principais alterações:
- Financeiro: lançamentos mensais em tabela, com editar/excluir/incluir e salvar em lote.
- Competência nova pode herdar fornecedor, serviço, forecast e rateio da última competência do mesmo centro de custo; realizado e NF não são copiados.
- Campo NF/documento nos lançamentos financeiros.
- Usuários: controle de visualização por módulos, com padrão por perfil e proteção de áreas sensíveis no backend.

Após publicar, reinicie a aplicação para executar as migrações aditivas de `users.access_json` e `financial_monthly_costs.invoice_number`.
