# V73.2 HOTFIX1

Correções focadas em regressões observadas após a V73.2.

- Rastreabilidade & Jornada: mapa Leaflet passa a usar o mesmo padrão de resize do mapa de Equipes, com ResizeObserver e invalidateSize em resize/abertura.
- Configurações Operacionais: textos descritivos maiores e com melhor legibilidade.
- Dashboard Troca de Chip Recarga: filtro de equipamento (Recarga + TDI, somente Recarga, somente TDI) e filtro de status funcional.
- Troca de Chip Recarga: reconciliação de histórico por identidade operacional quando uma importação recria o BaseAsset com novo ID, preservando execuções já concluídas.
- Exportação da Troca de Chip passa a respeitar equipamento e status.
- Status administrativo passa a aceitar também TDI.

## Validação após deploy

1. Abrir Rastreabilidade & Jornada, mover/zoomar o mapa e redimensionar a janela/F12.
2. Na Dashboard Troca de Chip Recarga, comparar Total/Concluídos com a base histórica.
3. Testar os filtros Recarga + TDI, Somente Recarga, Somente TDI e Todos/Pendentes/Em andamento/Concluídos.
4. Confirmar que registros já concluídos antes da última importação continuam concluídos.
