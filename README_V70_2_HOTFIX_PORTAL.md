# V70.2 HOTFIX — Portal Cliente / Novo Agendamento

Correção localizada para o perfil Cliente no Portal do Cliente.

- Corrige o deslocamento/corte horizontal ao clicar em **Novo Agendamento** na barra lateral.
- Remove o scroll nativo causado pela navegação por âncora `#new`.
- Troca a navegação lateral por alternância de aba via JavaScript com `history.replaceState`, sem deslocar horizontalmente o viewport.
- Reforça contenção de largura dos painéis `#new` e `#history` e bloqueia overflow horizontal do conteúdo principal.
- Mantém a sidebar fixa e não altera os fluxos de agendamento, upload, revisão, assinatura ou histórico.

Arquivos alterados:
- `templates/customer_portal.html`

Base: V70.2.
