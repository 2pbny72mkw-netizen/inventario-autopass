# V73 ENXUTA — CONSOLIDADA

Base: V72.1 + estabilidade acumulada. Esta V73 substitui a primeira V73 parcial.

## Entregas V73
- GPS V73: watch contínuo, posição operacional + fila/reenvio, cache-bust, histórico por todos os pings do dia e mapa técnico/data.
- RH Equipes: mapa maior, atualização a cada 15 s, autocomplete e Técnico mais próximo (até 4 técnicos com GPS recente).
- Geofence: estado NA ESTAÇÃO/LOCALIDADE x FORA DA ÁREA usa o raio configurado; localidades externas cadastráveis em Gestão e integradas à referência GPS.
- Jornada: férias/folga autorizáveis; afastado/licença bloqueados; autorizações aparecem em Gestão e entram em Notificações.
- Meu Perfil: solicitação de folga e troca de folga; troca exige aceite do colega e aprovação da Gestão.
- RH > APT 2.0: carga inicial da planilha fornecida, importação CSV/XLSX, exportação, validade 40/30/15/vencida, status, PDF por APT e consulta pelo colaborador.
- Recarga/TDI: TDI oficial corrigido para 42; Recarga 629; sincronização de localidades externas; TDI incluído no matching da atividade; filtro Pendentes corrigido para incluir não iniciados.
- Dashboard Recarga: apenas um botão de exportação e exportação respeitando filtros.
- Atividade Recarga: filtros Data + Técnico + Status e exportação coerente; API V73 de execuções preparada para expansão do padrão às demais atividades.
- Gestão > Resumo dos Links: biblioteca de título/categoria/URL/observação.
- Configurações Operacionais: textos explicativos e comunicação visual 2.0.
- Mensagens globais: sucesso verde, erro vermelho, atenção amarelo e informação azul.
- Notificações: badge passa a contar alertas/assuntos, não a soma bruta de registros afetados; inclui jornada, trocas e APT.
- Arrow: novo menu superior com subcategoria inicial Agendas, sem regras internas ainda (aguarda detalhamento funcional).

## Observação
O padrão Data + Técnico foi implementado funcionalmente em Recarga nesta build e a API comum foi criada para expansão. Atividades com modelos de dados diferentes continuam exigindo adaptação específica para não falsificar autoria/data histórica.
