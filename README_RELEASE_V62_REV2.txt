V62 REV2 — ESTABILIDADE / MEMORIA

Motivo:
- Log de producao em 27/08/2026 mostrou POST /api/emv-chip-swaps/650113 seguido de SIGKILL com indicio de OOM.

Correcoes:
1. Uploads para Cloudflare R2 agora usam stream do FileStorage; removido f.read() das evidencias operacionais.
2. Limite padrao por arquivo: 15 MB (ACTIVITY_UPLOAD_MAX_MB).
3. Limite padrao por requisicao: 40 MB (ACTIVITY_REQUEST_MAX_MB).
4. EMV salva evidencias uma por vez, fecha o stream e faz rollback controlado se houver falha.
5. Base EMV indexada por terminal para gravacao.
6. Mesma protecao aplicada a Recarga, Garagem, Panoramica, Inventario e Relatorio de Visita.

Esta revisao e focada em estabilidade. Nao amplia o escopo funcional da V62 REV1.

Diagnostico adicional de producao:
- Varias evidencias EMV entre ~3 MB e ~16 MB eram servidas por /uploads/r2__...;
  a rota antiga baixava o objeto R2 inteiro para a RAM do worker antes de responder.
- V62 REV2 passa a redirecionar midias R2 para URL temporaria assinada, retirando o
  trafego pesado do unico worker Gunicorn.
- Galeria EMV usa lazy loading e thumb_url.
- ADM pode retificar status EMV sem justificativa; Gestor Field continua com motivo obrigatorio.
