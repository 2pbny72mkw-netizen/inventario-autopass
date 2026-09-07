# Sistema de Gestão — V78.2 REV2 ENXUTA

Hotfix sobre V78.2 REV1.

- Corrigido botão **+ Nova BOM**: restaurado `bomForm()`.
- Corrigido **Editar estrutura**, que utiliza o mesmo formulário.
- Criação usa `POST /api/engineering/boms`; edição usa `PATCH /api/engineering/boms/<id>`.
- Mantido hotfix da Formação Comercial da REV1.
- Cache-buster atualizado para `v78.2.rev2`.
