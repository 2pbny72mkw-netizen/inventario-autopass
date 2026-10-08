# V85.44 REV8 — PWA / cache operacional seguro

- Service Worker atualizado para cache seguro de recursos estáticos.
- Cache runtime das telas de Bobinas e Estoque Field após carregamento autenticado bem-sucedido.
- Fallback offline para `/field/bobinas` e `/field/estoque` quando já visitadas no aparelho.
- Cache de fallback somente-leitura para opções/status de Bobinas necessários à operação com sinal instável.
- POSTs e APIs mutáveis não são cacheados pelo Service Worker.
- Fila offline de Bobinas continua no IndexedDB e é preservada.
- Logout limpa o cache privado de páginas, sem apagar a fila operacional IndexedDB.
- Versão: V85.44 REV8.
