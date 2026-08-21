V50.3 - Hotfix de estabilização

1. Dashboard ATM: corrigido bug de inicialização. A carga não depende mais da existência do botão Aplicar, removido nas versões anteriores.
2. Dashboard ATM: falhas de API passam a ser exibidas explicitamente, sem mascarar erro como contagem zero.
3. Dashboard Implantação: navegação dedicada e cache HTTP desativado para evitar conteúdo antigo/atividade na URL da dashboard.
4. PWA: cache V50.3; navegações continuam fora do Service Worker.

Teste de aceite:
- Dashboard ATM deve exibir a base retornada por /api/dashboard/inventory-atm (602 no universo sem filtros).
- Dashboard Implantação deve abrir /implantacao-hardware/dashboard e exibir o Command Center da Implantação.
