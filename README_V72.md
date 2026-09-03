# V72 — Jornada & Histórico GPS

Base: V71.7 (inclui V71.6 HOTFIX3).

## Histórico GPS por estações
- Nova área em Gestão: Rastreabilidade & Jornada.
- Habilitação individual por usuário: `Histórico GPS por estações`.
- Coleta por geofence: o navegador acompanha movimento e o backend só grava quando ocorre entrada em uma estação.
- Enquanto permanece na mesma estação não grava repetidamente.
- Ao sair do raio e retornar, registra nova passagem.
- Consulta por técnico + data, mapa, linha conectando os pontos e linha do tempo.
- Retenção configurável, padrão 7 dias.
- Raio, intervalo de ping e movimento mínimo configuráveis.
- Permissão própria: `management.gps_history`.

## Controle de jornada
- Parâmetro individual por usuário: `Controle de jornada / bloquear fora da escala`.
- Chave mestre em Gestão > Configurações para rollout seguro; inicia DESATIVADA.
- Técnico Field pode ser controlado; Técnico Implantação pode permanecer flexível.
- Fora da escala, após senha válida, o técnico entra na tela de solicitação de autorização.
- Solicitação por duração + motivo.
- Gestor/ADM com permissão aprova/recusa e pode ajustar a duração.
- Autorização temporária libera login somente até o horário aprovado.
- No fim da jornada/autorização o backend bloqueia e o frontend encerra a sessão operacional.
- Férias/Afastamento/Licença não podem ser liberados pelo fluxo simples de hora extra.
- Permissão própria: `management.work_authorizations`.

## Gestão / Configurações
Novos parâmetros:
- retenção do histórico GPS;
- raio da estação;
- frequência de ping de geofence;
- movimento mínimo;
- chave mestre de controle de jornada;
- antecedência do aviso;
- extensão máxima;
- padrão Field e padrão Implantação.

## Banco
Novas tabelas:
- technician_station_history
- work_access_requests
- v72_system_config

Novas colunas em users:
- gps_history_enabled
- journey_control_enabled

Migração aditiva/idempotente. Nenhuma tabela/dado existente é removido.


## Adequação mobile das dashboards
A própria V72 inclui a correção de visualização pelo celular; não há versão separada.
- seletor compacto de Dashboard no mobile;
- troca entre dashboards respeitando as permissões do usuário;
- KPIs em 2 colunas;
- cards e gráficos ajustados à largura da tela;
- filtros empilhados;
- tabelas com rolagem interna;
- sem rolagem horizontal global;
- layout desktop preservado.

## V72 consolidada — Engenharia + Garagem
- Engenharia: Cadastro de Itens, importação da Codificação.xlsx, BOM, revisões, custos Nacional/Importado e exportação.
- Garagem: normalização do nome da empresa (corrige divergências como Vila Galvão), retirada de produtividade por técnico, progresso por empresa em largura total com todas as empresas e remoção da tendência/previsão.

### Correção adicional
- Versão exibida corrigida para V72.
- Menu Engenharia passa a aparecer para ADM/Gestor mesmo antes de ajuste manual da matriz.
- APIs de Engenharia recebem fallback seguro para ADM/Gestor.
- Atividade Garagem passa a normalizar o nome da empresa também no frontend.
- Texto de progresso da atividade preparado para leitura mais clara.

## V72 — correção de estabilidade e performance
- Eliminado o ciclo de redirecionamento `/gerencial` ↔ `/dashboard`.
- `/dashboard` agora usa destino seguro conforme acesso/perfil.
- Compatibilidade controlada para `/api/chip-swaps/`; clientes atuais usam `/api/chip-swaps`.
- Tratamento específico do caminho acidental `/api/chip-swaps//`, sem canonicalização global.
- Cache/Service Worker atualizado para `v72`.
- Mantido o índice crítico `ix_techpos_user_captured` no startup aditivo.
