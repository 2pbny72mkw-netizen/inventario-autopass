# V77.9.1

Versão corretiva consolidada sobre V77.8.1, com foco em dashboards gerenciais, Arrow, scroll e estabilidade visual.

## Testes prioritários
1. Abrir Dashboard POS, Validador + TDI e Bloqueio e confirmar chamada `/api/dashboard/inventory-equipment/...` no Network.
2. Confirmar cards/gráficos/tabelas e filtros.
3. Abrir Visão Geral e rolar até o fim.
4. Arrow: validar menu e alternância 7/30 dias.
5. Rastreabilidade: validar enquadramento 600px e avatares maiores.
6. Visão Panorâmica: validar somente universo ferroviário e contadores.

## V77.9.1 — Visão Panorâmica
- Consolidação não destrutiva de aliases de estação na resposta de `/api/panoramas`.
- Mescla segura somente quando empresa, linha e nome canônico da estação coincidem após retirar prefixo operacional (ex.: `ABR - AGUA BRANCA` = `AGUA BRANCA`).
- Preserva PanoramaPoint, PanoramaPhoto, IDs históricos, fotos, técnicos, coordenadas e status manual no banco; não executa exclusão/migração destrutiva.
- Registro principal prioriza histórico/fotos, depois pontos, override e coordenadas.
- Inclui `alias_location_ids` e `alias_count` para auditoria da consolidação.
- Adiciona compatibilidade JSON em `/api/panoramic/locations`, eliminando o 404/HTML observado no frontend legado.
