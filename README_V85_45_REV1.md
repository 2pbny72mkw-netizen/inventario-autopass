# V85.45 REV1 — Diagnóstico de desempenho

- Instrumentação de tempos totais, SQL e residual da aplicação no cabeçalho `Server-Timing`.
- Logs estruturados (sem parâmetros, corpos ou dados pessoais) para chamadas acima de 1 segundo em `/api/mapeamento-atm`, `/api/locations` e `/api/bobinas/registro`.
- Cada log contém identificador da requisição, quantidade de consultas, maior duração individual SQL e tamanho da resposta.
- Preservados os módulos, banco, permissões, cache, fluxo offline e conciliação da V85.45.

## Verificação após deploy
1. Executar os três fluxos em horário de uso normal.
2. Comparar P95/P99 e `Server-Timing` com a V85.45.
3. Observar `PERF_REV1` nos logs do Render para identificar gargalos.
4. Nenhuma migração de banco é necessária nesta revisão.

Observação: `app` é o tempo residual (tempo total menos tempo medido no driver SQL), incluindo processamento, serialização e outros overheads; não é medição isolada de CPU. Os logs só são emitidos para chamadas lentas nas três rotas selecionadas.
