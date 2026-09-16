# V81.12

## Visão Panorâmica — diagnóstico final
- Rastreamento direto de cada `PanoramaPhoto` no banco até `PanoramaPoint`, localidade original e localidade canônica.
- Exibe fotos no banco, vínculos válidos, localidades pendentes com evidência, fotos via alias e evidências órfãs.
- Filtros por pendente, alias e sem vínculo completo.
- Somente leitura: não recalcula status e não altera/exclui fotos.

## Armazenamento / Cloudflare R2
- Classifica objetos que não estão referenciados pelos módulos já inventariados, agrupando por prefixo do R2.
- Mostra módulo provável, quantidade, consumo e amostras das chaves.
- Mantém a medição V81.11 por módulo.
- Somente leitura: nenhuma exclusão nesta versão.
