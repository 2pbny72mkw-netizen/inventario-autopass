# Sistema de Gestão — V73.6.2

## Atualização de Firmware POS – CPTM

- Nova base padrão CPTM: **281 POS** (arquivo recebido em 04/09/2026).
- A campanha deixa de ter total fixo: o progresso usa sempre a **base ativa importada**.
- Novo botão **Importar base** para Gestor/Gestor Field.
- Modos de importação:
  - **Substituir base ativa**: somente a nova lista entra no total; registros anteriores ficam inativos para preservar histórico.
  - **Mesclar**: adiciona/atualiza equipamentos sem retirar os atuais.
- POS já existente mantém status, técnico, observações e evidências ao ser reimportado.
- Removidos da atividade os campos **Firmware anterior** e **Nova versão de firmware**.
- Evidências fotográficas continuam opcionais.
- No celular há duas opções: **Selecionar fotos** e **Tirar foto** (câmera traseira via `capture=environment`).
- Progresso geral e filtros passam a refletir somente a base ativa.

## Compatibilidade de banco

Migração aditiva automática: coluna `active` em `pos_firmware_cptm`. Não remove registros existentes.
