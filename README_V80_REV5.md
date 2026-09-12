# V80 REV5 — Coleta de Valores / Fechamentos válidos

Pacote ENXUTO para sobrepor ao projeto completo atualmente em produção.

## Alterações
- APP_RELEASE atualizado para V80 REV5.
- O ciclo transacional passa a usar somente fechamentos válidos do mesmo ATM.
- Um fechamento válido exige Valor Declarado/filipeta e não pode estar desconsiderado ou excluído.
- Registros apenas de observação/acompanhemento não cortam mais a janela entre slips.
- A janela permanece: transação > fechamento anterior e <= fechamento atual.
- Nova coluna Ações no Monitoramento: Não considerar e Excluir.
- “Não considerar” preserva o registro visível, mas o remove da cadeia de fechamentos.
- “Excluir” faz exclusão lógica, preservando usuário, data/hora e motivo para auditoria.
- Os ciclos posteriores são recalculados automaticamente.
- Exemplo esperado ATM 32852: se 08/09 não possui filipeta válida, o ciclo de 10/09 usa diretamente o fechamento válido de 01/09.

## Validação sugerida
1. Abrir ATM 32852 no Monitoramento.
2. Confirmar que 08/09 aparece como “Não é fechamento” quando não houver declarado.
3. Confirmar que 10/09 calcula Transações usando o fechamento válido anterior de 01/09.
4. Testar “Não considerar” e “Excluir” em um registro de teste.
5. Recarregar e confirmar que os ciclos seguintes foram recalculados.
