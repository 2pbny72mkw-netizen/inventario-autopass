INVENTÁRIO AUTOPASS — V56-B
Release estrutural consolidado / janela noturna

FOCO DA V56-B
- Performance, estabilidade, escala e redução de rotinas/consultas redundantes.
- Telemetria em Gestão exclusiva do perfil ADM.
- Índices aditivos para consultas críticas de Apuração, GPS, sessões, Financeiro e Telemetria.
- Preservação das rotinas operacionais homologadas da V56-A.

APURAÇÃO DE NUMERÁRIO — CAMADA ANALÍTICA
- Filtro central por Terminal + Localidade + Coleta inicial + Coleta final.
- Pesquisa por terminal/localidade e seleção de múltiplos terminais com Marcar todos/Limpar.
- Somatória das transações aprovadas entre as duas coletas x valor coletado na coleta final.
- Valor apurado/processado pela TBForte, quando disponível.
- Quantidade de cédulas processadas da coleta final, lida de PROCESSAMENTO / Qtde Process da TBForte.
- Diferença em R$ e %, ticket médio, média transacionada/dia e duração entre coletas.
- Diagnóstico automático: Conciliado / Atenção / Divergência relevante.
- Comparativo visual Transacionado x Coletado x Apurado e velocímetro de divergência.
- Visão múltiplos terminais ordenada pela maior divergência absoluta.
- Exportação Excel individual e consolidada, incluindo cédulas e indicadores analíticos.
- Drill-down das transações do período para auditoria.

TELEMETRIA / DESEMPENHO
- Gestão > Telemetria exclusiva ADM; rota/API também protegidas no backend.
- Saúde geral, média, P95, pico, erros 5xx, usuários ativos, rotas mais lentas e volume das bases.
- Raio-X para diagnóstico por print e direcionamento das próximas otimizações.

EQUIPES / GPS
- Estação/ponto de referência automático com faixa operacional de 500 m.
- Fora da faixa, mantém estação mais próxima + distância.
- Operação de Hoje: escalados, atraso, não logou, sem GPS, sem posição >10 min, última posição/localidade.

OUTROS
- Subpermissões por módulo/subatividade; Telemetria não é delegável.
- Chamados: evolução mensal em barras verticais com efeito de profundidade.
- Mantidas as correções homologadas da V56-A.5 / V56-A.4 HOTFIX3.

DEPLOY RECOMENDADO
1. Backup PostgreSQL antes do deploy.
2. Deploy noturno.
3. Aguardar inicialização e criação aditiva de índices/colunas/tabelas.
4. Validar Login > Field > Equipes > Financeiro > Usuários/Subpermissões > Gestão/Telemetria.
5. Em Apuração, importar novamente os extratos TBForte para popular Qtde Process/cédulas nas coletas já existentes.
6. Testar um terminal conhecido: coleta inicial > coleta final > Transacionado x Coletado x Apurado x Cédulas.
7. Não apagar banco nem executar migrações destrutivas.
