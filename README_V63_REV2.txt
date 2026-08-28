INVENTÁRIO AUTOPASS — V63 REV2

Objetivo
- Tornar a atualização das bases operacionais administrável por planilha, sem gerar nova versão do sistema a cada carga.

Layout padrão
- empresa | terminal | estação | linha | status
- status aceitos: PENDENTE, EM ANDAMENTO, CONCLUÍDO/CONCLUÍDA.

Módulos
- Troca de Chips EMV — Trilhos
- Troca de Chip Recarga — Validadores
- Troca de Chips — Garagem

Regra de segurança
- A importação é restrita a Gestor/ADM.
- Antes de aplicar, o sistema mostra prévia com lidos, existentes, novos, reabertos e pendentes fora do novo arquivo.
- Terminal existente + PENDENTE: reabre para PENDENTE, preservando auditoria/evidências históricas.
- Terminal novo: entra na base operacional.
- Pendente antigo ausente do novo arquivo: NÃO é apagado; sai do escopo operacional atual.
- Concluídos históricos ausentes do arquivo permanecem preservados.
- Não há DROP nem exclusão de evidências.

V63 REV2 substitui a sincronização fixa da planilha Trilhos V63 REV1 por um importador reutilizável.
