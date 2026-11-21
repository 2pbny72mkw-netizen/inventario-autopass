# -*- coding: utf-8 -*-
"""V88.0 REV19 — Paridade Web × Android (base do modelo híbrido, Build119).

1) Login único app → web
   POST /api/mobile/v1/web/code   (Bearer)  → devolve um código de uso único, válido por 60 s, e a URL /m/entrar.
   GET  /m/entrar?c=...&next=/rota          → consome o código, abre a sessão web do mesmo usuário (evento APP_WEB)
                                              e segue para a rota pedida. A sessão web fica marcada como "modo app".
   O código é assinado com a SECRET_KEY, amarrado ao token do aparelho (se o app sair, o código morre) e gravado
   em v109_app_codes para nunca ser usado duas vezes. Jornada controlada vale igual ao login da web.

2) Menu do app pelas permissões
   GET /api/mobile/v1/menu (Bearer) → mesmos grupos e telas do menu da web, filtrados pelas liberações efetivas
   do usuário (mesma regra de can_view). Cada item informa se o app tem tela nativa (native) e se precisa de
   internet (needs_internet). O catálogo não concede acesso: cada tela continua validando no servidor.

3) Modo app
   Quando a sessão foi aberta pelo app, base.html esconde a barra superior da web (o app tem a própria).
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from urllib.parse import quote

CODE_TTL_SECONDS = 60
FULL_ROLES = {"manager", "admin", "adm", "administrator", "administrador", "gestor"}

# Itens: (rótulo, caminho, permissões — basta uma; vazio = todos, chave nativa no app ou None)
CATALOG = [
    ("dashboard", "Dashboard", "dashboard", [
        ("Dashboard Gerencial", "/gerencial", ["dashboard", "field.dashboard", "implantation.dashboard", "finance.dashboard"], None),
    ]),
    ("atividades", "Atividades", "task_alt", [
        ("Central de Atividades", "/atividades", ["tasks.view", "arrow.view", "arrow.manage", "field.inventory", "field.preventive", "implantation.visits", "field.bobbins"], None),
        ("Gestão de Tarefas", "/gestao-tarefas", ["tasks.view"], None),
        ("Minhas atividades Arrow", "/arrow?mine=1#minhas", ["arrow.view"], "arrow"),
        ("Agenda Arrow", "/arrow#agenda", ["arrow.view"], None),
    ]),
    ("field", "Field", "engineering", [
        ("Atividade Bobinas", "/field/bobinas", ["field.bobbins"], "bobinas"),
        ("Estoque Field", "/field/estoque", ["field.bobbins"], "estoque"),
        ("Dashboard Bobinas", "/dashboard/bobinas", ["field.bobbins_dashboard"], None),
        ("Inventário", "/tecnico", ["field.inventory"], "inventario"),
        ("Preventivas", "/preventivas", ["field.preventive"], None),
        ("Equipamentos", "/patrimonio", ["field.equipment"], None),
        ("Evidências", "/evidencias-campo", ["field.evidence"], None),
        ("Visão Panorâmica", "/visao-panoramica", ["field.panorama"], "panoramica"),
        ("Troca de Chips – Recarga", "/troca-chips", ["field.chip_recarga"], None),
        ("Treinamentos", "/field/treinamentos", ["field.training", "field.training.manage"], None),
        ("Mapeamento ATM", "/field/mapeamento-atm", ["field.atm_mapping"], None),
        ("Troca POS Metrô", "/field/troca-pos-metro", ["field.pos_metro"], None),
        ("Firmware POS – CPTM", "/firmware-pos-cptm", ["field.firmware_pos_cptm"], None),
    ]),
    ("implantacao", "Implantação", "construction", [
        ("Implantação de Hardware", "/implantacao-hardware", ["implantation.visits", "implantation.reports"], "implantacao"),
        ("QR Trilhos", "/qr-trilhos", ["implantation.qr.view", "implantation.qr.manage"], None),
        ("Repositório", "/implantacao-hardware/repositorio", ["implantation.repository.view"], None),
        ("Lista de Presença", "/implantacao-hardware/lista-presenca", ["implantation.attendance.view"], None),
        ("Troca de Chips EMV", "/troca-chips-emv", ["implantation.emv"], None),
        ("Troca de Chips Garagem", "/troca-chips-garagem", ["implantation.garage"], None),
    ]),
    ("arrow", "Arrow", "route", [
        ("Gestão Arrow", "/arrow#gestao", ["arrow.manage"], None),
        ("Dashboard Arrow", "/arrow#dashboard", ["arrow.dashboard"], None),
        ("Remoto", "/arrow#remoto", ["arrow.remote"], None),
    ]),
    ("rh", "RH", "groups", [
        ("Equipes", "/equipes", ["teams"], None),
        ("APT", "/rh/apt", ["teams.apt"], None),
        ("Usuários", "/usuarios", ["users.view"], None),
    ]),
    ("portal", "Portal do Cliente", "storefront", [
        ("Portal do Cliente", "/portal-cliente", ["portal.appointments", "portal.receive", "portal.manage"], None),
        ("Gestão de Agendamentos", "/portal-cliente/gestao-agendamentos", ["portal.manage"], None),
        ("Cadastro de Clientes", "/portal-cliente/cadastro-clientes", ["portal.manage"], None),
    ]),
    ("engenharia", "Engenharia e Estoque", "inventory_2", [
        ("Cadastro de Itens", "/engenharia#itens", ["engineering"], None),
        ("Estruturas BOM", "/engenharia#bom", ["engineering"], None),
        ("Estoque Central", "/engenharia/estoque", ["engineering.stock.view"], None),
        ("Controle de TAGs", "/engenharia/tags", ["engineering.tags.view"], None),
    ]),
    ("documentos", "Documentos & Materiais", "folder", [
        ("Dossiê & Materiais", "/documentos-materiais", ["materials"], None),
        ("Raio-X dos Colaboradores", "/documentos-materiais/raio-x", ["materials.dossier.view"], None),
        ("Preparação de Acessos", "/documentos/acessos", ["materials.access_lists.view"], None),
    ]),
    ("gestao", "Gestão", "monitoring", [
        ("Central Operacional", "/central-operacional", ["teams.today"], None),
        ("Inteligência Operacional", "/inteligencia-operacional", ["management.360"], None),
        ("Gestão 360", "/gestao-360", ["management.360"], None),
        ("Notificações", "/notificacoes", ["management.notifications"], None),
        ("Rastreabilidade de Jornada", "/gestao/rastreabilidade-jornada", ["management.gps_history", "management.work_authorizations"], None),
        ("Perfis", "/perfis", ["management.profiles"], None),
        ("Diagnóstico", "/diagnostico", ["management.diagnostics"], None),
        ("Saúde da Plataforma", "/saude-plataforma", ["management.health"], None),
        ("Configurações", "/configuracoes", ["management.settings"], None),
    ]),
    ("financeiro", "Financeiro", "payments", [
        ("Lançamentos", "/financeiro/lancamentos", ["finance.entries", "finance.support", "finance.suppliers"], None),
        ("Caixinha", "/financeiro/caixinha", ["finance.petty_cash.view", "finance.petty_cash.manage"], None),
    ]),
    ("conta", "Minha conta", "person", [
        ("Meus avisos", "/meus-avisos", [], "tela:avisos"),
        ("Meu Perfil", "/meu-perfil", [], "perfil"),
        ("Sobre / Versões", "/sobre", ["about.versions"], None),
    ]),
]


def safe_next(path):
    p = str(path or "").strip()
    if not p.startswith("/") or p.startswith("//") or "\\" in p or "\n" in p or "\r" in p:
        return None
    if p.startswith(("/m/entrar", "/login", "/logout", "/api/")):
        return None
    return p[:500]


def _telas_por_caminho():
    try:
        import v110_specs
        return {t.get("web"): t for t in v110_specs.SPECS if t.get("web")}
    except Exception:
        return {}


def build_menu(access, full, groups, submodules):
    def ok(perm):
        if full:
            return True
        if perm in groups:
            return perm in access or any(x in access for x in groups[perm][1])
        if perm in submodules:
            return perm in access or perm.split(".", 1)[0] in access
        return perm in access

    out = []
    for key, label, icon, items in CATALOG:
        vis = []
        for ilabel, path, perms, native in items:
            if perms and not any(ok(p) for p in perms):
                continue
            if native is None:  # REV20: tela montada pelo motor nativo do app (v110_specs)
                tela = _telas_por_caminho().get(path)
                if tela:
                    native = tela.get("nativa") or ("tela:" + tela["key"])
            vis.append({"label": ilabel, "path": path, "native": native, "needs_internet": native is None})
        if vis:
            out.append({"key": key, "label": label, "icon": icon, "items": vis})
    return out


def install_app_web(app, H):
    from flask import jsonify, redirect, request, session, url_for
    from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

    ser = URLSafeTimedSerializer(app.secret_key, salt="v109-app-web")
    state = {"ready": False}

    def ensure():
        if state["ready"]:
            return
        H["exec"]("""CREATE TABLE IF NOT EXISTS v109_app_codes (
            nonce VARCHAR(40) PRIMARY KEY, user_id INTEGER NOT NULL, used_at TIMESTAMP NOT NULL)""")
        H["commit"]()
        state["ready"] = True

    def is_full(user):
        if H["strict"]():
            return bool(H["is_principal_user"](user))
        return (getattr(user, "role", "") or "").strip().lower() in FULL_ROLES

    @app.post("/api/mobile/v1/web/code")
    @H["mobile_auth_required"]
    def v109_web_code():
        user = request.mobile_user
        data = request.get_json(silent=True) or {}
        nxt = safe_next(data.get("next")) or ""
        tok = H["bearer"]() or ""
        code = ser.dumps({"u": user.id, "n": secrets.token_hex(12), "t": hashlib.sha256(tok.encode()).hexdigest()[:16]})
        url = "/m/entrar?c=" + quote(code, safe="") + ("&next=" + quote(nxt, safe="") if nxt else "")
        return jsonify({"ok": True, "url": url, "expires_in": CODE_TTL_SECONDS})

    @app.get("/m/entrar")
    def v109_app_enter():
        code = request.args.get("c") or ""
        nxt = safe_next(request.args.get("next"))
        try:
            data = ser.loads(code, max_age=CODE_TTL_SECONDS)
        except SignatureExpired:
            return _fail("Link expirado. Volte ao app e toque de novo.")
        except BadSignature:
            return _fail("Link inválido.")
        user = H["get_user"](int(data.get("u") or 0))
        if not user or not user.active or (getattr(user, "personnel_status", None) or "ATIVO").upper() == "INATIVO":
            return _fail("Usuário inativo.")
        if not H["token_alive"](user.id, data.get("t") or ""):
            return _fail("Sessão do app encerrada. Entre de novo no app.")
        ensure()
        try:
            H["exec"]("INSERT INTO v109_app_codes (nonce,user_id,used_at) VALUES (:n,:u,:t)",
                      {"n": str(data.get("n"))[:40], "u": user.id, "t": datetime.utcnow()})
            H["exec"]("DELETE FROM v109_app_codes WHERE used_at < :lim", {"lim": datetime.utcnow() - timedelta(days=1)})
            H["commit"]()
        except Exception:
            H["rollback"]()
            return _fail("Este link já foi usado. Volte ao app e toque de novo.")
        js = H["journey"](user)
        if not js.get("allowed"):
            session.clear()
            session.permanent = True
            session["pending_user_id"] = user.id
            session["pending_user_name"] = user.name
            session["pending_reason"] = js.get("reason") or "FORA_DA_JORNADA"
            session["app_mode"] = 1
            return redirect(url_for("v72_outside_journey_page"))
        H["start_session"](user, "APP_WEB")
        session["app_mode"] = 1
        return redirect(nxt or H["landing"](user))

    def _fail(msg):
        html = ("<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
                "<body style='font-family:system-ui;background:#f3f6fa;color:#16283d;padding:32px'>"
                "<h2 style='font-size:20px'>Não foi possível abrir</h2><p style='font-size:15px'>" + msg + "</p></body>")
        return html, 400

    @app.get("/api/mobile/v1/menu")
    @H["mobile_auth_required"]
    def v109_mobile_menu():
        user = request.mobile_user
        full = is_full(user)
        groups = build_menu(H["access_set"](user), full, H["groups"], H["submodules"])
        return jsonify({"ok": True, "version": "rev19", "base_url": request.host_url.rstrip("/"), "groups": groups})

    @app.context_processor
    def _v109_ctx():
        try:
            return {"app_mode": bool(session.get("app_mode"))}
        except Exception:
            return {"app_mode": False}

    return True
