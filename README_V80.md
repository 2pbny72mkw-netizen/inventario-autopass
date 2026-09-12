# V80 — Monitoramento Inteligente / Coleta de Valores

Base oficial: ZIP confirmado pelo usuário como a versão atualmente em produção. A correção de navegação da V79.5 REV4 foi incorporada antes da evolução para V80.

## Escopo implementado
- `APP_RELEASE = V80` e histórico em **Sobre** atualizado.
- Monitoramento da Coleta de Valores preservado e ampliado com:
  - **Análise IA · Divergências**;
  - **Análise IA · Ocorrências**.
- As duas análises respeitam período e filtros ativos: programação, status, operadora, linha, estação, ATM e diferença.
- Indicadores financeiros calculados no backend: negativas, zeradas, positivas, sem valor, total declarado, total apurado, saldo líquido e diferença absoluta.
- Rankings e gráficos Dash 2.0 por ATM, localidade, linha e operadora.
- Ocorrências classificadas de forma auditável em: Fechadura/cofre, Falta de suporte, Coleta não realizada, BAG/lacre, ATM/manutenção, Acesso/autorização, Transportadora, Reagendamento e Outros.
- Painel específico de localidades com falha de fechadura/cofre.
- Tabelas de origem para auditoria dos casos negativos e das ocorrências classificadas.
- Nova API: `GET /api/financeiro/coletas/v80/analise`.

## Conciliação de transações
A conciliação existente continua usando janela entre duas coletas/slips consecutivos do mesmo ATM. A regra de fechamento da V80 não foi alterada para inventar campos ainda não validados. Quando o novo arquivo de transações for recebido, a importação deve ser ajustada para os campos reais de produto, voucher e valor efetivamente recebido.

## Banco de dados
Não há alteração destrutiva de schema. Apenas registro de migração `V80-001` no mecanismo de histórico existente.

## Arquivos alterados na ENXUTA
- `app.py`
- `templates/financial_cash_collection.html`
- `static/cash_collection_v79.js`
- `templates/about.html`
- `templates/base.html` *(correção REV4 preservada)*
- `templates/field_dashboard.html` *(correção REV4 preservada)*
- `README_V80.md`
