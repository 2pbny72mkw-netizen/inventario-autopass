# V79.2 — Coleta de Valores

## Escopo
- Mantém a base mestre oficial de 602 ATMs; não cria cadastro paralelo.
- Monitoramento por Data inicial / Data final (até 366 dias).
- Filtro por programação (terça/quarta/quinta/sexta), status, operadora, linha, estação, ATM e diferença.
- Ordenação crescente/decrescente pelos cabeçalhos principais.
- Tabela por ocorrência prevista, com Próxima previsão.
- Edição de data, hora, valor declarado, valor apurado e observação.
- Reagendamento de ocorrência sem alterar a regra recorrente da ATM.
- Status Pendente de coleta e Reagendada.
- Composição opcional de cédulas, com total calculado e conferência contra o valor declarado.
- Histórico TBForte JAN-AGO/2026 carregado a partir do extrato consolidado enviado, correlacionado somente às ATMs oficiais.
- Exportação Excel respeitando os filtros ativos.

## Dados do extrato
- Transporte: 2.850 registros lidos.
- Processamento: registros correlacionados por ATM + data + GTV, somando Cédula/Moeda quando aplicável.
- 2.814 eventos de transporte tiveram correspondência direta no processamento por ATM/data/GTV.
- Registros sem correspondência permanecem com os dados disponíveis, sem inventar valor apurado.

## Auditoria
Edição e reagendamento geram AuditEvent. A programação mestre não é sobrescrita por um reagendamento pontual.

## Validações
- python -m py_compile app.py
- Jinja parse financial_cash_collection.html
- node --check cash_collection_v79.js
- unzip -t pacote final
