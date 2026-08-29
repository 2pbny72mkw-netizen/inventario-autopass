# V69.3.2 — correção estrutural e navegação

Base: arquivo principal enviado em 29/08/2026.

## Correções
- `/dashboard` não abre mais a tela intermediária `dashboard_hub`; redireciona para a Central `/gerencial`.
- Dashboard Garagem passa a ser painel nativo da Central com menu lateral (`/gerencial?view=garage`).
- `/troca-chips-garagem/dashboard` redireciona para o painel Garagem na Central.
- Tela operacional Garagem aponta diretamente para a Central ao clicar em Dashboard.
- Migração PostgreSQL aditiva/idempotente para `collaborator_documents`:
  - `invoice_number VARCHAR(120)`
  - `invoice_file VARCHAR(600)`
  - `invoice_original_name VARCHAR(255)`
- Corrigida migração fiscal do Portal para usar `db.inspect`.
- `/api/materials/pending-count` usa COUNT de colunas estáveis e não materializa o modelo inteiro.
- Raio-X passa a considerar colaboradores ativos, excluindo apenas Cliente e Consulta.
- Raio-X consulta somente `user_id/status` dos documentos para maior tolerância a migrações aditivas.
- Raio-X exibe erro explícito se a API falhar, em vez de permanecer silenciosamente zerado.
- Nome institucional padronizado para `Sistema de Gestão` nas telas principais.
- Cache-bust do CSS/Service Worker atualizado para `v69-3-2`.

## Validação realizada
- `python -m py_compile app.py`
- Parsing Jinja dos templates alterados.
- Sintaxe JS existente da Central/Garagem validada com `node --check`.

## Teste pós-deploy prioritário
1. Acessar Dashboard no menu superior: deve abrir `/gerencial` diretamente.
2. Na lateral, clicar Dashboard Garagem: deve permanecer na Central e mostrar o painel Garagem.
3. Abrir Documentos & Materiais > Raio-X: colaboradores devem aparecer.
4. Confirmar no console/network que `/api/materials/pending-count` e `/api/materials/xray` retornam HTTP 200.
5. Confirmar no log do Render a mensagem `V69.3.2: schema collaborator_documents validado.`
