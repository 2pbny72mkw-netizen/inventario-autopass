# V70.1 — Estabilização Performance & Saúde

Base: V70 / V69.5 estável.

## Correções
- Dashboard Chamados registrado como dashboard nativa configurável e visível por padrão na Central.
- Migração V70.1-001 registrada de forma idempotente.
- Limpar em Acessos/visualização passa a zerar também Perfil, Empresa livre e Empresas vinculadas ao Cliente.
- Saúde da Plataforma separa RAM do container de RSS do processo e mostra pico (VmHWM), PID e threads.
- Imports pesados de PowerPoint/PIL/boto3 passam a ser carregados sob demanda quando possível, reduzindo pressão de memória no startup.
- Cache bust atualizado para V70.1.

## Validação sugerida
1. Gestão > Configuração de Dashboards: Dashboard Chamados deve aparecer.
2. /gerencial: Dashboard Chamados deve aparecer na lateral quando visível.
3. RH > Usuários: Limpar acessos deve zerar Perfil e Empresa(s).
4. Gestão > Saúde da Plataforma: conferir RAM container, RSS processo, pico, PID e threads.
5. Regressão rápida em Chamados, ATM, Recarga, EMV e Garagem.
