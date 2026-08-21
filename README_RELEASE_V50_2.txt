Inventário Autopass — V50.2 ENXUTO

Hotfix estrutural de PWA/cache.

- Service Worker não intercepta navegação, HTML, dashboards, APIs ou rotas autenticadas.
- /static usa network-first; cache apenas como fallback.
- Caches antigos são apagados automaticamente na ativação.
- Registro usa /sw.js?v=v50-2 e updateViaCache=none.
- sw.js e manifest são enviados com no-store/no-cache.
- Manifest corrigido com ícones quadrados 192x192 e 512x512.
- Versionamento visual/cache atualizado para V50.2.

CORRECAO ADICIONAL V50.2:
- Incluidas no pacote enxuto as bases ATM exigidas pelo backend:
  data/atm_official_082026.json (602 ATMs)
  data/atm_complement_20260820.json (TeamViewer/complemento)
  data/atm_financial_082026.json (financeiro ATM)
- Evita Dashboard ATM zerada quando o deploy utiliza somente o pacote enxuto.
