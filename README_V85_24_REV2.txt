V85.24 REV2 — PATCH ENXUTO

Correções:
- Gestão de Tarefas: corrigido erro JavaScript "missing ) after argument list" da REV1.
- Corrigida expressão de ordenação prioridade/data que interrompia toda a inicialização do Kanban.
- Simplificada a geração da ação Renomear etiqueta para evitar erro de sintaxe.
- Identificação atualizada para V85.24 REV2.

Arquivos alterados:
- app.py
- templates/management_tasks_v854.html

Validações:
- Python py_compile: OK
- JavaScript node --check: OK
- Jinja parse: OK
- ZIP integrity: OK
