AUTOPASS — V10.0 CAMPO INTELIGENTE

Escopo funcional
- Login de usuário case-insensitive; senha continua case-sensitive.
- Raio operacional de localidades próximas configurável e limitado a 3 km nesta fase.
- Estações físicas agrupadas por nome, preservando múltiplas linhas/operações no mesmo ponto.
- Check-in operacional automático ao selecionar estação próxima, com distância e qualidade do GPS.
- Qualidade GPS: acima de 80 m não valida geograficamente sem justificativa.
- Precisão GPS continua registrada, porém o círculo fica oculto por padrão; camada opcional de auditoria.
- Avatar/foto unificado no Mapa de Equipes e cards, com cache-busting.
- Service Worker V10 usa network-first para arquivos estáticos, evitando JS/CSS antigo em cache.
- Versões de módulos atualizadas para V10.0.
- Ajustes visuais discretos em KPIs, estação mais próxima e check-in.

Privacidade / jornada
- V10 mantém a localização da equipe sob controle explícito do técnico.
- Regra futura registrada: encerrar coleta ao logout/fim efetivo da jornada, considerando hora extra e entrada antecipada.

Teste de liberação
1. Login usando variação de maiúsculas/minúsculas no usuário.
2. Mapa de Equipes: foto no card, mapa normal e fullscreen.
3. Trocar foto do usuário e validar atualização.
4. Técnico: nenhuma estação acima de 3.000 m na lista automática.
5. Selecionar estação próxima e validar mensagem de check-in.
6. Estação integrada (Luz/Brás/Barra Funda): escolher linha depois da estação.
7. Dashboard: camada de precisão GPS não deve aparecer por padrão.
8. Smoke test online e offline/sincronização.
