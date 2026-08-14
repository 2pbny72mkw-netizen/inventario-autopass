INVENTÁRIO AUTOPASS — RELEASE CAMPO 1408-5
=============================================

OBJETIVO
Concentrar várias evoluções em um único deploy.

INCLUÍDO
- requirements.txt na raiz (corrige o build do Render).
- Base detalhada regenerada a partir da planilha INVENTARIO AUTOPASS - EQUIPAMENTOS DE CAMPO - 1408.xlsm.
- Tipos tratados: ATM, Validador de Recarga, POS de Bilheteria, TDI e Bloqueio.
- Correção de linha POS: L01 - AZUL -> 01 - AZUL.
- TDI de Sacomã associado ao METRO / 02 - VERDE.
- TDI de Grajaú associado à VIA MOBILIDADE / 09 - ESMERALDA.
- Bloqueios CCR associados à VIA MOBILIDADE.
- Ativos INATIVOS/estoque não são oferecidos ao técnico como previsão de campo.
- Painel de dados da base ao selecionar um ativo.
- ATM mostra Leasing, vencimento de contrato, produtos, transações, PIX e fixação.
- Validador/TDI mostram aplicação, BOM, BU, TOP e versão.
- POS mostra terminal, modelo e fornecedor.
- Bloqueio mostra identificação, modelo, versão, tipo e data de instalação.
- Editar/Excluir preservados.
- Fila offline preservada; 409 de duplicidade é tratado como registro resolvido.
- technician.js com identificador 1408-5 e cache-busting.
- Sincronização automática inteligente da base por sentinelas.
- Rota de diagnóstico /api/base/summary para Gestor.

ORDEM DE SUBIDA
Substitua os arquivos mantendo exatamente as pastas e faça um único Commit.
Depois no Render: Deploy latest commit.

TESTES RÁPIDOS
1) /tecnico -> Console:
   window.AUTOPASS_TECHNICIAN_VERSION
   Esperado: "1408-5"

2) Como Gestor, abra:
   /api/base/summary
   Deve retornar base_version = "1408-5" e contagens por tipo.

3) Teste uma estação com:
   ATM -> selecionar ativo e conferir dados de contrato/leasing.
   Validador -> conferir Aplicação/BOM/BU/TOP/Versão.
   POS -> conferir terminal/modelo/fornecedor.
   TDI -> usar Sacomã ou Grajaú.
   Bloqueio -> usar estação com bloqueios na base.

4) Confirmar Editar/Excluir em registro sincronizado.

IMPORTANTE
O manager.js não foi alterado nesta rodada; o mapa aprovado permanece como está.
