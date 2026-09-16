# V81.9

## Monitoramento de Coletas — ordenação persistente

- Corrige a perda da ordenação ao usar **Mostrar mais**.
- A ordenação crescente/decrescente é aplicada ao conjunto completo filtrado antes da limitação visual de 10 linhas.
- Clicar em uma coluna ordenável preserva o estado **Mostrar mais/Recolher linhas**.
- Se a grade já estiver expandida, uma nova ordenação mantém todos os registros visíveis.
- **Mostrar mais** e **Recolher linhas** não alteram filtros nem ordenação.
- Uma alteração real de filtro reinicia a visualização em 10 linhas, mantendo a regra de ordenação ativa sobre o novo conjunto.

Base: V81.8.
