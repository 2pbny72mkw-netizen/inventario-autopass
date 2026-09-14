# V80 REV11.3 — Correção Colar Report de Transações ATM

## Correção
- Substitui o fluxo **Importar Transações ATM** por **Colar Report de Transações**.
- O usuário cola diretamente o conteúdo do R0050, sem abrir seletor de arquivos.
- Validação local exige os cabeçalhos `cod_atm`, `data_hora_trans`, `valor`, `valor_recebido` e `status`.
- Exibe prévia com quantidade de linhas/colunas antes do processamento.
- O processamento reutiliza o importador transacional existente, preservando deduplicação, histórico, progresso e regras de negócio.
- Nenhuma alteração de banco de dados.

## Preservado
- Importação de apurações TB Forte permanece por arquivo.
- Colar reporte diário permanece inalterado.
- Histórico de transações e ciclos permanece inalterado.
