# Sistema de Gestão — V76.1

Release de estabilização consolidada sobre a V76.

Principais correções e evoluções:
- Equipes / Operação de Hoje: inclui colaborador com autorização extraordinária válida mesmo em folga/5x2; GPS autenticado passa a ser evidência operacional; alerta GPS >10 min não fica bloqueado por ausência de SessionEvent LOGIN; contadores e linha usam a mesma regra; geofence usa o raio parametrizado.
- Cadastros Field legados: saneamento único para usuários Técnico Field com GPS obrigatório que receberam Histórico GPS e Controle de Jornada como FALSE na migração antiga.
- Lista oficial de acesso Metrô/CPTM: foto maior, orientação EXIF corrigida, corte central sem distorção e tipografia maior.
- Firmware POS CPTM: barra de progresso mais espessa, percentual e quantidade concluída dentro do gráfico.
- Arrow Dashboard 2.0: KPIs de previstas/concluídas/em andamento/pendentes/atrasadas/técnicos/remotas; filtros globais; gráficos por status e técnico; cores por status; calendário 7/30 dias preservado.
- Central de Notificações: correção do layout das exceções automáticas e melhor separação visual por severidade.

Observações de validação após deploy:
1. Testar usuário 5x2 em sábado com autorização extraordinária aprovada — deve aparecer na Operação de Hoje.
2. Testar logout/login e confirmar coluna Login. Se SessionEvent falhar, GPS ainda deve evitar falso “NÃO LOGOU”.
3. Bloquear celular >10 min — KPI GPS >10 min deve acompanhar a linha.
4. Desbloquear e medir retomada automática do GPS/PWA.
