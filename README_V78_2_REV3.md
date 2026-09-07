# Sistema de Gestão / Inventário Autopass — V78.2 REV3 ENXUTA

## Engenharia — Cadastro Mestre Oficial
- `BASE_CADASTRO_BOHM_V8.xlsx` passa a ser a fonte oficial do Cadastro Mestre de Itens.
- Na primeira subida da REV3, uma migração idempotente sincroniza o cadastro para conter somente os códigos da base oficial.
- A base embarcada contém 1.051 itens: 581 nacionais e 470 importados; 1.051 marcados como ativos no arquivo recebido.
- Itens existentes com o mesmo `CODIGO` são atualizados; itens fora da base oficial são removidos.
- Vínculos de BOM que apontem para itens removidos também são eliminados para evitar referências inválidas; o processo informa a quantidade afetada.
- O cadastro preserva rastreabilidade da origem (`CHAVE`, marca, CNPJ do fornecedor e payload da linha oficial).
- `CODIGO` é a chave mestre. `CODIGO_INTERNO` não é inferido como MPN/PN de fornecedor.
- O preço de referência usa `HOMOLOG_PRECO_VENDA`; origem usa `DESCR_FAMILIA`; NCM usa `CLASSIFICACAO`; categoria usa `DESCR_GRUPO`.

## Botões do Cadastro de Itens
- **Baixar base oficial Excel**: baixa a própria `BASE_CADASTRO_BOHM_V8` utilizada pelo sistema.
- **Importar base oficial Excel**: aceita a mesma estrutura de colunas e sincroniza o cadastro como base completa, não como carga incremental.

## Arquivos alterados
- `app.py`
- `templates/engineering.html`
- `templates/about.html`
- `static/engineering_v72.js`
- `data/BASE_CADASTRO_BOHM_V8.xlsx`
