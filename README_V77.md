# V77 — Controle de Bobinas ATM / Bobinômetro

Base: V76.2.

## Separação de experiência
- Técnico Field: **Field > Atividade Bobinas**. Tela curta para celular/PWA, sem dashboard pesado.
- Gestão/Consulta: **Field > Dashboard Bobinas / Insumos**. KPIs, filtros, posição atual, reservas e histórico.

## Regra operacional
- 100% = bobina nova / totalmente disponível.
- Leituras válidas: 0, 10, 20 ... 100%.
- Troca realizada exige nova bobina em 100%.
- Bobina instalada e estoque reserva são controles independentes.
- Origem da troca: reserva da estação, trazida pelo técnico ou outra origem.
- Somente a troca usando reserva da estação reduz automaticamente o estoque local.
- Reserva pode ser conferida, acrescida ou retirada independentemente de troca.
- Técnico/data/hora/GPS são vinculados automaticamente ao usuário autenticado.

## Dashboard
KPIs: ATMs monitoradas, reservas em campo, críticas <=10%, atenção 20–30%, trocas em 30 dias e sem leitura >=30 dias.
Filtros: operadora, linha, estação e ATM. Exportação Excel respeita os filtros principais.

## Banco
Novas tabelas aditivas e idempotentes:
- atm_bobbin_station_stock
- atm_bobbin_readings
Migração: V77-001.
