# V80 REV7 — Coleta de Valores

- Corrige a fonte de fechamento: R0050/Data Coleta é associado por ATM + data da coleta, sem exigir coincidência de horário manual.
- Deduplica os fechamentos sistêmicos por Código Coleta + Data Coleta.
- Horário manual permanece como fallback e evidência de auditoria.
- Adiciona BAG logo após ATM no Monitoramento, com filtro e ordenação.
- Amplia a largura útil do Monitoramento e compacta margens laterais para reduzir scroll horizontal.
- Mantém integralmente as regras e funcionalidades da V80 REV6.

Após o deploy, reimporte o R0050 caso os campos Data Coleta/Código Coleta ainda não estejam preenchidos na base transacional. A reimportação atualiza registros existentes sem duplicá-los.
