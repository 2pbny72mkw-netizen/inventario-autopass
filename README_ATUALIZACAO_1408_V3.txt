INVENTÁRIO AUTOPASS — CAMPO 1408 v3

O QUE MUDA NESTA VERSÃO
- technician.js passa a ser carregado com ?v=1408-3 para eliminar cache 304 antigo.
- Editar/Excluir aparecem em todo registro já sincronizado.
- Registros pendentes continuam com "Aguardando sincronização".
- Segurança permanece no backend.
- Mantém a base 1408 com ATM, Validador, POS, TDI e Bloqueio.

COMO TESTAR
1. Substitua os arquivos mantendo as mesmas pastas.
2. Faça Commit e Deploy latest commit no Render.
3. Abra /tecnico e pressione Ctrl+F5.
4. No Console, rode:
   window.AUTOPASS_TECHNICIAN_VERSION
   Deve retornar: "1408-3"
5. Selecione uma estação com registros.
6. Editar/Excluir devem aparecer nos registros já sincronizados.
