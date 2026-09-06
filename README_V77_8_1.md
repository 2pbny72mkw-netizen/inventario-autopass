# V77.8.1 — Corretiva de estabilização

## Correções centrais

### Agenda Arrow 2.0
- Restaurado o bloco `head` no template base. Os estilos específicos dos templates voltam a ser aplicados corretamente.
- Calendário 2.0 volta a renderizar em grade, com cards coloridos por status, filtros, resumo e navegação mensal.

### Central de Atividades
- O mesmo ajuste do `head` restaura as cores e o contraste dos cards das atividades no mobile.
- Continua dinâmica pela matriz de permissões: atividade operacional habilitada aparece na tela inicial; dashboards ficam fora.

### Rastreabilidade & Jornada
- O CSS validado em Console passa a ser efetivamente carregado: mapa 100% contido no shell, 600 px no desktop, overflow oculto, cantos arredondados.
- Ordem das panes Leaflet preservada: tiles 200, overlays 400, shadows 500, markers 600, tooltips 650, popups 700.
- Todas as posições GPS continuam plotadas com foto do técnico quando disponível.
- Linha do tempo inicia recolhida e usa scroll interno quando aberta.

### Visão Panorâmica
- Universo restringido ao escopo ferroviário da atividade: Metrô, CPTM, ViaMobilidade Linhas 8/9 e Linha 17.
- Localidades externas da base geral deixam de contaminar KPIs e filtros da Visão Panorâmica.

### Bobinas — auditoria de registro
- Linhas do Histórico da ATM passam a ser clicáveis.
- Modal mostra usuário/técnico, data/hora, linha/localidade, ATM, evento, percentual, reserva, variação, GPS, observações e foto enquanto estiver dentro da retenção.

### Bobinas — histórico por técnico/data
- Novo recorte gerencial por data e técnico.
- Resumo diário: quantidade de registros, ATMs atendidas, localidades, trocas, leituras sem troca e movimentações de bobina.
- Quadro “Resumo por técnico” permite comparar quantas atividades cada técnico executou no dia.
- Relação detalhada mostra cada ATM atendida e as movimentações de estoque/bobina no mesmo período.

## Base preservada
- Parque ATM oficial continua soberano: 602 ATMs = 590 instaladas + 12 em estoque.
