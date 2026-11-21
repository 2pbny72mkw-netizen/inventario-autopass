# -*- coding: utf-8 -*-
"""V88.0 REV20 — Motor de telas do app Android (Build120): web e app trocam só dados.

1) Ponte de dados  /api/mobile/v1/ponte/<caminho>   (Bearer do app)
   Executa a API da web (mesma regra de negócio, mesma permissão, mesma jornada) como o usuário do aparelho e
   devolve SÓ DADOS: JSON, arquivo (Excel/PDF/foto) ou, para formulários da web que respondem com redirecionamento,
   um JSON {ok, mensagens}. Página HTML nunca é devolvida (406). Nada de cookie/sessão web vai para o aparelho.

2) Telas  /api/mobile/v1/telas   (Bearer)
   Descrição das telas que o app monta com os 5 modelos nativos (lista, detalhe, formulário, painel, cadastro),
   filtrada pelas liberações do usuário. As descrições ficam em v110_specs.py: tela nova ou alterada chega ao app
   sem gerar Build novo.
"""
import hashlib
import io
import json

DENY_PREFIXES = ("/api/mobile/", "/login", "/logout", "/m/entrar", "/static/")
FILE_TYPES = ("application/vnd.", "application/pdf", "application/octet-stream", "image/", "text/csv", "application/zip")
FULL_ROLES = {"manager", "admin", "adm", "administrator", "administrador", "gestor"}


def allowed_target(path):
    p = "/" + str(path or "").lstrip("/")
    if "\\" in p or "\n" in p or "\r" in p or "/../" in p or p.endswith("/.."):
        return None
    if p.startswith(DENY_PREFIXES):
        return None
    return p


def perm_ok(perm, access, full, groups, submodules):
    if full:
        return True
    if perm in groups:
        return perm in access or any(x in access for x in groups[perm][1])
    if perm in submodules:
        return perm in access or perm.split(".", 1)[0] in access
    return perm in access


def screens_for(specs, access, full, groups, submodules):
    out = []
    for s in specs:
        perms = s.get("perms") or []
        if perms and not any(perm_ok(p, access, full, groups, submodules) for p in perms):
            continue
        out.append(s)
    return out


def specs_version(specs):
    return hashlib.sha1(json.dumps(specs, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:12]


def install_telas(app, H):
    from flask import jsonify, request, session
    import v110_specs

    def is_full(user):
        if H["strict"]():
            return bool(H["is_principal_user"](user))
        return (getattr(user, "role", "") or "").strip().lower() in FULL_ROLES

    @app.route("/api/mobile/v1/ponte/<path:alvo>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    @H["mobile_auth_required"]
    def v110_ponte(alvo):
        user = request.mobile_user
        target = allowed_target(alvo)
        if not target:
            return jsonify({"ok": False, "error": "Caminho não permitido."}), 403
        body = request.get_data(cache=True)
        env = dict(request.environ)
        env["PATH_INFO"] = target
        env["SCRIPT_NAME"] = ""
        env["wsgi.input"] = io.BytesIO(body)
        env["CONTENT_LENGTH"] = str(len(body))
        for k in ("HTTP_COOKIE", "HTTP_AUTHORIZATION"):
            env.pop(k, None)
        env["HTTP_ACCEPT"] = "application/json"
        # Android não envia PATCH: o app manda POST + X-HTTP-Method-Override
        ov = (request.headers.get("X-HTTP-Method-Override") or "").upper()
        if request.method == "POST" and ov in ("PATCH", "PUT", "DELETE"):
            env["REQUEST_METHOD"] = ov
        env.pop("HTTP_X_HTTP_METHOD_OVERRIDE", None)
        env["HTTP_X_SISTEMA_GESTAO_APP"] = "1"
        with app.app_context():  # contexto próprio: banco, g e cache de permissões isolados
            with app.request_context(env):
                session.clear()
                session.update(user_id=user.id, name=user.name, role=user.role, app_mode=1, via_app=1)
                resp = app.full_dispatch_request()
                flashes = list(session.get("_flashes") or [])
        resp.headers.pop("Set-Cookie", None)
        ctype = (resp.mimetype or "").lower()
        msgs = [m[1] if isinstance(m, (list, tuple)) and len(m) > 1 else str(m) for m in flashes]
        if 300 <= resp.status_code < 400:
            loc = resp.headers.get("Location", "")
            if "/login" in loc or "fora-da-jornada" in loc or "outside" in loc:
                return jsonify({"ok": False, "error": "Sessão fora da jornada ou sem acesso.", "mensagens": msgs}), 403
            erro = any(isinstance(m, (list, tuple)) and str(m[0]) in ("error", "danger", "erro") for m in flashes)
            return jsonify({"ok": not erro, "mensagens": msgs, "destino": loc}), (400 if erro else 200)
        if ctype == "application/json" or ctype.startswith(FILE_TYPES):
            return resp
        if resp.status_code >= 400:
            return jsonify({"ok": False, "error": "HTTP %d" % resp.status_code, "mensagens": msgs}), resp.status_code
        return jsonify({"ok": False, "error": "Esta função da web ainda não tem versão em dados.", "mensagens": msgs}), 406

    # REV22 — listas em dados para telas que na web só existiam como página (usadas pelo app via ponte)
    def _guard(*perms):
        if not session.get("user_id"):
            return jsonify({"ok": False, "error": "Sessão necessária."}), 401
        if not any(H["has_access"](p) for p in perms):
            return jsonify({"ok": False, "error": "Sem permissão."}), 403
        return None

    @app.get("/api/v110/usuarios")
    def v110_usuarios():
        g = _guard("users.view")
        if g:
            return g
        rows = H["sql"]("""SELECT u.id, u.name, u.username, u.role, u.company, u.job_title, u.email, u.phone, u.active,
                                  u.personnel_status, u.work_schedule_type, u.work_shift, u.admission_date, p.name AS profile
                           FROM users u LEFT JOIN system_profiles p ON p.id = u.system_profile_id
                           WHERE u.archived_at IS NULL ORDER BY u.name""")
        for r in rows:
            for k, v in list(r.items()):
                if hasattr(v, "isoformat"):
                    r[k] = v.isoformat()
            r["active"] = bool(r.get("active"))
        return jsonify({"ok": True, "rows": rows})

    @app.get("/api/v110/perfis")
    def v110_perfis():
        g = _guard("management.profiles", "users.view")
        if g:
            return g
        rows = H["sql"]("""SELECT p.id, p.name, p.base_role, p.active, p.access_json,
                                  (SELECT COUNT(*) FROM users u WHERE u.system_profile_id = p.id AND u.archived_at IS NULL) AS users
                           FROM system_profiles p ORDER BY p.name""")
        labels = H.get("labels") or {}
        for r in rows:
            try:
                acc = json.loads(r.pop("access_json") or "[]")
            except Exception:
                acc = []
            r["active"] = bool(r.get("active"))
            r["permissoes"] = len(acc) if isinstance(acc, list) else 0
            r["liberacoes"] = [{"chave": a, "nome": labels.get(a, a)} for a in (acc if isinstance(acc, list) else []) if isinstance(a, str)]
        return jsonify({"ok": True, "rows": rows})

    @app.get("/api/v110/pos-metro")
    def v110_pos_metro():
        g = _guard("field.pos_metro")
        if g:
            return g
        rows = H["sql"]("""SELECT p.id, p.client, p.line, p.station, p.terminal, p.terminal_number, p.model, p.manufacturer,
                                  p.serial, p.asset, p.status, p.installed_on,
                                  (SELECT COUNT(*) FROM v876_pos_metro_photos f JOIN v874_pos_metro_events e ON e.id = f.event_id
                                    WHERE e.pos_id = p.id) AS fotos
                           FROM v874_pos_metro p ORDER BY p.line, p.station, p.terminal""")
        for r in rows:
            if hasattr(r.get("installed_on"), "isoformat"):
                r["installed_on"] = r["installed_on"].isoformat()
            num = str(r.get("terminal_number") or "").strip()
            if not num:
                import re as _re
                m = _re.search(r"(\d+)$", str(r.get("terminal") or ""))
                num = m.group(1) if m else ""
            r["numero"] = num
        return jsonify({"ok": True, "rows": rows})

    @app.get("/api/mobile/v1/telas")
    @H["mobile_auth_required"]
    def v110_telas():
        user = request.mobile_user
        specs = v110_specs.SPECS
        mine = screens_for(specs, H["access_set"](user), is_full(user), H["groups"], H["submodules"])
        return jsonify({"ok": True, "versao": specs_version(specs), "telas": mine,
                        "app": {"ultimo_build": getattr(v110_specs, "APP_ULTIMO_BUILD", 0)}})

    return True
