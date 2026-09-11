# V79.5 REV3 — Correção Dashboard Bobinas na navegação

Base: V79.5 REV2.

## Correção
- O menu superior `Field` passa a exibir **Dashboard Bobinas** quando a permissão `field.bobbins_dashboard` / **Visualizar Dashboard Bobinas** estiver habilitada.
- A visualização não depende de `field.bobbins` (Atividade Bobinas) nem do nome do perfil.
- A rota `/dashboard/bobinas` e as APIs continuam protegidas pela mesma permissão de visualização.
- ADM mantém acesso integral pelas regras existentes.

## Preservado
- Banco e dados.
- Demais permissões.
- Atividade Bobinas e Estoque Field como controles independentes.
- Correções Arrow e Histórico da V79.5 REV2.

## Arquivos alterados
- `app.py`
- `templates/base.html`
- `templates/about.html`
