# Inventário Autopass — V80 REV2 ENXUTA

## Escopo
Evolução do Monitoramento de Coleta de Valores sobre a V80 REV1.

### Ciclo transacional na própria tabela
- Nova coluna **Transações** para coletas com fechamento real.
- Janela: `transação > fechamento anterior` e `transação <= fechamento atual` do mesmo ATM.
- Nova coluna **Dif. T × D** = Transações − Declarado.
- Mantida **Dif. A × D** = Apurado − Declarado.
- O valor de Transações é clicável e abre o detalhe do ciclo.

### Detalhe Inteligente do Ciclo
- fechamento anterior e atual;
- quantidade de transações válidas e total de registros do período;
- Transações, Declarado e Apurado;
- diferenças T×D, D×A e T×A;
- status e produtos presentes no ciclo;
- lista auditável das transações;
- análise textual automática do ciclo;
- resumo das cédulas R$2, R$5, R$10, R$20, R$50, R$100 e R$200.

### R0050 — composição de cédulas
A V80 REV2 passa a persistir as colunas `nota_2`, `nota_5`, `nota_10`, `nota_20`, `nota_50`, `nota_100` e `nota_200` do R0050.

**Importante após o deploy:** as transações já armazenadas antes da REV2 não possuem essas colunas preenchidas. Reimporte o mesmo R0050 uma vez. O importador usa a mesma chave de deduplicação: os registros existentes são atualizados/enriquecidos e não duplicados.

## Aplicação
Pacote ENXUTO. Sobrepor os arquivos ao projeto completo em produção.
