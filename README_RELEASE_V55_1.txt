INVENTÁRIO AUTOPASS — V55.1
Release de consolidação pós-homologação da V55.

PRINCIPAIS ENTREGAS
1. Gestão / Navegação
- Gestão agrupa Chamados, Central 360, Notificações, Diagnóstico e Configurações.
- Meu Perfil, Sobre e Sair posicionados à direita.
- Dashboard Implantação passa a usar rota canônica /dashboard/implantacao.
- Modo TV e Concorrência permanecem dentro do sidebar.

2. ADM Financeiro
- Perfil reconhecido no login, sem loop para /equipes.
- Landing page em Financeiro.
- Acesso ao módulo Financeiro e Dashboard Financeiro/ATM.
- Perfil documentado na tela Usuários.

3. Usuários
- Bloqueio de nomes completos duplicados, normalizando maiúsculas/minúsculas e espaços.
- Mensagem clara de usuário já cadastrado.

4. Chamados / TopDesk 2.0
- Período padrão inicia em 01/01/2026.
- Rankings Top 10 com Ver mais / Recolher.
- Quantidade + participação % na mesma linha.
- Comparação com referência/período anterior quando disponível.
- Central de Atenção com identificação amigável do ATM.
- Produtividade × Reincidência redesenhada com quadrantes, médias e legenda visual.
- Modo TV dedicado em /topdesk/tv.

5. Contratos / Vencimentos ATM
- Remoção da referência visual GPN como contrato gerencial.
- Base de vencimento validada pela planilha oficial enviada.
- 412 ATMs: vencimento Dez/2026.
- 100 ATMs: vencimento Fev/2028.
- 90 ATMs: sem contrato/vencimento informado na base atual de 602 ATMs.
- Filtros e exportação usam a mesma referência validada.

6. Dashboard ATM / ATM Financeiro
- Ranking de localidades com cores distintas.
- Parque × Contratado × Faturado redesenhado com barras agrupadas e divergências.
- % do parque faturado por modelo.
- Dashboard 2.0 com maior contraste e diferenciação visual.

7. Dashboard Financeiro 2.0 — multiproduto
- Nova rota /financeiro/dashboard.
- Filtro de competências com múltipla seleção.
- Filtro Centro de Custo.
- Filtro Produto: Todos, ATM, POS, Recarga, Rack, Bloqueio, Outros.
- Rateios cadastrados no Suporte a Campo alimentam a visão por produto.
- KPIs Realizado, Forecast, Desvio R$, Desvio % e Média mensal.
- Evolução Realizado × Forecast.
- Composição de custos por produto.
- Matriz histórica com custos nas linhas e competências nas colunas.
- ATM Financeiro preservado como detalhamento do produto ATM.

8. Coleta de Valores
- Ajustes visuais Dashboard 2.0.
- Gráficos deixam de ser monocromáticos.

9. Performance / regressão
- Mantidas otimizações da V55 para TopDesk, thumbnails/lazy loading/cache e importação.

VALIDAÇÕES LOCAIS EXECUTADAS
- app.py: compilação Python PASS.
- topdesk.js: sintaxe Node PASS.
- manager.js: sintaxe Node PASS.
- cash_collection.js: sintaxe Node PASS.
- sw.js: sintaxe Node PASS.
- Templates Jinja principais: parse PASS (9/9).
- JS inline do Dashboard Financeiro e TopDesk TV: sintaxe PASS.
- Checklist estático das rotas/perfis/regras principais: PASS.
- Contratos: teste independente resultou 412 / 100 / 90 conforme referência esperada.

HOMOLOGAÇÃO NO RENDER AINDA NECESSÁRIA
- Login ADM Financeiro e permissões reais no PostgreSQL/Render.
- Dashboard Implantação abrindo corretamente após deploy/cache.
- Filtros e cálculos financeiros com dados reais cadastrados.
- TopDesk TV e comparativos com base já importada.
- Regressão das demais dashboards e service worker em produção.
