AUTOPASS — V8.0 OPERAÇÃO + PWA/OFFLINE

- PWA instalável via manifest/service worker.
- /tecnico armazenado para funcionamento sem conexão após primeiro carregamento autenticado.
- IndexedDB existente foi preservado e integrado ao PWA.
- Fila de inventário com fotos permanece local até sincronização.
- client_uuid/sync_uuid garante idempotência de tentativas repetidas.
- Service Worker usa network-first para dados operacionais e cache como fallback.
- /offline informa o estado quando a tela ainda não estiver armazenada.
- API /api/v8/operacao adiciona KPIs de operação do dia/equipe.
- Patrimônio 360 passa a mostrar fotos/mídias das visitas da localidade.
- Navegação padronizada: Sobre e Sair permanecem por último.

VERSÃO: v1.8-operacao-pwa-offline


SINCRONIZAÇÃO AUTOMÁTICA
- Quando a conexão retorna, a fila local é detectada automaticamente.
- Aguarda poucos segundos para estabilizar a conexão e inicia o envio.
- Se houver falha temporária, tenta novamente com intervalo progressivo.
- Ao abrir a aplicação online, uma fila antiga também é sincronizada automaticamente.
- Ao sair do modo coleta local, a fila é enviada automaticamente se houver internet.
- Botão "Sincronizar agora" permanece como contingência/manual.
- client_uuid/sync_uuid mantém a operação idempotente e evita duplicidade em retries.
