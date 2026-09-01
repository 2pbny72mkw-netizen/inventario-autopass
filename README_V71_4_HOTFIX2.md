# V71.4 HOTFIX2

Correção crítica de navegação e desempenho.

## Redirect
A causa do `ERR_TOO_MANY_REDIRECTS` era:
`/dashboard -> /gerencial`, enquanto o `dashboard_required` enviava usuários sem permissão de Dashboard de volta para `/dashboard`.

Agora:
- `/gerencial` permanece a URL oficial.
- `/dashboard` é apenas alias de compatibilidade.
- usuário com permissão Dashboard: `/dashboard -> /gerencial`;
- usuário sem permissão Dashboard: vai diretamente para sua área segura, nunca retorna ao Dashboard;
- a rota raiz também respeita a permissão efetiva antes de abrir `/gerencial`.

## Desempenho EMV
Foi restaurada exatamente a implementação leve da V71.3 HOTFIX4 para:
`/api/emv-chip-swaps/`

Ela volta a responder payload SLIM, sem fotos/evidências e sem redirecionar para o pipeline completo.

## Banco
Sem migração estrutural.
