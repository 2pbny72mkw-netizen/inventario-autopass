AUTOPASS — V5.2 CENTRAL DE EQUIPES

BASE
Construído sobre o main.zip mais recente enviado após a V5.1.

EVOLUÇÕES
1. Correção definitiva do mapa fullscreen
   - usa Fullscreen API nativa do navegador
   - Leaflet invalidateSize em múltiplos momentos
   - botão Sair dentro da tela cheia
   - fallback para navegadores sem Fullscreen API

2. Escala por dias
   - tabela de 7, 14, 21 ou 31 dias
   - técnico nas linhas
   - datas nas colunas
   - Trabalho / Folga
   - turno e ponto de entrada visíveis
   - rolagem horizontal e coluna do técnico fixa

3. Gerenciamento da escala
   - Adicionar técnico
   - Vincular usuário existente
   - Nome manual quando necessário
   - Turno 05h–17h ou 11h–23h
   - Primeiro dia do ciclo 12x36
   - Ponto de entrada
   - Linhas
   - Supervisão
   - Editar / mudar escala
   - Remover técnico da escala sem excluir o usuário do sistema

4. Persistência
   - nova tabela PostgreSQL team_schedule_profiles
   - o JSON original serve apenas como seed inicial
   - alterações futuras ficam no banco e sobrevivem aos deploys

5. Localização
   - mantém anel verde / amarelo / vermelho / cinza
   - mantém mapa operacional
   - mantém localização autorizada pelo técnico

VERSÕES
Dashboard: dashboard-v5-2
Central de Equipes: teams-v5-2
Health: v5.2-central-operacional

TESTES APÓS LIVE
- /equipes
- Conferir escala por dias
- Gerenciar escala -> editar um técnico e cancelar/salvar
- Testar remover apenas com registro de teste
- Expandir mapa -> conferir tiles -> sair
- Console /gerencial:
  window.AUTOPASS_MANAGER_VERSION
  esperado dashboard-v5-2

6. Dashboard gerencial com cores executivas
   - cores suaves nos KPIs gerais
   - identidade visual por ATM, Recarga, POS, TDI e Bloqueio
   - Evidências e gráficos com destaques discretos
   - mantém fundo claro e leitura executiva

7. Sobre / Versões
   - botão Sobre no menu
   - página /sobre
   - versão da aplicação, dashboard, equipes e base
   - módulos disponíveis
   - histórico recente
   - crédito by Adil J. Poloni
