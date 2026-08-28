INVENTÁRIO AUTOPASS — V63 CORE 2.0

Base: V62 REV6. Mudança estrutural não destrutiva.

ENTREGAS PRINCIPAIS
1. API EMV com cache curto, filtros server-side e modo compact sem evidências para dashboards.
2. Cache da Troca de Chips Garagem com invalidação em gravação.
3. Dashboard gerencial: módulos pesados carregados sob demanda, reduzindo rajada de APIs na abertura.
4. Gzip automático para JSONs grandes quando suportado pelo navegador.
5. Server-Timing + X-Autopass-Release para diagnóstico de cada resposta.
6. PostgreSQL: correção da consulta de maiores tabelas (relname ambíguo).
7. Central de Processamentos em /api/processamentos, inicialmente com jobs de PowerPoint.
8. Telemetria passa a incluir jobs ativos/prontos/com erro.
9. PowerPoint persiste o job no navegador e retoma o acompanhamento após navegar e voltar.
10. Cache busting consolidado em V63.

SEM ALTERAÇÃO DE SCHEMA DESTRUTIVA / SEM DELETE DE HISTÓRICOS.
Rollback recomendado: V62 REV6.

TESTE DE ACEITE
- Login e Dashboard Geral abrem sem rajada de EMV/Recarga/Panorama quando essas abas não estão selecionadas.
- Abrir Dashboard EMV e verificar /api/emv-chip-swaps?compact=1&include_photos=0.
- Troca EMV salva e aparece imediatamente após cache invalidado.
- Telemetria mostra maiores tabelas PostgreSQL sem erro AmbiguousColumn.
- PowerPoint inicia, permite navegar, e ao voltar recupera o progresso.
- /api/processamentos lista o job.
- 0 erros 5xx e 0 SIGKILL no teste.
