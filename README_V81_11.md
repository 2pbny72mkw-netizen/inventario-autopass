# V81.11

## Diagnóstico da Visão Panorâmica
- Mantém o diagnóstico somente leitura.
- Exibe total de evidências, pendentes que ainda possuem evidência, fotos localizadas em aliases, IDs de localidade/alias e data da última evidência.
- Novos filtros: Pendentes com evidência e Fotos encontradas em alias.
- Objetivo: investigar a redução histórica de 48 para 31 localidades concluídas sem recalcular ou alterar status.

## Armazenamento e Retenção
- Mede os objetos do Cloudflare R2 por metadados, sem baixar as mídias.
- Consolida arquivos e MB por módulo/atividade.
- Mostra referências do banco sem objeto correspondente no R2 e objetos R2 não associados aos módulos inventariados.
- V81.11 permanece somente leitura: não há exclusão de evidências.
