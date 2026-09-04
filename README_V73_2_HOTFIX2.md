# V73.2 HOTFIX2

Correção cirúrgica da base Validador de Recarga + TDI e da Dashboard Troca de Chip Recarga.

- Unifica a fonte canônica Recarga/TDI entre Dashboard de Inventário e Troca de Chip.
- Ativos válidos sem casamento com `Location` continuam no total e aparecem como localidade não vinculada, em vez de desaparecerem silenciosamente.
- Reconcilia histórico de ChipSwap também por identidade operacional global (terminal/série/asset_key/top/qrcode), sem depender apenas do `location_id` antigo.
- Filtro Equipamento agora efetivamente separa Recarga + TDI / somente Recarga / somente TDI.
- Filtro Status passa a disparar a atualização da dashboard.
- Cache do `manager.js` atualizado para HF2.
- Histórico de versão atualizado em Sobre.

Validação após deploy: conferir total combinado e subtotais Recarga/TDI; depois conferir concluídos históricos e filtros. O hotfix não inventa nem fixa números em código: os totais são derivados da base persistida.
