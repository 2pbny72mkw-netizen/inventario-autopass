# V71.1 HOTFIX5

Aplicar sobre V71.1 + HOTFIX2 + HOTFIX3 + HOTFIX4.

Ajustes principais:
- Calendário: remove a faixa extensa de chips de bloqueios; mantém apenas um resumo e destaca o bloqueio diretamente na célula do dia.
- Clique em qualquer dia do calendário abre uma janela com a programação do dia.
- Janela diária pronta para impressão / salvar em PDF e compartilhar no WhatsApp.
- Compartilhamento no WhatsApp usa mensagem padronizada como ATIVIDADE AGENDADA ou NOVA ATIVIDADE e registra auditoria no sistema.
- Dia bloqueado pode ser liberado pela própria janela do calendário.
- Cadastro de clientes/garagens: botões Editar e Excluir/Inativar lado a lado.
- Editar abre modal amplo, em vez do formulário comprimido dentro da tabela.
- Filtros por busca, status e cadastro completo/pendente.
- KPI Cadastros pendentes.
- Regra de pendência: falta contato, e-mail, telefone/celular, endereço ou cidade/região.
- Exportação Excel de clientes/garagens com status de cadastro e lista de pendências.

Validação executada:
- py_compile app.py: OK
- parse Jinja logistics_schedule.html: OK
- parse Jinja customer_companies.html: OK
