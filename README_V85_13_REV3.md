# V85.13 REV3 — Consolidação Operacional

Base: `inventario-autopass-main (10)(1).zip` (V85.13).

## Implementado
- Central de Atividades transversal, sem migração/desduplicação de dados e respeitando a Matriz de Permissões.
- Central com Dashboard, Minhas Atividades, Todas as Atividades e acesso a Concluídas/Histórico pelos módulos de origem.
- Preventiva ATM, Field, Implantação, Arrow e Gestão de Tarefas expostos pela central conforme permissões.
- Dashboard Bobinas classificado em Field.
- Portal do Cliente: removidos botões manuais `Atualizar` de Recebimentos/Histórico e Devolver Equipamentos; filtros continuam atualizando a visão e buscas usam debounce.
- Financeiro / Monitoramento: big number principal de diferença alterado para `Transações − Apurado`; clique abre a composição T × A. A diferença Apurado − Declarado permanece disponível na tabela/auditoria.
- Release identificado como `V85.13 REV3`.

## Fora desta versão
- QR Trilhos operacional/configuração mestre: adiado para versão posterior conforme decisão de roadmap.
- Limpeza de evidências/R2 e refatoração de performance: versões posteriores.
- Engenharia / Preços e Valores tributários: versão seguinte do roadmap.

## Validação local executada
- `python -m py_compile app.py`
- compilação dos templates Jinja2
- validação sintática do JavaScript alterado quando `node` disponível
- integridade do ZIP final

Não foram executados testes contra Render, PostgreSQL de produção, R2 de produção ou equipamento físico.
