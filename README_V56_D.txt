V56-D — Performance & Consolidação Operacional

Principais mudanças:
- EMV: dashboard consolidado em uma única implementação JS, consumindo {ok, rows[]} e usando os IDs/filtros reais da tela.
- Equipes: assets estáticos realmente atualizados para V56-D, data operacional em America/Sao_Paulo e diagnóstico explícito de /api/equipes/status.
- Equipes backend: calendário e perfis sem N+1 de usuários.
- Mapa: rail-network leve; preserva correção Leaflet e evita /api/locations no fluxo de trilhos.
- /api/locations: cache curto de 20s para requisições concorrentes repetidas.
- TopDesk Dashboard: fast path por agregações SQL quando sem filtros; cache de 5 min.
- TopDesk Analytics: cache padrão ampliado para 5 min.
- Telemetria: Top 5 gargalos com decomposição SQL x aplicação.
- Service Worker/cache-busting renovados para impedir JS antigo após deploy.

Validação prioritária pós-deploy:
1) Dashboard EMV deve mostrar total/filtros/progresso.
2) Equipes deve mostrar escalados/operação do dia e mapa.
3) Telemetria: comparar TopDesk, locations, equipes/status e equipes/calendario.
