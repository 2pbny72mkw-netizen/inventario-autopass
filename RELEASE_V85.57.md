# Web V85.57 — Bobinas ATM com carga e inventário

Base: V85.56 REV1.
- Endpoint autenticado `/api/mobile/v1/field/bobinas/reserves` para snapshot completo das reservas por ATM.
- Endpoint `/api/mobile/v1/field/bobinas/registro` recebe `reserve_mode=ABASTECIMENTO|INVENTARIO`.
- Abastecimento: valida reserva anterior, saldo do técnico em **Bobina ATM**, debita somente bobinas acrescentadas à ATM, cria movimento de destinação e atualiza reserva atomicamente.
- Inventário: exige observação, atualiza reserva constatada sem débito de carga, registra tipo `INVENTARIO`.
- Eventos com client_event_id têm bloqueio transacional PostgreSQL e consulta idempotente.
- Clientes legados não podem aumentar reservas sem regra de carga.
- Eventos STOCK_WITHDRAW com `stock_kind=BOBINA_ATM` aceitam somente item Bobina ATM e múltiplos de seis bobinas.
- Não há migração de esquema; preserva dados existentes.

Homologação obrigatória: carga zero bloqueia abastecimento, inventário com carga zero, retirada caixa x6, duas tentativas do mesmo evento, reserva divergente, retorno da rede e conferência do histórico.
