# -*- coding: utf-8 -*-
"""V88.0 REV64 — GestãoClick (sistema anterior da Assistência), etapa 1: conexão e consulta.

Somente leitura. O servidor chama https://api.gestaoclick.com com a chave de API guardada nas variáveis do Render
GESTAOCLICK_ACCESS_TOKEN e GESTAOCLICK_SECRET_TOKEN (cabeçalhos access-token / secret-access-token).
Só faz GET: não existe caminho para cadastrar, editar ou excluir nada no GestãoClick.

Tela /gestao/gestaoclick (Gestor com liberação de Diagnóstico):
- situação da conexão (sem mostrar os tokens);
- resumo com o total de registros de cada recurso (OS, produtos, fornecedores, NFs, compras...);
- consulta livre a qualquer lista/registro (GET) para conhecer os campos antes da importação (etapa 2).
"""
import json
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.gestaoclick.com"
PATH_RE = re.compile(r"^[a-z_]+(?:/[a-z_]+)?(?:/\d+)?(?:/[a-z_]+)?$")
SUMMARY = [
    ("ordens_servicos", "Ordens de serviço"),
    ("situacoes_ordens_servicos", "Situações de OS"),
    ("produtos", "Produtos"),
    ("fornecedores", "Fornecedores"),
    ("clientes", "Clientes"),
    ("servicos", "Serviços"),
    ("vendas", "Vendas"),
    ("compras", "Compras"),
    ("notas_fiscais_produtos", "NF-e de produtos"),
    ("notas_fiscais_servicos", "NFS-e de serviços"),
    ("lojas", "Lojas"),
]
_LOCK = threading.Lock()
_LAST = [0.0]


def _tokens():
    return (os.environ.get("GESTAOCLICK_ACCESS_TOKEN") or "").strip(), (os.environ.get("GESTAOCLICK_SECRET_TOKEN") or "").strip()


def configured():
    a, s = _tokens()
    return bool(a and s)


def gc_get(path, params=None, timeout=25):
    """GET na API do GestãoClick. Devolve (status_http, json|texto). Respeita ~3 chamadas/s."""
    path = str(path or "").strip().strip("/")
    if not PATH_RE.match(path):
        raise ValueError("Caminho inválido")
    a, s = _tokens()
    if not (a and s):
        raise RuntimeError("Chave do GestãoClick não configurada no servidor")
    q = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v not in (None, "")})
    url = BASE + "/" + path + ("?" + q if q else "")
    req = urllib.request.Request(url, method="GET", headers={"access-token": a, "secret-access-token": s,
                                                             "Accept": "application/json", "User-Agent": "SistemaGestao/REV64"})
    with _LOCK:
        wait = 0.35 - (time.time() - _LAST[0])
        if wait > 0:
            time.sleep(wait)
        _LAST[0] = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            code = r.status
    except urllib.error.HTTPError as e:
        raw, code = e.read() or b"", e.code
    txt = raw.decode("utf-8", "replace")
    try:
        return code, json.loads(txt)
    except ValueError:
        return code, txt[:2000]


def _meta(body):
    if isinstance(body, dict):
        m = body.get("meta") or {}
        if isinstance(m, dict):
            return m
    return {}


def install_gestaoclick(app, H):
    """H: login_required, guard() -> resposta de erro ou None, render(template, **kw), audit(evento, detalhe)."""
    from flask import jsonify, request, abort

    login_required, guard = H["login_required"], H["guard"]

    @app.get("/gestao/gestaoclick")
    @login_required
    def v140_gc_page():
        if guard():
            abort(403)
        return H["render"]("gestaoclick_v140.html")

    @app.get("/api/gestaoclick/status")
    @login_required
    def v140_gc_status():
        g = guard()
        if g:
            return g
        if not configured():
            return jsonify({"ok": True, "configured": False,
                            "message": "Crie no Render as variáveis GESTAOCLICK_ACCESS_TOKEN e GESTAOCLICK_SECRET_TOKEN."})
        rows = []
        for path, label in SUMMARY:
            try:
                code, body = gc_get(path, {"pagina": 1})
                m = _meta(body)
                rows.append({"path": path, "label": label, "http": code,
                             "total": m.get("total_registros"), "pages": m.get("total_paginas"),
                             "error": None if code == 200 else (body.get("data") if isinstance(body, dict) else str(body)[:200])})
            except Exception as exc:
                rows.append({"path": path, "label": label, "http": None, "total": None, "pages": None, "error": str(exc)[:200]})
        ok = any(r["http"] == 200 for r in rows)
        try:
            H["audit"]("GESTAOCLICK_STATUS", "conexão %s" % ("ok" if ok else "falhou"))
        except Exception:
            pass
        return jsonify({"ok": True, "configured": True, "connected": ok, "rows": rows})

    @app.get("/api/gestaoclick/consulta")
    @login_required
    def v140_gc_query():
        g = guard()
        if g:
            return g
        path = (request.args.get("caminho") or "").strip().strip("/")
        params = {k: v for k, v in request.args.items() if k != "caminho"}
        try:
            code, body = gc_get(path, params)
        except ValueError:
            return jsonify({"ok": False, "error": "Caminho inválido (use só letras, _ e /, ex.: ordens_servicos ou produtos/123)."}), 400
        except RuntimeError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        except Exception as exc:
            return jsonify({"ok": False, "error": "Falha ao consultar o GestãoClick: %s" % str(exc)[:200]}), 502
        return jsonify({"ok": code == 200, "http": code, "meta": _meta(body), "body": body,
                        "error": None if code == 200 else "GestãoClick respondeu HTTP %s" % code})
