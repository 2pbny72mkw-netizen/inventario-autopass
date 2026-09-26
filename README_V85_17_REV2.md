# V85.17 REV2 — Enxuta de Homologação

Correção focada no Monitoramento de Coletas:
- linhas **Não realizada** geradas pela programação passam a ser selecionáveis;
- exclusão individual/em lote aceita lançamentos persistidos e ocorrências planejadas;
- ocorrência planejada excluída deixa de aparecer no Monitoramento sem apagar a programação recorrente;
- preserva ATM, R0050, dados-fonte e demais ciclos;
- motivo obrigatório e auditoria da operação.

Teste principal: ATM 11056 / Tucuruvi / 01/09/2026. Após excluir a linha Não realizada, confirmar que a programação de terça-feira e as demais coletas permanecem.
