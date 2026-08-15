AUTOPASS — V1.1 OPERACIONAL + DASHBOARD EXECUTIVO V2.5

Evoluções principais:
- KPIs e localidades carregam antes do GPS/mapa.
- GPS/mapa deixam de bloquear os Big Numbers.
- Atualização automática a cada 120 segundos.
- Indicador de tempo de carregamento.
- Big Numbers e filtros executivos preservados.
- Exportação CSV conforme filtros executivos.
- Novo indicador Não classificados para reconciliação.
- /api/dashboard passa a retornar inventory.classified e inventory.unclassified.
- Ranking de pendências considera os cinco tipos.
- Mapa atual preservado para evitar regressão.

Mapa - próxima etapa:
- Linha 4-Amarela: revisar referências geográficas.
- Linha 17-Ouro: incluir localidades/pontos na base.

Arquivos alterados:
- app.py
- static/manager.js
- static/app.css
- templates/manager.html

Teste após Live:
1. window.AUTOPASS_MANAGER_VERSION -> dashboard-v2-5
2. /api/dashboard -> release v1.1-operacional-dashboard-v2.5
3. Confirmar KPIs, filtros, Exportar CSV, mapa e tela técnica.
