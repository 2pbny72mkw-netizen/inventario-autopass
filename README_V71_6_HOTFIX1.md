# V71.6 HOTFIX1

Correção pontual da regressão do Dashboard/Troca de Chips Recarga + TDI.

Erro:
`NameError: name 'or_' is not defined`

A V71.6 passou a usar `or_(...)` para reunir Validador de Recarga e TDI, mas o helper não estava importado do SQLAlchemy.

Consequências:
- `/api/chip-swaps/dashboard` retornava HTTP 500;
- o frontend recebia HTML de erro;
- aparecia `Unexpected token '<'`;
- o Dashboard Recarga ficava zerado.

Correção:
- adicionado `or_` ao import do SQLAlchemy.

Sem alteração de banco.
Sem alteração da lógica funcional da V71.6.
