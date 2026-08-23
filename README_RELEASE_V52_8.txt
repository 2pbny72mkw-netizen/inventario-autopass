INVENTÁRIO AUTOPASS — V52.8 ENXUTA
==================================
Base: V52.7 ENXUTA
Escopo: Dashboard Chamados 2.0 + progresso de importação TopDesk + primeira camada de redução de bandwidth.

IMPLEMENTADO
1. Release/cache atualizados para V52.8.
2. Dashboard Chamados com KPIs coloridos por semântica, rankings multicoloridos, heatmap com escala de intensidade e dispersão produtividade x reincidência com cores de quadrante.
3. Importação TopDesk em background, com job_id e polling de progresso.
4. Progresso exibe fase, %, processados/total, novos, atualizados, ignorados, erros e tempo decorrido.
5. Bloqueio de dupla importação simultânea no mesmo processo.
6. Deduplicação preservada pelo número do incidente/chave estável.
7. TopDeskImportBatch continua registrando carga concluída no banco.
8. Erro de importação passa a ser mostrado explicitamente; botão é reabilitado ao finalizar/interromper.
9. /uploads suporta ?thumb=1 para imagens, gerando miniatura JPEG de até 520 px.
10. Galeria de Visão Panorâmica usa thumb_url para miniatura e mantém original no link de abertura.
11. Evidências da Troca de Chips Recarga usam thumbnail na grade e original no clique.
12. Fotos de técnicos no mapa passam a solicitar thumbnail.
13. Cache privado de imagens estáticas/evidências ampliado para evitar download repetido de arquivos imutáveis.
14. Fotos de usuários deixam de usar no-cache e passam a permitir cache privado; thumbnail suportada.
15. loading=lazy/decoding=async preservado/adicionado nas galerias alteradas.

VALIDAÇÃO PRÉ-PACOTE
PASS - python -m py_compile app.py
PASS - node --check static/topdesk.js
PASS - node --check static/manager.js
PASS - node --check static/chip_swap.js
PASS - endpoint /api/topdesk/import/<job_id>/status presente no código
PASS - importação antiga síncrona substituída pelo fluxo job/polling
PASS - APP_RELEASE=V52.8 e service worker autopass-v52-8
PASS - thumbnail URL presente nos payloads de Panorama e Chip Swap
PASS - nome do script TopDesk atualizado para v52-8

LIMITAÇÃO DE TESTE LOCAL
O ambiente de geração não possui as dependências Flask/SQLAlchemy instaladas, portanto não foi possível subir a aplicação completa localmente contra o banco. A compilação Python e a sintaxe JS foram validadas. O comportamento em background deve ser homologado no Render, principalmente caso o serviço use mais de um processo Gunicorn, pois o status operacional da importação é mantido em memória do processo durante a carga.

TESTE DE ACEITE NO RENDER
A. Chamados > importar planilha: confirmar que % e contadores avançam durante a carga.
B. Confirmar conclusão e recarga automática dos KPIs.
C. Aplicar filtro por técnico/linha e conferir que todos os gráficos mudam.
D. Abrir Panorâmica e observar no Network que a grade solicita ?thumb=1; clicar numa foto e confirmar abertura do original.
E. Conferir que imagens já vistas não são novamente transferidas integralmente ao navegar/reabrir a tela.
