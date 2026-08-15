AUTOPASS — V1 OPERACIONAL + DASHBOARD EXECUTIVO V2
===================================================

BASELINE
- Construído sobre o ZIP do repositório enviado após a release 1408-5 ficar Live.
- Preserva tela técnica, Editar/Excluir, base 1408-5 e mapa metroferroviário aprovado.

PRINCIPAIS EVOLUÇÕES
- Dashboard executivo com big numbers: parque previsto, inventariado, faltante, cobertura, divergências e inoperantes.
- Big numbers por ATM, Validador, POS, TDI e Bloqueio.
- Cada família mostra previsto, levantado, faltante e percentual.
- Filtros executivos por empresa, linha e tipo.
- Ranking das localidades com maior pendência.
- Gráfico/barra de avanço por tipo de equipamento.
- Tabela de localidades passa a considerar os cinco tipos na previsão.
- API /api/dashboard passa a devolver by_type e missing.
- API /api/locations passa a devolver expected_by_type e expected_total.
- /health identifica release v1-operacional-dashboard-v2.
- Cache-busting do manager.js e variável window.AUTOPASS_MANAGER_VERSION.

DEPLOY
1. Substitua os arquivos/pastas do repositório pelo conteúdo deste ZIP mantendo a estrutura.
2. Não suba __pycache__ caso apareça localmente.
3. Commit único no GitHub.
4. Render -> Deploy latest commit.

TESTE DE VERSÃO
Console em /gerencial:
window.AUTOPASS_MANAGER_VERSION
Esperado: "dashboard-v2-1"

Teste /health:
release deve ser "v1-operacional-dashboard-v2".

ROTEIRO DE TESTE
1. Abrir /gerencial e validar os 6 KPIs superiores.
2. Conferir os 5 cards ATM/Validador/POS/TDI/Bloqueio.
3. Testar filtro Empresa -> Linha -> Tipo.
4. Conferir ranking de maiores pendências.
5. Conferir tabela por localidade com os cinco tipos.
6. Conferir mapa, legenda, linhas e nomes de estações (não devem regredir).
7. Abrir /tecnico e confirmar cadastro + Editar + Excluir.
8. Validar uma localidade de cada tipo de equipamento.

OBSERVAÇÃO
Os totais executivos são calculados pela associação dos ativos da base 1408-5 às localidades. Na primeira validação, compare os big numbers com a planilha/base oficial; qualquer diferença será tratada como reconciliação de dados, sem apagar inventários já realizados.
