INVENTÁRIO AUTOPASS — RELEASE CAMPO 1408 v1
==============================================

ARQUIVOS PARA SUBSTITUIR / ADICIONAR
- app.py
- static/technician.js
- templates/technician.html
- data/base_assets_1408.json

O manager.js atual não precisa ser alterado nesta rodada.

PRINCIPAIS ALTERAÇÕES
1. Identificador de release no /health: campo-1408-v1.
2. Correção consolidada da identificação de Gestor para Editar/Excluir.
3. Base detalhada carregada a partir da planilha 1408:
   - ATM: 603 registros
   - Validador: 630 registros
   - POS: 590 registros
   - TDI: 42 registros
   - Bloqueio: 1.610 registros
   - Total: 3.475 registros
4. Novos tipos no formulário: TDI e Bloqueio.
5. Validador e TDI usam os campos Aplicação, BOM, BU, TOP e Versão.
6. Bloqueio usa Modelo, Instalação e Versão, além dos campos gerais.
7. Pendências passam a considerar a base detalhada e incluem TDI/Bloqueio quando existirem na localidade.
8. ATM passa a preservar também Leasing e vencimento de contrato na base detalhada.
9. Nova rota administrativa para forçar atualização da base:
   /admin/sincronizar-base-1408

ORDEM DE TESTE APÓS O DEPLOY
1. Abrir /health e confirmar:
   {"ok":true,"database":"connected","release":"campo-1408-v1"}
2. Entrar como Gestor em /tecnico.
3. Selecionar uma estação.
4. Confirmar Editar/Excluir nos registros sincronizados.
5. Testar ATM, Validador, POS, TDI e Bloqueio no seletor Tipo.
6. Conferir se os ativos da base aparecem de acordo com a localidade.
7. Se necessário, abrir /admin/sincronizar-base-1408 uma vez como Gestor.

OBSERVAÇÃO
As rotas de alteração/exclusão continuam protegidas no backend. O controle visual da tela não é a camada de segurança.
