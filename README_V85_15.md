# V85.15 — Evidências, Armazenamento e Performance

- Base: V85.14 homologada.
- Central de Diagnóstico: simulação somente leitura de retenção de evidências concluídas em 30/60/90 dias.
- Estima quantidade e espaço R2 potencialmente elegível, sem baixar ou excluir arquivos.
- Protege por desenho módulos sem data de conclusão inequívoca ou com política própria; limpeza futura exige regras para auditoria/fraude/divergência/investigação/legal.
- Diagnóstico de performance PostgreSQL: linhas estimadas, sequential scans, index scans, dead tuples e conferência dos índices críticos já monitorados.
- Nenhum DELETE de evidência e nenhum CREATE INDEX automático nesta versão.
