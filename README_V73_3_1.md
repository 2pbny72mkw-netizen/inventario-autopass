# Sistema de Gestão — V73.3.1

Revisão enxuta de estabilização sobre a V73.3.

## Correções
- Rastreabilidade: mapa 600 px, contenção `overflow:hidden`, legenda compacta, z-index/pointer-events e pan/zoom.
- Leaflet: ícones padrão por URL absoluta e tiles OSM versionados.
- GPS: `/api/tecnico/position` também avalia geofence e persiste `technician_station_history` na mesma transação; `geofence-ping` permanece como compatibilidade.
- Histórico: deduplicação de posições no mesmo instante/coordenada.
- Troca de Chips: filtros Equipamento, Status e Resultado atualizam imediatamente.
- Recarga/TDI: terminal é identidade primária dentro de empresa + linha + localidade, sem hardcode de totais.

## Validação pós-deploy
1. Ctrl+F5 e confirmar Sobre = V73.3.1.
2. Rastreabilidade: testar pan/zoom, legenda e consulta de Emerson/Jorge.
3. Após nova posição dentro da estação, consultar o diagnóstico e confirmar `last_station`.
4. Troca de Chips: alternar combinado/Recarga/TDI e confirmar atualização automática.
5. Consultar `/api/chip-swaps/base-diagnostico` e validar os totais canônicos.
