# V82.35 REV1 — patch enxuto

Aplicar app.py sobre a mesma base V82.35 pré-homologação. Mobile bootstrap exclui registros Arrow com deleted_at preenchido, como a API Web; informa can_execute. Iniciar apenas PLANEJADA; concluir PLANEJADA/EM ANDAMENTO. Não altera banco.

IMPORTANTE: calendário Web pode ter filtros adicionais. Não há evidência de que #1/#2 estejam excluídas do banco. Testar com atividade nova e conferir eventos rejeitados. Não publicar em produção sem homologação.
