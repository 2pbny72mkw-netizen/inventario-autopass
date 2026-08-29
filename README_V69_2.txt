V69.2 — 29/08/2026
Base: V69 REV1

PRINCIPAIS ALTERAÇÕES
- Portal do Cliente / Recebimento redesenhado no padrão Dashboard 2.0.
- Melhor contraste de textos, KPIs coloridos, progresso por agendamento e compactação para desktop.
- Filtro por cliente adicionado em Agendamentos recebidos.
- Modal de recebimento com "Baixar todos os PDFs" em arquivo ZIP.
- PDFs individuais agora usam o padrão AG-AAAA-NNNNNN-XX_SN-SERIAL.pdf.
- Downloads de PDFs ficam registrados em AuditEvent e aparecem como indicador "OS · Baixado" com data/hora.
- Assinatura eletrônica continua disponível, mas passa a ser opcional.
- Perfil Cliente entra diretamente em /portal-cliente após login e ao acessar a raiz.
- "Meus documentos e minha carga" não é exibido para perfil Cliente.
- Corrigido erro 500 da exportação de Telemetria causado por ws[2:] no openpyxl.
- Cache/PWA atualizado de versões antigas para v69-2.
- Portal externo usa /static/autopass-logo.png, sem logotipo aproximado/inventado.

ARQUIVOS ALTERADOS
- app.py
- templates/customer_portal.html
- templates/profile.html
- templates/base.html
- static/sw.js
- sw.js

VALIDAÇÕES EXECUTADAS
- python -m py_compile app.py: OK
- Parse Jinja de customer_portal.html, profile.html e base.html: OK
