# V77.9.4

Correção consolidada do Dashboard de Bobinas.

- Big Numbers compactos, seguindo o padrão executivo de referência, com ícones semânticos.
- Card ATMs monitoradas mostra parque oficial, quantidade sem monitoramento e cobertura.
- Clique em ATMs monitoradas abre a lista nominal de ATMs oficiais sem leitura/monitoramento.
- API `/api/bobinas/dashboard` passa a retornar `missing_atms`.
- Termômetro de Armários/Estoques redesenhado como cobertura da meta: reserva disponível, meta e percentual real, sem escala fixa visual saturada.
- Saldo de estoque prioriza o item canônico `Bobina ATM`, com fallback legado.
- Mantidos os ajustes administrativos auditados da V77.9.3 e o scroll da Visão Geral já corrigido.
