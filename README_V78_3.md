# Sistema de Gestão / Inventário Autopass — V78.3 ENXUTA

## Engenharia — Estruturas BOM
- **Fabricante** substitui Fornecedor na visualização principal da BOM e nas exportações de estrutura/estudo.
- Componentes são agrupados por **Material**, **Consumo** e **Serviço**, mantendo a separação por origem e usando paletas claras diferentes.
- Cada grupo exibe quantidade de itens e subtotal nacionalizado.
- A classificação de Consumo é também inferida do Cadastro Mestre para embalagens/itens de consumo quando aplicável.
- Quantidades de componentes continuam aceitando frações (ex.: `0,2` caixa por produto).

## Importados — USD / FOB
- Item mestre com origem **IMPORTADO** abre na BOM com moeda **USD** e campo **FOB unitário (US$)**.
- O custo nacionalizado usa `FOB × fator de importação × cotação USD/BRL`.
- Para vínculo legado importado gravado em BRL, o sistema marca **FOB pendente** e não reutiliza silenciosamente o valor em reais como dólares.
- Ao editar/salvar o componente importado, a moeda aplicada passa a ser USD.

## Formação Comercial — Simulação de Venda
- Preço e Margem ficam dentro de um retângulo próprio **SIMULAÇÃO DE VENDA**.
- **Informar preço**: Preço é editável; Margem é calculada, bloqueada e exibida em outra paleta.
- **Informar margem**: Margem é editável; Preço é calculado, bloqueado e exibido em outra paleta.
- Nunca há dois campos de comando editáveis ao mesmo tempo.

## Preservado
- `BASE_CADASTRO_BOHM_V8.xlsx` continua como base oficial do Cadastro Mestre.
- Aba Codificação e regra `GG.OO.TT.SSSSS` preservadas.
- BOM multinível, Where Used, EOL/substitutos, clonagem/revisões e Estudos salvos preservados.

## Arquivos alterados
- `app.py`
- `templates/engineering.html`
- `templates/about.html`
- `static/engineering_v72.js`
- `README_V78_3.md`
