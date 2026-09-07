# Sistema de Gestão / Inventário Autopass — V78.4

## Engenharia de Produto
- BOM multinível visível: produto final = nível 0; componentes/subestruturas = nível 1; componentes das subestruturas vinculadas = níveis 2, 3 e seguintes.
- Subestruturas continuam sendo BOMs reutilizáveis, vinculadas a um item do Cadastro Mestre do tipo `SUBESTRUTURA`.
- Nova visão em árvore com expandir/recolher e botão `Abrir BOM` para navegar pela subestrutura.
- Botão `Subestruturas / Níveis` com referência do fluxo de criação e lista das subestruturas já vinculadas.
- Classificação `Material / Consumo / Serviço` passa a respeitar a alteração feita na própria BOM. O Cadastro Mestre apenas sugere o grupo na inclusão.
- Nacional e Importado ganharam paletas visuais distintas; Material, Consumo e Serviço mantêm diferenciação dentro de cada origem.
- Para itens nacionais, a coluna FOB US$ fica vazia. O custo em reais é exibido em coluna própria.
- Para itens importados, mantém FOB em USD e custo nacionalizado em R$.
- Exportação Excel de BOM/estudo também separa `FOB Unit. US$` de `Custo Unit. R$`.
- Menu Engenharia corrigido para exibir: Cadastro de Itens, Estruturas BOM, Preço de Venda / Locação, Revisões e Codificação.

## Compatibilidade
- Sem alteração destrutiva no banco nesta revisão.
- Mantida a base oficial `BASE_CADASTRO_BOHM_V8` e as regras de codificação configuráveis.
