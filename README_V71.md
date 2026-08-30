# V71 — Agendamento & Programação Leva e Traz

Base: V70.2 + HOTFIX Portal aprovado.

## Entregas
- Matriz Leva e Traz importável pela aba **Resumo** da planilha padrão.
- Modelo padrão disponível no sistema: `MODELO_LEVA_E_TRAZ_PADRAO.xlsx`.
- Importação preserva histórico, inclui/atualiza garagens e inativa registros ausentes da nova matriz.
- Datas de solicitação, prevista e programada separadas no banco.
- Cálculo automático da próxima data operacional conforme o dia semanal da garagem.
- Datas bloqueadas (feriado/sem operação) são ignoradas pelo cálculo.
- Portal do Cliente mostra a data da solicitação e a próxima data disponível antes da finalização.
- Opção "Precisa solicitar outra data?" com motivo/observação.
- Confirmação ao cliente: "Agendamento realizado com sucesso" + próxima data + situação "Na programação".
- Nova área interna **Portal do Cliente > Gestão de Agendamentos**.
- Resumo de solicitações do dia, garagens e quantidade de equipamentos.
- Visões "Solicitados hoje", "Programados para hoje" e "Todos".
- Calendário mensal com garagens/agendamentos/equipamentos por dia.
- Ajuste manual de data programada pela recepção, com bloqueio de datas sem operação.
- Matriz visual separada por Segunda a Sexta.

## Planilha padrão
A V71 considera a aba **Resumo** como fonte oficial do Leva e Traz. O formato esperado é:
- Coluna A: Garagem (com linhas de seção Segunda, Terça, Quarta, Quinta, Sexta)
- Coluna B: Contato
- Coluna C: Endereço
- Coluna D: Região

A planilha fornecida nesta versão contém 38 garagens na aba Resumo.

## Banco / migração
Migração aditiva `V71-001`:
- cria `logistics_garage_routes`
- cria `logistics_blocked_dates`
- adiciona em `customer_appointments`: `request_date`, `expected_date`, `programmed_date`, `alternate_date_requested`, `alternate_reason`
- cria índices das novas datas de agendamento

Nenhum histórico de agendamento recebido/concluído é recalculado pela importação.
