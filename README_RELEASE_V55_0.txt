INVENTÁRIO AUTOPASS — V55.0
===========================
Base: main completo recebido após V52.8.
Objetivo: salto estrutural com foco em Gestão, TopDesk/Chamados, performance, Central 360 e eficiência de mídia.

1. GESTÃO NO MENU SUPERIOR
- Nova aba superior "Gestão".
- Agrupa Chamados, Central 360, Notificações e Diagnóstico.
- Dispatcher mantém acesso a Chamados; Gestor/Gestor Field veem o conjunto gerencial.
- Nova tela /notificacoes.

2. TOPDESK / CHAMADOS — PERFORMANCE
- Removido N+1 de Location na análise: Location passa a ser join/preload.
- Importação pré-carrega chamados existentes por número e localidades uma única vez.
- Commit de importação em lotes maiores (1000), reduzindo overhead.
- Índices adicionados para operador, data textual, localização/status, equipamento/status e categoria/subcategoria.
- Cache de analytics por filtro com TTL configurável (padrão 180 s), invalidado após importação.
- Filtros diretamente indexáveis são aplicados no banco antes da etapa legada em Python.

3. IMPORTAÇÃO EM BACKGROUND / NAVEGAÇÃO
- Importação continua no servidor em thread de background.
- Novo endpoint /api/topdesk/import/active.
- Banner global mostra percentual/processados/fase mesmo após navegar para outra tela.
- Proteção contra carga concorrente mantida.

4. INTELIGÊNCIA COM REFERÊNCIA
- Rankings de falhas, linhas e localidades passam a trazer:
  * volume;
  * participação % no recorte;
  * comparação com período anterior quando início/fim forem definidos;
  * comparação com média das categorias quando não houver período explícito.
- Equipamentos crônicos passam a mostrar participação e múltiplo da média do parque.
- Central de Atenção usa o múltiplo da média como contexto.

5. CENTRAL 360
- Chamados TopDesk entram no resumo gerencial.
- Busca Global 360 passa a localizar número de chamado, objeto e falha TopDesk.
- Acesso rápido para Chamados 2.0.

6. EVIDÊNCIAS TEMPORÁRIAS / BANDWIDTH
- Criados fluxos administrativos de limpeza de evidências de:
  * Troca de Chip Recarga;
  * Troca de Chip EMV – Trilhos.
- A limpeza só é autorizada quando todos os registros da campanha estiverem concluídos e exige CONFIRMAR.
- Registros operacionais, autoria, datas, resultado, status e auditoria são preservados.
- Visão Panorâmica NÃO entra nessa limpeza e permanece permanente.
- Diagnóstico passa a exibir volume de TopDesk, quantidade/tamanho de mídia local e fotos temporárias.
- Mantidas miniaturas/lazy loading/cache introduzidos na V52.8.

7. PWA / MOBILE
- Service Worker e cache atualizados para V55.
- Manifesto atualizado para o escopo V55.
- Importação TopDesk pode ser acompanhada globalmente no navegador.

VALIDAÇÃO ANTES DO ZIP
----------------------
PASS — app.py compila (py_compile)
PASS — static/topdesk.js (node --check)
PASS — static/manager.js (node --check)
PASS — sw.js (node --check)
PASS — 9 templates alterados analisados pelo parser Jinja2
PASS — testes puros de cálculo de período anterior / participação / variação
PASS — checklist estático de 17 requisitos críticos

LIMITAÇÃO DE TESTE LOCAL
------------------------
O ambiente de geração não contém Flask/SQLAlchemy instalados e não possui acesso à internet para instalá-los.
Por isso, não foi possível subir a aplicação Flask completa contra um banco local nesta execução.
A homologação runtime no Render continua necessária para confirmar tempos reais de PostgreSQL, sessão e service worker.

TESTES PRIORITÁRIOS NO RENDER
-----------------------------
1. Gestão > Chamados / Central 360 / Notificações / Diagnóstico.
2. Abrir Chamados com ~50 mil registros e comparar tempo de primeira carga e segunda carga (cache).
3. Filtrar período e confirmar % / comparação com período anterior.
4. Iniciar importação e navegar para outra tela; confirmar banner global e conclusão.
5. Pesquisa Global 360 por número de chamado e ID de ATM.
6. Diagnóstico: conferir contagem TopDesk e mídia.
7. Não executar limpeza de fotos de EMV/Recarga até a campanha estar integralmente concluída e validada.
