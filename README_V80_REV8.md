# V80 REV8 — Coleta de Valores

- Descoberta automática de fechamentos diretamente no R0050 por ATM + Código Coleta + Data Coleta.
- Fechamentos intermediários/extra aparecem mesmo sem lançamento prévio no Monitoramento.
- Cadeia cronológica do ATM passa a considerar os fechamentos sistêmicos consecutivos.
- Ciclos transacionais são recalculados entre Data Coleta anterior e Data Coleta atual.
- Fechamentos já associados a registros existentes não são duplicados visualmente.
- Exemplo de validação: ATM 50054 deve reconhecer 02/09 10:19:29, 04/09 14:12:10 e 08/09 11:22:01 quando presentes no R0050.

Pacote ENXUTO: sobrepor ao projeto completo em produção.
