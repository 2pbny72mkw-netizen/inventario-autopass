# V80 REV11 ENXUTA

Base cumulativa: V80 REV10.

## Alterações

- Monitoramento de Coletas passa a ter rota própria no Financeiro: `/financeiro/monitoramento-coletas`.
- Menu Financeiro recebe o subitem **Monitoramento de Coletas**; Coleta de Valores permanece para custos/programação/fila.
- Monitoramento em modo full-width, com margens laterais mínimas e células mais compactas para reduzir scroll horizontal.
- Nova coluna **Dif. T × A** = Transações − Apurado, entre Transações e Dif. T × D, com ordenação crescente/decrescente.
- Novo Big Number **Divergências T × A**, clicável, com quantidade, saldo, diferença absoluta e drill-down dos ciclos.
- Novo Big Number **Sem apuração TB Forte**, clicável, listando fechamentos do filtro sem Valor Apurado.
- Novo botão **Importar Apurações TB Forte** no Monitoramento.
- Importador aceita CSV/XLSX com aliases de Data, ATM/Ponto, GTV, Valor Declarado, Valor Apurado e Diferença.
- Associação prioriza ATM + data + GTV; quando não existe ocorrência no Monitoramento mas existe fechamento R0050 na data, cria a ocorrência financeira vinculada ao horário sistêmico do R0050.
- Auditoria da importação TB Forte em `AuditEvent` (`FIN_TBFORTE_APURACAO_IMPORTED`).
- Detalhe do ciclo passa também a exibir **Dif. T × A**.
- Histórico Sobre atualizado para V80 REV11.

## Deploy

Este pacote é ENXUTO. Sobreponha os arquivos ao projeto completo em produção; não substitua o projeto inteiro apenas por este ZIP.

## Validação recomendada

1. Abrir Financeiro > Monitoramento de Coletas e confirmar o layout full-width.
2. Validar ordenação da coluna Dif. T × A.
3. Clicar nos Big Numbers T × A e Sem apuração TB Forte.
4. Importar um relatório real TB Forte em CSV/XLSX e validar ATM, data, GTV, Declarado e Apurado.
5. Conferir um ATM com fechamento R0050 sem lançamento prévio: a importação deve criar/associar a ocorrência sem duplicar fechamento existente.
