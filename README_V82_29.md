# Inventário Autopass — V82.29 ENXUTA

Pacote consolidado de estabilização, SQL/memória/concorrência e ajustes funcionais.

## Performance / SQL / concorrência
- Cache curto (20 s, configurável por `FIN_CASH_PAYLOAD_CACHE_TTL`) no payload pesado de `/api/financeiro/coletas/v79`, reduzindo recomputação quando usuários consultam o mesmo período simultaneamente.
- Índices aditivos para ciclos de coleta ativos e correlação por terminal/data de processamento.
- Mantidas as otimizações/cache da V82.28 em Mapeamento ATM e `/api/locations`.
- Service Worker recebe versão V82.29 para forçar atualização do shell e reduzir retenção de dashboard anterior.
- Não aumenta automaticamente o número de workers: a telemetria V82.28 mostrou RAM ~72,7% com 1 worker; primeiro reduzimos carga/recomputação.

## Dashboard ATM / Mapeamento
- Drill-down Dashboard ATM 2.0 com contraste forte, fundo sólido, tabela ampla, cabeçalho fixo e scroll interno.
- Big Numbers do Mapeamento ATM clicáveis, com relação de ATMs do indicador e abertura direta do registro/evidências.

## RH / APT
- Área ampliada lateralmente e tabela com largura útil maior.
- Scroll horizontal interno preservando legibilidade e ações.

## Bobinas
- Programação futura passa a exibir Localidades/CDs, Caixas, Avulsas e Total em bobinas.
- Campo de bobinas avulsas no cadastro/edição.
- Total calculado pela configuração `BOBBIN_ROLLS_PER_BOX`.
- Novo detalhe persistente `bobbin_delivery_details` para avulsas sem alterar a tabela principal de programação.

## Financeiro / Caixinha
- Forma de pagamento removida da interface.
- Backend grava `DINHEIRO` automaticamente em abertura e movimentos.

## Arrow
- Colaborador alocado pode iniciar/concluir a própria atividade e registrar observação/impedimento, sem receber permissão administrativa para editar o planejamento.
- Histórico operacional gravado em `arrow_activity_executions`.
- Criação permite repetir por mais X dias, com opção de somente dias úteis; cada ocorrência é independente.

## Validação
- `python -m py_compile app.py`
- `node --check` nos scripts alterados/inline extraídos
- teste de integridade do ZIP
