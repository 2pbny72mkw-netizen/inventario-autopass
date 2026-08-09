# ATUALIZAÇÃO PARA POSTGRESQL / RENDER

Esta versão usa PostgreSQL quando a variável `DATABASE_URL` estiver configurada.
Se `DATABASE_URL` não existir, o sistema usa SQLite apenas para testes locais.

## Render
Build Command:
`pip install -r requirements.txt`

Start Command:
`gunicorn app:app`

Health Check:
`/health`

## Variáveis de ambiente necessárias
- `DATABASE_URL`: use a Internal Database URL do PostgreSQL do Render.
- `INVENTARIO_SECRET_KEY`: gere uma chave aleatória forte no Render.

## Importante
As fotos e vídeos ainda são gravados na pasta local `uploads/`.
Isso serve para desenvolvimento, mas não é armazenamento persistente adequado no Render.
Na próxima etapa, substitua por Cloudflare R2, Amazon S3 ou equivalente.

## Credenciais iniciais de demonstração
Gestor: `admin` / `Admin@123`
Técnico: `tecnico` / `Tecnico@123`

Altere as senhas antes de liberar o sistema para uso real.
