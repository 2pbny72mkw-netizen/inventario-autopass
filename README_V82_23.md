# Inventário Autopass — V82.23

## Correções
- Financeiro > Monitoramento de Coletas: importação TBForte não depende mais de já existir fechamento R0050 na mesma data.
- Apuração TBForte sem R0050 é preservada por ATM + data + GTV, com Declarado e Apurado, ficando aguardando correlação transacional.
- Registro TBForte sem horário real não corta o ciclo R0050 e não exibe horário fictício 00:00.
- RH > APT: área da tabela limitada à largura útil da tela e rolagem horizontal interna sempre disponível.
- Tabela APT ampliada para preservar colunas e ações sem comprimir o conteúdo.

## Validação sugerida
- Reimportar/confirmar a apuração do ATM 12154 de 16/09/2026 e verificar Declarado/Apurado/GTV no monitoramento.
- Em RH > APT, confirmar a barra horizontal na base da tabela e navegar até Arquivo APT/Ações.
