# Inventário Autopass — V82.12 ENXUTA

Correções em RH > APT/PT.

- Nova PT para o mesmo colaborador reaproveita automaticamente NR10, NR35, ASO e Integração do cadastro ativo existente.
- Esses campos deixam de ser solicitados novamente no fluxo `+ Incluir PT`.
- A nova PT solicita apenas os dados próprios da autorização (linha, número, validade, status/observação quando aplicável).
- Backend também herda os dados compartilhados, evitando dependência exclusiva da interface.
- Linhas APT 4, 5, 8 e 9 aceitam variações usuais de nomenclatura e são normalizadas para a descrição configurada.
- Corrigido fluxo de Salvar: validações exibem a pendência real e erros do backend são apresentados ao usuário.
- Edição de uma APT existente continua permitindo atualização explícita dos dados documentais.
- Registros e PTs anteriores do colaborador são preservados.
