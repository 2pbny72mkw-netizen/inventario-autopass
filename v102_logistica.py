# -*- coding: utf-8 -*-
"""V88.0 REV14 — Leva e Traz: atividade avulsa por dia, com motorista.

Uma atividade avulsa é um serviço do dia que não nasce de agendamento do cliente
(ex.: buscar peças no fornecedor, levar documento à garagem X). Ela aparece no
calendário operacional, na janela do dia e na mensagem de WhatsApp do motorista.

Regras:
- Só a equipe do Portal (recebimento/gestão; não o motorista) cria, altera, conclui e exclui.
- Data bloqueada no calendário não aceita atividade nova nem mudança para ela.
- Motorista: um dos motoristas do Leva e Traz (usuário com a liberação ou avulso), gravado com o nome
  do momento (se o cadastro do motorista for removido, a atividade continua legível).
- Excluir = marcar CANCELADA (fica no banco e na auditoria). Nada é apagado.
"""
from datetime import date, datetime

STATUSES = ("PENDENTE", "CONCLUIDA", "CANCELADA")


def install_adhoc(app, db, H):
    from flask import jsonify, request, session, abort

    login_required, staff, drivers, audit, is_blocked = H["login_required"], H["staff"], H["drivers"], H["audit"], H["is_blocked"]
    state = {"t": None}

    def table():
        if state["t"] is not None:
            return state["t"]
        t = db.Table(
            "v102_logistics_adhoc", db.metadata,
            db.Column("id", db.Integer, primary_key=True),
            db.Column("activity_date", db.Date, nullable=False, index=True),
            db.Column("title", db.String(160), nullable=False),
            db.Column("place", db.String(200)),
            db.Column("time_hint", db.String(20)),
            db.Column("driver_key", db.String(20)),
            db.Column("driver_name", db.String(120)),
            db.Column("notes", db.Text),
            db.Column("status", db.String(20), nullable=False, default="PENDENTE", index=True),
            db.Column("created_by", db.Integer),
            db.Column("created_at", db.DateTime, nullable=False, default=datetime.utcnow),
            db.Column("updated_by", db.Integer),
            db.Column("updated_at", db.DateTime),
            extend_existing=True,
        )
        t.create(bind=db.engine, checkfirst=True)
        state["t"] = t
        return t

    def as_dict(r):
        return {
            "id": r.id, "date": r.activity_date.isoformat() if r.activity_date else "",
            "title": r.title or "", "place": r.place or "", "time": r.time_hint or "",
            "driver_key": r.driver_key or "", "driver_name": r.driver_name or "",
            "notes": r.notes or "", "status": r.status or "PENDENTE",
        }

    def month_range(raw):
        try:
            y, m = [int(x) for x in str(raw).split("-", 1)]
            start = date(y, m, 1)
        except Exception:
            t = date.today()
            start = date(t.year, t.month, 1)
        end = date(start.year + 1, 1, 1) if start.month == 12 else date(start.year, start.month + 1, 1)
        return start, end

    def clean(data, partial=False):
        """Valida o corpo. Devolve (valores, erro)."""
        out = {}
        if not partial or "date" in data:
            try:
                out["activity_date"] = date.fromisoformat(str(data.get("date") or "")[:10])
            except Exception:
                return None, "Informe a data da atividade."
            if is_blocked(out["activity_date"]):
                return None, "A data está bloqueada no calendário operacional."
        if not partial or "title" in data:
            title = (data.get("title") or "").strip()[:160]
            if not title:
                return None, "Descreva a atividade (o que o motorista vai fazer)."
            out["title"] = title
        for k, col, n in (("place", "place", 200), ("time", "time_hint", 20)):
            if not partial or k in data:
                out[col] = (data.get(k) or "").strip()[:n] or None
        if not partial or "notes" in data:
            out["notes"] = (data.get("notes") or "").strip()[:1000] or None
        if not partial or "driver_key" in data:
            key = (data.get("driver_key") or "").strip()[:20]
            if key:
                d = next((x for x in drivers() if x.get("key") == key), None)
                if not d:
                    return None, "Motorista não encontrado. Atualize a tela e escolha de novo."
                out["driver_key"], out["driver_name"] = key, d.get("name") or ""
            else:
                out["driver_key"], out["driver_name"] = None, None
        if "status" in data:
            st = str(data.get("status") or "").upper()
            if st not in ("PENDENTE", "CONCLUIDA"):
                return None, "Situação inválida."
            out["status"] = st
        return out, None

    @app.get("/api/portal/logistics/adhoc")
    @login_required
    def v102_adhoc_list():
        if not staff():
            abort(403)
        t = table()
        start, end = month_range(request.args.get("month"))
        with db.engine.connect() as c:
            rows = c.execute(
                t.select().where(t.c.activity_date >= start, t.c.activity_date < end, t.c.status != "CANCELADA")
                .order_by(t.c.activity_date, t.c.time_hint, t.c.id)
            ).fetchall()
        return jsonify({"ok": True, "items": [as_dict(r) for r in rows]})

    @app.post("/api/portal/logistics/adhoc")
    @login_required
    def v102_adhoc_create():
        if not staff():
            abort(403)
        t = table()
        vals, err = clean(request.get_json(silent=True) or {})
        if err:
            return jsonify({"ok": False, "error": err}), (409 if "bloqueada" in err else 400)
        vals.update(status="PENDENTE", created_by=session.get("user_id"), created_at=datetime.utcnow())
        with db.engine.begin() as c:
            new_id = c.execute(t.insert().values(**vals)).inserted_primary_key[0]
        audit("V102_ADHOC_CREATED", new_id, f'{vals["activity_date"].isoformat()} · {vals["title"]}' + (f' · motorista: {vals["driver_name"]}' if vals.get("driver_name") else ""))
        return jsonify({"ok": True, "id": new_id})

    @app.post("/api/portal/logistics/adhoc/<int:aid>")
    @login_required
    def v102_adhoc_update(aid):
        if not staff():
            abort(403)
        t = table()
        with db.engine.connect() as c:
            cur = c.execute(t.select().where(t.c.id == aid)).fetchone()
        if not cur or cur.status == "CANCELADA":
            abort(404)
        prev_status, prev_date, prev_title = cur.status, cur.activity_date, cur.title
        data = request.get_json(silent=True) or {}
        # Concluir/reabrir não deve esbarrar no bloqueio da data já gravada.
        if "date" in data and str(data.get("date"))[:10] == prev_date.isoformat():
            data = {k: v for k, v in data.items() if k != "date"}
        vals, err = clean(data, partial=True)
        if err:
            return jsonify({"ok": False, "error": err}), (409 if "bloqueada" in err else 400)
        if not vals:
            return jsonify({"ok": True, "unchanged": True})
        vals.update(updated_by=session.get("user_id"), updated_at=datetime.utcnow())
        with db.engine.begin() as c:
            c.execute(t.update().where(t.c.id == aid).values(**vals))
        what = "CONCLUIDA" if vals.get("status") == "CONCLUIDA" else ("REABERTA" if vals.get("status") == "PENDENTE" and prev_status == "CONCLUIDA" else "ALTERADA")
        audit("V102_ADHOC_" + what, aid, f'{(vals.get("activity_date") or prev_date).isoformat()} · {vals.get("title") or prev_title}')
        return jsonify({"ok": True})

    @app.post("/api/portal/logistics/adhoc/<int:aid>/excluir")
    @login_required
    def v102_adhoc_delete(aid):
        if not staff():
            abort(403)
        t = table()
        with db.engine.begin() as c:
            cur = c.execute(t.select().where(t.c.id == aid)).fetchone()
            if not cur or cur.status == "CANCELADA":
                abort(404)
            c.execute(t.update().where(t.c.id == aid).values(status="CANCELADA", updated_by=session.get("user_id"), updated_at=datetime.utcnow()))
        audit("V102_ADHOC_CANCELLED", aid, f'{cur.activity_date.isoformat()} · {cur.title}')
        return jsonify({"ok": True})
