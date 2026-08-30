# Sistema de Gestão — V69.5 ENXUTA

Base: V69.4 aprovada nos testes 1–6.

## Evoluções principais
- Raio-X: pendência do colaborador passa a considerar somente ação que depende dele. Solicitações de material abertas deixam de tornar o solicitante PENDENTE; CORRECAO_SOLICITADA/RASCUNHO ficam como ação da gestão.
- Dossiê/Documentos: exclusão administrativa de documentos de teste/indevidos com motivo obrigatório e AuditEvent. Movimentos vinculados ao documento excluído são desfeitos para não manter carga artificial de teste.
- Entrega de Materiais: filtros prévios por Empresa, Cargo, Situação e busca; contador exibidos/total/selecionados; seleção preservada ao trocar filtros; Selecionar/Limpar visíveis atua só no resultado filtrado.
- Dashboard Garagem 2.1: big numbers preservados, novo donut de conclusão, barra consolidada Concluídos/Em andamento/Pendentes, legenda e correção visual para manter `0 / 457` na mesma linha.
- Cache/release atualizado para V69.5.

## Observação conceitual
Solicitação de material é demanda para a área responsável e não irregularidade do colaborador. O Raio-X mede regularidade/ação pendente do colaborador.

## Instalação
Aplicar os arquivos deste ZIP sobre a V69.4 e realizar novo deploy.
