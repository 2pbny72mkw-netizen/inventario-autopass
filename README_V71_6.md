# V71.6 — Dashboards por Base Prevista + TDI na Recarga + Garagem sem anexo obrigatório

Base funcional: V71.5, preservando a linha estável V71.3 HOTFIX5.

## 1. Dashboards POS / Validador + TDI / Bloqueio
- Parque previsto vem de `BaseAsset`.
- Inventariado vem de `Inventory`.
- KPIs: Parque previsto, Inventariado, Faltante, Cobertura, Localidades e Divergências.
- Filtros por operadora/empresa, linha, estação/localidade, modelo e status.
- Validador + TDI possui filtro adicional por tipo.
- Mantém gráficos e detalhamento do parque.

## 2. Troca de Chips Recarga + TDI
- TDI entra no mesmo fluxo operacional da Recarga.
- TDI aparece como ativo previsto e como pendência quando ainda não concluído.
- Filtro Tipo: Recarga + TDI / Validador de Recarga / TDI.
- KPIs e progresso respeitam o filtro Tipo.
- Registro de troca aceita ativos VALIDATOR e TDI.

## 3. Troca de Chips Garagem
- Evidência/foto deixa de ser obrigatória.
- Resultado `Testado - OK` conclui a atividade sem anexo.
- Para resultado com anormalidade, observação é obrigatória.
- Evidências continuam disponíveis de forma opcional.

## Banco
Sem migração estrutural.
