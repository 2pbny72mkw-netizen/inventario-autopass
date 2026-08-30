# V71.1 HOTFIX4 — Feriados 2026 e destaque de bloqueios

Aplicar sobre V71.1 + HOTFIX2 + HOTFIX3.

## Ajustes
- Dias bloqueados passam a ficar destacados em vermelho no calendário operacional.
- O motivo do bloqueio aparece dentro da própria célula do dia.
- Mantém o hover dos agendamentos; quando houver agendamento em data bloqueada, o tooltip também informa o bloqueio.
- Carga única e idempotente dos feriados oficiais de 2026 usados na operação em São Paulo:
  - 01/01 — Confraternização Universal
  - 25/01 — Aniversário da Cidade de São Paulo
  - 03/04 — Paixão de Cristo
  - 21/04 — Tiradentes
  - 01/05 — Dia do Trabalho
  - 04/06 — Corpus Christi
  - 09/07 — Revolução Constitucionalista / Data Magna de SP
  - 07/09 — Independência do Brasil
  - 12/10 — Nossa Senhora Aparecida
  - 02/11 — Finados
  - 15/11 — Proclamação da República
  - 20/11 — Dia da Consciência Negra
  - 25/12 — Natal
- Pontos facultativos e emendas não são bloqueados automaticamente.
- O ADM continua podendo desbloquear ou incluir datas manualmente após a carga inicial.
- Migração registrada como `V71.1-HF4`.
