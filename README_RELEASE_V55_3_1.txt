V55.3.1 — HOTFIX POSTGRESQL

Correção exclusiva de deploy/migração:
- Corrigido financial_suppliers.pending_profile para BOOLEAN NOT NULL DEFAULT FALSE.
- Removido DEFAULT 0 incompatível com PostgreSQL para coluna BOOLEAN.
- Revisão do pacote confirmou ausência de outros DEFAULT 0/1 aplicados a BOOLEAN.
- APP_RELEASE e cache atualizados para V55.3.1.
- Funcionalidades e rotas da V55.3 preservadas.

Aceite após deploy:
1. Deploy inicia sem psycopg2.errors.DatatypeMismatch.
2. /api/release/routes-v553 retorna release V55.3.1 e rotas true.
3. Testar Dashboard Financeiro, Dashboard Implantação, Lançamentos e Coleta de Valores.
