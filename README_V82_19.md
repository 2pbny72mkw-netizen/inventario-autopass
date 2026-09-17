# Inventário Autopass — V82.19 ENXUTA

Base: V82.18 ENXUTA.

## Alteração validada nesta revisão
- Reprogramação de coletas 2x/semana: pares fixos Dia 1 → Dia 2:
  - TER → QUI
  - QUA → SEX
  - QUI → TER
  - SEX → QUA
- A regra é usada pelo cálculo central que alimenta proposta, terminal_plan, ativação/aplicação e exportação.
- APP_RELEASE atualizado para V82.19.

## Observação sobre os demais itens do escopo V82.19
A base ENXUTA V82.18 disponível contém app.py e financial_petty_cash.html, mas não contém o template atm_mapping_v82.html nem o template global do menu. Portanto, esta revisão não declara como concluídas alterações visuais que dependem desses arquivos (renderização das fotos persistidas ao reabrir o modal e inclusão visível de Caixinha no menu Financeiro). O backend V82.18 já retorna photo_items e exige foto persistida para concluir, mas a interface antiga pode não renderizá-los.
