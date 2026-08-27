V62 REV6 — INFRAESTRUTURA, OBSERVABILIDADE E POWERPOINT ASSÍNCRONO

Aplicar sobre a V62 REV5.

Principais alterações:
1. Visão Panorâmica: PowerPoint passa a ser gerado em segundo plano.
   - POST cria job e responde imediatamente.
   - Tela acompanha percentual/status a cada 2s.
   - Download ocorre somente quando o arquivo estiver pronto.
   - Uma geração por vez, evitando concorrência e cliques duplicados.
   - Exportação direta síncrona foi desativada para não bloquear o único worker web.
   - Imagens são compactadas para 960x720 / JPEG 55 durante o PPTX para reduzir RAM/CPU.
2. Telemetria 2.0 (somente ADM):
   - tamanho atual do PostgreSQL;
   - maiores tabelas, dados, índices e linhas estimadas;
   - conexões atuais / máximo quando disponível;
   - R2: quantidade de objetos, volume total e maior arquivo;
   - RAM do processo, limite de memória do container quando exposto, workers/CPU;
   - arquivos locais/temporários.
   - limite do banco só é mostrado quando o ambiente/provedor o disponibiliza via DATABASE_STORAGE_LIMIT_MB ou DATABASE_STORAGE_LIMIT_GB.
3. Cache/service worker atualizado para V62 REV6.
4. APP_RELEASE atualizado para V62 REV6.

Sem alteração de schema do banco.

Teste recomendado:
- abrir Telemetria e validar bloco Capacidade e armazenamento;
- abrir Visão Panorâmica e gerar PowerPoint uma única vez;
- durante a geração, navegar para outra tela e confirmar que o sistema permanece responsivo;
- confirmar status PRONTO e download do PPTX;
- conferir logs para ausência de SIGKILL/500.
