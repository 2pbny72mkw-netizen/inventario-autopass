# V80 REV6 — Coleta de Valores / fechamento sistêmico R0050

Base: V80 REV5.

## Alterações
- A conciliação passa a priorizar `Data Coleta` do relatório R0050 como instante sistêmico de fechamento.
- O horário manual permanece preservado como fallback e para auditoria; não é sobrescrito silenciosamente.
- O importador R0050 passa a armazenar também `Data Coleta`, `Codigo Coleta`, `abertura_servico` e `fechamento_servico`.
- A janela do ciclo usa: `transação > fechamento anterior` e `transação <= fechamento atual`, priorizando R0050 nos dois extremos quando disponível.
- Na tabela do Monitoramento, a nova coluna **Última coleta** aparece antes de **Data prevista** e usa o fechamento efetivo do ciclo.
- Fonte visual do fechamento:
  - `R0050` em verde/teal suave;
  - `MANUAL` em amarelo suave.
- Quando o horário R0050 difere do manual, o horário manual continua visível como referência de auditoria.
- O `Código Coleta` do R0050 aparece no detalhe/tooltip do ciclo.
- O controle **Mostrar mais / Recolher linhas** foi movido para cima da tabela.
- Histórico Sobre atualizado para V80 REV6.

## Validação com a ATM 32852
Com o arquivo de referência R0050 fornecido:
- fechamento anterior R0050: 01/09/2026 11:56:06;
- fechamento atual R0050: 10/09/2026 09:08:02;
- considerando status `A + VOUCHER`: 385 transações;
- total efetivo: R$ 9.768,00;
- declarado: R$ 9.768,00;
- Dif. T × D: R$ 0,00.

Isso confirma a regra esperada para o exemplo discutido.

## Pós-deploy
Reimporte uma vez o R0050 já utilizado. A importação é incremental/upsert e não duplica as transações; essa reimportação é necessária para preencher os novos campos sistêmicos de `Data Coleta` nos registros que já estavam no banco.
