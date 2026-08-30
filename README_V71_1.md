# V71.1 — Portal do Cliente / Logística

Base: V71 + HOTFIX1.

## Entregas
- Gestão de Agendamentos e Recebimentos consolidada na mesma tela.
- Recebimento por equipamento diretamente na gestão logística, usando o fluxo já existente do Portal.
- Cabeçalho e tipografia ajustados ao padrão Dashboard 2.0, com maior contraste.
- Cadastro de Clientes reformulado para "Clientes, Garagens e Acessos".
- KPIs de empresas/garagens, contatos e acessos externos.
- Acessos de perfil Cliente passam a ser criados/editados nessa tela; RH/Usuários deixa de listar e oferecer criação de perfil Cliente.
- Importação da Matriz Leva e Traz passa a aproveitar a aba "Contato Garagem": cria cadastros de garagens ausentes e preenche campos vazios de contato, e-mail, telefone, endereço e região.
- A aba Resumo garante cadastro para toda garagem existente na matriz, mesmo sem linha completa em Contato Garagem.
- Importação continua idempotente e preserva dados manuais já preenchidos.
- Prefixo de novos acessos externos: CL001, CL002...
- Release: V71.1.

## Arquivos alterados
- app.py
- templates/logistics_schedule.html
- templates/customer_companies.html
- templates/users.html

## Validação
- python -m py_compile app.py
- parsing Jinja dos templates alterados
