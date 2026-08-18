Inventário Autopass — V39.7.2 PERFORMANCE HOTFIX (ENXUTO)

Base: V39.7.1
Arquivos alterados:
- app.py

Correções de performance:
- Verificação/criação das tabelas de Troca de Chips somente uma vez por processo Gunicorn.
- Associação de Validadores de Recarga às localidades em uma única passagem indexada por linha.
- Remoção do cruzamento repetitivo localidade x todos os ativos.
- Fotos e técnicos carregados em lote, eliminando consultas N+1.
- Cache curto (20 s) do payload de Troca de Chips, invalidado imediatamente após gravação.
- Dashboard de Troca de Chips sem consulta individual de usuário para cada registro.

Não altera dados existentes nem remove funcionalidades.
