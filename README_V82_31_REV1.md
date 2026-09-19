# Inventário Autopass — V82.31 REV1

Deploy concentrado de estabilização.

- Cadastro de jornada: campos independentes de horário inicial e final com seletor de hora/minuto (`type=time`).
- Escala 12x36 aceita horários personalizados e jornadas que atravessam a meia-noite.
- Backend continua usando `work_start_time`/`work_end_time`; `work_shift` é mantido por compatibilidade.
- Controle de jornada desativado permanece sem bloqueio de escala no backend.
- Mapeamento ATM: correção do gerador PowerPoint (`python-pptx`) ao aplicar fonte no `Run`, evitando `AttributeError` no `Paragraph`.
- APT: removido cálculo por viewport/margem negativa; card usa 100% do container e mantém scroll horizontal próprio.
