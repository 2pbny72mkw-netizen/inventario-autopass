# V78.9.2 — Consolidação Arrow / APT / Garagem / Financeiro

Base: V78.9.1.

## Alterações
- Usuários: `users.view` passa a visualizar o cadastro completo; ações continuam controladas pelas permissões específicas e regras de governança.
- Troca de Chips Garagem: leitura/gravação passam a usar `implantation.garage` (sem dependência indevida de `field`); mensagem de erro HTTP mais clara.
- Arrow: fluxo Operadora → Linha → Estação para trilhos; OUTROS usa cadastro estruturado de localidades.
- Arrow: cadastro de nova localidade pela própria tela e carga inicial das 27 garagens com sigla/endereço.
- Arrow: atividades podem vincular `arrow_location_id`, preservando localidade estruturada.
- APT: colaborador obrigatório do Cadastro de Usuários (`user_id`), nome/empresa automáticos; Linha em lista controlada das linhas que exigem APT (04/05 conforme base).
- Financeiro: NF/Documento incluído no Histórico de competências e no Excel financeiro.

## Migração
- Cria `arrow_locations` se necessário.
- Adiciona `arrow_activities.arrow_location_id` se necessário.
- Carga idempotente das 27 garagens iniciais.
