# V71.4 — Padronização de URLs e APIs

- `/gerencial` é a URL canônica da Central de Dashboards.
- `/dashboard` fica apenas como alias legado 308.
- A raiz direciona os perfis diretamente ao destino canônico, eliminando redirects em cadeia.
- URLs com `//` ou barra final são normalizadas globalmente com HTTP 308, preservando método/body.
- `/api/emv-chip-swaps` passa a ser a única leitura canônica do EMV.
- `/api/emv-chip-swaps/` deixa de executar um segundo pipeline de dados.
- Aliases antigos de dashboards usam redirect permanente controlado.
- Service Worker/cache atualizado para V71.4.
- Sem migração estrutural de banco.
