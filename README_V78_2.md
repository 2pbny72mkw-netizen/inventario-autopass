# Sistema de Gestão — V78.2 ENXUTA

Base: V78.1.

## Engenharia
- Quantidade de produção somente inteira (mínimo 1), validada no frontend e backend.
- Estudos salvos com Abrir, Duplicar e Excel diretamente na lista.
- Cadastro Mestre: modelo Excel para download/importação.
- Estruturas BOM: clonagem como nova estrutura/produto, além de Nova Revisão; origem da clonagem registrada.
- Cadastro de item: Tipo (Material, Subestrutura, Produto acabado, Serviço, Embalagem).
- Ciclo de vida: Ativo, Descontinuação, EOL e Inativo; data/observação e item substituto.
- Subestrutura pode ser vinculada a uma BOM própria e reutilizada em outras estruturas.
- Where Used: mostra uso direto e uso indireto por subestrutura, com impacto antes de decisões de EOL/inativação.
- Histórico Sobre atualizado para V78.2.

Observação: substituição de item não altera BOM homologada silenciosamente; o cadastro registra o substituto e o impacto para decisão de Engenharia.
