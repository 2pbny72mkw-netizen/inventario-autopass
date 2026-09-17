# Inventário Autopass — V82.18

Versão consolidada.

- Mapeamento ATM: evidência fotográfica obrigatória no backend; conclusão só ocorre após foto persistida; API devolve as fotos existentes para reabertura sem perda do histórico.
- Visão Panorâmica: amplia escopo de operadoras para ViaMobilidade/ViaQuatro/CCR e preserva linhas/localidades reais.
- Monitoramento de Coletas: Excel filtrado passa a espelhar a tabela com BAG, última coleta, transações e diferenças T×A, T×D e A×D.
- Financeiro · Caixinha: estrutura de permissões, abertura de caixinha, entradas/despesas, comprovantes, big numbers, saldo e prestação de contas PDF; preparada para dois níveis de aprovação.
- Release: V82.18.

Observação: mensagens globais de sucesso devem usar a categoria `success` do layout base; a padronização visual depende do `base.html` da instalação completa, que não integra o pacote enxuto atual.
