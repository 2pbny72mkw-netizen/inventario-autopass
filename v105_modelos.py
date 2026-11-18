# -*- coding: utf-8 -*-
"""V88.0 REV16 — Leva e Traz: cadastro de modelos de equipamento (sem gerar versão).

Tela: Portal do Cliente › Gestão de Agendamentos › botão "Modelos de equipamento" (abas Modelos e Padronizar).
O Portal do Cliente passa a ler a lista de modelos ATIVOS daqui (/api/portal/equipment-models).

Tabelas (criadas no primeiro uso, SQL que roda no PostgreSQL e no SQLite):
- v105_equipment_models  : nome (maiúsculas, único), descrição interna, ordem, ativo. Nasce com os 14 modelos de antes.
- v105_model_changes     : cada "Juntar"/"Renomear" com os ids dos equipamentos alterados e o texto anterior (desfazer).
- v105_model_ignored     : textos digitados que o administrador mandou ignorar na padronização.
Regras: só a equipe do Portal (mesma de Gestão de Agendamentos) mexe; modelo já usado não é excluído (só inativado);
renomear/juntar corrige os agendamentos antigos com prévia, auditoria e desfazer. Nada é apagado dos agendamentos.
"""
import json
import re
import threading
from datetime import datetime

DEFAULT_MODELS = ['V770MG', 'V770', 'V3680', 'V3680MG', 'V3695', 'B80', 'BF700', 'BF80',
                  'T80', 'T81', 'T90', 'DK620', 'DK621', 'K4']
EQ = "customer_appointment_equipments"
AP = "customer_appointments"


def norm_name(v):
    return " ".join(str(v or "").upper().split())[:120]


def key(v):
    """Chave de comparação para sugestões: maiúsculas, sem espaço, hífen, ponto, barra."""
    return re.sub(r"[\s\-\./_]+", "", str(v or "").upper())


def install_models(app, H):
    """H: login_required, staff, audit(event, id, detail), sql(q, p)->list[dict], exec(q, p), commit(), rollback(), is_pg()."""
    from flask import jsonify, request, session, abort

    login_required, staff, audit = H["login_required"], H["staff"], H["audit"]
    sql, ex, commit, rollback = H["sql"], H["exec"], H["commit"], H["rollback"]
    st = {"ready": False}
    lock = threading.Lock()

    def ensure():
        if st["ready"]:
            return
        with lock:
            if st["ready"]:
                return
            pk = "SERIAL PRIMARY KEY" if H["is_pg"]() else "INTEGER PRIMARY KEY AUTOINCREMENT"
            existed = True
            try:
                sql("SELECT id FROM v105_equipment_models WHERE 1=0", {})
            except Exception:
                rollback()
                existed = False
            ex(f"""CREATE TABLE IF NOT EXISTS v105_equipment_models (id {pk}, name VARCHAR(120) NOT NULL UNIQUE,
                   description VARCHAR(200), sort_order INTEGER NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1,
                   created_by INTEGER, created_at TIMESTAMP, updated_by INTEGER, updated_at TIMESTAMP)""", {})
            ex(f"""CREATE TABLE IF NOT EXISTS v105_model_changes (id {pk}, kind VARCHAR(20) NOT NULL,
                   old_text VARCHAR(120), new_text VARCHAR(120), equipment_ids TEXT, qty INTEGER NOT NULL DEFAULT 0,
                   model_id INTEGER, created_by INTEGER, created_at TIMESTAMP, undone_by INTEGER, undone_at TIMESTAMP)""", {})
            ex("""CREATE TABLE IF NOT EXISTS v105_model_ignored (text VARCHAR(120) PRIMARY KEY,
                  created_by INTEGER, created_at TIMESTAMP)""", {})
            if not existed:
                now = datetime.utcnow()
                for i, m in enumerate(DEFAULT_MODELS, 1):
                    ex("INSERT INTO v105_equipment_models (name, sort_order, active, created_at) VALUES (:n, :o, 1, :t)",
                       {"n": m, "o": i, "t": now})
            commit()
            st["ready"] = True

    def models(active_only=False):
        q = "SELECT id, name, description, sort_order, active FROM v105_equipment_models"
        if active_only:
            q += " WHERE active = 1"
        return sql(q + " ORDER BY sort_order, name", {})

    def usage():
        rows = sql(f"""SELECT TRIM(e.equipment) AS t, COUNT(*) AS n, COUNT(DISTINCT e.appointment_id) AS ap,
                              MAX(a.created_at) AS last
                       FROM {EQ} e JOIN {AP} a ON a.id = e.appointment_id
                       WHERE e.equipment IS NOT NULL AND TRIM(e.equipment) <> ''
                       GROUP BY TRIM(e.equipment)""", {})
        return {r["t"]: r for r in rows}

    def iso(v):
        if v is None:
            return ""
        return v.isoformat() if hasattr(v, "isoformat") else str(v)[:19]

    def uid():
        return session.get("user_id")

    def ids_with_text(text):
        return [r["id"] for r in sql(f"SELECT id FROM {EQ} WHERE TRIM(equipment) = :t", {"t": text})]

    def set_text(ids, value):
        for i in range(0, len(ids), 500):
            chunk = ids[i:i + 500]
            names = {f"i{k}": v for k, v in enumerate(chunk)}
            ex(f"UPDATE {EQ} SET equipment = :v WHERE id IN ({','.join(':' + k for k in names)})", dict(names, v=value))

    def log_change(kind, old, new, ids, model_id=None):
        ex("""INSERT INTO v105_model_changes (kind, old_text, new_text, equipment_ids, qty, model_id, created_by, created_at)
              VALUES (:k, :o, :n, :ids, :q, :m, :u, :t)""",
           {"k": kind, "o": old, "n": new, "ids": json.dumps(ids), "q": len(ids), "m": model_id, "u": uid(), "t": datetime.utcnow()})

    def get_model(mid):
        r = sql("SELECT id, name, description, sort_order, active FROM v105_equipment_models WHERE id = :i", {"i": mid})
        return r[0] if r else None

    def name_taken(name, except_id=None):
        r = sql("SELECT id FROM v105_equipment_models WHERE name = :n", {"n": name})
        return any(x["id"] != except_id for x in r)

    def fail(msg, code=400):
        return jsonify({"ok": False, "error": msg}), code

    # ---------- Portal do Cliente: lista de modelos ativos ----------
    @app.get("/api/portal/equipment-models")
    @login_required
    def v105_models_public():
        ensure()
        return jsonify({"ok": True, "models": [m["name"] for m in models(active_only=True)]})

    # ---------- Gestão: aba Modelos ----------
    @app.get("/api/portal/equipment-models/admin")
    @login_required
    def v105_models_admin():
        if not staff():
            abort(403)
        ensure()
        use = usage()
        out = []
        for m in models():
            u = use.get(m["name"]) or {}
            out.append({"id": m["id"], "name": m["name"], "description": m["description"] or "", "order": m["sort_order"],
                        "active": bool(m["active"]), "uses": int(u.get("n") or 0), "appointments": int(u.get("ap") or 0),
                        "last": iso(u.get("last"))})
        names = {m["name"] for m in out}
        ignored = {r["text"] for r in sql("SELECT text FROM v105_model_ignored", {})}
        pending = [t for t in use if t not in names and t not in ignored]
        return jsonify({"ok": True, "models": out, "pending": len(pending),
                        "pending_items": sum(int(use[t]["n"]) for t in pending),
                        "total_items": sum(int(r["n"]) for r in use.values())})

    @app.post("/api/portal/equipment-models")
    @login_required
    def v105_models_create():
        if not staff():
            abort(403)
        ensure()
        d = request.get_json(silent=True) or {}
        name = norm_name(d.get("name"))
        if not name:
            return fail("Informe o nome do modelo.")
        if name_taken(name):
            return fail(f"O modelo {name} já existe.", 409)
        order = d.get("order")
        if order in (None, ""):
            r = sql("SELECT MAX(sort_order) AS m FROM v105_equipment_models", {})
            order = int((r[0]["m"] if r else 0) or 0) + 1
        try:
            order = int(order)
        except Exception:
            return fail("Ordem inválida.")
        ex("""INSERT INTO v105_equipment_models (name, description, sort_order, active, created_by, created_at)
              VALUES (:n, :d, :o, :a, :u, :t)""",
           {"n": name, "d": (d.get("description") or "").strip()[:200] or None, "o": order,
            "a": 0 if d.get("active") is False else 1, "u": uid(), "t": datetime.utcnow()})
        commit()
        new_id = sql("SELECT id FROM v105_equipment_models WHERE name = :n", {"n": name})[0]["id"]
        audit("V105_MODELO_CRIADO", new_id, name)
        return jsonify({"ok": True, "id": new_id, "name": name})

    @app.post("/api/portal/equipment-models/<int:mid>")
    @login_required
    def v105_models_update(mid):
        if not staff():
            abort(403)
        ensure()
        cur = get_model(mid)
        if not cur:
            abort(404)
        d = request.get_json(silent=True) or {}
        vals, changed_ids = {}, []
        if "name" in d:
            name = norm_name(d.get("name"))
            if not name:
                return fail("Informe o nome do modelo.")
            if name != cur["name"]:
                if name_taken(name, mid):
                    return fail(f"Já existe o modelo {name}. Para unir os dois, inative um deles e use Padronizar.", 409)
                vals["name"] = name
                changed_ids = ids_with_text(cur["name"])
                if d.get("preview"):
                    return jsonify({"ok": True, "preview": True, "items": len(changed_ids)})
        if "description" in d:
            vals["description"] = (d.get("description") or "").strip()[:200] or None
        if "order" in d:
            try:
                vals["sort_order"] = int(d.get("order"))
            except Exception:
                return fail("Ordem inválida.")
        if "active" in d:
            vals["active"] = 1 if d.get("active") else 0
        if not vals:
            return jsonify({"ok": True, "unchanged": True})
        try:
            sets = ", ".join(f"{k} = :{k}" for k in vals)
            ex(f"UPDATE v105_equipment_models SET {sets}, updated_by = :u, updated_at = :t WHERE id = :i",
               dict(vals, u=uid(), t=datetime.utcnow(), i=mid))
            if "name" in vals and changed_ids:
                set_text(changed_ids, vals["name"])
                log_change("RENOMEAR", cur["name"], vals["name"], changed_ids, mid)
            commit()
        except Exception:
            rollback()
            raise
        what = []
        if "name" in vals:
            what.append(f'nome {cur["name"]} → {vals["name"]} ({len(changed_ids)} equipamento(s) corrigidos)')
        if "active" in vals:
            what.append("ativado" if vals["active"] else "inativado")
        if "sort_order" in vals:
            what.append(f'ordem {vals["sort_order"]}')
        if "description" in vals:
            what.append("descrição")
        audit("V105_MODELO_ALTERADO", mid, f'{cur["name"]}: ' + ", ".join(what))
        return jsonify({"ok": True, "items": len(changed_ids)})

    @app.post("/api/portal/equipment-models/<int:mid>/excluir")
    @login_required
    def v105_models_delete(mid):
        if not staff():
            abort(403)
        ensure()
        cur = get_model(mid)
        if not cur:
            abort(404)
        n = len(ids_with_text(cur["name"]))
        if n:
            return fail(f"{cur['name']} já foi usado em {n} equipamento(s). Inative em vez de excluir.", 409)
        ex("DELETE FROM v105_equipment_models WHERE id = :i", {"i": mid})
        commit()
        audit("V105_MODELO_EXCLUIDO", mid, cur["name"])
        return jsonify({"ok": True})

    # ---------- Gestão: aba Padronizar ----------
    @app.get("/api/portal/equipment-models/padronizar")
    @login_required
    def v105_std_list():
        if not staff():
            abort(403)
        ensure()
        ms = models()
        names = {m["name"] for m in ms}
        bykey = {}
        for m in ms:
            bykey.setdefault(key(m["name"]), m)
        ignored = {r["text"] for r in sql("SELECT text FROM v105_model_ignored", {})}
        items = []
        for t, u in usage().items():
            if t in names or t in ignored:
                continue
            sug = bykey.get(key(t))
            if not sug:  # prefixo único: "dk" → DK620/DK621 vira sugestão só se houver um único modelo que começa com o texto
                cands = [m for m in ms if key(m["name"]).startswith(key(t))] if len(key(t)) >= 2 else []
                options = [c["name"] for c in cands]
            else:
                options = [sug["name"]]
            items.append({"text": t, "items": int(u["n"]), "appointments": int(u["ap"]), "last": iso(u.get("last")),
                          "suggestion": sug["name"] if sug else "", "suggestion_id": sug["id"] if sug else None,
                          "safe": bool(sug), "options": options})
        items.sort(key=lambda x: (-x["items"], x["text"]))
        hist = sql("""SELECT id, kind, old_text, new_text, qty, created_at, undone_at FROM v105_model_changes
                      ORDER BY id DESC LIMIT 30""", {})
        return jsonify({"ok": True, "items": items, "ignored": sorted(ignored),
                        "history": [{"id": h["id"], "kind": h["kind"], "old": h["old_text"], "new": h["new_text"], "qty": h["qty"],
                                     "at": iso(h["created_at"]), "undone": bool(h["undone_at"])} for h in hist]})

    @app.post("/api/portal/equipment-models/padronizar/juntar")
    @login_required
    def v105_std_join():
        """{items:[{text, model_id}], preview: bool}. Corrige o texto dos equipamentos para o nome do modelo."""
        if not staff():
            abort(403)
        ensure()
        d = request.get_json(silent=True) or {}
        reqs = d.get("items") or []
        if not reqs:
            return fail("Nada selecionado.")
        plan = []
        for it in reqs:
            text = str(it.get("text") or "").strip()
            m = get_model(int(it.get("model_id") or 0)) if str(it.get("model_id") or "").isdigit() else None
            if not text or not m:
                return fail(f"Escolha o modelo para “{text or '?'}”.")
            if text == m["name"]:
                continue
            ids = ids_with_text(text)
            plan.append({"text": text, "model": m["name"], "model_id": m["id"], "ids": ids})
        if d.get("preview"):
            return jsonify({"ok": True, "preview": [{"text": p["text"], "model": p["model"], "items": len(p["ids"])} for p in plan]})
        try:
            for p in plan:
                if p["ids"]:
                    set_text(p["ids"], p["model"])
                    log_change("JUNTAR", p["text"], p["model"], p["ids"], p["model_id"])
            commit()
        except Exception:
            rollback()
            raise
        for p in plan:
            audit("V105_PADRONIZADO", p["model_id"], f'“{p["text"]}” → {p["model"]} ({len(p["ids"])} equipamento(s))')
        return jsonify({"ok": True, "done": [{"text": p["text"], "model": p["model"], "items": len(p["ids"])} for p in plan]})

    @app.post("/api/portal/equipment-models/padronizar/criar")
    @login_required
    def v105_std_create():
        """Cria um modelo a partir do texto digitado e já junta esse texto a ele."""
        if not staff():
            abort(403)
        ensure()
        d = request.get_json(silent=True) or {}
        text = str(d.get("text") or "").strip()
        name = norm_name(d.get("name") or text)
        if not text or not name:
            return fail("Texto inválido.")
        if name_taken(name):
            return fail(f"O modelo {name} já existe: use Juntar.", 409)
        try:
            r = sql("SELECT MAX(sort_order) AS m FROM v105_equipment_models", {})
            ex("""INSERT INTO v105_equipment_models (name, sort_order, active, created_by, created_at)
                  VALUES (:n, :o, 1, :u, :t)""",
               {"n": name, "o": int((r[0]["m"] if r else 0) or 0) + 1, "u": uid(), "t": datetime.utcnow()})
            mid = sql("SELECT id FROM v105_equipment_models WHERE name = :n", {"n": name})[0]["id"]
            ids = ids_with_text(text) if text != name else []
            if ids:
                set_text(ids, name)
                log_change("CRIAR", text, name, ids, mid)
            commit()
        except Exception:
            rollback()
            raise
        audit("V105_MODELO_CRIADO", mid, f'{name} (a partir de “{text}”, {len(ids)} equipamento(s))')
        return jsonify({"ok": True, "id": mid, "name": name, "items": len(ids)})

    @app.post("/api/portal/equipment-models/padronizar/ignorar")
    @login_required
    def v105_std_ignore():
        if not staff():
            abort(403)
        ensure()
        d = request.get_json(silent=True) or {}
        text = str(d.get("text") or "").strip()[:120]
        if not text:
            return fail("Texto inválido.")
        if d.get("undo"):
            ex("DELETE FROM v105_model_ignored WHERE text = :t", {"t": text})
        elif not sql("SELECT text FROM v105_model_ignored WHERE text = :t", {"t": text}):
            ex("INSERT INTO v105_model_ignored (text, created_by, created_at) VALUES (:t, :u, :n)",
               {"t": text, "u": uid(), "n": datetime.utcnow()})
        commit()
        audit("V105_PADRONIZAR_IGNORADO" if not d.get("undo") else "V105_PADRONIZAR_REATIVADO", 0, text)
        return jsonify({"ok": True})

    @app.post("/api/portal/equipment-models/padronizar/desfazer/<int:cid>")
    @login_required
    def v105_std_undo(cid):
        """Volta o texto original só nos equipamentos que ainda estão com o texto aplicado."""
        if not staff():
            abort(403)
        ensure()
        r = sql("SELECT * FROM v105_model_changes WHERE id = :i", {"i": cid})
        if not r or r[0]["undone_at"]:
            abort(404)
        c = r[0]
        ids = json.loads(c["equipment_ids"] or "[]")
        try:
            still = [x["id"] for x in sql(f"SELECT id, equipment FROM {EQ} WHERE TRIM(equipment) = :n", {"n": c["new_text"]})
                     if x["id"] in set(ids)]
            set_text(still, c["old_text"])
            if c["kind"] == "RENOMEAR" and c["model_id"] and not name_taken(c["old_text"], c["model_id"]):
                ex("UPDATE v105_equipment_models SET name = :n, updated_by = :u, updated_at = :t WHERE id = :i",
                   {"n": c["old_text"], "u": uid(), "t": datetime.utcnow(), "i": c["model_id"]})
            ex("UPDATE v105_model_changes SET undone_by = :u, undone_at = :t WHERE id = :i",
               {"u": uid(), "t": datetime.utcnow(), "i": cid})
            commit()
        except Exception:
            rollback()
            raise
        audit("V105_PADRONIZACAO_DESFEITA", cid, f'{c["new_text"]} → “{c["old_text"]}” ({len(still)} de {len(ids)} equipamento(s))')
        return jsonify({"ok": True, "items": len(still), "of": len(ids)})
