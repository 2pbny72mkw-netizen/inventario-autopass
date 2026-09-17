# Inventário Autopass V82.27 — ENXUTA

Escopo consolidado da V82.27:

- Troca de Chips – Recarga: após POST 200 / status CONCLUÍDA, o front-end encerra imediatamente o estado "Salvando..." e atualiza a listagem em segundo plano.
- Financeiro > Reprogramação de Coletas: o gráfico diário passa a exibir **ATMs e Localidades**. ATMs da estratégia agressiva 2x/semana são contabilizadas nos dois dias, sem alterar o universo físico de 256 ATMs.
- Dashboard Bobinas: novo histórico/programação de entregas futuras para CDs/Localidades, com Localidade, Data da entrega, Status e Quantidade em caixas.
- Status das entregas: PROGRAMADO, EM_ANDAMENTO e ENTREGUE, com filtro e manutenção do histórico.
- Estoque de Bobinas por Localidade/CDs/Armários fica independente dos filtros analíticos da Dashboard e representa sempre a posição atual completa.
- Estoque passa a apresentar Caixas, Bobinas avulsas e Total em bobinas.
- Conversão de caixa parametrizada por `BOBBIN_ROLLS_PER_BOX` (padrão atual: 6), evitando valor fixo na interface e no importador.
- O Histórico da ATM existente permanece separado do histórico de entregas.

Arquivos alterados: `app.py`, `static/chip_swap.js`, `static/cash_collection_v79.js`, `templates/bobbin_dashboard_v77.html`.
