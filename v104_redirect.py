# -*- coding: utf-8 -*-
"""V88.0 REV16 — troca de endereço: o serviço antigo redireciona as TELAS para o endereço novo.

Ligado SÓ pela variável de ambiente REDIRECT_TO no serviço antigo do Render, por exemplo:
    REDIRECT_TO = https://sistema-gestao-autopass.onrender.com
Sem a variável (serviço novo, ou antes da troca) não faz nada.

O que é redirecionado: abertura de telas no navegador (GET/HEAD fora de /api).
O que NÃO é redirecionado (continua atendido normalmente pelo serviço antigo, mesmo banco):
- /api/...            → o app Android e qualquer chamada em andamento seguem funcionando até o app ser atualizado;
- /health             → monitoramento do Render;
- /static/..., /.well-known/..., /sw.js, /manifest... → arquivos técnicos;
- POST/PUT/DELETE     → um formulário enviado no endereço antigo não é perdido.
Redirecionamento temporário (302) por padrão: se mudar de ideia, basta apagar a variável.
REDIRECT_PERMANENT=1 troca para 301 (use só quando a mudança estiver definitiva).
"""
import os
from urllib.parse import urlsplit

_SKIP_PREFIXES = ("/api/", "/health", "/static/", "/.well-known/", "/sw.js", "/manifest", "/favicon")


def install_redirect(app):
    from flask import request, redirect

    target = (os.environ.get("REDIRECT_TO") or "").strip().rstrip("/")
    if not target:
        return False
    parts = urlsplit(target)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        app.logger.error("REV16: REDIRECT_TO inválido (%s); redirecionamento desligado", target)
        return False
    target_host = parts.netloc.lower()
    code = 301 if os.environ.get("REDIRECT_PERMANENT") == "1" else 302

    @app.before_request
    def _v104_redirect_old_address():
        if request.method not in ("GET", "HEAD"):
            return None
        if (request.host or "").lower() == target_host:  # já está no endereço novo
            return None
        path = request.path or "/"
        if path.startswith(_SKIP_PREFIXES):
            return None
        qs = request.query_string.decode("utf-8", "ignore")
        return redirect(target + path + (("?" + qs) if qs else ""), code=code)

    app.logger.info("REV16: telas redirecionadas para %s (%s)", target, code)
    return True
