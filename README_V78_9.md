# V78.9 — Perfis & Permissões sem amarrações indiretas

## Regra central
- ADM (`manager`) permanece superusuário.
- Qualquer outro perfil usa exclusivamente a Matriz de Permissões / `access_json` efetivo.
- Nome do perfil-base não acrescenta nem remove permissões.
- Perfil-base passa a representar apenas comportamento operacional/legado, não autorização de módulos.

## Correções principais
- Removidos acréscimos automáticos de Bobinas para Técnico e Gestor Field.
- Removidos filtros de permissões que impediam RH de salvar acessos Field/Financeiro/Gestão quando marcados.
- `_parse_access_form` grava exatamente as permissões marcadas.
- Usuário vinculado a `SystemProfile` recebe exatamente as permissões do perfil configurável.
- Login, `/` e `/dashboard` escolhem a tela inicial pelas permissões efetivas, não pelo nome do perfil.
- Novas permissões de governança: `users.roles.manage` e `users.scope.all`.
- Menus e rotas principais de Field, Implantação, Financeiro, Gestão, RH/APT, Portal e Engenharia foram alinhados à matriz.
- Dashboard Bobinas passa a depender de `field.bobbins_dashboard`; Atividade Bobinas de `field.bobbins`; estoque de `field.stock_manage`.
- Configuração de dashboards deixa de usar lista de roles como autorização efetiva; o legado fica apenas armazenado para compatibilidade.
- Exclusão definitiva de estrutura BOM permanece exclusiva do ADM, conforme regra de exceção.

## Teste de regressão recomendado
1. Criar/editar perfil RH.
2. Marcar apenas `Atividade Bobinas`, `Dashboard de Bobinas / Insumos` e `Alterar estoque consolidado / armários / bobinas`.
3. Salvar, atualizar a página e confirmar que as três permissões permanecem marcadas.
4. Sair e entrar novamente com usuário vinculado ao perfil.
5. Confirmar acesso a Bobinas e ausência dos módulos não marcados.
