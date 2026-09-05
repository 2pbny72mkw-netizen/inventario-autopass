# Sistema de Gestão Autopass — V73.6.3 ENXUTA

Correção focada na Dashboard ATM da V73.6.2.

## Diagnóstico confirmado
- A base oficial ATM está disponível e o endpoint de contratos retorna 602 ativos.
- A tela `Dashboard ATM` permanecia com KPIs em zero.
- Foi mantido o endpoint canônico `/api/dashboard/inventory-atm` e adicionado um carregador dedicado, versionado e sem cache para a tela ATM.

## Alterações
- `APP_RELEASE` atualizado para `V73.6.3`.
- Novo `static/atm_dashboard_v7363.js` carregado após `equipment_inventory_dashboards.js`.
- O novo carregador atualiza KPIs, filtros, gráficos, ranking, tabela e exportação CSV usando `/api/dashboard/inventory-atm`.
- Cache-buster por arquivo novo + `cache: no-store`, reduzindo risco de JS antigo retido pelo Service Worker.
- Histórico `Sobre` atualizado.

## Validação pós-deploy
1. Abrir Dashboard ATM.
2. Network → confirmar `/api/dashboard/inventory-atm?...` com HTTP 200 e `ok: true`.
3. Confirmar que `Total oficial`, `Alocados`, `Estoque`, `Estações CPTM`, `Estações Metrô` e `TeamViewer` deixam de permanecer em zero.
4. Testar filtros Operadora/Linha/Localidade/Modelo/Contrato/Posse/Status e `Limpar filtros`.
5. Testar Atualizar e Exportar CSV.

Pacote enxuto: substitua apenas os arquivos contidos no ZIP.
