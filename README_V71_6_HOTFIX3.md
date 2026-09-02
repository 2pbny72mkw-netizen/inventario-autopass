# V71.6 HOTFIX3

Base: V71.6 HOTFIX2.

## Objetivo
Corrigir o comportamento intermitente em que o menu da dashboard era selecionado, porém o conteúdo permanecia vazio.

## Causa tratada
- Service Worker antigo ainda servindo cache da linha `v71-4-hf2`.
- Dois fluxos JavaScript podiam disputar a ativação do mesmo painel.
- Chamadas duplicadas para dashboards de Inventário.

## Alterações
- Service Worker atualizado para `v71-6-hf3`.
- Limpeza automática de caches antigos da aplicação.
- Ativação de dashboards centralizada e determinística no `manager.js`.
- Fallback de reativação caso o painel seja ocultado por uma corrida de eventos.
- Removido o listener duplicado de ativação no `equipment_inventory_dashboards.js`.
- Deduplicação de requests idênticos em andamento para POS, Validador + TDI e Bloqueio.
- Mantém todas as correções do HOTFIX1 e HOTFIX2.

## Banco
Sem migração estrutural.
