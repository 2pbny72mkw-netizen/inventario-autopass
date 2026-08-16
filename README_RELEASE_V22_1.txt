Inventário Autopass V22.1

Hotfix concentrado após homologação da V22.0.

1. /api/dashboard mantém os KPIs principais mesmo se tendência/evidências falharem.
2. /api/equipes/calendario retorna JSON inclusive em erro e respeita 7/14/21/31 dias.
3. Reimportação do WhatsApp não ignora SHA antes de tentar reparar mídia histórica.
4. Registro R2 existente, mas objeto ausente, é reenviado.
5. Cards de Evidências corrigidos para a chave items.
6. Cache/PWA atualizado para v22-1.

Antes da carga completa do WhatsApp: validar /r2-status?test=1 e importar uma amostra pequena.
