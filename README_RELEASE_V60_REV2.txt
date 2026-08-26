INVENTÁRIO AUTOPASS — V60 REV2
Base: V60 Revisada homologada
Foco: Performance + Financeiro 2.0

ENTREGAS FINANCEIRO
1. Cadastro de empresas/fornecedores
   - busca por nome, nome fantasia, CNPJ, contato e ID de centro de custo;
   - botão Limpar;
   - edição em tela/modal com todos os campos;
   - prevenção de novos duplicados por nome normalizado ou CNPJ;
   - função ADM para consolidar duplicados preservando serviços e lançamentos;
   - nova Central de Pendências de Cadastro para regularização;
   - novo campo ID Centro de Custo.

2. Centros de custo cadastrados
   - CVD0011 — SUPORTE E CAMPO
   - CFD0024 — ASSISTENCIA TECNICA
   - CVD0016 — IMPLANTAÇÃO HW
   - CFD0025 — MECANICA
   - CVD0017 — ENGENHARIA HW
   - CVD0020 — LINHA 17

3. Lançamentos
   - Projeto sempre visível no novo lançamento e na edição;
   - ID de centro de custo preenchido automaticamente;
   - NF/documento disponível no formulário completo;
   - ao selecionar fornecedor, carrega serviços cadastrados;
   - mostra os últimos rateios do fornecedor para reaproveitamento;
   - botão Limpar no novo lançamento;
   - fechamento mensal em lote passa a exibir Projeto;
   - botão Limpar na tabela mensal.

4. Desvio / Saving
   - gasto abaixo do forecast é apresentado como Saving positivo;
   - gasto acima do forecast permanece como desvio;
   - ajuste aplicado no histórico e na Dashboard Financeira.

PERFORMANCE
1. /api/chip-swaps
   - sincronização pesada da base removida do ciclo da requisição;
   - cache operacional ampliado de 20 s para 120 s;
   - objetivo: eliminar picos extremos observados na Telemetria.

2. /api/financeiro/apuracao/terminais
   - remove COUNT(*) integral sobre a base de transações;
   - usa MAX(id) no volume operacional da base append-only;
   - cache ampliado para 15 minutos;
   - índices adicionados para imported_at/source_file e lançamentos financeiros.

3. /usuarios e páginas com muitas verificações de permissão
   - cache das permissões no contexto da própria requisição;
   - reduz consultas repetidas provocadas por can_view() no Jinja.

OBSERVAÇÃO
A V60 REV2 mantém o escopo de RH, Preventiva ATM, Equipes, EMV, Panorâmicas e Central Operacional da V60 Revisada.
