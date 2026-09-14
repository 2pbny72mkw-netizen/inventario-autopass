# V80 REV12 — CORREÇÃO COLAR REPORT

## Objetivo
Corrigir o fluxo de carga das Transações ATM no Monitoramento.

## Alteração
- Substitui o botão **Importar Transações ATM** por **Colar Report de Transações**.
- O clique abre modal para colar diretamente o conteúdo do relatório R0050 copiado da origem.
- Valida os cabeçalhos obrigatórios: `cod_atm`, `data_hora_trans`, `valor`, `valor_recebido` e `status`.
- Exibe prévia simples com quantidade de linhas/colunas antes de liberar o processamento.
- Processa o conteúdo colado usando o mesmo importador incremental já existente no backend, preservando deduplicação/upsert, auditoria e histórico de cargas.
- A importação de apurações TB Forte permanece por arquivo, sem alteração.

## Versão
Aplicação / Dashboard / Equipes: **V80 REV12**.
