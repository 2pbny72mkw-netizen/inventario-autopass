# Sistema de Gestão Autopass — V85.51

## Implementado nesta versão (Web/backend)

- Nova rota autenticada `GET /api/financeiro/coletas/v851/auditoria-cronologia?start=2026-10-01&end=2026-10-12`.
- Exige as mesmas permissões do Monitoramento de Coletas.
- Auditoria **somente leitura** sobre o período informado, limitado a 366 dias.
- Resume quantidade de ATMs, eventos, janelas, referências corrigidas/ausentes e ATMs com ocorrências.
- Detecta janelas com início >= fim e intervalos sobrepostos por ATM; ignora janelas idênticas repetidas no payload.
- Retorna até 200 ocorrências por página com `offset` e `limit`, sem retornar dados financeiros sensíveis adicionais.
- Mantém a correção R0050 da V85.50 REV2, sem migração ou escrita em dados de coletas.
- Histórico de versões atualizado.

**Limite:** a auditoria verifica os eventos retornados no período; não é um rastreamento completo de toda a história do banco nem prova de que todos os fechamentos sejam corretos. Não foi executada no banco de produção.

## Evolução planejada — Android + Web + GPS + cache offline

**Não implementado na V85.51.** Próxima frente de trabalho, priorizada pelo usuário:

1. Cache local persistente e criptografado no Android e fila durável de eventos de turno, atividades, fotos e posições GPS.
2. Cada evento recebe identificador idempotente estável; backend reconhece reenvios sem duplicar registros.
3. Retomada após perda de sinal, reinício do app, troca de rede e reabertura do turno; envio em lotes com retentativas e backoff.
4. Estados visíveis: pendente, enviando, confirmado, erro recuperável, erro definitivo; não limpar cache antes da confirmação do servidor.
5. GPS associado a turno, com data/hora da captura, precisão e ordenação; impedir GPS de turno desligado e preservar registros capturados offline.
6. Web mostra último sincronismo, quantidade pendente e divergências sem confundir ausência de sinal com ausência de atividade.
7. Testes em dispositivo real: modo avião, perda intermitente de rede, encerramento forçado, bateria, login expirado, fotos grandes e filas longas.

**Critério de aceite:** zero perda/duplicação de atividades após reconexão, rastreabilidade de eventos GPS por turno e confirmação explícita de sincronização. Necessita homologação Android + Web + backend.

## Homologação V85.51

1. Abrir Sobre e confirmar V85.51.
2. Consultar a rota de auditoria com usuário autorizado e datas válidas; testar 403 e período inválido.
3. Conferir ATM 32551 (24/09, 01/10, 08/10) no Monitoramento.
4. Validar 5 cenários de coleta, incluindo R0050 intermediário, ausência de referência e programação não realizada.
5. Confirmar que não houve alteração de dados originais.
