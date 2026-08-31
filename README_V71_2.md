# V71.2 — Sistema de Gestão

Base: V71.1 HOTFIX5 (ZIP completo enviado em 31/08/2026).

## Alterações
- Dashboard Inventário: sincronização explícita dos três cards superiores (velocímetro, composição por tipo e divergências) com os mesmos KPIs/filtros já calculados pela dashboard.
- Elimina estado visual 0%/vazio após carregamento assíncrono quando os KPIs já possuem dados.
- Gestão de Agendamentos: Gestor/ADM pode cancelar agendamento com motivo e auditoria.
- Gestor/ADM pode excluir agendamento criado por engano/teste somente quando nenhum equipamento foi recebido; confirmação exige digitar o protocolo.
- Agendamentos cancelados permanecem no histórico e ganharam filtro Cancelados; deixam de compor programados/pendentes/calendário operacional.
- Migração aditiva V71.2-001 adiciona cancelled_at, cancelled_by e cancellation_reason.

## Aplicação
Sobrepor os arquivos desta ENXUTA sobre a base atualmente implantada e reiniciar o serviço.
