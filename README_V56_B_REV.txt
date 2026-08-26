INVENTÁRIO AUTOPASS — V56-B REV (REVISÃO CONSOLIDADA)

Objetivo: corrigir os pontos encontrados na homologação da V56-B sem abrir B.1/B.2/B.3.

Principais ajustes:
- Dashboard EMV Trilhos remodelada no mesmo padrão executivo da Troca de Chip Recarga: 5 KPIs, progresso, donut/status, filtros, progresso por estação e produtividade por técnico.
- /api/emv-chip-swaps otimizada para eliminar consultas repetitivas de fotos e busca repetida de nomes de estação.
- Equipes / Operação de Hoje passa a usar posição GPS do próprio dia e expõe status operacional, login, atraso, contagem de posições do dia e estação/localidade mais próxima.
- Popup do mapa mostra estação/localidade, relação até 500 m / mais próxima, distância, status, login e volume GPS do dia.
- Telemetria ADM ampliada com SQL médio e queries por requisição para diagnóstico por print.
- Migração aditiva das novas colunas de telemetria; nenhum dado operacional é removido.
- Apuração preserva conciliação Transacionado x Coletado x Apurado e quantidade de cédulas.

IMPORTANTE SOBRE IMPORTAÇÃO ATM:
A arquitetura atual do servidor web não garante execução persistente em background em todos os ambientes Render. Não declarar ao usuário que pode fechar a tela durante a carga até existir worker/fila dedicada. A revisão mantém consistência/duplicidade e a telemetria para diagnóstico; cargas grandes devem ser feitas na janela noturna.

VALIDAÇÃO PÓS-DEPLOY:
1. Login ADM.
2. Gestão > Telemetria: verificar SQL médio e Queries/req.
3. Dashboard > EMV Trilhos: comparar visual e filtros com Recarga.
4. RH > Equipes > Operação de Hoje: escalados, login, atraso, GPS, localidade/estação.
5. Mapa: técnico deve aparecer somente com posição válida do dia; popup deve informar estação/referência.
6. Financeiro > Apuração: validar bases existentes antes de nova carga grande.
