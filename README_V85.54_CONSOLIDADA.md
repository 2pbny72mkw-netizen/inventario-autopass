# V85.54 CONSOLIDADA — implantação e limites

Base: V85.51. Inclui três frentes em um único pacote de código:
- Processamento assíncrono: fila persistente PostgreSQL para **exportação CSV de tarefas**; worker separado `python worker_v8554.py`.
- Dashboards 2.0: painel operacional com KPIs de tarefas e atalhos aos dashboards Field, Implantação, Financeiro e Geral conforme Matriz de Permissões. Não substitui nem reescreve os painéis existentes.
- Gestão de tarefas: agenda mensal por responsável integrada ao Kanban já existente.

## Implantação Render
1. Backup do banco e implantação de teste.
2. Publicar o Web como antes.
3. Garantir a criação da tabela `report_jobs_v8554` pelo mecanismo de criação de tabelas existente no app; verificar antes de usar a fila.
4. Criar um **Background Worker** com o mesmo repositório e variáveis de ambiente (`DATABASE_URL`, `INVENTARIO_SECRET_KEY`), comando `python worker_v8554.py`.
5. Sem o worker, a criação de pedidos funciona, mas os relatórios permanecem PENDING.
6. Validar permissões, criação de tarefa, agenda, relatório, recuperação de worker e download.
7. Em caso de rollback, voltar à V85.51; não excluir as tabelas ou dados históricos.

## Escopo ainda não coberto
- Execução assíncrona de todos os relatórios e exportações existentes: requer adaptação individual.
- Consolidação de todos os indicadores Field/Implantação/Financeiro numa única consulta: nesta entrega são links para as telas oficiais.
- Calendário drag-and-drop e notificações automáticas: ainda não incluídos.
- Android, GPS e cache offline: planejados para V85.55.

A fila usa CSV armazenado no PostgreSQL: adequada apenas a relatórios pequenos e médios (até 10 mil tarefas). Não usar para arquivos pesados ou fotografias. 
