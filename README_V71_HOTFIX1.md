# V71 HOTFIX1 — Logística / Portal

Correções pontuais sobre a V71, sem mudança funcional de escopo.

## 1. Importação Leva e Traz
- normaliza e consolida garagens repetidas na própria aba `Resumo` antes de gravar;
- bloqueia a importação quando a mesma garagem aparece em dias da semana diferentes;
- mantém mapa em memória das novas garagens durante a mesma importação;
- usa `session.no_autoflush` ao tentar vincular a garagem ao cadastro de clientes, evitando INSERT prematuro;
- reimportar a mesma matriz passa a atualizar registros existentes, em vez de tentar criar uma segunda garagem.

Corrige o erro PostgreSQL `UniqueViolation` em `ix_logistics_garage_routes_garage_name` (ex.: Caieiras).

## 2. Schema legado do Portal do Cliente
A migração V71 agora valida/cria também, de forma aditiva e idempotente, as colunas:
- `customer_appointments.invoice_number`
- `customer_appointments.invoice_file`
- `customer_appointments.invoice_original_name`

Corrige o erro `UndefinedColumn` ao abrir Gestão de Agendamentos em bancos que vieram de versões anteriores.

## Deploy
Aplicar sobre a V71 já instalada e reiniciar o serviço. Nenhuma limpeza do banco é necessária.
