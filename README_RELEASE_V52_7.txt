INVENTÁRIO AUTOPASS — V52.7 ENXUTA
Dashboard Chamados / TopDesk 2.0

ENTREGAS
- Base histórica TopDesk 2026 incluída como carga de referência (50.436 linhas no arquivo recebido).
- Dashboard /topdesk redesenhada com filtros únicos e encadeados.
- KPIs: chamados, equipamentos, localidades, chamados/equipamento, operadores, reincidência 24h/7d/30d.
- Evolução mensal, top falhas, linhas, localidades e equipamentos crônicos.
- Heatmap Dia da Semana x Hora.
- Produtividade: volume, dias ativos, chamados/dia, equipamentos, localidades, linhas e reincidência 7d.
- Visual Produtividade x Reincidência.
- Central de Atenção para equipamentos crônicos.
- Exportação Excel filtrada com abas Chamados, Produtividade e Crônicos.
- Preserva integralmente os arquivos da V52.6 no pacote enxuto.

REGRAS
- Reincidência = mesmo ID do objeto + mesma subcategoria em janela temporal. É indicador de contexto, não avaliação isolada do técnico.
- Linha/estação/modelo são extraídos do padrão de ID do objeto quando disponíveis e complementados pela localidade vinculada.
- Todos os componentes da Dashboard Chamados e o Excel usam o mesmo conjunto de filtros.

VALIDAÇÃO PRÉ-PACOTE
PASS: app.py compila.
PASS: static/topdesk.js passa node --check.
PASS: endpoints /api/topdesk/analytics e /topdesk/export.xlsx presentes.
PASS: filtros, heatmap, produtividade, reincidência e crônicos presentes no front-end.
PASS: V52.6 preservada por sobreposição sobre o main de referência.
LIMITAÇÃO: comportamento no PostgreSQL/Render depende da carga/migração e deve ser homologado após deploy.
