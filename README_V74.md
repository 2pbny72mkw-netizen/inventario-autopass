# V74 — Dossiê, Pessoas & Governança

Base: V73.6.4 recebida em 04/09/2026.

## Entregas implementadas
- Correção do Dashboard EMV visível: renderização agora usa os IDs `emvDash*` e a API canônica `/api/emv-chip-swaps?compact=1&include_photos=0`.
- Cadastro mestre de colaboradores ampliado com data de admissão, data de desligamento e locais de atuação (Metrô/CPTM/L4/L5/Outros).
- Novo cadastro de Autorizações de Acesso, sempre vinculado a `user_id`.
- Autorizações por operadora, tipo, número, emissão, validade, linhas/áreas, status, observações e PDF comprobatório.
- Cálculo de situação: válida, vence em 30 dias, vencida, pendente, suspensa, revogada, sem validade ou inativa.
- Endpoint de elegibilidade operacional por colaborador/operadora/linha para integração futura com Arrow.
- RH com empresa definida fica restrito, na gestão de usuários e autorizações, aos colaboradores da própria empresa.
- Migração aditiva/idempotente para os novos campos de `users` e tabela `access_authorizations`.
- Histórico Sobre atualizado para V74.

## Preservado da base
- Escala/jornada e autorização extraordinária V72/V73.
- Histórico GPS/geofence e retenção existentes.
- APT/NR10/NR35/ASO/Integração existentes.
- Dossiê & Materiais existentes.
- Correção ATM existente na base recebida.

## Checklist antes do deploy
1. `python -m py_compile app.py`.
2. `node --check static/manager.js`.
3. Validar login ADM/Gestor/RH.
4. Dashboard EMV: conferir total/concluídos/em andamento/pendentes e filtros.
5. Usuários: criar/editar colaborador com admissão, desligamento e locais de atuação.
6. RH > Autorizações de Acesso: cadastrar autorização Metrô com PDF e conferir validade.
7. Testar `/api/rh/autorizacoes-acesso/eligibilidade/<user_id>?operator=METRO`.
8. Confirmar que RH de empresa definida não visualiza colaboradores de outra empresa.
9. Regressão ATM, Equipes/GPS, APT e Dossiê.
