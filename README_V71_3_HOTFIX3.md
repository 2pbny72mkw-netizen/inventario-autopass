# V71.3 HOTFIX3 — Sincronização de status Recarga / Garagem / EMV

Objetivo: garantir que filtro, KPI, card, status administrativo e Pendências gerais usem o mesmo estado operacional canônico.

## Correções
- Padroniza status para PENDENTE, EM ANDAMENTO e CONCLUÍDA nos três módulos.
- EMV: o seletor administrativo passa a abrir selecionando o status real do registro, eliminando o caso em que um item concluído aparecia visualmente como PENDENTE no combo.
- EMV: alteração administrativa invalida imediatamente o cache da atividade/dashboard.
- EMV: ao excluir a última evidência de um registro já iniciado, o estado passa para EM ANDAMENTO em vez de voltar a um falso PENDENTE sem registro.
- Recarga: filtro, tag, bloqueio do formulário e seletor administrativo usam o mesmo status normalizado.
- Garagem: filtro, KPIs e tags usam o mesmo status normalizado.
- Backend: helper único de status operacional evita divergências por grafias CONCLUIDO / CONCLUÍDO / CONCLUIDA / CONCLUÍDA.
- Mantém auditoria das alterações administrativas existentes.

## Banco
Sem alteração estrutural de banco.

## Testes técnicos
- `python -m py_compile app.py`
- `node --check` nos JS de Recarga, Garagem e EMV
- parse Jinja dos três templates alterados
