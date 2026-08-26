INVENTÁRIO AUTOPASS — V56-C

Objetivo: consolidar correções funcionais diagnosticadas na V56-B REV4 sem reintroduzir regressões de performance.

Correções principais:
1. Dashboard EMV: leitura robusta de {ok, rows}; normalização de status CONCLUÍDA/PENDENTE/EM ANDAMENTO; diagnóstico no Console com quantidade recebida.
2. Equipes/Mapa: proteção contra map.hasLayer(null) e inicialização das camadas antes da sincronização dos checkboxes.
3. Cache: manager.js e teams.js com nova versão; service worker usa novo namespace para invalidar assets antigos.
4. UI: menu/dropdowns ficam acima do Leaflet.
5. Mantidos os dados e rotinas da V56-B REV4, inclusive Apuração e importação em background.

TESTE APÓS DEPLOY
- Dashboard EMV: Operadora/Linha/Estação devem ser populados e totais > 0.
- Console: deve aparecer [V56-C] EMV API: N registro(s) recebidos.
- Equipes: abrir mapa e confirmar ausência do erro _leaflet_id in null; técnicos devem poder ser renderizados.
- Menu Gestão sobre o mapa: dropdown deve permanecer na frente.
- Telemetria: verificar P95/erros após os testes.
