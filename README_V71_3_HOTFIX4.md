# V71.3 HOTFIX4 — Atividades EMV / Recarga / Garagem

## Correção principal
O HOTFIX3 passou a usar `normStatus()` nas telas de EMV e Recarga, porém a função não havia sido declarada nesses dois JavaScripts. O erro interrompia o `draw/render` após o carregamento da API e deixava a atividade com KPIs 0 e sem registros, apesar de o Dashboard continuar com os dados corretos.

## Ajustes
- EMV: adicionada normalização canônica de status no frontend antes de filtros, KPIs e cards.
- Recarga: mesma correção para evitar a mesma regressão.
- Garagem: revisada; já possuía a função canônica. Mantida a regra e acrescentado tratamento explícito de falha de API.
- As três atividades agora não silenciam falhas de carregamento como se fossem "base zerada"; exibem mensagem de erro quando a API falhar.
- Cache-busting atualizado para `v71-3-hf4`.
- Release: `V71.3 HOTFIX4`.

## Banco
Sem alteração estrutural de banco.
