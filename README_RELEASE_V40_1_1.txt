V40.1.1 — HOTFIX VISÃO PANORÂMICA MOBILE

Correção objetiva do NOK observado em Android/Chrome:
- O botão Salvar fotos aceitava arquivos da galeria, mas a câmera usa um input separado.
- O input visível de galeria estava marcado como required; por isso o navegador bloqueava o envio com "Selecione um ou mais arquivos" mesmo quando 1 foto da câmera já estava pronta.
- Removido o required nativo do input de galeria.
- A validação agora considera a coleção unificada câmera + galeria antes do envio.
- Mantido feedback Salvando..., tratamento de erro e confirmação.
