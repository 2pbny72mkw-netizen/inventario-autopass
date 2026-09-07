# Sistema de Gestão / Inventário Autopass — V78.4 REV1

## Engenharia / BOM multinível
- Produto final exibido explicitamente como N0.
- Itens e subestruturas diretas exibidos como N1.
- Componentes de BOMs vinculadas exibidos automaticamente como N2, N3 e níveis seguintes.
- Árvore com indentação, chips N0/N1/N2+, expandir/recolher e identificação visual de subestrutura.
- Roll-up de custo: subestrutura usa automaticamente o custo unitário da BOM vinculada; o preço não é digitado manualmente no nível superior.
- Fluxo `+ Criar subestrutura` cria uma BOM reutilizável e um item mestre do tipo SUBESTRUTURA já vinculado.
- Inclusão permite alternar entre Item simples e Subestrutura existente.

## Visual
- Nacional e Importado usam famílias de cor claramente diferentes.
- Material, Consumo e Serviço mantêm variações dentro de cada origem.
- Legenda de níveis e origem adicionada à tela.

## Mantido
- Nacional sem FOB em USD; custo em R$.
- Importado com FOB em USD e custo nacionalizado em R$.
- Quantidade fracionada permitida nos componentes da BOM.
- Classificação Material/Consumo/Serviço permanece editável por vínculo na BOM.
- Base oficial BOHM e regras configuráveis de codificação preservadas.
