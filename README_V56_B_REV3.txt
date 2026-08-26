INVENTÁRIO AUTOPASS — V56-B REV3
Data: 25/08/2026 — janela noturna

Correções prioritárias desta revisão:
1. Apuração / Transações ATM
   - progresso real por linhas: total, processadas, incluídas, erros, registros/s, ETA e heartbeat;
   - carga em lotes de 2.000 com inserções de 1.000 e commits controlados;
   - retomada visual do job ativo ao voltar para a tela (enquanto o mesmo processo do servidor estiver ativo);
   - alerta visual quando não houver heartbeat por mais de 120 s;
   - importação idempotente por source_hash, reduzindo risco de duplicidade em repetição.

2. EMV Trilhos
   - data_emv.xlsx incluído também no pacote ENXUTO;
   - carregamento da base EMV com fallback e cache apenas quando houver dados;
   - eliminação de busca técnica repetitiva terminal a terminal: mapa técnico carregado uma única vez;
   - preservação do dataset esperado para filtros, cards e gráficos.

3. Equipes / Operação de Hoje
   - correção da referência 12x36 quando a data-base foi cadastrada como FOLGA;
   - login do dia considera eventos LOGIN;
   - mantém última posição GPS, atraso, sem GPS, sem posição >10 min e estação mais próxima;
   - cache-busting do JS da tela para evitar navegador usando versão anterior.

Observação:
O job de importação roda em background dentro do processo web. Navegar para outra tela é permitido; reiniciar/redeployar o serviço ainda interrompe o job atual.
