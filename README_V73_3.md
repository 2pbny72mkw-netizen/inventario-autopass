# V73.3 — Consolidação

- Motor metroferroviário compartilhado derivado do mapa validado da Dashboard.
- Dashboard, Rastreabilidade e Equipes usam a mesma composição de trilhos/estações/fallback 4 e 17.
- Rastreabilidade exibe posições gerais e eventos de passagem por estação, priorizando `technician_station_history`.
- GPS envia geofence junto com toda posição aceita (inicial, periódica e movimento) e expõe `AutopassGpsDebug()` para diagnóstico.
- Endpoint ADM/Gestão: `/api/gestao/historico-gps/diagnostico/<id>`.
- Cadastro de usuários mostra ID técnico do banco.
- Nome não é mais tratado como chave única durante edição; login, código, e-mail e celular continuam únicos.
- Técnico Implantação continua com GPS/histórico, mas sem bloqueio rígido de jornada.
- Recarga/TDI: deduplicação revisada para não considerar número de terminal globalmente único; endpoint de diagnóstico `/api/chip-swaps/base-diagnostico`.

Aplicar sobre V73.2 HOTFIX4. Após deploy, executar Ctrl+F5.
