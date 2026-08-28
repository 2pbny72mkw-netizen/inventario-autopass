V66 REV3 — REVISÃO CONSOLIDADA

1. RH / Usuários
- Corrige regressão em que os botões Editar/Ativar podiam desaparecer após a primeira linha.
- Causa raiz: user_access(u) sobrescrevia o cache de permissões do usuário autenticado durante a renderização da tabela.
- Cache agora é mantido somente para o usuário da sessão.
- Restrições de RH continuam: administra apenas Técnico Field e Técnico Implantação.

2. GPS / Equipes
- O popup da posição atual deixa de depender apenas da localidade associada ao registro.
- Calcula a estação com referência geográfica mais próxima entre as localidades cadastradas.
- Exibe estação, linha, empresa e distância em metros.
- Se não houver referência geográfica disponível, informa explicitamente.

3. Versão/cache
- APP_RELEASE V66 REV3.
- Cache/service worker atualizado para v66-rev3.
- Histórico Sobre atualizado.
