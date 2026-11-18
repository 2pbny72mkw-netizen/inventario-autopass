# -*- coding: utf-8 -*-
"""V88.0 REV17 — eficiência: fotos do banco no R2, limpeza automática de GPS, compactação, cache do mapa do R2.

1) Fotos que ficavam DENTRO do banco (Troca POS Metrô, AP POS Metrô, foto do material) passam a ir para o R2.
   - Coluna nova r2_key nas 3 tabelas; o conteúdo no banco fica vazio quando a foto está no R2.
   - Fotos novas já vão para o R2 (se o R2 estiver configurado; senão continuam no banco, como antes).
   - Fotos antigas: botão no Diagnóstico migra em lotes, conferindo a cópia no R2 antes de esvaziar o banco.
2) Eventos de sincronização do app: GPS_POSITION/GPS_SIGNAL com mais de 7 dias são apagados sozinhos
   (o ponto já está na tabela de GPS). Roda em segundo plano no máximo a cada 6 h por processo.
3) Compactação (VACUUM FULL) das tabelas que mais liberam espaço, por botão, só administrador principal.
4) Mapa do armazenamento (R2): resultado guardado por 30 min (antes ~11 s a cada clique, travando o servidor).
5) API da Coleta de Valores (tela aposentada) responde 410.
"""
import os
import threading
import time
import uuid
from datetime import datetime, timedelta

PHOTO_TABLES = {  # tabela -> coluna com o conteúdo
    "v876_pos_metro_photos": "content",
    "v8738_pos_metro_ap_photos": "content",
    "v86_material_photos": "data",
}
GPS_TYPES = ("GPS_POSITION", "GPS_SIGNAL")
GPS_DAYS = 7
COMPACT_TABLES = ("v876_pos_metro_photos", "v8738_pos_metro_ap_photos", "v86_material_photos", "mobile_sync_events")
EXT = {".jpg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}


class _Photos:
    """Usado pelos módulos de foto via app.extensions['v107']."""

    def __init__(self, db, text, r2_ok, r2_put, r2_get, r2_del, logger, is_pg):
        self.db, self.text, self.r2_ok, self.r2_put, self.r2_get, self.r2_del = db, text, r2_ok, r2_put, r2_get, r2_del
        self.log, self.is_pg = logger, is_pg
        self.cols_ok = False
        self.tried = False

    def ensure_columns(self):
        if self.cols_ok:
            return
        for t in PHOTO_TABLES:
            try:
                if self.is_pg():
                    self.db.session.execute(self.text(f"ALTER TABLE IF EXISTS {t} ADD COLUMN IF NOT EXISTS r2_key VARCHAR(300)"))
                else:
                    cols = [r[1] for r in self.db.session.execute(self.text(f"PRAGMA table_info({t})")).fetchall()]
                    if cols and "r2_key" not in cols:
                        self.db.session.execute(self.text(f"ALTER TABLE {t} ADD COLUMN r2_key VARCHAR(300)"))
                self.db.session.commit()
            except Exception:
                self.db.session.rollback()
                self.log.exception("REV17: coluna r2_key em %s", t)
                return
        self.cols_ok = True

    @staticmethod
    def _key(table, row_id, mime):
        ext = next((e for e, m in EXT.items() if m == (mime or "").lower()), ".bin")
        return f"db-fotos/{table}/{datetime.utcnow():%Y/%m}/{row_id}-{uuid.uuid4().hex[:10]}{ext}"

    def store(self, table, row_id, data, mime):
        """Envia a foto (já gravada no banco com o id) ao R2 e esvazia o conteúdo no banco. Não faz commit.
        Se o R2 não estiver disponível ou falhar, deixa a foto no banco (comportamento antigo) e devolve False."""
        if table not in PHOTO_TABLES or not data or not self.r2_ok():
            return False
        if not self.cols_ok:  # coluna criada no início do processo (antes de qualquer gravação)
            return False
        try:
            key = self._key(table, row_id, mime)
            self.r2_put(key, data, mime)
            col = PHOTO_TABLES[table]
            self.db.session.execute(self.text(f"UPDATE {table} SET r2_key = :k, {col} = :e WHERE id = :i"),
                                    {"k": key, "e": b"", "i": row_id})
            return True
        except Exception:
            self.log.exception("REV17: foto %s/%s ficou no banco (R2 falhou)", table, row_id)
            return False

    def read(self, table, row_id, inline):
        """Conteúdo da foto: do banco se ainda estiver lá; senão do R2."""
        if inline:
            return bytes(inline)
        if not self.cols_ok:
            return b""
        try:
            key = self.db.session.execute(self.text(f"SELECT r2_key FROM {table} WHERE id = :i"), {"i": row_id}).scalar()
        except Exception:
            key = None
        if not key:
            return b""
        return self.r2_get(key)

    def keys_where(self, table, where, params):
        if not self.cols_ok:
            return []
        try:
            return [r[0] for r in self.db.session.execute(
                self.text(f"SELECT r2_key FROM {table} WHERE r2_key IS NOT NULL AND ({where})"), params).fetchall() if r[0]]
        except Exception:
            return []

    def delete_keys(self, keys):
        """Apaga objetos do R2 depois que o registro já saiu do banco (melhor esforço; falha só vai ao log)."""
        n = 0
        for k in keys or []:
            try:
                self.r2_del(k)
                n += 1
            except Exception:
                self.log.exception("REV17: não apagou %s do R2", k)
        return n


def install_eficiencia(app, db, H):
    """H: text, login_required, guard()->resp|None, is_principal(), audit(event, id, detail), is_pg(),
    r2_ok(), r2_put(key, bytes, mime), r2_get(key), r2_del(key)."""
    from flask import jsonify, request

    text, login_required, guard, is_principal, audit, is_pg = (H["text"], H["login_required"], H["guard"],
                                                             H["is_principal"], H["audit"], H["is_pg"])
    ph = _Photos(db, text, H["r2_ok"], H["r2_put"], H["r2_get"], H["r2_del"], app.logger, is_pg)
    app.extensions["v107"] = ph
    gps = {"tick": 0.0, "running": False, "last": None}
    lock = threading.Lock()

    # ---------------- 2) limpeza automática de GPS nos eventos de sincronização ----------------
    def gps_cleanup(max_batches=20, batch=5000):
        cutoff = datetime.utcnow() - timedelta(days=GPS_DAYS)
        total = 0
        for _ in range(max_batches):
            if is_pg():
                q = ("DELETE FROM mobile_sync_events WHERE id IN (SELECT id FROM mobile_sync_events "
                     "WHERE event_type IN ('GPS_POSITION','GPS_SIGNAL') AND received_at < :c ORDER BY id LIMIT :n)")
            else:
                q = ("DELETE FROM mobile_sync_events WHERE id IN (SELECT id FROM mobile_sync_events "
                     "WHERE event_type IN ('GPS_POSITION','GPS_SIGNAL') AND received_at < :c ORDER BY id LIMIT :n)")
            n = db.session.execute(text(q), {"c": cutoff, "n": batch}).rowcount or 0
            db.session.commit()
            total += n
            if n < batch:
                break
        return total

    def gps_job():
        try:
            with app.app_context():
                t0 = time.time()
                n = gps_cleanup()
                gps["last"] = {"em": datetime.utcnow().isoformat() + "Z", "apagados": n, "segundos": round(time.time() - t0, 1)}
                if n:
                    audit("V107_GPS_RETENCAO", 0, f"{n} evento(s) GPS de sincronização com mais de {GPS_DAYS} dias apagados")
        except Exception as exc:
            gps["last"] = {"em": datetime.utcnow().isoformat() + "Z", "erro": str(exc)[:200]}
            app.logger.exception("REV17: limpeza automática de GPS")
            try:
                with app.app_context():
                    db.session.rollback()
            except Exception:
                pass
        finally:
            gps["running"] = False

    @app.before_request
    def _v107_tick():
        if not ph.cols_ok and not ph.tried:
            ph.tried = True  # 1x por processo, antes da rota: cria r2_key nas tabelas de foto
            ph.ensure_columns()
        now = time.time()
        if now - gps["tick"] < 6 * 3600 or gps["running"]:
            return None
        with lock:
            if now - gps["tick"] < 6 * 3600 or gps["running"]:
                return None
            gps["tick"], gps["running"] = now, True
        threading.Thread(target=gps_job, name="v107-gps-retencao", daemon=True).start()
        return None

    # ---------------- 1) fotos do banco → R2 (Diagnóstico) ----------------
    def photo_status():
        ph.ensure_columns()
        out = []
        for t, col in PHOTO_TABLES.items():
            try:
                r = db.session.execute(text(
                    f"SELECT COUNT(*), SUM(CASE WHEN r2_key IS NOT NULL THEN 1 ELSE 0 END), "
                    f"SUM(CASE WHEN r2_key IS NULL AND {col} IS NOT NULL AND length({col}) > 0 THEN 1 ELSE 0 END), "
                    f"COALESCE(SUM(length({col})), 0) FROM {t}")).fetchone()
                size = db.session.execute(text(f"SELECT pg_total_relation_size('{t}')")).scalar() if is_pg() else None
                out.append({"tabela": t, "fotos": int(r[0] or 0), "no_r2": int(r[1] or 0), "no_banco": int(r[2] or 0),
                            "mb_no_banco": round(int(r[3] or 0) / 1048576.0, 1),
                            "tabela_mb": round(int(size) / 1048576.0, 1) if size is not None else None})
            except Exception as exc:
                db.session.rollback()
                out.append({"tabela": t, "erro": str(exc)[:160]})
        db.session.rollback()
        return out

    @app.get("/api/diagnostico/fotos-banco/v107")
    @login_required
    def v107_photos_get():
        g = guard()
        if g:
            return g
        sync = None
        try:
            r = db.session.execute(text(
                "SELECT COUNT(*) FROM mobile_sync_events WHERE event_type IN ('GPS_POSITION','GPS_SIGNAL') AND received_at < :c"),
                {"c": datetime.utcnow() - timedelta(days=GPS_DAYS)}).scalar()
            sync = {"gps_mais_de_7d": int(r or 0), "ultima_limpeza": gps["last"], "rodando": gps["running"]}
            if is_pg():
                sync["tabela_mb"] = round((db.session.execute(text("SELECT pg_total_relation_size('mobile_sync_events')")).scalar() or 0) / 1048576.0, 1)
            db.session.rollback()
        except Exception as exc:
            db.session.rollback()
            sync = {"erro": str(exc)[:160]}
        return jsonify({"ok": True, "r2": bool(H["r2_ok"]()), "fotos": photo_status(), "sync": sync,
                        "compactar": list(COMPACT_TABLES), "postgres": bool(is_pg())})

    @app.post("/api/diagnostico/fotos-banco/v107/migrar")
    @login_required
    def v107_photos_migrate():
        g = guard()
        if g:
            return g
        if not is_principal():
            return jsonify({"ok": False, "error": "Somente o administrador principal."}), 403
        if not H["r2_ok"]():
            return jsonify({"ok": False, "error": "R2 não configurado nesta instância."}), 400
        ph.ensure_columns()
        try:
            lote = max(1, min(40, int((request.get_json(silent=True) or {}).get("lote") or 15)))
        except (TypeError, ValueError):
            lote = 15
        moved, failed, mb = 0, [], 0.0
        deadline = time.time() + 20  # cada chamada fica curta; a tela repete até acabar
        for t, col in PHOTO_TABLES.items():
            if moved >= lote or time.time() > deadline:
                break
            try:
                rows = db.session.execute(text(
                    f"SELECT id, {col}, {'mimetype' if col == 'content' else 'mime'} FROM {t} "
                    f"WHERE r2_key IS NULL AND {col} IS NOT NULL AND length({col}) > 0 ORDER BY id LIMIT :n"),
                    {"n": lote - moved}).fetchall()
            except Exception as exc:
                db.session.rollback()
                failed.append(f"{t}: {str(exc)[:120]}")
                continue
            for row_id, data, mime in rows:
                if time.time() > deadline:
                    break
                data = bytes(data or b"")
                key = ph._key(t, row_id, mime)
                try:
                    H["r2_put"](key, data, mime)
                    back = H["r2_get"](key)  # confere a cópia antes de esvaziar o banco
                    if len(back) != len(data) or back[:64] != data[:64]:
                        raise RuntimeError("cópia no R2 diferente do original")
                    db.session.execute(text(f"UPDATE {t} SET r2_key = :k, {col} = :e WHERE id = :i AND r2_key IS NULL"),
                                       {"k": key, "e": b"", "i": row_id})
                    db.session.commit()
                    moved += 1
                    mb += len(data) / 1048576.0
                except Exception as exc:
                    db.session.rollback()
                    failed.append(f"{t}#{row_id}: {str(exc)[:120]}")
                    try:
                        H["r2_del"](key)
                    except Exception:
                        pass
            del rows
        if moved:
            audit("V107_FOTOS_PARA_R2", 0, f"{moved} foto(s) do banco copiadas para o R2 e conferidas ({mb:.1f} MB)")
        restantes = sum(x.get("no_banco", 0) for x in photo_status())
        return jsonify({"ok": True, "migradas": moved, "mb": round(mb, 1), "falhas": failed[:20], "restantes": restantes})

    @app.post("/api/diagnostico/compactar/v107")
    @login_required
    def v107_compact():
        g = guard()
        if g:
            return g
        if not is_principal():
            return jsonify({"ok": False, "error": "Somente o administrador principal."}), 403
        if str((request.get_json(silent=True) or {}).get("confirmacao") or "").strip() != "COMPACTAR":
            return jsonify({"ok": False, "error": "Digite COMPACTAR para confirmar."}), 400
        if not is_pg():
            return jsonify({"ok": False, "error": "Compactação só existe no PostgreSQL."}), 400
        db.session.rollback()
        res = []
        with db.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as c:
            for t in COMPACT_TABLES:
                try:
                    before = c.execute(text(f"SELECT pg_total_relation_size('{t}')")).scalar() or 0
                    t0 = time.time()
                    c.execute(text(f"VACUUM (FULL, ANALYZE) {t}"))
                    after = c.execute(text(f"SELECT pg_total_relation_size('{t}')")).scalar() or 0
                    res.append({"tabela": t, "antes_mb": round(before / 1048576.0, 1), "depois_mb": round(after / 1048576.0, 1),
                                "segundos": round(time.time() - t0, 1)})
                except Exception as exc:
                    res.append({"tabela": t, "erro": str(exc)[:160]})
        total = round(sum(r.get("antes_mb", 0) - r.get("depois_mb", 0) for r in res), 1)
        audit("V107_COMPACTAR", 0, f"VACUUM FULL em {len(res)} tabela(s): {total} MB devolvidos")
        return jsonify({"ok": True, "tabelas": res, "liberado_mb": total})

    # ---------------- 4) mapa do R2 com resultado guardado ----------------
    ep = "v88b_r2_map"
    if ep in app.view_functions:
        orig = app.view_functions[ep]
        cache = {}

        def v107_r2_map_cached(*a, **kw):
            if request.args.get("formato") == "csv":
                return orig(*a, **kw)
            k = request.args.get("dias") or "7"
            hit = cache.get(k)
            if hit and request.args.get("fresh") != "1" and time.time() - hit[0] < 1800:
                resp = jsonify(dict(hit[1], guardado_em=hit[2], do_cache=True))
                return resp
            resp = orig(*a, **kw)
            try:
                if getattr(resp, "status_code", 200) == 200 and resp.is_json:
                    cache[k] = (time.time(), resp.get_json(), datetime.utcnow().isoformat() + "Z")
            except Exception:
                pass
            return resp

        app.view_functions[ep] = v107_r2_map_cached

    # ---------------- 5) API da Coleta de Valores (tela aposentada) ----------------
    for rule in list(app.url_map.iter_rules()):
        if rule.rule == "/api/financeiro/coletas/v79" and "GET" in (rule.methods or ()):
            app.view_functions[rule.endpoint] = lambda *a, **k: (jsonify({"ok": False, "error": "Coleta de Valores foi aposentada (V88.0 REV17)."}), 410)

    return ph
