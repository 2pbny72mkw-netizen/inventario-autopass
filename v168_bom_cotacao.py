# -*- coding: utf-8 -*-
"""V88.0 REV68 — Engenharia › BOM: status de cotação por item (linha da BOM).

Status: NAO_COTADO (padrão), EM_COTACAO, COTADO, AGUARDANDO_DEFINICAO.
O status fica na linha da BOM (o mesmo item pode estar cotado numa BOM e não em outra) e guarda quem mudou e quando.
Quem pode mudar: "Criar / revisar BOM" (engineering.bom.manage) ou "Revisar valores da BOM — Estoque / Compras"
(engineering.review.prices). Toda mudança vai para a auditoria.

Tabela nova (aditiva): v168_bom_item_quotes. Linha sem registro = Não cotado.
"""
from datetime import datetime

STATUS = (("NAO_COTADO", "Não cotado"), ("EM_COTACAO", "Em cotação"), ("COTADO", "Cotado"), ("AGUARDANDO_DEFINICAO", "Aguardando definição"))
LABEL = dict(STATUS)
EDIT_PERMS = ("engineering.bom.manage", "engineering.review.prices")
_READY = {"ok": False}


def install_bom_cotacao(app, H):
    """H: login_required, can, engine(), text, bom_item_get(id) -> (bom_item, bom) | None, user_name(), audit(event, entity_id, detail), fmt_br(dt)."""
    from flask import jsonify, request

    text = H["text"]

    def ensure():
        if _READY["ok"]:
            return
        with H["engine"]().begin() as c:
            c.execute(text("CREATE TABLE IF NOT EXISTS v168_bom_item_quotes (bom_item_id INTEGER PRIMARY KEY, bom_id INTEGER NOT NULL,"
                           " status VARCHAR(30) NOT NULL, user_name VARCHAR(180), updated_at TIMESTAMP NOT NULL)"))
            c.execute(text("CREATE INDEX IF NOT EXISTS ix_v168_quotes_bom ON v168_bom_item_quotes (bom_id)"))
        _READY["ok"] = True

    def can_edit():
        return any(H["can"](p) for p in EDIT_PERMS)

    def status_map(bom_item_ids):
        """{bom_item_id: status} para a exportação; ids ausentes = NAO_COTADO."""
        ids = [int(i) for i in bom_item_ids if str(i or "").isdigit()]
        if not ids:
            return {}
        ensure()
        out = {}
        with H["engine"]().connect() as c:
            for i in range(0, len(ids), 500):
                part = ids[i:i + 500]
                q = "SELECT bom_item_id, status FROM v168_bom_item_quotes WHERE bom_item_id IN (" + ",".join(f":k{j}" for j in range(len(part))) + ")"
                for r in c.execute(text(q), {f"k{j}": v for j, v in enumerate(part)}):
                    out[int(r[0])] = r[1]
        return out

    @app.get("/api/engineering/cotacao")
    @H["login_required"]
    def v168_cotacao_get():
        if not (H["can"]("engineering.bom.view") or H["can"]("engineering.pricing.view")):
            return jsonify({"ok": False, "error": "Sem permissão."}), 403
        boms = [int(x) for x in str(request.args.get("boms") or "").split(",") if x.strip().isdigit()][:200]
        itens = {}
        if boms:
            try:
                ensure()
                q = ("SELECT bom_item_id, status, user_name, updated_at FROM v168_bom_item_quotes WHERE bom_id IN ("
                     + ",".join(f":b{j}" for j in range(len(boms))) + ")")
                with H["engine"]().connect() as c:
                    for r in c.execute(text(q), {f"b{j}": v for j, v in enumerate(boms)}):
                        itens[str(r[0])] = {"s": r[1], "by": r[2] or "", "at": H["fmt_br"](r[3])}
            except Exception:
                app.logger.exception("REV68: falha ao ler status de cotação")
                return jsonify({"ok": False, "error": "Não foi possível ler os status de cotação."}), 500
        return jsonify({"ok": True, "can_edit": can_edit(), "status": [{"k": k, "l": l} for k, l in STATUS], "itens": itens})

    @app.post("/api/engineering/cotacao")
    @H["login_required"]
    def v168_cotacao_post():
        if not can_edit():
            return jsonify({"ok": False, "error": "Sem liberação para mudar o status de cotação."}), 403
        d = request.get_json(silent=True) or {}
        st = str(d.get("status") or "").upper()
        if st not in LABEL:
            return jsonify({"ok": False, "error": "Status de cotação inválido."}), 400
        bi = int(d.get("bom_item_id") or 0) if str(d.get("bom_item_id") or "").isdigit() else 0
        found = H["bom_item_get"](bi) if bi else None
        if not found:
            return jsonify({"ok": False, "error": "Item da BOM não encontrado."}), 404
        x, bom = found
        nome = (H["user_name"]() or "")[:180]
        now = datetime.utcnow()
        try:
            ensure()
            with H["engine"]().begin() as c:
                old = c.execute(text("SELECT status FROM v168_bom_item_quotes WHERE bom_item_id=:i"), {"i": bi}).scalar()
                c.execute(text("DELETE FROM v168_bom_item_quotes WHERE bom_item_id=:i"), {"i": bi})
                c.execute(text("INSERT INTO v168_bom_item_quotes (bom_item_id, bom_id, status, user_name, updated_at) VALUES (:i,:b,:s,:n,:t)"),
                          {"i": bi, "b": bom.id, "s": st, "n": nome, "t": now})
            H["audit"]("BOM_ITEM_QUOTE_STATUS", str(bi), f"{bom.product_code} {bom.revision} · linha {bi} · "
                       f"{LABEL.get(old or 'NAO_COTADO')} → {LABEL[st]} por {nome}")
        except Exception:
            app.logger.exception("REV68: falha ao gravar status de cotação %s", bi)
            return jsonify({"ok": False, "error": "Não foi possível gravar o status."}), 500
        return jsonify({"ok": True, "bom_item_id": bi, "item": {"s": st, "by": nome, "at": H["fmt_br"](now)}})

    return status_map
