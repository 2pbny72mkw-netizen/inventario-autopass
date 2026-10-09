# Autopass V85.45 — Conciliação R0050 + Performance

- Reconcilia R0050 com coleta/apuração existente do mesmo ATM e mesma data quando há uma única candidata, evitando `COLETA_EXTRA_R0050` artificial.
- A reconciliação é aplicada também ao histórico na leitura e não exclui registros persistidos.
- Em dias ambíguos, com mais de uma coleta candidata, preserva as linhas separadas para evitar consolidação incorreta.
- Amplia cache de Mapeamento ATM para 5 min; mutações existentes continuam invalidando o cache.
- Amplia cache leve de `/api/locations` e do cálculo de ativos esperados para 30 min, reduzindo recomputações de aplicação observadas na telemetria.
- Base: V85.44 REV9.
