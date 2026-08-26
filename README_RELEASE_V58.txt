V58 — Performance + Operação 2.0

Principais evoluções:
- Equipes: sincronização de perfis de escala em lote com TTL, removendo N+1 de centenas de queries por requisição.
- Equipes: mantém Operação de Hoje, equipe prevista, login/GPS e estação mais próxima no fuso America/Sao_Paulo.
- Locations: resposta padrão leve; cálculo pesado de referência GPS observada somente em ?observed=1 para o fluxo Técnico.
- TopDesk: cache por filtros funcionais (ignora cache-busters) e KPIs principais em uma única agregação SQL.
- Financeiro/Apuração: cache curto de terminais, JOIN/subquery para metadados e agregação de contagem/últimas datas; índices adicionais.
- Frontend/PWA: cache-busting V58 e service worker atualizado no arquivo realmente servido.
- Telemetria permanece como baseline para medir P95, SQL e queries/requisição.

Critérios desejados de homologação:
- Equipes status/calendário: queda drástica das queries/requisição.
- /api/locations: resposta padrão abaixo da rota pesada anterior.
- TopDesk repetido: cache HIT sem recálculo por timestamp de frontend.
- Apuração/terminais repetido: cache HIT e menor custo SQL.
