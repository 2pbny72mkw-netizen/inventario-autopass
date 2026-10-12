# Web V85.56
Base: V85.55 REV1.
- /api/mobile/v1/sync/events: aplica eventos GPS_SIGNAL (SEM_SINAL / RECUPERADO) com envelope de auditoria existente e event_id idempotente.
- /api/mobile/v1/gps/signal-history: endpoint autenticado de consulta das últimas 100 ocorrências do próprio usuário.
- GPS_POSITION preserva o provedor de origem (gps/network), sem inventar coordenadas.
- Nenhuma tabela nova; não altera permissões existentes nem módulos de Bobinas.
Limites: sem tela administrativa Web de GPS; histórico via endpoint autenticado. Requer homologação em Render.
