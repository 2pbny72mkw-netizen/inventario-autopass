# V80 REV9 — Performance + CSV R0050

Base: V80 REV8 ENXUTA.

## Alterações

- APP_RELEASE atualizado para `V80 REV9`.
- Importação de transações aceita `.csv`, `.xlsx` e `.xlsm`.
- CSV R0050 processado em streaming, sem carregar o arquivo inteiro em memória.
- CSV usa a mesma chave `source_hash` e o mesmo upsert do XLSX: registros conhecidos são atualizados e não duplicados.
- Mantidos Data Coleta, Código Coleta, status, produto, voucher, valor recebido e composição de cédulas.
- Monitoramento de Coleta de Valores passa a pré-carregar em lote:
  - fechamentos R0050 por ATM + Código Coleta + Data Coleta;
  - agregados de quantidade/valor por ciclo e status selecionados;
  - fechamentos manuais válidos necessários à cadeia.
- O payload principal deixa de consultar Data Coleta e somatórios de transações repetidamente para cada ocorrência, eliminando o principal padrão N+1 da REV8.
- `/api/financeiro/coletas/v80/transacoes/status` consolida count/max import/max transação em uma única consulta agregada.
- Preservadas as regras da REV8: R0050 é fonte sistêmica prioritária, descoberta automática de fechamentos extras e cadeia cronológica por ATM.

## Validação recomendada pós-deploy

1. Confirmar `V80 REV9` no cabeçalho/Sobre.
2. Importar o CSV R0050 consolidado de agosto/setembro.
3. Confirmar que uma reimportação não aumenta artificialmente a quantidade de transações.
4. Validar ATM 50054: fechamentos 02/09 10:19:29 → 04/09 14:12:10 → 08/09 11:22:01.
5. Validar ATM 11056: Data Coleta sistêmica deve prevalecer sobre 12:00 manual.
6. Exportar nova telemetria após alguns acessos ao Monitoramento e comparar `/api/financeiro/coletas/v79` com a REV8.
