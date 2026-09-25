# V85.14 — Engenharia + Gestão

Base recebida: pacote aprovado pelo usuário após V85.13 REV4. O código-base ainda identificava APP_RELEASE como V85.13 REV3; nesta entrega o release passa a V85.14.

## Implementado
- Engenharia > Preços e Valores: premissa Texomobi -> Autopass, Lucro Presumido, operação interna SP.
- Alíquotas IPI, ICMS, PIS e COFINS permanecem editáveis.
- Preço com IPI: retirada do IPI embutido.
- ICMS calculado sobre preço sem IPI, conforme premissa do motor.
- Base de PIS/COFINS exclui o ICMS calculado.
- Receita líquida, custo industrial, lucro e margem sobre receita líquida.
- Memória de cálculo mostra bases e valores tributários.
- Gestão de Tarefas/Kanban/Agenda existente preservada, incluindo source_type/source_id para vínculo operacional.
- Histórico Sobre atualizado.

## Homologação necessária
A memória tributária deve ser confrontada com 1-2 operações reais e validada pelo contador antes de uso fiscal definitivo.
