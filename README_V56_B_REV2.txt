INVENTÁRIO AUTOPASS — V56-B REV2

Foco desta revisão consolidada:
1. Apuração Financeira: importação Excel desacoplada da requisição HTTP.
   - Upload inicia job em segundo plano e retorna imediatamente.
   - Tela acompanha status/progresso por polling.
   - Usuário pode navegar para outra tela após a mensagem de processamento em segundo plano.
   - Importação de transações continua em lotes e com deduplicação por source_hash.
2. EMV: cache permanente da configuração técnica de bloqueios.
   - Evita reler block_config_v18.json para cada bloqueio.
   - Mantém cache da base EMV e rede de estações já existente.
3. Equipes / Operação de Hoje:
   - elimina consultas N+1 de usuário, GPS e login.
   - busca usuários, última posição, contagens GPS e sessão em consultas consolidadas.
4. TopDesk Dashboard:
   - cache de 60 segundos por conjunto de filtros para evitar recalcular ~50 mil chamados em refreshs repetidos.
5. Índices adicionais para sessão e perfis de escala.
6. Telemetria permanece exclusiva do perfil ADM e passa a medir os ganhos desta revisão.

TESTE NOTURNO RECOMENDADO
- Gestão > Telemetria: registrar print antes/depois.
- Dashboard EMV: abrir e conferir tempo da rota /api/emv-chip-swaps.
- Equipes > Operação de Hoje: conferir dados e Queries/req da rota /api/equipes/status.
- Financeiro > Apuração: iniciar importação e confirmar a mensagem "Processando em segundo plano · você pode sair desta página".
- Navegar para outra tela, aguardar e retornar à Apuração; se o worker não reiniciou, a importação continua no servidor.
- Após concluir, confirmar Transações ATM > 0 na Telemetria.

OBSERVAÇÃO
O job de importação roda em thread no processo web atual. Ele sobrevive à navegação do usuário, mas não a um restart/redeploy do serviço. Uma fila externa persistente (Redis/Celery/RQ) exigiria infraestrutura adicional no Render.
