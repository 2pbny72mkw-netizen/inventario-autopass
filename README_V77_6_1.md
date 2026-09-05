# V77.6.1 — Corretiva Bobinas + Estoque Field

## Correções da Dashboard de Bobinas
- Filtros dependentes em cascata: Operadora → Linha → Estação.
- O Detalhe da Estação parte da base oficial de ATMs e exibe todas as ATMs oficiais da localidade, mesmo sem leitura de bobina.
- Leituras importadas/atividade apenas enriquecem a ATM oficial com percentual, técnico, data e reserva.
- Percentuais exibidos como badges coloridos e tipografia ampliada.
- Mantida a base soberana de 602 ATMs: 590 instaladas + 12 em estoque.

## Estoque Field
- Nova visão visual de estoque.
- Seleção de estoque com cards de quantidade por item.
- Matriz comparativa: itens nas linhas e estoques nas colunas, permitindo confrontar quantidades de forma imediata.
- Mantidos os fluxos de retirada, carga do técnico, destinação, ocorrência e regularização.

## Implantação
Pacote ENXUTO: substituir apenas os arquivos contidos no ZIP e reiniciar a aplicação.
