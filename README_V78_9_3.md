# V78.9.3 — Arrow / APT

Base: V78.9.2.

## Arrow
- Nova aba **Minhas atividades — usuário**, com as atividades atribuídas ao colaborador logado.
- Calendário geral continua visível; atividades sem permissão de alteração abrem em modo somente leitura.
- Cada colaborador recebe cor visual estável no calendário e o card mostra o nome do responsável; o status permanece em badge separado.
- Filtro **Empresa do colaborador** antes do Técnico; o combo de Técnico é reduzido conforme a empresa selecionada.
- Campo antigo **Operadora** padronizado visualmente como **Empresa da atividade**: METRO, CPTM, MOTIVA ou OUTROS. OUTROS continua usando localidades cadastradas/garagens e permite nova localidade para quem possui `arrow.manage`.
- Big Numbers clicáveis: Total, Concluídas, Em andamento, Planejadas, Atrasadas e Canceladas abrem modal com o detalhamento das atividades do recorte atual.
- Botão **Excluir atividade** no modal, com exclusão lógica, auditoria e permissão `arrow.delete`/gestão.
- Técnicos não podem editar/excluir atividade de outro técnico, mesmo que visualizem o calendário.
- Notificação interna ao colaborador em nova alocação e em alterações relevantes/cancelamento; link direciona para Minhas atividades.
- Menu Arrow ganha **Minhas atividades** e acesso às notificações para usuários Arrow que não tenham o módulo gerencial de notificações.

## APT
- Linhas controladas por cadastro `apt_required_lines`, com carga inicial: 04 - AMARELA, 05 - LILÁS, 08 - DIAMANTE e 09 - ESMERALDA.
- Criação/edição de APT valida contra esse cadastro, evitando texto livre.
- Modal **Incluir colaborador / APT** ganha filtro por empresa antes da seleção do usuário.
- Filtros da tela APT passam a aplicar automaticamente ao alterar combos; busca textual usa debounce. Removido o botão Aplicar; permanece **Limpar filtros**.

## Migração aditiva/idempotente
- Cria `apt_required_lines` se necessário e semeia 04/05/08/09.
- Adiciona `arrow_activities.deleted_at` e `arrow_activities.deleted_by` se necessário.
- Registra `V78.9.3-001` em `schema_migrations`.

## Arquivos alterados
- `app.py`
- `templates/arrow_v75.html`
- `templates/apt_v73.html`
- `templates/base.html`
- `templates/notifications.html`
- `templates/about.html`
