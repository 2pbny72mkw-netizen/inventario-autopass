V50.4 - Estabilização de backend e Financeiro ATM

Correções:
1. Dashboard Implantação: importa make_response no Flask e elimina NameError/HTTP 500.
2. Visão Geral/API dashboard: importa and_ do SQLAlchemy e elimina falha não crítica de produtividade/divergências.
3. Financeiro ATM: restaura o carregamento via /api/dashboard/atm-financial e renderização de cards, gráficos e tabela.
4. PWA/cache versionado para V50.4.

Aceite:
- /implantacao-hardware/dashboard retorna 200 e renderiza a Dashboard Implantação 2.0.
- Financeiro ATM deixa de exibir zeros quando a API possui dados.
- Logs não registram NameError para make_response ou and_.
