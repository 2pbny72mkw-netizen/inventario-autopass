AUTOPASS INVENTÁRIO — V9.1

Correções e consolidação:
- Avatar do técnico no mapa limitado a 48 px, inclusive em tela cheia.
- Clique no avatar mantém popup de informações e passa a exibir precisão GPS quando disponível.
- Identificação visual dos módulos atualizada para V9.1 (Equipes, Evidências e Patrimônio 360).
- Tela Sobre atualizada com histórico V7, V8, V9.0 e V9.1.
- Cache-busting de teams.js e patrimonio.js atualizado para V9.1.
- Mantida a base da V9: RH, localização inteligente e preparação para proximidade/geofence.

Teste dirigido recomendado após deploy:
1) mapa normal e fullscreen: avatar pequeno;
2) clique no avatar: popup abre normalmente;
3) usuário RH: cadastro/edição/permissões;
4) lançamento online + offline/sincronização;
5) uma nova foto de equipamento e consulta em Evidências/Patrimônio 360.

Observação sobre mídias antigas: não reimportar antes de validar uma nova foto no storage atual.
