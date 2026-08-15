AUTOPASS — V6.0 CENTRAL OPERACIONAL

Construído sobre o main mais recente enviado durante os testes da V5.2.1.

ENTREGAS PRINCIPAIS

1. EQUIPES X USUÁRIOS
- Equipe pode ser vinculada explicitamente a um usuário ativo.
- Mostra Vinculado / Não vinculado.
- Permite trocar ou remover o vínculo.
- Vínculo é utilizado para foto, localização e histórico.

2. TÉCNICOS / SUPERVISORES / APOIO
- Técnicos: 12x36.
- Supervisores: 12x36.
- Apoio: 5x2, segunda a sexta, 08:00–18:00.
- Categoria visível nos cards, tabela e Excel.

3. GESTÃO DE ESCALA
- Alterar turno.
- Alterar 12x36 / 5x2.
- Alterar primeiro dia do ciclo.
- Alterar ENTRADA / ponto de início.
- Alterar linhas.
- Alterar supervisão.
- Adicionar/remover integrante da escala sem excluir o usuário.
- Dados persistem no PostgreSQL.

4. MAPA OPERACIONAL
- CSS Leaflet isolado.
- tiles forçados a 256x256.
- ResizeObserver recalcula o mapa quando o container muda.
- recalculado no fullscreen e ao voltar.
- mantém ocultar/mostrar e tela cheia.

5. EXCEL
- botão Exportar Excel na aba Equipes.
- respeita período e filtro de categoria.
- abas Escala por Dia, Resumo e Vínculo Usuários.

6. CORES
- Dashboard executivo com cores mais presentes.
- Equipes, Evidências, Usuários, Lançamento e Sobre também recebem identidade visual.
- mantém fundo claro e leitura executiva.

VERSÕES
- Dashboard: dashboard-v6-0
- Equipes: teams-v6-0
- Health: v6.0-central-operacional

TESTES
1. /gerencial -> window.AUTOPASS_MANAGER_VERSION = dashboard-v6-0
2. /equipes -> tabela com Técnico/Supervisor/Apoio
3. Gerenciar escala -> editar Entrada de um técnico
4. Vincular um perfil de escala ao usuário correspondente
5. Exportar Excel
6. Expandir mapa / sair / voltar ao mapa normal
7. Apoio deve aparecer somente seg-sex, 08:00-18:00
