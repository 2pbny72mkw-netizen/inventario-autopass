# Sistema de Gestão — V76.2

Release de estabilização sobre a V76.1, concentrada em continuidade GPS e persistência das Configurações Operacionais.

## Correções principais

- Configurações Operacionais passam a ter PostgreSQL como fonte autoritativa.
- Deploy não volta mais `Raio GPS de referência` para 3000 m nem `Intervalo GPS operacional` para 300 s.
- Migração `V76.2-001` é idempotente: preenche apenas chaves ainda ausentes e preserva qualquer valor já gravado pelo administrador.
- Seed inicial para instalações que ainda não possuíam as chaves persistidas: raio operacional 250 m, intervalo operacional 60 s, raio histórico 250 m, ping em movimento 10 s e movimento mínimo 20 m.
- `session_gps.js` passa a manter heartbeat periódico em primeiro plano, independente de cliques em Dashboard/Atividades.
- Ao retornar ao PWA por `visibilitychange`, `focus`, `pageshow` ou reconexão, o GPS força retomada imediata.
- `watchPosition()` continua responsável por movimento relevante; heartbeat operacional não depende de deslocamento.
- `AutopassGpsDebug()` informa release, visibilidade, último envio, intervalo e última coordenada para diagnóstico.

## Limite conhecido

Navegadores/PWA podem ser suspensos pelo sistema operacional quando a tela está bloqueada ou outro aplicativo permanece em primeiro plano. A V76.2 garante continuidade enquanto o PWA está efetivamente ativo/visível e retomada ao voltar ao primeiro plano; rastreamento garantido em background exige aplicativo nativo/híbrido com permissão de localização em segundo plano.
