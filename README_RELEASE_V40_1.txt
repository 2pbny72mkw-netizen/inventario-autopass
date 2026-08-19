V40.1 — HOTFIX URGENTE VISÃO PANORÂMICA MOBILE

Escopo desta entrega:
- Corrige o fluxo de Salvar fotos no Android/Chrome mobile.
- Botão passa a mostrar Salvando... e fica bloqueado durante o envio.
- Status visível informa quantidade selecionada, envio, sucesso ou falha.
- Tratamento de timeout e respostas 500/HTML sem deixar a tela silenciosa.
- Backend sempre retorna JSON no upload panorâmico e faz rollback em erro.
- Limite de 25 MB por foto com mensagem clara.
- Mantém câmera e galeria, inclusive quando ambos são usados no mesmo ponto.
- Atualiza versão para V40.1 e histórico.

Checklist incremental:
PAN-UP-01 Selecionar 1 foto da galeria e salvar.
PAN-UP-02 Selecionar 2+ fotos e salvar.
PAN-UP-03 Tirar foto pela câmera e salvar.
PAN-UP-04 Durante envio aparece Salvando... / Enviando.
PAN-UP-05 Após sucesso contador e status da estação atualizam.
PAN-UP-06 Em falha aparece mensagem visível; botão volta a ficar disponível.
PAN-UP-07 Regressão: Importar ZIP do WhatsApp continua disponível para Gestor.
