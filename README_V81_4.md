# V81.4

## Monitoramento
- Programação de Coletas e Fila de Prioridades passam a aparecer como abas dentro de Monitoramento de Coletas.
- Fila de Prioridades: cabeçalhos clicáveis com ordenação crescente/decrescente para criticidade, ATM, operadora, linha, estação, tempo sem coleta, falhas e último motivo.
- Ordenação atua sobre o conjunto filtrado carregado, preservando filtros.

## Performance
- Mantida a eliminação de N+1 da V81.3 na Saúde das Fontes.
- Cache curto (60 s) para os agregados de Saúde das Fontes e reutilização pelo Filtro Inteligente, reduzindo consultas repetidas em refreshs sucessivos.
- Base transacional detalhada permanece íntegra; nenhuma transação R0050 é removida ou resumida de forma destrutiva.

## Compatibilidade
- Banco, dados, permissões, módulos e histórico preservados.
