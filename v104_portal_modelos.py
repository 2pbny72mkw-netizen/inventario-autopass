# -*- coding: utf-8 -*-
"""V88.0 REV15.2 - Portal do Cliente › Agendamento: inclui modelos novos na lista "Equipamento / modelo".
Injeta na lista PC_MODELS da página /portal-cliente (sem substituir o template). Para incluir outro modelo no futuro, basta acrescentar em EXTRA_MODELS."""
import re

EXTRA_MODELS = ["Thinker Board"]
_RX = re.compile(r"(const\s+PC_MODELS\s*=\s*\[)([^\]]*)(\])")


def add_models(html):
    """Devolve (html, quantidade de modelos incluídos). Idempotente."""
    m = _RX.search(html)
    if not m:
        return html, 0
    body = m.group(2)
    add = [x for x in EXTRA_MODELS if ("'" + x + "'") not in body and ('"' + x + '"') not in body]
    if not add:
        return html, 0
    body = body.rstrip() + ("," if body.strip() else "") + ",".join("'" + x.replace("'", "\\'") + "'" for x in add)
    return html[:m.start()] + m.group(1) + body + m.group(3) + html[m.end():], len(add)


def install_models(app):
    from flask import request

    @app.after_request
    def v104_models(response):
        if request.path != "/portal-cliente" or response.status_code != 200 or response.mimetype != "text/html" or response.direct_passthrough:
            return response
        try:
            html = response.get_data(as_text=True)
        except Exception:
            return response
        new, n = add_models(html)
        if n:
            response.set_data(new)
        return response
    return None
