# -*- coding: utf-8 -*-
"""V88.0 REV67 — Engenharia › BOM: selos de revisão por área.

Selos (cada um: sim/não + quem marcou + quando):
- mecanica  "Engenharia Mecânica"        liberação engineering.review.mechanical   (estrutura)
- hardware  "Engenharia de Hardware"     liberação engineering.review.hardware     (estrutura)
- estoque   "Estoque"                    liberação engineering.review.stock        (estrutura)
- valores   "Estoque / Compras (valores)" liberação engineering.review.prices      (valores)

Toda marcação é gravada (histórico completo); o estado do selo é a última marcação da área.
Cada marcação guarda a "impressão digital" da BOM no momento:
- estrutura: itens, quantidades e subestruturas vinculadas;
- valores: origem, moeda e custo de cada item, fator de importação e câmbio.
Se a BOM mudar depois, o selo aparece como "desatualizado" e pede nova revisão.

Tabela nova (aditiva): v160_bom_reviews. Nenhuma tabela existente é alterada.
"""
import hashlib
import json
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

AREAS = (
    ("mecanica", "Engenharia Mecânica", "engineering.review.mechanical", "estrutura"),
    ("hardware", "Engenharia de Hardware", "engineering.review.hardware", "estrutura"),
    ("estoque", "Estoque", "engineering.review.stock", "estrutura"),
    ("valores", "Estoque / Compras", "engineering.review.prices", "valores"),
)
AREA_BY_KEY = {a[0]: a for a in AREAS}
PERMISSIONS = {a[2]: "Revisar BOM — " + (a[1] if a[3] == "estrutura" else "valores (Estoque / Compras)") for a in AREAS}
_TZ = ZoneInfo("America/Sao_Paulo")
_READY = {"ok": False}


def fingerprints(bom_json):
    """(estrutura, valores) — resumo estável da BOM calculada por _eng_bom_json."""
    items = bom_json.get("items") or []
    est = sorted((int(x.get("item_id") or 0), round(float(x.get("quantity") or 0), 6), int(x.get("linked_bom_id") or 0)) for x in items)
    val = sorted((int(x.get("item_id") or 0), str(x.get("origin") or ""), str(x.get("currency") or ""),
                  round(float(x.get("unit_cost") or 0), 4), round(float(x.get("nationalized_unit_cost") or 0), 2)) for x in items)
    val.append(("fator", round(float(bom_json.get("import_factor") or 0), 4), round(float(bom_json.get("usd_brl") or 0), 4)))

    def h(obj):
        return hashlib.sha1(json.dumps(obj, separators=(",", ":")).encode()).hexdigest()[:20]
    return h(est), h(val)


def fmt_br(dt):
    if not dt:
        return ""
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            return dt
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_TZ).strftime("%d/%m/%Y %H:%M")


def install_bom_revisao(app, H):
    """H: login_required, can(perm), engine, text, bom_get(bid), bom_json(bom), user_id(), user_name(), audit(event, entity_id, detail)."""
    from flask import jsonify, request

    text = H["text"]

    def ensure():
        if _READY["ok"]:
            return
        with H["engine"]().begin() as c:
            c.execute(text("CREATE TABLE IF NOT EXISTS v160_bom_reviews (id BIGINT PRIMARY KEY, bom_id INTEGER NOT NULL, area VARCHAR(20) NOT NULL,"
                           " approved INTEGER NOT NULL, user_id INTEGER, user_name VARCHAR(180), fp_structure VARCHAR(40), fp_values VARCHAR(40),"
                           " created_at TIMESTAMP NOT NULL)"))
            c.execute(text("CREATE INDEX IF NOT EXISTS ix_v160_bom_reviews_bom ON v160_bom_reviews (bom_id, area, created_at)"))
        _READY["ok"] = True

    def can_view():
        return H["can"]("engineering.bom.view") or H["can"]("engineering.pricing.view")

    def payload(bid, bom):
        ensure()
        with H["engine"]().connect() as c:
            rows = c.execute(text("SELECT id, area, approved, user_name, created_at, fp_structure, fp_values FROM v160_bom_reviews"
                                  " WHERE bom_id=:b ORDER BY created_at DESC, id DESC LIMIT 200"), {"b": bid}).fetchall()
        fp_est, fp_val = fingerprints(H["bom_json"](bom))
        last = {}
        for r in rows:
            last.setdefault(r[1], r)
        areas = []
        for key, label, perm, tipo in AREAS:
            r = last.get(key)
            item = {"area": key, "label": label, "tipo": tipo, "can_mark": bool(H["can"](perm)),
                    "approved": False, "by": "", "at": "", "estado": "pendente"}
            if r:
                item.update({"approved": bool(r[2]), "by": r[3] or "", "at": fmt_br(r[4])})
                if r[2]:
                    atual = fp_val if tipo == "valores" else fp_est
                    gravado = r[6] if tipo == "valores" else r[5]
                    item["estado"] = "ok" if gravado == atual else "desatualizada"
                else:
                    item["estado"] = "desmarcada"
            areas.append(item)
        hist = [{"area": AREA_BY_KEY.get(r[1], (r[1], r[1]))[1], "approved": bool(r[2]), "by": r[3] or "", "at": fmt_br(r[4])} for r in rows[:100]]
        return {"ok": True, "bom_id": bid, "areas": areas, "historico": hist}

    @app.get("/api/engineering/boms/<int:bid>/revisoes")
    @H["login_required"]
    def v160_bom_reviews_get(bid):
        if not can_view():
            return jsonify({"ok": False, "error": "Sem permissão."}), 403
        bom = H["bom_get"](bid)
        if not bom:
            return jsonify({"ok": False, "error": "BOM não encontrada."}), 404
        try:
            return jsonify(payload(bid, bom))
        except Exception:
            app.logger.exception("REV67: falha ao ler revisões da BOM %s", bid)
            return jsonify({"ok": False, "error": "Não foi possível ler as revisões."}), 500

    @app.post("/api/engineering/boms/<int:bid>/revisoes")
    @H["login_required"]
    def v160_bom_reviews_post(bid):
        data = request.get_json(silent=True) or {}
        area = AREA_BY_KEY.get(str(data.get("area") or "").strip().lower())
        if not area:
            return jsonify({"ok": False, "error": "Área de revisão inválida."}), 400
        if not H["can"](area[2]):
            return jsonify({"ok": False, "error": f"Você não tem liberação para marcar a revisão de {area[1]}."}), 403
        bom = H["bom_get"](bid)
        if not bom:
            return jsonify({"ok": False, "error": "BOM não encontrada."}), 404
        approved = 1 if data.get("approved") else 0
        try:
            ensure()
            fp_est, fp_val = fingerprints(H["bom_json"](bom))
            nome = (H["user_name"]() or "")[:180]
            with H["engine"]().begin() as c:
                c.execute(text("INSERT INTO v160_bom_reviews (id, bom_id, area, approved, user_id, user_name, fp_structure, fp_values, created_at)"
                               " VALUES (:i,:b,:a,:p,:u,:n,:fe,:fv,:t)"),
                          {"i": time.time_ns() // 1000, "b": bid, "a": area[0], "p": approved, "u": H["user_id"](), "n": nome,
                           "fe": fp_est, "fv": fp_val, "t": datetime.utcnow()})
            H["audit"]("BOM_REVIEW_" + ("OK" if approved else "UNDO"), str(bid),
                       f"{bom.product_code} {bom.revision} · {area[1]} · {'revisado' if approved else 'desmarcado'} por {nome}")
            return jsonify(payload(bid, bom))
        except Exception:
            app.logger.exception("REV67: falha ao gravar revisão da BOM %s", bid)
            return jsonify({"ok": False, "error": "Não foi possível gravar a revisão."}), 500
