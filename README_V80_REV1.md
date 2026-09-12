# Sistema de Gestão Autopass — V80 REV1

Pacote ENXUTO para sobreposição sobre o projeto completo confirmado como produção.

## Coleta de Valores

### Importação de Transações ATM
- Novo botão no Monitoramento para importar o relatório R0050 em XLSX.
- Compatível com o layout atual contendo `cod_atm`, `data_hora_trans`, `idtrn`, `tipo_produto`, `produto`, `voucher_gerado`, `voucher_number`, `valor`, `valor_recebido`, `status` e `Status Desc`.
- Mantém compatibilidade com o importador transacional legado.
- Carga incremental por chave estável da transação; registros já conhecidos não são duplicados e podem ter a fotografia atualizada.
- Exibe última importação, arquivo, data máxima da base transacional e quantidade armazenada.
- Histórico das últimas importações pelo card de status.
- Conciliação passa a preferir `valor_recebido` quando disponível, com fallback para o valor legado.

### Programação de Coletas
- Filtros próprios: Operadora, Linha, Estação/Localidade, ATM e Programação.
- Cabeçalhos com ordenação cíclica: sem ordem → crescente → decrescente → sem ordem.
- Coleta extra não elimina a agenda-base; o Monitoramento passa a informar a próxima previsão recorrente também para extras.

### Planejamento de Auditoria
- Botão disponível no Monitoramento e na Programação.
- Usa o período selecionado no Monitoramento.
- Consolida por data e localidade: ATMs, coletas regulares, extras e reagendadas.
- Regra inicial: 1 auditor por localidade/dia.
- Mostra pico de necessidade, gráfico diário e detalhamento por localidade/ATM.
- Não otimiza ainda deslocamentos ou compartilhamento entre localidades em horários diferentes.

## Banco de dados
Migração aditiva em `financial_atm_transactions`:
- `received_value`
- `external_tx_id`
- `product_type`
- `product_name`
- `voucher_generated`
- `voucher_number`
- `status_desc`
- `source_collection_code`

Nenhuma tabela ou dado anterior é removido.
