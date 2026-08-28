V66 REV1 — PLATAFORMA OPERACIONAL INTELIGENTE

1. GPS OPERACIONAL
- Obrigatório para Técnico Field, Técnico Implantação, Gestor Field e Dispatcher.
- A primeira posição válida é exigida por nova sessão de login.
- Captura periódica padrão: 5 minutos (configurável por TEAM_GPS_INTERVAL_SECONDS).
- Perda temporária de GPS/internet após validação não bloqueia a operação.
- Fila local de posições em indisponibilidade de rede.
- Logout encerra o envio.
- Retenção móvel/FIFO padrão de 7 dias.

2. VISÃO PANORÂMICA / POWERPOINT
- Geração continua em background durante a navegação.
- Clique durante "Gerando..." permite cancelar o processamento.
- O job registra os filtros usados.
- Ao mudar Empresa/Linha/Status/Busca, o botão volta a permitir PowerPoint para o novo recorte.
- Arquivo pronto só aparece como "Baixar PowerPoint" quando corresponde aos filtros atuais.

3. PERFORMANCE
- Eliminado N+1 de _op_active_map na Recarga. A consulta da base operacional passa a ocorrer uma vez por montagem do payload, em vez de uma vez por validador.

4. SOBRE / VERSÕES
- Histórico recente passa a mostrar V66 REV1, V66 e V63 REV2 no topo.
