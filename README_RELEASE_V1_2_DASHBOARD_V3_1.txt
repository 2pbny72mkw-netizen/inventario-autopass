AUTOPASS — V1.2 OPERACIONAL + DASHBOARD EXECUTIVO V3.1
=========================================================

BASE
Construído sobre o main.zip mais recente enviado pelo usuário.

OBJETIVOS DESTA RELEASE
- Reduzir fortemente a sensação de lentidão do Dashboard.
- Fazer Empresa / Linha / Tipo atuarem de verdade sobre a visão executiva.
- Trocar CSV por exportação Excel (.xlsx).
- Usar os Big Numbers oficiais informados:
  ATM = 590
  POS = 972
  Recarga = 629
  Bloqueio = 1.610
  Total oficial = 3.801
- Manter TDI como controle técnico separado do total oficial.
- Preservar tela técnica, inclusão, edição, exclusão, GPS e mapa atual.

PRINCIPAIS ALTERAÇÕES

1. PERFORMANCE
- /api/dashboard não recalcula mais o casamento pesado da base por localidade.
- KPIs oficiais são carregados primeiro.
- /api/locations vem em uma segunda fase.
- Mapa/GPS continua carregando depois dos KPIs.
- Associação BaseAsset x Location usa índice por linha e cache de 10 minutos.
- Cache é invalidado quando a base 1408 é sincronizada novamente.
- /api/locations passa a usar agregações pequenas por localização/tipo.

2. FILTROS EXECUTIVOS
- Empresa + Linha + Tipo passam a atualizar:
  * Parque previsto
  * Inventariado
  * Faltante
  * Cobertura
  * Divergências
  * Inoperantes
  * Big Numbers por produto
  * Ranking de localidades críticas
  * Tabela de localidades
- Cards ATM / Recarga / POS / TDI / Bloqueio continuam clicáveis.
- Linha é recalculada conforme a Empresa selecionada.
- Contexto do filtro aparece abaixo da barra executiva.

3. BIG NUMBERS OFICIAIS
- ATM: 590
- POS: 972
- Recarga: 629
- Bloqueio: 1.610
- TOTAL OFICIAL: 3.801
- TDI aparece como controle técnico e não soma no total oficial.

4. EXCEL
Novo botão "Exportar Excel".
Gera arquivo .xlsx com:
- Resumo Executivo
- Localidades
- Inventário Realizado
A exportação respeita Empresa / Linha / Tipo selecionados.

5. RECONCILIAÇÃO
- /api/locations agora entrega inventoried_by_type.
- Divergências por localidade também passam a vir na API.
- Tabela de localidades mostra Divergências e Inoperantes separadamente.
- Registros não classificados continuam disponíveis no diagnóstico.

6. MAPA
- Mapa atual foi preservado para não introduzir regressões.
- Linha 4-Amarela e Linha 17-Ouro continuam mapeadas para intervenção específica futura.

ARQUIVOS PRINCIPAIS ALTERADOS
- app.py
- requirements.txt
- static/manager.js
- static/app.css
- templates/manager.html

COMO SUBIR
1. Descompacte este ZIP.
2. No GitHub, faça upload do conteúdo mantendo as mesmas pastas.
3. Commit único.
4. Render -> Deploy latest commit.
5. Aguarde Live.
6. Ctrl+F5 em /gerencial.

TESTES APÓS LIVE
1. Console:
   window.AUTOPASS_MANAGER_VERSION
   Esperado: "dashboard-v3-1"

2. Conferir Big Numbers sem filtros:
   ATM 590
   POS 972
   Recarga 629
   Bloqueio 1.610
   Parque oficial 3.801

3. Testar:
   Empresa = METRO
   Linha = 01 - AZUL
   Tipo = ATM
   Os KPIs e tabela devem mudar.

4. Clicar no card ATM e depois clicar novamente para retirar o filtro.

5. Exportar Excel com e sem filtros.

6. Confirmar que /tecnico continua permitindo:
   incluir
   editar
   excluir

7. Conferir mapa/GPS após o carregamento dos KPIs.

NOTA
O primeiro carregamento das localidades depois de um cold start ainda pode ser mais lento
que os seguintes. A diferença é que os KPIs agora são entregues antes e o casamento da base
fica cacheado em memória por 10 minutos.
