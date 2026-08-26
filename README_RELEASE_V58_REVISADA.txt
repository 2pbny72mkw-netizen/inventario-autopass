V58 REVISADA — estabilidade da Central Operacional

- Corrige race condition da tela Equipes: dados não dependem mais da inicialização do Leaflet.
- Remove startup prematuro antes das declarações V39/V40.
- Inicialização determinística: dados -> mapa -> atualização periódica.
- Falha de mapa não zera cards, Operação de Hoje ou Equipe Prevista.
- Corrige N+1 do calendário ao reutilizar usuários já carregados em lote.
- Mantém a V58 como base e preserva EMV, Apuração e otimizações anteriores.
