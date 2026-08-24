INVENTÁRIO AUTOPASS — V55.4
===========================
Objetivo: fechar a V55 como baseline funcional antes da reestruturação arquitetural V56.

IMPLEMENTADO
- Dashboard Financeiro 2.0 redesenhada: 6 KPIs, tendência, pico mensal, evolução Realizado x Forecast, composição por produto, Top fornecedores, Top serviços e Central de Atenção Financeira.
- Dashboard Implantação 2.0: leitura executiva compacta, KPIs coloridos, progresso e status sem o excesso visual de velocímetro/pizza 3D.
- Filtro Modelo ATM saneado na API: somente modelos oficiais TCI, MK, MKNEO, TCINEO, MINIWALL, TCIPLUS e DCASH; demais valores ficam como Modelo não identificado.
- Versionamento V55.4 e cache dos assets principais atualizados.
- Rotas Financeiro/Implantação corrigidas na V55.3.1 preservadas.

VALIDAÇÃO TÉCNICA
- Python compila.
- Templates Jinja carregam sintaticamente.
- JavaScript inline/arquivos verificados sintaticamente quando Node disponível.
- ZIP enxuto contém somente arquivos alterados desta baseline.

HOMOLOGAÇÃO NO RENDER
1. Dashboard Financeiro abre no shell e carrega dados.
2. Dashboard Implantação abre no shell e carrega dados.
3. Filtro Modelo ATM não exibe IDs numéricos como modelo.
4. Financeiro: filtros alteram todos KPIs/gráficos.
5. Implantação: filtros alteram KPIs/gráficos.
