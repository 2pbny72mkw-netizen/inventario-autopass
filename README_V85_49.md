# V85.49 — Pacote consolidado (etapa de performance)

Base: V85.48. Sem migrações de banco.

## Implementado
- Histórico técnico de bobinas: fotos e estoque carregados em lotes de até 500 IDs, eliminando consultas N+1 na serialização.
- Reutilização de consulta diária quando não há filtro de técnico.
- Fotos de usuários: limite de 16 MiB e 64 entradas para cache de imagens originais, evitando retenção excessiva de RAM.
- Redis opcional (`REDIS_URL`): cache somente do JSON oficial imutável de ATM; chave baseada em SHA-256 do arquivo para invalidação automática. Sem Redis, sistema continua funcionando.
- Versão Web/PWA V85.49.

## Não incluído neste pacote
- Paginação generalizada de APIs, migrações/índices, cache Redis de dados autenticados, agregações financeiras ou tarefas assíncronas. Essas intervenções requerem testes integrados adicionais.

## Testes após deploy
1. Histórico técnico de bobinas: com/sem filtro de técnico, comparar registros e movimentos, fotos, saldo de estoque.
2. Fotos de usuários, miniaturas e permissões.
3. Dashboard ATM e overrides cadastrais.
4. Drive Técnico, PDFs e lista de presença.
5. Telemetria: consultas por rota, RAM, P95 e P99.

## Redis
- Configuração opcional: `REDIS_URL` com URL segura e credenciais gerenciadas.
- Sem REDIS_URL: fallback local.
- Nenhum conteúdo privado ou financeiro é armazenado no Redis por esta versão.
