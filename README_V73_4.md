# Sistema de Gestão — V73.4

Versão de estabilização consolidada.

## Rastreabilidade & Jornada
- Mapa encapsulado em um shell físico de 600 px com contenção de layout/pintura, evitando invasão dos controles e das seções seguintes.
- Abertura padrão centrada na Grande São Paulo com zoom 11.
- Mantém o motor compartilhado `AutopassRailMap`, trilhos, estações, legenda, fullscreen e interação.
- Consulta de histórico continua podendo enquadrar somente o trajeto selecionado.

## Catálogo de Materiais
- Restaura miniaturas das fotos já armazenadas no R2.
- Visualização da foto em nova janela.
- Edição mostra foto atual, permite substituir por JPG/PNG/WEBP e remover a foto.
- Restaura o link para compra no formulário e na listagem.
- Não exige reupload das fotos existentes.

## Recarga / TDI
- Refina a identidade canônica sem hardcode de totais:
  - Validador: terminal contextual + série quando disponível, evitando fundir equipamentos físicos distintos.
  - TDI: terminal global quando disponível, reduzindo duplicidades de reimportação/movimentação.
- Mantém diagnóstico `/api/chip-swaps/base-diagnostico` para conferência após deploy.

## Deploy
Pacote enxuto: substituir somente os arquivos presentes no ZIP e reiniciar o serviço.
