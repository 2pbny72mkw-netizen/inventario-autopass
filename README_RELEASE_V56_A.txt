INVENTÁRIO AUTOPASS — V56-A — DADOS & PERFORMANCE
Data: 25/08/2026
Base: V55.4 homologada

OBJETIVO
Primeiro checkpoint estrutural da V56. Mantém a experiência funcional da V55.4 e começa a substituir processamento legado por dimensões normalizadas/indexadas no PostgreSQL.

ENTREGAS
1. TopDesk / Chamados
- Novas dimensões persistidas: created_at, line_code, station_code e model_code.
- Importações novas já gravam as dimensões normalizadas.
- Backfill idempotente dos chamados existentes em lotes de 1.000 registros.
- Filtro temporal passa a usar created_at indexado, eliminando parsing de data para cada chamado em cada abertura.
- Linha, estação e modelo passam a usar colunas próprias/indexadas.
- Mantidos object_id e created_at_text originais para auditoria/compatibilidade.

2. Índices V56-A
- created_at
- line_code + created_at
- station_code + created_at
- model_code + created_at
- operator + created_at
- índices V55 de status/categoria/equipamento preservados.

3. Dashboard / Analytics
- Cache TopDesk preservado e invalidado após importação.
- Redução do conjunto processado em Python: filtros principais são aplicados no banco antes do analytics.
- Histórico padrão permanece 2026 em diante.

4. Diagnóstico
- Novo endpoint /api/v56a/performance para Gestor/ADM Financeiro.
- Exibe quantidade de chamados e percentual já normalizado.

5. Financeiro
- Título visual "Command Center Financeiro" simplificado para "Financeiro".
- Dados e importações já homologados da V55.4 preservados.

IMPORTANTE NO PRIMEIRO DEPLOY
O primeiro boot da V56-A pode levar mais tempo que os boots seguintes porque normaliza os chamados TopDesk existentes e cria os novos índices. Isso ocorre uma vez por registro. Não interromper o primeiro deploy enquanto o Render estiver executando o startup.

NÃO ENTRA NESTE CHECKPOINT
- Modularização completa/Blueprints (V56-B).
- Alembic/background persistente/UPSERT financeiro definitivo (V56-B).
- Envio de Relatório de Visita por e-mail/WhatsApp (V56-C).

VALIDAÇÕES REALIZADAS
- app.py compilado com py_compile.
- Estrutura ZIP validada.
- Teste de import runtime não executado neste ambiente por ausência das dependências Flask instaladas no container de empacotamento.
