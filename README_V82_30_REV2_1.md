# Inventário Autopass — V82.30 REV2.1

Hotfix dirigido do Monitoramento de Coletas.

## Financeiro — cache fail-safe
- A falha identificada na etapa `cache-write` deixa de provocar HTTP 500.
- O resultado financeiro já calculado é devolvido normalmente mesmo se a gravação do cache falhar.
- A falha do cache continua registrada no log como `FIN_MONITOR_CACHE_WRITE_ERROR`, com ID diagnóstico, duração, tempo SQL, quantidade de queries e tipo da exceção.
- Não executa rollback de banco por falha de cache.
- Em falha, o cache parcial é limpo e a requisição segue em modo `cache-bypass`.
- Não altera, exclui ou reimporta transações R0050/TB Forte.

Release: `V82.30 REV2.1`
