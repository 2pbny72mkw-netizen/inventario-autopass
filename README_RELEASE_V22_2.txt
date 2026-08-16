Inventário Autopass V22.2 HOTFIX

Correções principais:
- Corrige HTTP 500 em /api/dashboard causado por timedelta não importado.
- Corrige calendário/escala 7/14/21/31 dias pelo mesmo erro de timedelta.
- Service Worker reescrito para evitar clone de Response já consumida e não cachear rotas gerenciais/API críticas.
- Manifest PWA corrigido com ícones quadrados 192x192 e 512x512.
- Releases/cache atualizados para V22.2.

Após deploy:
1. Forçar atualização/recarregar sem cache ou fechar/reabrir PWA.
2. Validar Dashboard com números.
3. Validar Equipes 7/14/21.
4. Só depois validar R2 e pequena reimportação de mídias.
