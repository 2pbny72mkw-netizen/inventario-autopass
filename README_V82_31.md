# Inventário Autopass — V82.31

Base: V82.30 REV3.

## Correções desta versão
- RH > APT: área ampliada para praticamente 100% da viewport, com margens mínimas e rolagem horizontal/vertical própria da tabela.
- Cadastro de usuários: template completo restaurado no pacote enxuto, incluindo o controle individual `Controle de jornada / bloquear fora da escala`.
- Jornada: backend mantém `journey_control_enabled` como fonte de verdade. Desmarcado = `SEM_CONTROLE`, sem bloqueio por escala/horário; horário permanece apenas como dado administrativo.
- `/api/v72/session-status` passa a devolver também `journey_control_enabled` para diagnóstico direto da configuração efetivamente persistida.
- GPS obrigatório e histórico GPS permanecem independentes do controle de jornada.
