# V71.4 — Dashboards de Parque pelo Inventário

Base funcional: V71.3 HOTFIX5.

## Novos dashboards
- Dashboard POS
- Dashboard Validador de Recarga + TDI
- Dashboard Bloqueio

## Fonte dos dados
Todos os novos dashboards consultam exclusivamente a tabela `inventory` do Sistema de Gestão,
com dimensões de `locations` e complementos técnicos de `base_assets` quando vinculados.
A planilha não é consultada pelos dashboards em produção.

## Conteúdo
Filtros globais por empresa, linha, localidade, modelo e status.
Validador + TDI possui filtro adicional por tipo.
KPIs de total inventariado, localidades, modelos, conciliação com base e divergências.
Gráficos por operação, mix de modelos, ranking de localidades, status, fornecedores e versões/tipo de instalação.
Tabela detalhada e exportação CSV do recorte.

## Navegação
Novos itens na lateral da Central de Inteligência:
Dashboard POS, Dashboard Validador + TDI e Dashboard Bloqueio.

## Banco
Sem migração estrutural.
