# Inventário Autopass — V82.14 ENXUTA

Base: V82.13 ENXUTA. Aplicar os arquivos deste pacote sobre a versão completa em produção.

## Troca de Chip Recarga
- Filtros deixam de exigir a seleção completa Empresa → Linha → Localidade.
- Sem localidade selecionada, a área inferior consolida os validadores compatíveis com Empresa/Linha e continua respeitando Status, Data e Técnico.
- KPIs e progresso da seleção acompanham o universo filtrado.
- Ao selecionar uma localidade, permanece o fluxo operacional individual existente.

## Reprogramação de coletas — estratégia agressiva
- ATMs cuja média de Valor Apurado ultrapassa a referência mantêm dois dias efetivos em `terminal_plan`.
- A tela passa a exibir os dias associados aos ATMs 2x/semana (ex.: Quinta + Terça), e não apenas o contador “acima da referência”.
- Alterar o primeiro dia recalcula o segundo dia dos ATMs 2x.
- Gráficos/carga diária continuam contabilizando as duas ocorrências.
- Exportação Excel passa a ser por ATM, com frequência, 1º dia, 2º dia, média apurada, histórico utilizado e motivo.
- Endpoint de aplicação direta foi alinhado à mesma regra: respeita estratégia/histórico/referência e grava 8 ocorrências/mês para ATMs 2x/semana.
- Linha 17/Ouro permanece na regra específica de 2x/mês.
- O total de ATMs permanece como equipamentos únicos; a segunda coleta aumenta ocorrências, não o universo de ATMs.

## Validação
- `python -m py_compile app.py`
- `node --check static/cash_collection_v79.js`
- `node --check static/chip_swap.js`
