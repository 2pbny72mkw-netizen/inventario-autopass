# V71.5 — Correção dos novos dashboards de Inventário

Base: V71.4, mantendo a linha estável da V71.3 HOTFIX5.

## Corrigido
- Dashboard POS deixa de abrir com painel vazio.
- Dashboard Validador + TDI deixa de abrir com painel vazio.
- Dashboard Bloqueio deixa de abrir com painel vazio.
- Os três painéis agora são ativados tanto pelo menu lateral quanto por URL com `?view=...`.
- O carregamento ocorre mesmo se o JavaScript entrar após o `DOMContentLoaded`.
- Estado visual dos painéis é controlado por classe `is-active`, sem depender apenas do switcher legado do `/gerencial`.
- Fonte permanece exclusivamente no Inventário do Sistema.
- Sem migração estrutural de banco.

## URLs de teste
- `/gerencial?view=pos-inventory`
- `/gerencial?view=validator-tdi-inventory`
- `/gerencial?view=block-inventory`
