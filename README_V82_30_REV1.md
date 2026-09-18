# Inventário Autopass — V82.30 REV1

Correção dirigida sobre a V82.30.

## RH / APT
- Remove o posicionamento por `left:50% + transform`, que podia deslocar/cortar o início da tabela.
- Card ocupa a largura real do viewport com margem segura.
- Tabela mantém largura própria (1760 px) dentro de container com rolagem horizontal real.
- Barra horizontal superior sincronizada com a tabela; zoom do navegador não é requisito operacional.

## Dashboard Bobinas — Estoque por Localidade / CDs e Armários
- Novo botão `+ Novo estoque / localidade` para usuários com `field.stock_manage`.
- Cadastro de ponto com tipo (CD/Armário/Estoque), empresa, linha, estação/referência, saldo e justificativa.
- Ações `Editar` e `Excluir` por linha.
- Edição altera cadastro/saldo com movimento e auditoria.
- Exclusão é lógica (`active=false`): preserva saldos/movimentos históricos e registra auditoria.
- Corrige totalizadores de caixas/avulsas para somar a decomposição física de cada localidade, em vez de decompor apenas o total global.

## Mapeamento ATM — Book PowerPoint
- Evidências fotográficas agora usam encaixe proporcional (`contain`).
- A proporção original é preservada; não força simultaneamente largura e altura.
- Imagens são centralizadas no quadro disponível, evitando deformação/esticamento.
- Mantida compactação prévia das imagens para controle de memória/tamanho do PPTX.

## Release
`V82.30 REV1`
