# V79.4 REV2 — Coleta de Valores + Engenharia

## Coleta de Valores
- Modais compactos (máx. 84vh), cabeçalho/fechar visível, scroll interno, ESC e clique no fundo para fechar.
- Filtro ATM digitável/pesquisável, com colagem e sugestões da base oficial.
- Ordenação da Diferença: negativos mais críticos primeiro, depois zero, positivos e sem valor ao final.
- Preserva Dash 2.0, edição por ATM, reporte diário, criticidade e fila de prioridades da V79.4.

## Engenharia
- Nova BOM de Produto N0 carrega somente itens ativos do Cadastro Mestre com códigos iniciados por 00.01 ou 00.03.
- Combo exibe Código · Descrição.
- Regra validada também no backend para impedir criação indevida via API.

Google Sheets automático permanece fora desta revisão até definição da autenticação/estrutura da planilha.
