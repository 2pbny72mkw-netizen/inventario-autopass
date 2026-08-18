Inventário Autopass — V39.5

Correção direcionada ao erro de insuficiência de memória em Android após tirar fotos.

Principais mudanças:
- A lista de pendências passa a usar uma store de metadados separada, sem carregar Blobs/fotos para montar a tela.
- A verificação de duplicidade também deixa de percorrer os registros com fotos.
- Em Android, fotos capturadas não são mais decodificadas em canvas no navegador, eliminando o maior pico de RAM observado.
- O envio reutiliza o Blob original sem criar uma segunda cópia File em memória.
- A sincronização não redesenha a fila a cada item; atualiza ao final do ciclo.
- Migração automática do IndexedDB da V1 para V2, preservando as pendências existentes.
