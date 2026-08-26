INVENTÁRIO AUTOPASS — V60 REVISADA

Escopo consolidado:
1. RH / Equipes em modo leitura
   - garante para o perfil RH as subvisualizações Mapa, Operação por Data e Escala, inclusive para cadastros antigos com access_json anterior às subpermissões;
   - atualização do mapa e carga operacional não dependem de botões que possam estar ausentes para o perfil;
   - leitura dos perfis de escala liberada para visualizadores de Equipes, mantendo criação/edição/exclusão restritas ao Gestor;
   - preserva as restrições de RH para perfis administrativos/gerenciais.

2. Solicitação = Preventiva ATM (preparação TOPdesk)
   - nova tela /preventivas;
   - fluxo Localidade -> ATM -> Serviço -> Descrição -> Evidências -> GPS;
   - tipo fixo PREVENTIVA e origem Sistema de Gestão de Campo;
   - protocolo interno PV-... enquanto a API TOPdesk não estiver ativada;
   - bloqueio de duplicidade por ATM + Serviço enquanto houver preventiva ativa;
   - histórico das preventivas recentes;
   - estrutura de banco preparada para número e SLA TOPdesk;
   - anexos locais em uploads/preventive (JPG, PNG, WEBP e PDF, até 8 arquivos).

3. Dashboard EMV / Recarga — refinamento visual
   - nomes de estação/técnico alinhados à esquerda e sem recuo/quebra desnecessária;
   - a barra perde largura antes do texto, preservando legibilidade.

4. Cache / versão
   - cache-busting dos assets alterados e service worker atualizado para V60 REV.

IMPORTANTE
- A integração real com TOPdesk/Zenvia NÃO está ativada nesta revisão. A tela registra protocolo interno e deixa o registro em AGUARDANDO_INTEGRACAO.
- Para RH, as telas operacionais são leitura. Rotas de criação/edição/exclusão de escala continuam restritas ao Gestor.
