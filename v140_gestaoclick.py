# -*- coding: utf-8 -*-
"""V88.0 REV64 — GestãoClick (sistema anterior da Assistência): conexão, consulta e carga única.

Somente leitura. O servidor chama https://api.gestaoclick.com com a chave de API guardada nas variáveis do Render
GESTAOCLICK_ACCESS_TOKEN e GESTAOCLICK_SECRET_TOKEN (cabeçalhos access-token / secret-access-token).
Só faz GET: não existe caminho para cadastrar, editar ou excluir nada no GestãoClick.

Tela /gestao/gestaoclick (Gestor com liberação de Diagnóstico):
- situação da conexão (sem mostrar os tokens);
- resumo com o total de registros de cada recurso (OS, produtos, fornecedores, NFs, compras...);
- consulta livre a qualquer lista/registro (GET) para conhecer os campos;
- "Importar tudo": carga em segundo plano, página por página, gravando cada registro como veio (JSON) em
  v140_gc_raw (recurso + id). Retoma de onde parou. Depois da carga a chave pode ser apagada; os dados ficam aqui.
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
DEFAULT_IMPORT = ["situacoes_ordens_servicos", "ordens_servicos", "produtos", "fornecedores", "clientes", "servicos",
                  "compras", "vendas", "notas_fiscais_produtos", "notas_fiscais_servicos"]
_LOCK = threading.Lock()
_JOB = {"thread": None, "stop": False}
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


# ---------------- carga única (segundo plano) ----------------
def ensure_tables(engine):
    from sqlalchemy import text
    with engine.begin() as c:
        c.execute(text("CREATE TABLE IF NOT EXISTS v140_gc_raw (resource VARCHAR(60) NOT NULL, gc_id VARCHAR(60) NOT NULL, "
                       "data TEXT, imported_at TIMESTAMP, PRIMARY KEY (resource, gc_id))"))
        c.execute(text("CREATE TABLE IF NOT EXISTS v140_gc_jobs (resource VARCHAR(60) PRIMARY KEY, status VARCHAR(20), page INTEGER, "
                       "pages INTEGER, total INTEGER, imported INTEGER, error VARCHAR(500), started_at TIMESTAMP, finished_at TIMESTAMP, "
                       "user_name VARCHAR(180))"))


def _rec_id(rec, page, idx):
    if isinstance(rec, dict):
        for k in ("id", "codigo", "numero"):
            if rec.get(k) not in (None, ""):
                return str(rec[k])[:60]
    return "p%d_%d" % (page, idx)


def _run_jobs(engine, log):
    from datetime import datetime
    from sqlalchemy import text
    try:
        while not _JOB["stop"]:
            with engine.begin() as c:
                row = c.execute(text("SELECT resource, page FROM v140_gc_jobs WHERE status IN ('fila','rodando') "
                                     "ORDER BY started_at, resource LIMIT 1")).first()
            if not row:
                return
            res, page = row[0], int(row[1] or 0) + 1
            with engine.begin() as c:
                c.execute(text("UPDATE v140_gc_jobs SET status='rodando', error=NULL WHERE resource=:r"), {"r": res})
            fails = 0
            while not _JOB["stop"]:
                try:
                    code, body = gc_get(res, {"pagina": page}, timeout=60)
                except Exception as exc:
                    code, body = None, str(exc)
                if code != 200 or not isinstance(body, dict):
                    fails += 1
                    if fails < 4:
                        time.sleep(3 * fails)
                        continue
                    err = ("HTTP %s: " % code if code else "") + (json.dumps(body, ensure_ascii=False) if isinstance(body, dict) else str(body))
                    with engine.begin() as c:
                        c.execute(text("UPDATE v140_gc_jobs SET status='erro', error=:e, finished_at=:t WHERE resource=:r"),
                                  {"e": err[:500], "t": datetime.utcnow(), "r": res})
                    break
                fails = 0
                data = body.get("data")
                if isinstance(data, dict):
                    data = [data]
                data = data or []
                m = _meta(body)
                pages = m.get("total_paginas")
                now = datetime.utcnow()
                with engine.begin() as c:
                    for i, rec in enumerate(data):
                        p = {"r": res, "i": _rec_id(rec, page, i), "d": json.dumps(rec, ensure_ascii=False, separators=(",", ":")), "t": now}
                        c.execute(text("INSERT INTO v140_gc_raw (resource, gc_id, data, imported_at) VALUES (:r,:i,:d,:t) "
                                       "ON CONFLICT (resource, gc_id) DO UPDATE SET data=excluded.data, imported_at=excluded.imported_at"), p)
                    n = c.execute(text("SELECT COUNT(*) FROM v140_gc_raw WHERE resource=:r"), {"r": res}).scalar()
                    c.execute(text("UPDATE v140_gc_jobs SET page=:p, pages=:ps, total=:t, imported=:n WHERE resource=:r"),
                              {"p": page, "ps": pages, "t": m.get("total_registros"), "n": int(n or 0), "r": res})
                done = (not data) or (pages is not None and page >= int(pages)) or (pages is None and not m)
                if done:
                    with engine.begin() as c:
                        c.execute(text("UPDATE v140_gc_jobs SET status='concluida', finished_at=:t WHERE resource=:r"),
                                  {"t": datetime.utcnow(), "r": res})
                    break
                page += 1
    except Exception:
        log("REV64: falha na carga do GestãoClick")
    finally:
        _JOB["thread"] = None


def start_worker(engine, log):
    if _JOB["thread"] and _JOB["thread"].is_alive():
        return False
    _JOB["stop"] = False
    t = threading.Thread(target=_run_jobs, args=(engine, log), daemon=True, name="v140-gestaoclick")
    _JOB["thread"] = t
    t.start()
    return True


def install_gestaoclick_import(app, H):
    """H: login_required, guard(), engine, audit(evento, detalhe), user_name()."""
    from datetime import datetime
    from flask import jsonify, request
    from sqlalchemy import text

    login_required, guard, engine = H["login_required"], H["guard"], H["engine"]
    log = lambda msg: app.logger.exception(msg)

    def ensure():
        ensure_tables(engine)

    @app.get("/api/gestaoclick/importacao")
    @login_required
    def v140_gc_import_status():
        g = guard()
        if g:
            return g
        ensure()
        with engine.begin() as c:
            jobs = [dict(r._mapping) for r in c.execute(text("SELECT * FROM v140_gc_jobs ORDER BY started_at, resource"))]
            counts = {r[0]: int(r[1]) for r in c.execute(text("SELECT resource, COUNT(*) FROM v140_gc_raw GROUP BY resource"))}
            size = c.execute(text("SELECT COALESCE(SUM(LENGTH(data)),0) FROM v140_gc_raw")).scalar()
        for j in jobs:
            for k in ("started_at", "finished_at"):
                if j.get(k) is not None and hasattr(j[k], "isoformat"):
                    j[k] = j[k].isoformat() + "Z"
        running = bool(_JOB["thread"] and _JOB["thread"].is_alive())
        return jsonify({"ok": True, "running": running, "jobs": jobs, "counts": counts, "bytes": int(size or 0),
                        "configured": configured(), "default": DEFAULT_IMPORT})

    @app.post("/api/gestaoclick/importar")
    @login_required
    def v140_gc_import_start():
        g = guard()
        if g:
            return g
        if not configured():
            return jsonify({"ok": False, "error": "Chave do GestãoClick não configurada no servidor."}), 400
        ensure()
        body = request.get_json(silent=True) or {}
        res = body.get("recursos") or DEFAULT_IMPORT
        res = [str(r).strip().strip("/") for r in res if PATH_RE.match(str(r).strip().strip("/") or "")][:30]
        if not res:
            return jsonify({"ok": False, "error": "Nenhum recurso válido."}), 400
        restart = bool(body.get("recomecar"))
        now = datetime.utcnow()
        with engine.begin() as c:
            for i, r in enumerate(res):
                cur = c.execute(text("SELECT status FROM v140_gc_jobs WHERE resource=:r"), {"r": r}).first()
                if cur is None:
                    c.execute(text("INSERT INTO v140_gc_jobs (resource, status, page, imported, started_at, user_name) "
                                   "VALUES (:r,'fila',0,0,:t,:u)"), {"r": r, "t": now.replace(microsecond=i), "u": H["user_name"]()})
                elif restart or cur[0] == "concluida":
                    c.execute(text("UPDATE v140_gc_jobs SET status='fila', page=0, error=NULL, finished_at=NULL, started_at=:t, user_name=:u "
                                   "WHERE resource=:r"), {"r": r, "t": now.replace(microsecond=i), "u": H["user_name"]()})
                else:
                    c.execute(text("UPDATE v140_gc_jobs SET status='fila', error=NULL WHERE resource=:r"), {"r": r})
        started = start_worker(engine, log)
        try:
            H["audit"]("GESTAOCLICK_IMPORT", "recursos: " + ", ".join(res))
        except Exception:
            pass
        return jsonify({"ok": True, "started": started, "recursos": res})

    @app.post("/api/gestaoclick/importar/parar")
    @login_required
    def v140_gc_import_stop():
        g = guard()
        if g:
            return g
        _JOB["stop"] = True
        ensure()
        with engine.begin() as c:
            c.execute(text("UPDATE v140_gc_jobs SET status='pausada' WHERE status IN ('fila','rodando')"))
        return jsonify({"ok": True})
