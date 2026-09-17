# Inventário Autopass — V82.20 ENXUTA

Correções desta revisão:

- Financeiro: item **Caixinha** conectado ao menu quando o usuário possui `finance.petty_cash.view` ou `finance.petty_cash.manage`. As rotas e permissões já existentes passam a ficar acessíveis pela navegação.
- Mapeamento ATM: ao abrir uma ATM, o modal passa a renderizar as evidências persistidas retornadas pela API em **Fotos já salvas (N)**, com miniaturas clicáveis para visualização ampliada.
- Mapeamento ATM: separação entre **Fotos já salvas** e **Novas fotos**; novas evidências continuam sendo acrescentadas sem apagar as anteriores.
- Evidência cujo arquivo não puder ser carregado é sinalizada como **Evidência indisponível**.
- Mantida a obrigatoriedade de pelo menos uma evidência persistida para conclusão do mapeamento.
- Preservada a regra V82.19 de pares da reprogramação 2x/semana: Terça→Quinta, Quarta→Sexta, Quinta→Terça e Sexta→Quarta.
