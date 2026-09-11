# Sistema de Gestão Autopass — V79.5

Base: V79.4 REV2. Versão enxuta, sem reconstrução de módulos.

## Alterações
1. Arrow: nova permissão `arrow.edit` — **Editar atividade Arrow**. Visualização (`arrow.view`), criação/alocação (`arrow.manage`) e exclusão (`arrow.delete`) permanecem independentes. ADM mantém acesso integral.
2. Arrow: removida a restrição de edição/exclusão baseada em nome de perfil. A Matriz de Permissões é a fonte de verdade.
3. Arrow/Motiva: APT válida deixa de ser bloqueio para a alocação inicial. O acesso Motiva do colaborador continua sendo verificado; a validade da APT permanece como informação de governança/RH.
4. Cadastro de usuários: jornada estruturada em **Início da jornada**, **Fim da jornada**, **Início da refeição** e **Fim da refeição**. Refeição é flexível e não interfere no bloqueio de jornada.
5. Migração: horários legados são preservados e convertidos de forma aditiva; `work_shift` continua mantido para compatibilidade.
6. Bobinas: a permissão existente `field.bobbins_dashboard` passa a ser exibida explicitamente como **Visualizar Dashboard Bobinas** na Matriz. Rota e APIs continuam protegidas pela permissão.
7. Sobre: histórico atualizado para V79.5.

## Regressão mínima recomendada
- Login e landing page por permissão.
- Perfis & Permissões: salvar/remover `Editar atividade Arrow` e `Visualizar Dashboard Bobinas`.
- Arrow: usuário somente visualização abre modal sem salvar; usuário com `arrow.edit` edita; `arrow.delete` funciona de forma independente; criação continua exigindo `arrow.manage`.
- Arrow/Motiva: alocação de colaborador com acesso Motiva e APT vencida/ausente deve ser permitida.
- Usuários: criar/editar jornada; validar migração dos formatos `05:00-17:00` e `08:00-12:00-13:00-17:00`.
- Jornada/GPS: bloqueio deve considerar apenas início/fim, nunca refeição.
- Dashboard Bobinas: sem permissão, menu/rota devem permanecer bloqueados; com permissão, acesso normal.
