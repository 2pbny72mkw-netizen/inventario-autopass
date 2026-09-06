# V77.8 — Estabilização operacional

## Escopo

### Rastreabilidade & Jornada
- Mapa GPS contido em janela fixa de 600 px, largura 100%, cantos arredondados e overflow oculto.
- Hierarquia Leaflet validada em campo: tile 200, overlay 400, shadow 500, marker 600, tooltip 650, popup 700.
- Todas as posições GPS do período são plotadas; passagens por estação continuam contabilizadas separadamente.
- Cada posição usa a foto do técnico quando houver foto cadastrada; fallback para marcador azul quando não houver.
- Trajeto em azul e reenquadramento automático após consulta.
- Linha do tempo inicia recolhida e, ao abrir, usa scroll interno.
- KPIs rápidos: data, estações, posições e retenção.

### Jornada extraordinária
- Autorizações APROVADAS vencidas passam automaticamente para EXPIRADA quando approved_until <= agora.
- A tela fora da jornada considera como estado atual somente solicitação PENDENTE.
- Notificações antigas de autorização deixam de permanecer como não lidas após decisão/expiração.
- Aprovação e recusa encerram a notificação correspondente.

### Central de Atividades
- A Central passa a listar automaticamente atividades operacionais habilitadas pela matriz de permissões.
- Inclui, conforme acesso: Inventário, Troca de Chip Recarga, Visão Panorâmica, Controle de Bobinas, Atualização Firmware POS, Troca de Chip Garagem, EMV Trilhos e Implantação de Hardware.
- Dashboards e áreas administrativas continuam fora da Central.
- Cards grandes e responsivos para uso móvel.

### Agenda Arrow 2.0
- Calendário visual 2.0 com cores leves por status.
- Filtros por técnico, operadora, status, prioridade e busca.
- Navegação mensal, resumo do período e criação/edição de atividades.

### Visão Panorâmica
- Frontend alinhado ao payload real de /api/panoramas.
- Recalcula Localidades, Pendentes, Em andamento, Concluídas, Fotos, progresso e gráfico de status a partir dos dados retornados.
- Filtros Empresa → Linha → Status → Localidade atualizam o recorte sem zerar os dados reais.

### Sobre
- Release atualizada para V77.8 e histórico mantido apenas na seção própria.

## Validação recomendada pós-deploy
1. Rastreabilidade: consultar técnico com histórico e confirmar foto em todas as posições, trajeto visível, mapa contido e timeline recolhida.
2. Jornada: confirmar que autorização do dia anterior não aparece como vigente; testar nova solicitação/aprovação/expiração.
3. Visão Panorâmica: validar que os KPIs deixam de ficar zerados e as localidades aparecem nos filtros.
4. Central de Atividades: testar com Técnico Field e confirmar cards somente das atividades habilitadas.
5. Arrow: navegar entre meses, criar e editar uma atividade.
