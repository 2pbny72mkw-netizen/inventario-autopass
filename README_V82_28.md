# Inventário Autopass — V82.28 ENXUTA

Versão de estabilização orientada pela telemetria da V82.27.

## Performance
- Cache de 15 min para a base oficial de ATMs com venda em dinheiro, evitando reconstrução repetida da base/complemento em cada request.
- Cache curto (60 s) para `/api/mapeamento-atm`, com invalidação imediata após salvar mapeamento, alterar status administrativo ou excluir evidência.
- Preservado o cache de `/api/locations` já existente na base, com modo leve e TTL configurável.
- Mantido cache do dashboard TopDesk para reduzir recomputações consecutivas.

## Telemetria V2
- Incluído P99 além do P95.
- Contadores de requests >= 1 s, >= 2 s e >= 5 s.
- Saúde passa a considerar lentidão severa mesmo com HTTP 200: ocorrência >= 5 s pode classificar como CRÍTICO; >= 2 s/P95 elevado gera ATENÇÃO.
- Exportação XLSX passa a registrar P99 e faixas de lentidão por rota.
- Mantidos SQL médio, queries/request, memória, conexões e capacidade já existentes.

## Configurações
- `CASH_ATMS_CACHE_TTL` (padrão 900 s)
- `ATM_MAPPING_API_CACHE_TTL` (padrão 60 s)
- `LOCATIONS_API_CACHE_TTL` (padrão 900 s, já existente)

## Escopo
Nenhuma reconstrução funcional. Banco, módulos, permissões e histórico são preservados. Esta versão não altera schema de banco.
