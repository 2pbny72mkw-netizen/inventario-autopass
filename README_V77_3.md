# Inventário Autopass — V77.3

## Escopo consolidado

- Base oficial ATM soberana: **602 ATMs = 590 instaladas + 12 em estoque**. A planilha de bobinas nunca cria ATM.
- Importador de Bobinas reescrito para leitura sequencial (`iter_rows`) e validação em memória, eliminando consultas repetidas por linha/célula.
- Importação como retrato: substitui somente eventos anteriores de `IMPORTACAO`; registros de campo são preservados.
- ATMs fora da base oficial, ATMs em estoque e divergências de localidade ficam separadas para tratamento, sem alterar o parque.
- Novo histórico persistente de divergências por lote (`atm_bobbin_import_divergences`).
- Dashboard Bobinas reconstruída conforme o esboço aprovado: KPIs brancos com ícones, tabela por estação, detalhe da estação, histórico da ATM, evolução e indicadores.
- KPI de cobertura usa como denominador as 590 ATMs instaladas (ou o universo oficial filtrado).
- Reservas confirmadas nas ATMs, armários, distribuição e saldo legado não localizado permanecem separados.
- Importações exibem barra de progresso, prévia detalhada e confirmação antes da gravação.
- GPS da Atividade Bobinas é evidência no salvamento; não bloqueia nem determina a localidade escolhida.
- Estoque Field: corrigido `FieldLoadRegularization.requested_at` no dashboard (erro 500) e retirada para carga passa a ter rollback e mensagem controlada.
- Importação Estoque Field mostra destino/ponto/item na prévia.

## Migração

- `V77.3-001`
- Cria somente a tabela aditiva `atm_bobbin_import_divergences` quando ausente.
- Não altera nem recria a base oficial ATM.

## Pós-deploy recomendado

1. Abrir Dashboard Bobinas e validar `Base oficial: 602 · 590 instaladas · 12 estoque`.
2. Validar uma planilha de bobinas sem confirmar e revisar divergências.
3. Confirmar a importação e verificar imediatamente KPIs/tabelas do dashboard.
4. Abrir `/api/bobinas/dashboard` e confirmar `summary.official_total=602`, `official_installed=590`, `official_stock=12`.
5. Abrir Estoque Field e confirmar `/api/field-stock/dashboard` em HTTP 200.
6. Testar uma retirada para carga com saldo disponível e confirmar baixa + carga do técnico.
