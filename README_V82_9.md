# Inventário Autopass — V82.9 (ENXUTA)

Patch incremental sobre a V82.8.

## RH · APT/PT
- tabela mais larga, com laterais reduzidas e área própria de scroll horizontal/vertical;
- botão Recolher/Expandir tabela;
- ações Editar, Inativar/Reativar e Excluir em linha horizontal;
- botão `+ Incluir PT` em cada PT já cadastrada, permitindo nova PT para o mesmo usuário sem alterar as existentes.

## Monitoramento · Reprogramação de coletas
- `Tornar vigente` exclusivo do ADM principal, validado também no backend;
- botão não é exibido aos demais usuários;
- estratégia agressiva usa exclusivamente `Valor Apurado` das últimas 2 ou 3 coletas com apuração disponível;
- ausência de valor apurado é desconsiderada, sem fallback para declarado/coletado e sem converter em zero;
- campo renomeado para `Valor apurado de referência (R$)`.
