# V71.3 HOTFIX5 — GPS Técnico Implantação

Base: V71.3 HOTFIX4 (estável)

## Correção
- Corrige o POST `/api/tecnico/position`.
- Remove a dependência exclusiva de `@field_required`.
- Mantém login obrigatório.
- Autoriza explicitamente Técnico Implantação e demais perfis operacionais habilitados.
- Não altera URLs, dashboards, APIs de EMV/Recarga/Garagem ou regras da V71.4.
- Sem migração de banco.

## Motivo
Na V71.3 HOTFIX4 o navegador obtinha a localização, mas o backend devolvia 403 para
Técnico Implantação porque o endpoint exigia permissão genérica `field`.
