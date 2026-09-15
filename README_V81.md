# V81 — Central Analítica de Conciliação de Coletas

Marco funcional: três fontes oficiais (Programação/Realizado, R0050 e TB Forte), qualidade/completude das fontes, monitoramento em campo dinâmico e filtro inteligente seguro.

## Implementado nesta entrega
- versão V81 visível no sistema;
- painel de saúde das fontes e ciclo conciliável até;
- completude por ciclos realizados no período;
- monitoramento em campo por grupos persistentes, inclusão em massa e encerramento com histórico;
- filtro inteligente em linguagem natural convertido em filtros autorizados, sem SQL livre;
- preservação do motor V80 de janelas R0050, T×D, D×A e T×A;
- importação por colagem do R0050 e TB Forte preservadas.

## Regra de integridade
Ausência de dado não é zero. Análises com fontes incompletas são sinalizadas como parciais.
