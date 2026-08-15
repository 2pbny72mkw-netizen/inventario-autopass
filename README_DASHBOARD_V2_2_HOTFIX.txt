AUTOPASS — Dashboard Executivo V2.2 Hotfix

CAUSA ENCONTRADA
O backend /api/dashboard está correto e retorna os dados.
O frontend parava em loadAll() porque tentava escrever no elemento #openLocations,
que não existe no manager.html.

CORREÇÕES
- #openLocations agora é opcional e não interrompe o carregamento.
- IDs duplicados de Divergências/Inoperantes foram corrigidos na área de Qualidade.
- Versão do manager.js alterada para dashboard-v2-2.
- Cache-busting atualizado para ?v=dashboard-v2-2.

VALIDAÇÃO INTERNA
IDs referenciados mas ausentes no HTML: ['openLocations']
IDs duplicados restantes: []

UPLOAD
Substitua somente:
- static/manager.js
- templates/manager.html

Depois Commit + Deploy latest commit + Ctrl+F5.

TESTE
window.AUTOPASS_MANAGER_VERSION
Esperado: "dashboard-v2-2"
