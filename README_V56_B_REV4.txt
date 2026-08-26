V56-B REV4 — revisão consolidada

1. Equipes
- mantém uma única regra de escala para calendário/Operação de Hoje/equipe prevista;
- última posição GPS + estação mais próxima no popup;
- mapa usa endpoint ferroviário leve e deixa de refazer /api/locations no componente compartilhado;
- cache-busting teams-v56-b-rev4.

2. Performance
- /api/locations elimina N+1 de referência observada e calcula estatísticas GPS em lote;
- preserva ganhos da REV3.

3. Apuração
- mostra última transação armazenada e última carga;
- gráfico Transacionado x Coletado x Apurado mostra também diferença Coletado x Apurado em R$ e %;
- preserva importação background e carga incremental/anti-duplicidade.

4. Chamados
- card Evolução mensal compactado e barras distribuídas na largura;
- rótulos jan/26, fev/26 etc.

5. EMV
- preserva data_emv.xlsx e fallback defensivo da REV3; API otimizada mantida.
