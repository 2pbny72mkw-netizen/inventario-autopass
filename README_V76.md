# V76 — Mobile, Notificações e Continuidade Operacional

A V76 incorpora integralmente a evolução prevista para V75.1.

## V75.1 incorporada
- Corrige o erro 500 de `POST /documentos/acessos/<operadora>/gerar.pdf`: a rota passa a usar a função real de elegibilidade da V74.1/V75.
- Mantém PDF oficial Metrô/CPTM com logo Autopass e validação obrigatória de FORNECEDOR, NOME, CPF, RG e FOTO.
- Arrow passa de lista para calendário operacional visual.
- Alternância 7 dias / 30 dias.
- Clique no dia abre inclusão de atividade.
- Atividade: data, início/fim, operadora, técnico, prioridade, local, descrição, remoto/TeamViewer e observações.
- Clique na atividade permite editar/reprogramar/alocar.
- Mantém elegibilidade automática Metrô/CPTM/Motiva(APT) e vínculo de materiais.

## V76 — notificações e continuidade
- Nova tabela de notificações direcionadas por usuário, com severidade, categoria, ação e leitura.
- Solicitação de acesso fora da jornada gera alerta URGENTE para gestores.
- Central de Notificações combina alertas críticos e exceções automáticas existentes.
- PWA/Service Worker exibe notificação local quando o sistema/app está ativo e a permissão do navegador foi concedida.
- Canal WhatsApp Business Cloud API opcional para alertas URGENTES/CRÍTICOS.
- A decisão de aprovação/rejeição permanece dentro do Sistema de Gestão para preservar autenticação e auditoria.

## Configuração opcional do WhatsApp no Render
- `WHATSAPP_CLOUD_TOKEN`
- `WHATSAPP_PHONE_NUMBER_ID`
- `WHATSAPP_ALERT_RECIPIENTS` — números E.164 separados por vírgula.
- `WHATSAPP_ALERT_TEMPLATE` — nome do template previamente aprovado no WhatsApp Business.
- `WHATSAPP_ALERT_TEMPLATE_LANG` — padrão `pt_BR`.

Sem essas variáveis, o sistema continua funcionando normalmente e registra `NAO_CONFIGURADO` no canal WhatsApp.

## Observação técnica importante
O PWA não substitui Web Push remoto quando o navegador/processo estiver totalmente encerrado pelo sistema operacional. Nesta V76, eventos críticos podem usar WhatsApp Business como canal externo. Uma futura etapa pode adicionar Web Push VAPID/APNs/FCM se houver necessidade de background nativo mais forte.

## Pós-deploy
1. Gerar PDF Metrô e CPTM com cadastro completo.
2. Arrow: testar 7 dias, 30 dias, clique no dia, criação e edição.
3. Validar bloqueio Arrow por acesso Metrô/CPTM/Motiva.
4. Solicitar autorização fora da jornada e confirmar alerta na Central de Notificações.
5. Com PWA instalado, conceder permissão de notificações e repetir uma solicitação.
6. Se WhatsApp estiver configurado, validar entrega em número autorizado/opt-in.
7. Regressão: ATM, EMV, Equipes/GPS, APT, Materiais, Portal e Financeiro.
