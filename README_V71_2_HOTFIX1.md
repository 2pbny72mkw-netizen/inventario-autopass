# Sistema de Gestão — V71.2 HOTFIX1 ENXUTA

Base: V71.2.

## Correções
- Dashboard Inventário: Velocímetro superior passa a usar diretamente o mesmo `pct` calculado pela Execução consolidada.
- Dashboard Inventário: Composição superior passa a usar diretamente o mesmo `mix` calculado pelo Mix do parque.
- Dashboard Inventário: Divergências superiores usam o mesmo `metrics.divergences` do recorte.
- Removida a sincronização V71.2 baseada em leitura do DOM, que ficava fora do bloco renderizado do template.
- Cache-busting atualizado para `v71-2-hf1` em CSS, manager.js e Service Worker; cache estático também recebe nova chave.
- Identificação da Central atualizada para V71.2 HOTFIX1.
- Agendamentos CANCELADOS deixam de aparecer no calendário, tooltip, modal do dia e mensagem de WhatsApp. Permanecem em Cancelados/Todos/histórico.
- Correção visual da seleção das abas de agendamentos incluindo a aba Cancelados.
- Documentos & Materiais padronizado com o cabeçalho claro do Raio-X dos Colaboradores, com identificação atual da versão.

## Banco
Nenhuma alteração de schema neste hotfix.
