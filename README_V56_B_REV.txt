Inventário Autopass — V56-B REVISADA (correção de boot)

Correção aplicada após falha no deploy Render:
- registro da telemetria SQL não acessa mais db.engine fora do application context;
- listeners SQL são registrados dentro de app.app_context();
- evita erro "Working outside of application context" no boot do Gunicorn.

Escopo funcional da V56-B revisada permanece inalterado.
