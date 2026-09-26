# V85.17 REV3 — Correções de homologação

Correções pontuais sobre a V85.17 REV2:

- adiciona `import copy` para o cache do Monitoramento;
- protege a renderização quando `summary` estiver ausente/nulo;
- mantém as funções de seleção/exclusão em lote dentro do mesmo escopo do estado `V` e de `load()`, corrigindo `ReferenceError: V is not defined`;
- atualiza cache-busting do JavaScript/CSS;
- nenhuma nova funcionalidade e nenhuma alteração de regra financeira.
