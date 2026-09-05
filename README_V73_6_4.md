# Sistema de Gestão — V73.6.4

## Escopo
Correção restrita ao Dashboard EMV · Trilhos e versionamento do asset principal do Dashboard.

## Diagnóstico confirmado antes da versão
- `/api/chip-swaps/dashboard` responde `ok: true`.
- Resumo observado no ambiente: 646 total, 560 concluídos, 1 em andamento, 85 pendentes, 86,7%.
- O frontend exibia 0 porque o cockpit recalculava os KPIs apenas pelas linhas/validators em vez de usar o `summary` consolidado da API no recorte padrão.

## Alterações
- `static/manager.js`: `chipDashRender()` usa `chipDashData.summary` sem filtros.
- Com filtros, os KPIs continuam sendo recalculados pelo recorte visível.
- Produtividade sem filtros usa `chipDashData.technicians`; com filtros continua derivada dos itens visíveis.
- `templates/manager.html`: cache-buster de `manager.js` atualizado para `v73-6-4`.
- `app.py`: `APP_RELEASE = V73.6.4`.
- `templates/about.html`: histórico V73.6.4.

## Regressão pós-deploy
1. Dashboard EMV deve abrir com 646 / 560 / 1 / 85 / 86,7% no recorte padrão (enquanto a base não mudar).
2. Validar Operadora, Linha, Estação, Status e Resultado.
3. Validar Progresso por estação e Produtividade por técnico.
4. Validar Dashboard ATM, que não deve regredir.
5. No Network, `/api/chip-swaps/dashboard` deve responder 200 e `manager.js?v=v73-6-4` deve ser carregado.
