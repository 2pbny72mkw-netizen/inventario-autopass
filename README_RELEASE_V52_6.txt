INVENTÁRIO AUTOPASS — V52.6

Objetivo: versão consolidada de estabilização antes da V55.

VALIDAÇÕES EXECUTADAS ANTES DO PACOTE
- Python: app.py compilado com py_compile.
- JavaScript: manager.js, financial_cost_management.js, chip_swap.js, cash_collection.js e hardware_implantation_dashboard.js validados com node --check.
- Checklist estático de aceite: 16/16 itens críticos PASS.

ALTERAÇÕES PRINCIPAIS
1. Dashboard Implantação: rota dedicada /implantacao-hardware/dashboard preservada e link direto no menu.
2. Filtro executivo: Empresa/Linha/Tipo/Situação aplicados ao recorte; status passou a participar do filtro global.
3. Visões Panorâmicas: painel executivo passa a respeitar Empresa/Linha/Situação do filtro superior.
4. Troca de Chips Recarga: Empresa -> Linha -> Localidade encadeados pelos registros reais da atividade; localidades sem ativos não entram; GPS não seleciona nem filtra estação; botão Limpar filtros.
5. Central Financeira: centro de custo em combo; serviço em campo único; Projeto para Implantação; valor e Forecast; rateio dinâmico Produto + percentual; validação 100%; edição completa sem prompt; exclusão administrativa e auditoria já suportadas pelo backend.
6. Produtos do rateio: lista dinâmica derivada dos tipos de equipamento da base, com aliases operacionais e fallbacks.
7. ATM Financeiro: Distribuição por contrato convertida de donut para barras horizontais; cores distintas e consistentes por modelo; Parque x Contrato x Faturado inclui diferença; bloco de divergências por modelo.
8. Dashboard 2.0: removidos Pizza explodida do parque e Parque por tipo 3D; substituídos por composição em barras e divergências do recorte. Inteligência Executiva recebe contraste claro.
9. Fontes: nome do arquivo Excel retirado do detalhamento financeiro e da Coleta de Valores.
10. Contratos ATM: vencimento não é inferido. API V30 usa somente datas existentes na base oficial importada; ausência vira SEM DATA.
11. Cache/release: V52.6.

OBSERVAÇÃO DE HOMOLOGAÇÃO
Comportamentos dependentes do banco PostgreSQL/Render e do conteúdo efetivamente importado devem ser confirmados no ambiente após deploy. O pacote evita afirmar datas de contrato que não estejam presentes na base oficial.
