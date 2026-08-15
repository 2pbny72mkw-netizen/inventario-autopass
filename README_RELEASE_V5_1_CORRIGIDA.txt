AUTOPASS V5.1 — CENTRAL OPERACIONAL CORRIGIDA

Diagnóstico do V5.0:
- O deploy estava realmente Live no commit V5.0.
- Porém o pacote continha static/teams.js e as rotas /equipes, mas NÃO continha templates/teams.html.
- O menu templates/base.html também não tinha o link Equipes.
- manager.js continuava identificado como dashboard-v4-1-1.
Por isso Equipes não aparecia apesar do commit V5.0 estar Live.

CORREÇÕES / EVOLUÇÕES V5.1
- cria templates/teams.html
- adiciona Equipes no menu Gestor
- mapa operacional dos técnicos
- avatar/foto com anel:
  verde <=5 min
  amarelo 6-15 min
  vermelho >15 min
  cinza sem sinal
- escala 12x36 carregada de data/technician_schedule_v5.json
- usa horário/data America/Sao_Paulo
- exibe ponto de entrada, turno, linhas e supervisão
- botão Atualizar
- botão Expandir mapa + ESC
- tela do técnico ganha Ativar/Desativar localização
- localização é enviada somente após autorização do navegador
- envio limitado aproximadamente a 1 vez a cada 90 segundos
- manager version passa a dashboard-v5-1 para confirmar o deploy
- /health identifica v5.1-central-operacional

TESTES APÓS LIVE
1. /gerencial Console:
   window.AUTOPASS_MANAGER_VERSION
   esperado: dashboard-v5-1

2. Verificar menu:
   Dashboard | Evidências | Equipes | Lançamento | Usuários | Sair

3. Abrir /equipes.
4. Confirmar técnicos escalados, turnos e pontos de entrada.
5. Em /tecnico clicar "Ativar localização".
6. Autorizar localização no navegador.
7. Voltar a /equipes e clicar Atualizar.
