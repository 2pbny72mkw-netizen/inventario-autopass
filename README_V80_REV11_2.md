# V80 REV11.2 — ENXUTA

Correções:
- Nova permissão `finance.monitoring` / **Monitoramento de Coletas** na Matriz de Permissões.
- Migração única preserva acesso: perfis/usuários com `finance.collection` recebem `finance.monitoring`.
- Menu Financeiro separa Coleta de Valores de Monitoramento de Coletas.
- APIs compartilhadas de Coleta/Monitoramento aceitam qualquer uma das duas permissões; a rota do Monitoramento exige `finance.monitoring`.
- Importação de apurações TBForte aceita `finance.monitoring` ou `finance.apuracao`.
- Grade do Monitoramento com scroll vertical próprio (~500 px), scroll horizontal no mesmo container e cabeçalho sticky.
- Mostrar mais/Recolher linhas altera apenas os registros da grade; filtros e Big Numbers permanecem acima.

Aplicar sobre o projeto completo atualmente em produção.
