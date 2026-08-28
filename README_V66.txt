V66 — PLATAFORMA OPERACIONAL INTELIGENTE

1. GPS Operacional 2.0
- obrigatório para iniciar atividade de campo (Técnico Field, Técnico Implantação e Gestor Field)
- captura inicial e periódica, padrão 5 min via TEAM_GPS_INTERVAL_SECONDS
- cada captura gera novo registro
- tolerância a perda temporária de sinal; fila local limitada para reenvio
- logout/fechamento encerra o timer
- retenção FIFO de 7 dias (TEAM_GPS_RETENTION_DAYS)

2. Inteligência Operacional
- nova tela Gestão > Inteligência Operacional
- capacidade Field, GPS recente, trabalho aberto, SLA em risco
- anomalias de GPS
- priorização automática explicável por prioridade + idade + ausência de técnico

3. PowerPoint Panorama
- removido banner global
- acompanhamento somente na Visão Panorâmica
- job continua no servidor ao navegar e é recuperado ao retornar
- removido botão redundante interno

4. Base técnica
- release e assets atualizados para V66
- mantém importador operacional V63 REV2 e demais módulos existentes
