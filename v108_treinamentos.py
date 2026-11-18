# -*- coding: utf-8 -*-
"""V88.0 REV18 — Field › Treinamentos dos técnicos (substitui a planilha informal).

Tela /field/treinamentos: matriz técnico × tipo de treinamento, filtros, KPIs clicáveis, registrar para um ou vários
técnicos (turma), editar/excluir, tipos editáveis (sem gerar versão, validade opcional), exportar Excel (matriz e lista)
e importar a planilha atual com prévia.

Tabelas (criadas no primeiro uso; SQL que roda no PostgreSQL e no SQLite):
- v108_training_types   : nome único, ordem, validade em meses (opcional), ativo. Nasce com os 11 tipos da planilha.
- v108_training_records : técnico (users.id), tipo, data realizada, aplicado por, observação, origem; exclusão lógica.
Liberações: field.training (ver/exportar) e field.training.manage (registrar, editar, excluir, tipos, importar).
"""
import io
import json
import re
import threading
import unicodedata
from datetime import date, datetime, timedelta

DEFAULT_TYPES = ["Treinamento", "POS", "Validadores", "Rack", "ATM", "Imagem", "Access Point", "Vivo Box",
                 "Programas", "Crimpagem", "Pendrive"]
ALIASES = {"ACESSPOINT": "Access Point", "ACCESSPOINT": "Access Point", "VIVOBOX": "Vivo Box", "VALIDADOR": "Validadores"}
TECH_ROLES = ("technician", "technician_implantation")
MIN_DATE = date(2020, 1, 1)


def fold(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode()
    return " ".join(s.lower().split())


def tkey(s):
    return re.sub(r"[^A-Z0-9]", "", fold(s).upper())


def parse_date(v, today):
    """Aceita date/datetime ou texto dd/mm/aaaa (também aaaa-mm-dd). Devolve (date, erro)."""
    if v is None or (isinstance(v, str) and not v.strip()):
        return None, None
    if isinstance(v, datetime):
        d = v.date()
    elif isinstance(v, date):
        d = v
    else:
        s = str(v).strip()
        m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", s) or None
        try:
            if m:
                d = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", s[:10]):
                d = date.fromisoformat(s[:10])
            else:
                return None, f"data inválida “{s}”"
        except ValueError:
            return None, f"data inválida “{s}”"
    if d < MIN_DATE:
        return None, f"data antes de 2020 ({d.strftime('%d/%m/%Y')})"
    if d > today:
        return None, f"data futura ({d.strftime('%d/%m/%Y')})"
    return d, None


def install_trainings(app, H):
    """H: login_required, has_access(perm), sql(q,p)->list[dict], exec(q,p), commit, rollback, is_pg(), audit(ev,id,detail),
    today() -> date (Brasília), render(template, **ctx), release()."""
    from flask import jsonify, request, session, abort, send_file

    login_required, has, sql, ex, commit, rollback, audit = (H["login_required"], H["has_access"], H["sql"], H["exec"],
                                                             H["commit"], H["rollback"], H["audit"])
    st = {"ready": False}
    lock = threading.Lock()

    def can_view():
        return has("field.training") or has("field.training.manage")

    def can_manage():
        return has("field.training.manage")

    def ensure():
        if st["ready"]:
            return
        with lock:
            if st["ready"]:
                return
            pk = "SERIAL PRIMARY KEY" if H["is_pg"]() else "INTEGER PRIMARY KEY AUTOINCREMENT"
            existed = True
            try:
                sql("SELECT id FROM v108_training_types WHERE 1=0", {})
            except Exception:
                rollback()
                existed = False
            ex(f"""CREATE TABLE IF NOT EXISTS v108_training_types (id {pk}, name VARCHAR(80) NOT NULL UNIQUE,
                   sort_order INTEGER NOT NULL DEFAULT 0, validity_months INTEGER, active INTEGER NOT NULL DEFAULT 1,
                   created_by INTEGER, created_at TIMESTAMP, updated_by INTEGER, updated_at TIMESTAMP)""", {})
            ex(f"""CREATE TABLE IF NOT EXISTS v108_training_records (id {pk}, user_id INTEGER NOT NULL, type_id INTEGER NOT NULL,
                   done_on DATE NOT NULL, trainer VARCHAR(120), notes TEXT, source VARCHAR(20) NOT NULL DEFAULT 'MANUAL',
                   created_by INTEGER, created_at TIMESTAMP, updated_by INTEGER, updated_at TIMESTAMP,
                   deleted_by INTEGER, deleted_at TIMESTAMP)""", {})
            ex("CREATE INDEX IF NOT EXISTS ix_v108_rec_user ON v108_training_records (user_id)", {})
            if not existed:
                now = datetime.utcnow()
                for i, n in enumerate(DEFAULT_TYPES, 1):
                    ex("INSERT INTO v108_training_types (name, sort_order, active, created_at) VALUES (:n, :o, 1, :t)",
                       {"n": n, "o": i, "t": now})
            commit()
            st["ready"] = True

    def uid():
        return session.get("user_id")

    def iso(v):
        if v is None:
            return ""
        return v.isoformat()[:10] if hasattr(v, "isoformat") else str(v)[:10]

    def types(active_only=False):
        q = "SELECT id, name, sort_order, validity_months, active FROM v108_training_types"
        if active_only:
            q += " WHERE active = 1"
        return sql(q + " ORDER BY sort_order, name", {})

    def techs():
        """Técnicos ativos (Field e Implantação) + quem já tem registro, mesmo com outro perfil."""
        rows = sql(f"""SELECT id, name, role, job_title, company, active, personnel_status FROM users
                       WHERE (active = :a AND role IN ('{TECH_ROLES[0]}','{TECH_ROLES[1]}')
                              AND COALESCE(personnel_status,'ATIVO') NOT IN ('DESLIGADO','INATIVO'))
                          OR id IN (SELECT user_id FROM v108_training_records WHERE deleted_at IS NULL)
                       ORDER BY name""", {"a": True})
        return [{"id": r["id"], "name": r["name"], "job_title": r.get("job_title") or "",
                 "role": r.get("role") or "", "company": " ".join(str(r.get("company") or "").split()),
                 "active": bool(r.get("active"))} for r in rows]

    def records():
        rows = sql("""SELECT r.id, r.user_id, r.type_id, r.done_on, r.trainer, r.notes, r.source, r.created_at, u.name AS by_name
                      FROM v108_training_records r LEFT JOIN users u ON u.id = r.created_by
                      WHERE r.deleted_at IS NULL ORDER BY r.done_on DESC, r.id DESC""", {})
        return [{"id": r["id"], "user_id": r["user_id"], "type_id": r["type_id"], "date": iso(r["done_on"]),
                 "trainer": r.get("trainer") or "", "notes": r.get("notes") or "", "source": r.get("source") or "",
                 "by": r.get("by_name") or ""} for r in rows]

    def fail(msg, code=400):
        return jsonify({"ok": False, "error": msg}), code

    # ---------------- tela e dados ----------------
    @app.get("/field/treinamentos")
    @login_required
    def v108_training_page():
        if not can_view():
            abort(403)
        ensure()
        return H["render"]("field_treinamentos_v108.html", can_manage=can_manage())

    @app.get("/api/field/treinamentos")
    @login_required
    def v108_training_data():
        if not can_view():
            abort(403)
        ensure()
        return jsonify({"ok": True, "today": H["today"]().isoformat(), "can_manage": can_manage(),
                        "types": [{"id": t["id"], "name": t["name"], "order": t["sort_order"], "validity": t["validity_months"],
                                   "active": bool(t["active"])} for t in types()],
                        "techs": techs(), "records": records()})

    # ---------------- registrar / editar / excluir ----------------
    def clean_common(d):
        today = H["today"]()
        dt, err = parse_date(d.get("date"), today)
        if err or not dt:
            return None, (err or "Informe a data realizada.")
        try:
            tid = int(d.get("type_id"))
        except (TypeError, ValueError):
            return None, "Escolha o tipo de treinamento."
        t = sql("SELECT id, name, active FROM v108_training_types WHERE id = :i", {"i": tid})
        if not t or not t[0]["active"]:
            return None, "Tipo de treinamento inexistente ou inativo."
        return {"done_on": dt, "type_id": tid, "type_name": t[0]["name"],
                "trainer": (d.get("trainer") or "").strip()[:120] or None,
                "notes": (d.get("notes") or "").strip()[:1000] or None}, None

    @app.post("/api/field/treinamentos")
    @login_required
    def v108_training_create():
        if not can_manage():
            abort(403)
        ensure()
        d = request.get_json(silent=True) or {}
        vals, err = clean_common(d)
        if err:
            return fail(err)
        try:
            ids = sorted({int(x) for x in (d.get("user_ids") or [])})
        except (TypeError, ValueError):
            return fail("Técnico inválido.")
        if not ids:
            return fail("Escolha ao menos um técnico.")
        if len(ids) > 200:
            return fail("No máximo 200 técnicos por vez.")
        names = {r["id"]: r["name"] for r in sql(
            f"SELECT id, name FROM users WHERE id IN ({','.join(':u%d' % i for i in range(len(ids)))})",
            {f"u{i}": v for i, v in enumerate(ids)})}
        missing = [i for i in ids if i not in names]
        if missing:
            return fail("Técnico não encontrado no cadastro.")
        now = datetime.utcnow()
        try:
            for u in ids:
                ex("""INSERT INTO v108_training_records (user_id, type_id, done_on, trainer, notes, source, created_by, created_at)
                      VALUES (:u, :t, :d, :tr, :n, 'MANUAL', :by, :at)""",
                   {"u": u, "t": vals["type_id"], "d": vals["done_on"], "tr": vals["trainer"], "n": vals["notes"], "by": uid(), "at": now})
            commit()
        except Exception:
            rollback()
            raise
        audit("V108_TREINAMENTO_REGISTRADO", vals["type_id"],
              f'{vals["type_name"]} em {vals["done_on"].strftime("%d/%m/%Y")} para {len(ids)} técnico(s): ' + ", ".join(names[i] for i in ids)[:350])
        return jsonify({"ok": True, "created": len(ids)})

    def get_rec(rid):
        r = sql("SELECT * FROM v108_training_records WHERE id = :i AND deleted_at IS NULL", {"i": rid})
        return r[0] if r else None

    @app.post("/api/field/treinamentos/<int:rid>")
    @login_required
    def v108_training_update(rid):
        if not can_manage():
            abort(403)
        ensure()
        cur = get_rec(rid)
        if not cur:
            abort(404)
        d = request.get_json(silent=True) or {}
        d.setdefault("type_id", cur["type_id"])
        d.setdefault("date", iso(cur["done_on"]))
        vals, err = clean_common(d)
        if err:
            return fail(err)
        ex("""UPDATE v108_training_records SET type_id = :t, done_on = :d, trainer = :tr, notes = :n, updated_by = :by, updated_at = :at
              WHERE id = :i""", {"t": vals["type_id"], "d": vals["done_on"], "tr": vals["trainer"], "n": vals["notes"],
                                 "by": uid(), "at": datetime.utcnow(), "i": rid})
        commit()
        audit("V108_TREINAMENTO_ALTERADO", rid, f'{vals["type_name"]} em {vals["done_on"].strftime("%d/%m/%Y")} (técnico {cur["user_id"]})')
        return jsonify({"ok": True})

    @app.post("/api/field/treinamentos/<int:rid>/excluir")
    @login_required
    def v108_training_delete(rid):
        if not can_manage():
            abort(403)
        ensure()
        cur = get_rec(rid)
        if not cur:
            abort(404)
        ex("UPDATE v108_training_records SET deleted_by = :by, deleted_at = :at WHERE id = :i",
           {"by": uid(), "at": datetime.utcnow(), "i": rid})
        commit()
        audit("V108_TREINAMENTO_EXCLUIDO", rid, f'tipo {cur["type_id"]} em {iso(cur["done_on"])} (técnico {cur["user_id"]})')
        return jsonify({"ok": True})

    # ---------------- tipos ----------------
    def clean_type(d, partial=False):
        out = {}
        if not partial or "name" in d:
            name = " ".join(str(d.get("name") or "").split())[:80]
            if len(name) < 2:
                return None, "Informe o nome do tipo."
            out["name"] = name
        if "order" in d:
            try:
                out["sort_order"] = int(d.get("order"))
            except (TypeError, ValueError):
                return None, "Ordem inválida."
        if "validity" in d:
            v = d.get("validity")
            if v in (None, "", 0, "0"):
                out["validity_months"] = None
            else:
                try:
                    v = int(v)
                except (TypeError, ValueError):
                    return None, "Validade inválida (meses)."
                if not 1 <= v <= 120:
                    return None, "Validade entre 1 e 120 meses (ou vazio = não vence)."
                out["validity_months"] = v
        if "active" in d:
            out["active"] = 1 if d.get("active") else 0
        return out, None

    def type_name_taken(name, except_id=None):
        return any(t["id"] != except_id and tkey(t["name"]) == tkey(name) for t in types())

    @app.post("/api/field/treinamentos/tipos")
    @login_required
    def v108_type_create():
        if not can_manage():
            abort(403)
        ensure()
        vals, err = clean_type(request.get_json(silent=True) or {})
        if err:
            return fail(err)
        if type_name_taken(vals["name"]):
            return fail("Já existe um tipo com esse nome.", 409)
        if "sort_order" not in vals:
            r = sql("SELECT MAX(sort_order) AS m FROM v108_training_types", {})
            vals["sort_order"] = int((r[0]["m"] if r else 0) or 0) + 1
        ex("""INSERT INTO v108_training_types (name, sort_order, validity_months, active, created_by, created_at)
              VALUES (:n, :o, :v, :a, :by, :at)""",
           {"n": vals["name"], "o": vals["sort_order"], "v": vals.get("validity_months"), "a": vals.get("active", 1),
            "by": uid(), "at": datetime.utcnow()})
        commit()
        audit("V108_TIPO_CRIADO", 0, vals["name"])
        return jsonify({"ok": True})

    @app.post("/api/field/treinamentos/tipos/<int:tid>")
    @login_required
    def v108_type_update(tid):
        if not can_manage():
            abort(403)
        ensure()
        cur = sql("SELECT * FROM v108_training_types WHERE id = :i", {"i": tid})
        if not cur:
            abort(404)
        vals, err = clean_type(request.get_json(silent=True) or {}, partial=True)
        if err:
            return fail(err)
        if "name" in vals and type_name_taken(vals["name"], tid):
            return fail("Já existe um tipo com esse nome.", 409)
        if not vals:
            return jsonify({"ok": True, "unchanged": True})
        sets = ", ".join(f"{k} = :{k}" for k in vals)
        ex(f"UPDATE v108_training_types SET {sets}, updated_by = :by, updated_at = :at WHERE id = :i",
           dict(vals, by=uid(), at=datetime.utcnow(), i=tid))
        commit()
        audit("V108_TIPO_ALTERADO", tid, f'{cur[0]["name"]}: ' + ", ".join(f"{k}={v}" for k, v in vals.items()))
        return jsonify({"ok": True})

    # ---------------- exportar Excel ----------------
    def filtered(args):
        """Mesma regra da tela: técnico (nome contém), empresa, tipo, período (de/até) e situação (feito/falta)."""
        today = H["today"]()
        ts = [t for t in types() if t["active"]]
        tid = args.get("tipo")
        if tid and str(tid).isdigit():
            ts = [t for t in ts if t["id"] == int(tid)]
        de = args.get("de") or ""
        ate = args.get("ate") or ""
        q = fold(args.get("tecnico") or "")
        sit = (args.get("situacao") or "").lower()
        recs = [r for r in records() if (not de or r["date"] >= de) and (not ate or r["date"] <= ate)]
        emp = fold(args.get("empresa") or "")
        tt = [t for t in techs() if (not q or q in fold(t["name"]))
              and (not emp or fold(t["company"] or "(sem empresa)") == emp)]
        latest = {}
        for r in recs:  # já vem do mais recente para o mais antigo
            latest.setdefault((r["user_id"], r["type_id"]), r)
        type_ids = {t["id"] for t in ts}

        def done_any(u):
            return any((u, t) in latest for t in type_ids)

        if sit == "feito":
            tt = [t for t in tt if done_any(t["id"])]
        elif sit == "falta":
            tt = [t for t in tt if any((t["id"], x) not in latest for x in type_ids)]
        return today, ts, tt, latest, recs

    def expired(rec, t, today):
        m = t.get("validity_months")
        if not m:
            return False
        y, mo = divmod(date.fromisoformat(rec["date"]).month - 1 + m, 12)
        d0 = date.fromisoformat(rec["date"])
        y += d0.year
        try:
            due = d0.replace(year=y, month=mo + 1)
        except ValueError:
            due = d0.replace(year=y, month=mo + 1, day=28)
        return due < today

    @app.get("/api/field/treinamentos/exportar")
    @login_required
    def v108_training_export():
        if not can_view():
            abort(403)
        ensure()
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
        today, ts, tt, latest, recs = filtered(request.args)
        wb = Workbook()
        bold = Font(bold=True, color="FFFFFF")
        head = PatternFill("solid", fgColor="0F1E3D")
        green = PatternFill("solid", fgColor="DCFCE7")
        amber = PatternFill("solid", fgColor="FEF3C7")
        if request.args.get("formato") == "lista":
            ws = wb.active
            ws.title = "Treinamentos"
            ws.append(["Técnico", "Empresa", "Cargo", "Tipo de treinamento", "Data realizada", "Aplicado por", "Observação", "Origem", "Registrado por"])
            tname = {t["id"]: t["name"] for t in types()}
            tech = {t["id"]: t for t in techs()}
            ids = {t["id"] for t in tt}
            allowed = {t["id"] for t in ts}
            for r in recs:
                if r["user_id"] in ids and r["type_id"] in allowed:
                    u = tech.get(r["user_id"], {})
                    ws.append([u.get("name", r["user_id"]), u.get("company", ""), u.get("job_title", ""), tname.get(r["type_id"], r["type_id"]),
                               date.fromisoformat(r["date"]), r["trainer"], r["notes"], r["source"], r["by"]])
                    ws.cell(ws.max_row, 5).number_format = "DD/MM/YYYY"
            widths = [38, 22, 26, 20, 14, 22, 50, 10, 24]
            fname = "treinamentos_lista.xlsx"
        else:
            ws = wb.active
            ws.title = "Matriz"
            ws.append(["Técnico", "Empresa"] + [t["name"] for t in ts] + ["Total"])
            for u in tt:
                row = [u["name"], u["company"]]
                fills = []
                n = 0
                for t in ts:
                    r = latest.get((u["id"], t["id"]))
                    if r:
                        n += 1
                        row.append(date.fromisoformat(r["date"]))
                        fills.append(amber if expired(r, t, today) else green)
                    else:
                        row.append("")
                        fills.append(None)
                row.append(f"{n}/{len(ts)}")
                ws.append(row)
                for j, f in enumerate(fills, 3):
                    c = ws.cell(ws.max_row, j)
                    c.number_format = "DD/MM/YYYY"
                    c.alignment = Alignment(horizontal="center")
                    if f:
                        c.fill = f
            ws.append(["Cobertura", ""] + [f"{sum(1 for u in tt if (u['id'], t['id']) in latest)}/{len(tt)}" for t in ts] + [""])
            for c in ws[ws.max_row]:
                c.font = Font(bold=True)
            widths = [38, 22] + [14] * len(ts) + [8]
            fname = "treinamentos_matriz.xlsx"
        for c in ws[1]:
            c.font, c.fill = bold, head
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[ws.cell(1, i).column_letter].width = w
        ws.freeze_panes = "B2"
        info = wb.create_sheet("Filtros")
        info.append(["Gerado em", datetime.utcnow().strftime("%d/%m/%Y %H:%M") + " UTC"])
        for k, lbl in (("tecnico", "Técnico"), ("empresa", "Empresa"), ("tipo", "Tipo"), ("situacao", "Situação"), ("de", "De"), ("ate", "Até")):
            info.append([lbl, request.args.get(k) or "todos"])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return send_file(buf, as_attachment=True, download_name=fname,
                         mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # ---------------- importar planilha (uma vez, com prévia) ----------------
    def read_sheet(f):
        name = (f.filename or "").lower()
        raw = f.read()
        if len(raw) > 5 * 1024 * 1024:
            raise ValueError("Arquivo maior que 5 MB.")
        if name.endswith((".xlsx", ".xlsm")):
            from openpyxl import load_workbook
            ws = load_workbook(io.BytesIO(raw), data_only=True, read_only=True).worksheets[0]
            rows = [list(r) for r in ws.iter_rows(values_only=True)]
        else:
            text = raw.decode("utf-8-sig", "ignore")
            sep = "\t" if "\t" in text.split("\n", 1)[0] else ";"
            rows = [line.split(sep) for line in text.splitlines()]
        rows = [r for r in rows if any(str(c or "").strip() for c in r)]
        if not rows:
            raise ValueError("Planilha vazia.")
        return rows

    def plan_import(rows):
        today = H["today"]()
        header = [str(c or "").strip() for c in rows[0]]
        tlist = types()
        by_key = {tkey(t["name"]): t for t in tlist}
        cols = []  # (indice, nome do tipo, id ou None)
        for i, h in enumerate(header[1:], 1):
            if not h:
                continue
            k = tkey(h)
            name = ALIASES.get(k) or (by_key[k]["name"] if k in by_key else h.strip().title())
            t = by_key.get(tkey(name))
            cols.append((i, name, t["id"] if t else None))
        people = sql("SELECT id, name, active FROM users ORDER BY name", {})
        by_name = {}
        for p in people:
            by_name.setdefault(fold(p["name"]), p)
        existing = {(r["user_id"], r["type_id"], r["date"]) for r in records()}
        items, invalid, names = [], [], {}
        for r in rows[1:]:
            nm = " ".join(str(r[0] or "").split()) if r else ""
            if not nm:
                continue
            p = by_name.get(fold(nm))
            if not p:  # primeiro + último nome
                parts = fold(nm).split()
                cands = [x for x in people if parts and fold(x["name"]).split()[:1] == parts[:1]
                         and fold(x["name"]).split()[-1:] == parts[-1:]]
                p = cands[0] if len(cands) == 1 else None
            names[nm] = {"user_id": p["id"] if p else None, "user_name": p["name"] if p else "",
                         "suggestions": [] if p else [x["name"] for x in people
                                                      if fold(nm).split()[:1] == fold(x["name"]).split()[:1]][:5]}
            for i, tname, tid in cols:
                v = r[i] if i < len(r) else None
                if v is None or (isinstance(v, str) and not v.strip()):
                    continue
                d, err = parse_date(v, today)
                if err:
                    invalid.append({"name": nm, "type": tname, "value": str(v).strip()[:20], "error": err})
                    continue
                items.append({"name": nm, "type": tname, "type_id": tid, "date": d.isoformat()})
        return {"columns": [{"name": n, "new": tid is None} for _, n, tid in cols], "names": names, "items": items,
                "invalid": invalid, "existing": existing}

    @app.post("/api/field/treinamentos/importar")
    @login_required
    def v108_training_import():
        if not can_manage():
            abort(403)
        ensure()
        f = request.files.get("arquivo")
        if not f:
            return fail("Escolha a planilha (.xlsx, .csv ou .txt).")
        try:
            plan = plan_import(read_sheet(f))
        except ValueError as exc:
            return fail(str(exc))
        except Exception:
            return fail("Não foi possível ler a planilha. Use .xlsx (1ª aba) ou texto separado por tabulação/ponto e vírgula.")
        mapping = {}
        try:
            mapping = {k: int(v) for k, v in json.loads(request.form.get("mapa") or "{}").items() if str(v).isdigit()}
        except Exception:
            mapping = {}
        for nm, info in plan["names"].items():
            if nm in mapping:
                info["user_id"] = mapping[nm]
        ready = [it for it in plan["items"] if plan["names"][it["name"]]["user_id"]]
        skipped_names = sorted(n for n, i in plan["names"].items() if not i["user_id"])
        if request.form.get("confirmar") != "1":
            return jsonify({"ok": True, "preview": True, "columns": plan["columns"], "registros": len(plan["items"]),
                            "prontos": len(ready), "tecnicos": len(plan["names"]), "invalidos": plan["invalid"],
                            "nomes": [{"name": n, **i} for n, i in sorted(plan["names"].items())],
                            "sem_tecnico": skipped_names})
        now = datetime.utcnow()
        created = dup = 0
        try:
            tid_by_name = {t["name"]: t["id"] for t in types()}
            for c in plan["columns"]:
                if c["name"] not in tid_by_name:
                    r = sql("SELECT MAX(sort_order) AS m FROM v108_training_types", {})
                    ex("INSERT INTO v108_training_types (name, sort_order, active, created_by, created_at) VALUES (:n, :o, 1, :by, :at)",
                       {"n": c["name"], "o": int((r[0]["m"] if r else 0) or 0) + 1, "by": uid(), "at": now})
                    tid_by_name = {t["name"]: t["id"] for t in types()}
            for it in ready:
                u = plan["names"][it["name"]]["user_id"]
                t = tid_by_name[it["type"]]
                if (u, t, it["date"]) in plan["existing"]:
                    dup += 1
                    continue
                plan["existing"].add((u, t, it["date"]))
                ex("""INSERT INTO v108_training_records (user_id, type_id, done_on, source, created_by, created_at)
                      VALUES (:u, :t, :d, 'IMPORTACAO', :by, :at)""",
                   {"u": u, "t": t, "d": date.fromisoformat(it["date"]), "by": uid(), "at": now})
                created += 1
            commit()
        except Exception:
            rollback()
            raise
        audit("V108_TREINAMENTOS_IMPORTADOS", 0, f"{created} registro(s) importados; {dup} repetido(s) ignorados; "
              f"{len(plan['invalid'])} data(s) inválida(s) e {len(skipped_names)} nome(s) sem técnico ficaram de fora")
        return jsonify({"ok": True, "importados": created, "repetidos": dup, "invalidos": plan["invalid"], "sem_tecnico": skipped_names})
