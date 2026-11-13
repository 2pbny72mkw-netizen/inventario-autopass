# -*- coding: utf-8 -*-
"""V88.0 REV13 — Limpeza do banco (T-Report e Chamados), aposentadoria de telas e fim do polling de importação TopDesk.

- Tela "Limpeza do banco" (/diagnostico/limpeza-banco, só o Gestor com acesso ao Diagnóstico): prévia com linhas e MB,
  confirmação digitada, e TRUNCATE (devolve o espaço na hora; não precisa VACUUM FULL). Cada limpeza vai para a auditoria.
- Menu: tira os links de Chamados, Apuração, Coleta de Valores e Monitoramento de Coletas (as rotas continuam existindo, sem dados).
- /api/topdesk/import/active (8,5 mil chamadas/30 dias, 3,4 consultas cada) responde sem tocar no banco quando não houve importação neste processo.
"""
import json
import re
import time
from datetime import datetime

TARGETS = {
    "treport": {
        "label": "T-Report (transações de ATM)",
        "confirm": "APAGAR T-REPORT",
        "tables": ("financial_atm_transactions", "financial_atm_daily_summary"),
        "note": "Apaga todas as transações e o consolidado diário. Apuração, Coleta de Valores e Monitoramento de Coletas ficam sem o \"valor do sistema\" (telas aposentadas do menu). "
                "Lançamentos, Caixinha e Fornecedores não dependem disso.",
    },
    "chamados": {
        "label": "Chamados (TopDesk)",
        "confirm": "APAGAR CHAMADOS",
        "tables": ("topdesk_activities", "topdesk_tickets"),
        "note": "Apaga todos os chamados e suas atividades. Contadores de chamados em dashboards e na busca passam a zero.",
    },
}

RETIRED_HREFS = ("/trabalho", "/topdesk", "/financeiro/coleta-valores", "/financeiro/monitoramento-coletas", "/financeiro/apuracao")
_ANCHOR = re.compile(r'<a\b[^>]*\bhref="(?:%s)(?:[/?#][^"]*)?"[^>]*>.*?</a>' % "|".join(re.escape(h) for h in RETIRED_HREFS), re.S | re.I)
_LAST_IMPORT = {"at": 0.0}


def retire_menu_links(html):
    """Remove os links aposentados do HTML do menu. Devolve (html, quantidade)."""
    return _ANCHOR.subn("", html)


def install_cleanup(app, db, text, H):
    from flask import jsonify, request, render_template, abort, session
    login_required, guard, audit = H["login_required"], H["guard"], H["audit"]

    def sizes(conn, tables):
        out = {}
        for t in tables:
            ok = conn.execute(text("SELECT to_regclass(:t) IS NOT NULL"), {"t": t}).scalar()
            if not ok:
                out[t] = {"exists": False, "rows": 0, "mb": 0.0}
                continue
            n = int(conn.execute(text("SELECT COUNT(*) FROM " + t)).scalar() or 0)
            b = int(conn.execute(text("SELECT pg_total_relation_size(CAST(:t AS regclass))"), {"t": t}).scalar() or 0)
            out[t] = {"exists": True, "rows": n, "mb": round(b / 1048576.0, 1)}
        return out

    @app.get("/diagnostico/limpeza-banco")
    @login_required
    def v101_cleanup_page():
        if guard():
            abort(403)
        return render_template("limpeza_banco.html", app_release=H["release"]())

    @app.get("/api/diagnostico/limpeza/v101/plano")
    @login_required
    def v101_cleanup_plan():
        g = guard()
        if g:
            return g
        if not H["is_pg"]():
            return jsonify({"ok": False, "error": "Disponível apenas no PostgreSQL."}), 400
        with db.engine.connect() as conn:
            alvos = []
            for k, t in TARGETS.items():
                s = sizes(conn, t["tables"])
                alvos.append({"id": k, "label": t["label"], "confirm": t["confirm"], "note": t["note"],
                              "rows": sum(x["rows"] for x in s.values()), "mb": round(sum(x["mb"] for x in s.values()), 1), "tables": s})
            total = int(conn.execute(text("SELECT pg_database_size(current_database())")).scalar() or 0)
        return jsonify({"ok": True, "alvos": alvos, "banco_mb": round(total / 1048576.0, 1)})

    @app.post("/api/diagnostico/limpeza/v101/executar")
    @login_required
    def v101_cleanup_run():
        g = guard()
        if g:
            return g
        if not H["is_pg"]():
            return jsonify({"ok": False, "error": "Disponível apenas no PostgreSQL."}), 400
        d = request.get_json(silent=True) or {}
        t = TARGETS.get(str(d.get("alvo") or ""))
        if not t:
            return jsonify({"ok": False, "error": "Alvo inválido."}), 400
        if not d.get("backup_ok"):
            return jsonify({"ok": False, "error": "Confirme que existe backup recente do banco (pg_dump)."}), 400
        if str(d.get("confirmation") or "").strip().upper() != t["confirm"]:
            return jsonify({"ok": False, "error": "Digite exatamente: " + t["confirm"]}), 400
        try:
            with db.engine.begin() as conn:
                conn.execute(text("SET LOCAL lock_timeout = '20s'"))
                before = sizes(conn, t["tables"])
                existing = [x for x in t["tables"] if before[x]["exists"]]
                if existing:
                    conn.execute(text("TRUNCATE TABLE " + ", ".join(existing) + " RESTART IDENTITY"))
                if d.get("alvo") == "treport":
                    if conn.execute(text("SELECT to_regclass('financial_atm_summary_meta') IS NOT NULL")).scalar():
                        conn.execute(text("INSERT INTO financial_atm_summary_meta(id,source_count,source_max_id,refreshed_at,status) VALUES(1,0,0,CURRENT_TIMESTAMP,'READY') "
                                          "ON CONFLICT(id) DO UPDATE SET source_count=0,source_max_id=0,refreshed_at=CURRENT_TIMESTAMP,status='READY'"))
                after = sizes(conn, t["tables"])
            try:
                with db.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as c2:
                    for x in existing:
                        c2.execute(text("ANALYZE " + x))
            except Exception:
                pass
            freed = round(sum(before[x]["mb"] for x in existing) - sum(after[x]["mb"] for x in existing), 1)
            rows = sum(before[x]["rows"] for x in existing)
            audit(d.get("alvo"), rows, freed)
            H["after_purge"]()
            return jsonify({"ok": True, "alvo": d.get("alvo"), "linhas_apagadas": rows, "mb_liberados": freed, "antes": before, "depois": after})
        except Exception as exc:
            app.logger.exception("REV13 limpeza")
            return jsonify({"ok": False, "error": "Não foi possível limpar: " + str(exc)[:200]}), 500

    # --- importação TopDesk: sem polling no banco ---
    @app.before_request
    def v101_topdesk_poll():
        p = request.path
        if p == "/api/topdesk/import/active" and request.method == "GET":
            if time.time() - _LAST_IMPORT["at"] > 3600 and session.get("user_id"):
                r = jsonify({"ok": True, "active": False})
                r.headers["Cache-Control"] = "no-store"
                r.headers["X-Autopass-Poll"] = "skip"
                return r
        elif p == "/topdesk/import" and request.method == "POST":
            _LAST_IMPORT["at"] = time.time()
        return None

    # --- menu: tira telas aposentadas e põe o link da limpeza no Diagnóstico ---
    @app.after_request
    def v101_menu(response):
        if response.status_code != 200 or response.mimetype != "text/html" or response.direct_passthrough:
            return response
        if request.path.startswith("/api/") or not session.get("user_id"):
            return response
        try:
            html = response.get_data(as_text=True)
        except Exception:
            return response
        changed = False
        if 'href="/' in html:
            new, n = retire_menu_links(html)
            if n:
                html, changed = new, True
        if request.path == "/diagnostico" and "data-v101-clean" not in html and guard() is None:
            m = re.search(r"</h1>", html)
            if m:
                link = ('<p><a class="btn" data-v101-clean="1" href="/diagnostico/limpeza-banco" style="display:inline-block;margin:8px 0">'
                        'Limpeza do banco (T-Report e Chamados)</a></p>')
                html, changed = html[:m.end()] + link + html[m.end():], True
        if changed:
            response.set_data(html)
        return response

    return None
