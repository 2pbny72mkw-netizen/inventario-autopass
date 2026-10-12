# Web V85.58 — suporte LEITURA / INSPEÇÃO de bobinas

Base V85.57. Endpoint /api/mobile/v1/field/bobinas/registro aceita reserve_mode=LEITURA com client_event_id.
LEITURA exige reserva anterior consistente com servidor e não altera quantidade, carga ou movimento de estoque.
Mantém histórico percentual e idempotência. Sem migração de banco.
Publicar antes de Android Build 86.
