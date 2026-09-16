# Inventário Autopass — V82

## Mapeamento ATM
- Nova atividade em Field, controlada pela Matriz de Permissões (`field.atm_mapping` e `field.atm_mapping_manage`).
- Fase 1 usa a base oficial e exibe somente ATMs com venda em dinheiro.
- Registro individual por ATM: possui furos, furos tampados, acesso físico interno/externo, observação, GPS e uma ou mais fotos.
- Fotos podem ser capturadas pela câmera ou selecionadas da galeria e são armazenadas no R2 quando configurado.
- Dashboard operacional da atividade com filtros e indicadores de pendência, acesso e furos.

## Bobinas — desempenho
- Botão “Desempenho por Técnico” na Dashboard de Bobinas.
- Períodos 5, 7, 10, 15 e 30 dias.
- Ranking de trocas em ATM ou distribuição de bobinas, participação, dias ativos, média/dia e índice versus média agregada.
- Atividade Bobinas mostra “Meu desempenho” ao técnico, sem nomes, ranking ou métricas individuais dos demais.

## Banco
- Novas tabelas `atm_mappings` e `atm_mapping_photos`, criadas por `create_all(checkfirst=True)` no ciclo de migração existente.
- Nenhum dado anterior é removido.
