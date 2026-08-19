Inventário Autopass — V39.7.9 ENXUTO

Correções principais:
- Equipes: corrigido o bug que alimentava o fallback de trilhos na variável errada. O SVG lia v3978RailSource, mas a V39.7.8 preenchia v391RailSource; por isso o diagnóstico mostrava 0 pontos.
- Equipes: fallback local agora é desenhado mesmo se a API /api/equipes/rail-network falhar; diagnóstico exibe linhas e pontos efetivamente renderizados.
- Troca de Chips: resultado pós-troca obrigatório (OK, com defeito, não foi possível testar, inoperante, outro).
- Pendências exigem observação.
- Dashboard: gráfico/resumo dos resultados pós-troca e lista de pendências técnicas.
- Exportação Excel: opção específica para pendências, com resultado, observação, técnico, conclusão e fotos.
- Sobre/Versões atualizado para V39.7.9.
