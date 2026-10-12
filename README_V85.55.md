# Autopass V85.55 — Web + Android A5.8

Base Web: V85.54 CONSOLIDADA. Base Android: A5.7 REV11 Build 72.

## Entregas Web
- Kanban: barra horizontal superior sincronizada com a rolagem inferior.
- RDVT: formulário, pré-visualização e relatório imprimível/PDF na sequência de motivo/atividade, fotos e aceite.
- Nenhuma migração de dados; endpoints móveis existentes preservados.

## Android A5.8 (Build 73, código-fonte)
- Preserva SQLite offline existente e IDs únicos por evento.
- Serviço GPS de turno passa a solicitar reinício START_STICKY se o Android encerrar o processo, quando permitido pelo sistema; parada explícita impede retomada.
- Diagnóstico de falha de sincronização GPS visível e registros permanecem pendentes para nova tentativa.
- Identificação da versão A5.8 no login.
- Não altera formato do protocolo de sincronização do servidor.

## Limites e homologação
- O projeto Android precisa ser compilado no Android Studio (SDK 35, JDK 17). Não há APK compilado neste pacote.
- START_STICKY não garante captura contínua se o usuário revogar localização, o aparelho desativar GPS, aplicar restrições de bateria ou impedir foreground services.
- Sincronização de fotos e eventos permanece com as rotinas da A5.7; não afirmar funcionamento offline integral antes de testes reais.
- Testar perda de sinal, fechamento do app, GPS em estação subterrânea, recuperação, duplicidade e persistência após reinício do aparelho.
- Realizar backup e homologação antes de publicar em produção.
