# Inventário Autopass — V82.30 REV2

## Monitoramento de Coletas — diagnóstico controlado
- Instrumenta `/api/financeiro/coletas/v79` por etapa: acesso, período, status, cache, montagem do payload e resposta.
- Em falha, grava `FIN_MONITOR_ERROR` no log com ID de diagnóstico, etapa, duração, tempo SQL, quantidade de queries e traceback completo.
- A API passa a devolver JSON controlado no erro 500, evitando a página HTML genérica.
- O frontend não tenta mais executar `response.json()` cegamente: valida o corpo, informa HTTP/ID/etapa e registra detalhes no Console.
- Nenhuma alteração, exclusão ou reimportação de transações financeiras é executada por esta revisão.

## Objetivo do teste
Recarregar Financeiro > Monitoramento. Se a rota ainda falhar, copiar o código de diagnóstico exibido e localizar `FIN_MONITOR_ERROR id=<código>` no Render.
