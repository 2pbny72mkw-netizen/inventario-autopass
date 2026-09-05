# V77.6 — Bobinas / Dashboard reconstruída

Objetivo: destravar a homologação do módulo de Bobinas substituindo a tentativa de adaptar a dashboard V77.5.

- Mantém o menu superior padrão do Sistema de Gestão; não cria sidebar própria.
- Reproduz a área útil do esboço aprovado: KPIs, filtros, Linha/Estações, Detalhe da Estação, Histórico da ATM, Evolução e Indicadores.
- Detalhe da estação mantém cada ATM individual, percentual com badges coloridos, situação, reserva, última leitura, técnico e ação.
- Hierarquia funcional: Linha → Estação → ATM → Histórico / Evolução / Indicadores.
- Painel de Registro em Campo permanece à direita e Armários ficam no quadro compacto abaixo.
- Botão Importar planilha visível no cabeçalho abre modal de Bobinas+Armários ou Estoque Field/M16, com validação, prévia, divergências e confirmação.
- Base oficial ATM continua soberana: 602 total, 590 instaladas, 12 em estoque. A planilha não cria ATM.
- Importação preserva leituras individuais por ATM e trata reservas legadas não localizadas separadamente.
