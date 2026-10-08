# V85.44 REV9 — PWA / cache expandido

- Base: V85.44 REV8.
- Amplia o cache de navegação: toda página GET visitada online e retornada com sucesso pode ser reaberta como fallback offline.
- Mantém cache de estáticos e fila IndexedDB de Bobinas.
- APIs dinâmicas e métodos de mutação (POST/PUT/PATCH/DELETE) não são armazenados como páginas offline.
- Logout limpa o cache privado de páginas, preservando pendências operacionais locais.
- Service Worker versionado como REV9 para atualização após deploy.

Teste: visitar várias abas online, desligar a rede e retornar às abas já visitadas. Páginas não visitadas devem usar o fallback offline.
