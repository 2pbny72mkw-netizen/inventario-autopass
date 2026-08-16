V20.0 — Consolidação Executiva e Inteligência do Parque

Inclui a estabilização prevista para V19.1 dentro da V20.

Principais pontos:
- versões unificadas em V20.0 / dashboard-v20 / teams-v20;
- Bloqueio identificado pelo final do prefixo/terminal (ex.: 500502 => BLOQ02);
- configuração técnica do bloqueio ligada ao prefixo: grupo, linha lógica, IP, máscara, gateway, DNS1 e DNS2;
- IP esperado preenchido como referência no lançamento de Bloqueio;
- escala 7/14/21 dias reage à troca de período, data e categoria;
- mantém filtros e visão analítica executiva introduzidos nas versões anteriores;
- base 1408-5 preservada;
- preparação para Ficha Técnica 360 e inteligência operacional.

Teste prioritário após deploy:
1. Sobre deve exibir V20.0 nos três módulos.
2. Praça da Árvore: prefixo 500502 deve aparecer como BLOQ02 e exibir dados de rede.
3. Equipes: alternar 7, 14 e 21 dias deve mudar imediatamente as colunas da escala.
4. Alterar a data inicial deve reconstruir a escala.
5. Validar Dashboard com e sem filtros.
6. Validar lançamento mobile e desktop.
