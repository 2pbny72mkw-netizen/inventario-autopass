# Sistema de Gestão — V70 ENXUTA

Base: V69.5 aprovada/estável.

## Foco da versão
Performance, Banco e Saúde da Plataforma, aproveitando a janela operacional sem técnicos. O Portal do Cliente + Agendamento Inteligente fica para o ciclo posterior, quando a matriz Leva e Traz estiver disponível.

## Entregas
- Gestão → Saúde da Plataforma: consolida telemetria, tempo médio/P95/pico, erros 5xx, usuários ativos, RAM, PostgreSQL, R2, arquivos locais, jobs, maiores tabelas, gargalos, índices críticos e migrações.
- Banco: início de controle versionado de migrações (`schema_migrations`) e índices aditivos/idempotentes para PerformanceMetric, TopDesk, solicitações de material e documentos.
- Performance da Central: TopDesk, GPS, evidências e contratos ATM deixam de disparar cargas secundárias antes de sua visualização; passam a carregar sob demanda.
- Dashboard Chamados: nome padronizado na lateral da Central e acesso ao Dashboard completo.
- RH/Usuários: Editar, Ativar/Desativar e Excluir mantidos na mesma linha em desktop.
- Acessos/visualização: botão Recolher/Expandir acessos e Limpar reforçado para zerar checkboxes filhos e grupos.
- Cache/release atualizado para V70.

## Segurança de atualização
- Migrações são aditivas e idempotentes.
- Não há limpeza agressiva de histórico, GPS, documentos ou auditoria.
- A rota `/telemetria` permanece por compatibilidade e redireciona para `/saude-plataforma`.

## Testes recomendados
1. Gestão → Saúde da Plataforma abre sem erro e mostra PostgreSQL/RAM/índices/migrações.
2. Central → Dashboard Chamados aparece na lateral e carrega apenas ao selecioná-la.
3. Central → Mapa carrega GPS ao abrir; demais dashboards continuam funcionando.
4. RH → Usuários: ações em uma linha; Recolher/Expandir; Limpar acessos zera todos.
5. Configuração de Dashboards: Dashboard Chamados pode ser ocultado/ordenado.
6. Regressão: Field, Implantação, Documentos & Materiais, Financeiro e Portal.
