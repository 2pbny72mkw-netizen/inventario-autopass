# V73.2 HOTFIX4 — enxuta

Correção consolidada do mapa de Gestão > Rastreabilidade & Jornada.

## Alterações
- Rastreabilidade passa a usar o componente compartilhado `static/shared_rail_map.js` em vez de manter desenho paralelo dos trilhos.
- Validação geográfica da malha para evitar coordenadas externas deformando o enquadramento.
- Enquadramento inicial fixo em São Paulo (`-23.5505, -46.6333`, zoom 10).
- Uma única legenda e um único conjunto de camadas para Linhas, Estações e Histórico GPS.
- Fallback das Linhas 4-Amarela e 17-Ouro quando não existem registros dessas linhas na base.
- Histórico GPS continua em camada separada e só altera o enquadramento após consulta de técnico/data.
- Histórico da área Sobre atualizado para HOTFIX4.

## Arquivos alterados
- `app.py`
- `templates/management_tracking_v72.html`
- `templates/about.html`
- `static/shared_rail_map.js`
