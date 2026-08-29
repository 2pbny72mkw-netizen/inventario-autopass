V69.2.1 HOTFIX3 — PADRONIZAÇÃO UX / NAVEGAÇÃO / DASHBOARD 2.0

1. Menu principal padronizado
- Dashboard passa a ser a central única de dashboards.
- Removido Dashboard Field do submenu Field.
- Removido Dashboard Implantação do submenu Implantação de Hardware.
- Removido Dashboard Financeiro do submenu Financeiro.
- Field, Implantação e Financeiro ficam orientados a atividades.

2. Central de Dashboards
- /dashboard agora abre uma central de painéis, respeitando permissões.
- Acessos para Visão Geral, Field, Recarga, Panorâmica, EMV, Garagem, Implantação, ATM, Contratos ATM e Financeiro conforme permissão.

3. Dashboard Field 2.0 interativa
- Filtros automáticos: Empresa, Linha, Localidade, Tipo, Status, Técnico e Período.
- Big numbers clicáveis com detalhamento em modal.
- Barras por tipo clicáveis aplicam filtro global.
- Limpar filtros e Atualizar.
- Sem botão Aplicar.
- Drill-down de Equipamentos, Inoperantes, Divergências, Chamados, Trocas e Concluídas.

4. Correção dos atalhos Dashboard das atividades
- Recarga -> /gerencial?view=chips.
- Visão Panorâmica -> /gerencial?view=panorama.
- EMV -> /gerencial?view=emv.
- Garagem mantém dashboard dedicado.
- Implantação usa dashboard dedicado.
- Corrige o problema em que o botão Dashboard caía na Visão Geral.

5. Visão Panorâmica
- Filtro Empresa deixa de reaplicar seleção incompatível.
- Ao trocar Empresa, Linha é recalculada.
- Linha incompatível é automaticamente limpa.
- Opção Todas volta a funcionar como limpeza real do filtro.

6. Atividade 2.0
- Linguagem visual global mais compacta.
- Navegação contextual Atividade | Dashboard | Exportar quando aplicável.
- Melhoria de responsividade e contenção de rolagem horizontal.
- Tabelas usam rolagem local quando necessário, sem alargar a página inteira.

7. Implantação
- Tela principal passa a ser operacional.
- Retirado card duplicado de Dashboard do hub.
- Botão Dashboard contextual no topo.

8. Financeiro
- Dashboard retirado do submenu principal.
- Central Financeira recebe botão Dashboard contextual.
- Dashboard Financeiro permanece acessível pela Central de Dashboards.

ARQUIVOS DO HOTFIX ENXUTO
- app.py
- templates/base.html
- templates/dashboard_hub.html
- templates/field_dashboard.html
- templates/hardware_implantation.html
- templates/financial_cost_management.html
- templates/chip_swap.html
- templates/emv_chip_swap.html
- templates/panorama.html
- static/panorama.js

VALIDAÇÃO
- app.py: py_compile OK
- templates alterados: parse Jinja OK

Base: V69.2.1 + HOTFIX2.
