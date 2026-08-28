INVENTÁRIO AUTOPASS — V66 REV4 — PERFORMANCE 2.0

Base: V66 REV3.
Objetivo: reduzir gargalos de aplicação e N+1 antes da V67 — Dossiê & Materiais.

ALTERAÇÕES PRINCIPAIS
1. EMV
- cache separado FULL/SLIM;
- dashboard compact=1 não carrega evidências/fotos;
- schema EMV validado/migrado apenas uma vez por processo;
- rota GET aceita slash final sem redirecionamento;
- cabeçalho X-Autopass-Payload-Mode para telemetria/diagnóstico.

2. GPS /api/gps/recent
- removidas consultas de posição e check-in por técnico;
- última posição e último check-in do dia obtidos em lote;
- localidades carregadas em lote;
- objetivo: reduzir dezenas de queries por request para poucas consultas.

3. GARAGEM
- removido N+1 de _op_active_map('garagem');
- mapa operacional carregado uma vez por montagem do payload.

4. LOCALIDADES / INVENTÁRIO
- mantém cache leve/observado separado;
- referência observada em lote;
- contagem de anexos do inventário por localidade em uma consulta agregada.

5. VERSIONAMENTO
- APP_RELEASE = V66 REV4;
- histórico Sobre atualizado.

VALIDAÇÃO APÓS DEPLOY
- Confirmar /api/emv-chip-swaps?compact=1&include_photos=0 com queda forte do tempo de aplicação.
- Confirmar /api/gps/recent com queda de queries/request.
- Confirmar /api/garage-chip-swaps sem centenas de queries/request.
- Observar P95, média, RAM e 5xx por pelo menos uma janela operacional real.

Não aumenta WEB_CONCURRENCY nesta revisão. Primeiro medir os ganhos do código.
