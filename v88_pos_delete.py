"""V88.0 REV2 — exclusão definitiva de POS do Metrô (Field > Troca POS Metrô).
Módulo independente: usa SQL direto nas tabelas existentes e não altera o v874_pos_metro.py.
Regras: só quem tem 'field.pos_metro.import' (gestão); confirmação digitando a identificação do POS;
antes de apagar, grava um registro de auditoria (snapshot) em v88_pos_metro_exclusoes."""
import json
from datetime import datetime
from flask import request, session, redirect, jsonify, abort
from sqlalchemy import text

PERM = 'field.pos_metro.import'


def install_pos_delete(app, db, can):
    state = {'ok': False}

    def ensure():
        if state['ok']:
            return
        t = db.Table('v88_pos_metro_exclusoes', db.metadata,
                     db.Column('id', db.Integer, primary_key=True),
                     db.Column('pos_id', db.Integer, nullable=False),
                     db.Column('terminal', db.String(90)),
                     db.Column('linha', db.String(100)),
                     db.Column('estacao', db.String(150)),
                     db.Column('status', db.String(25)),
                     db.Column('qtd_eventos', db.Integer, default=0),
                     db.Column('qtd_fotos', db.Integer, default=0),
                     db.Column('excluido_por', db.Integer),
                     db.Column('excluido_em', db.DateTime, default=datetime.utcnow),
                     db.Column('snapshot', db.Text),
                     extend_existing=True)
        t.create(bind=db.engine, checkfirst=True)
        state['t'] = t
        state['ok'] = True

    @app.post('/field/troca-pos-metro/<int:pid>/excluir-pos')
    def v88_pos_delete(pid):
        if not session.get('user_id'):
            return redirect('/login')
        if not can(PERM):
            abort(403)
        ensure()
        try:
            row = db.session.execute(text('SELECT id,terminal,line,station,status,serial,model,manufacturer,client FROM v874_pos_metro WHERE id=:i'), {'i': pid}).mappings().first()
            if not row:
                return jsonify(error='POS não encontrado (talvez já excluído).'), 404
            typed = (request.form.get('confirmar') or '').strip().lower()
            if typed != (row['terminal'] or '').strip().lower():
                return jsonify(error='Confirmação inválida: digite exatamente a identificação do POS.'), 400
            events = [dict(r) for r in db.session.execute(text('SELECT id,old_serial,new_serial,old_model,new_model,notes,user_id,occurred_at FROM v874_pos_metro_events WHERE pos_id=:i ORDER BY id'), {'i': pid}).mappings()]
            ev_ids = [e['id'] for e in events]
            photos = []
            if ev_ids:
                photos = [dict(r) for r in db.session.execute(text('SELECT id,event_id,filename,mimetype,created_at FROM v876_pos_metro_photos WHERE event_id IN (SELECT id FROM v874_pos_metro_events WHERE pos_id=:i)'), {'i': pid}).mappings()]
            snap = json.dumps({'pos': dict(row), 'eventos': events, 'fotos': photos}, default=str, ensure_ascii=False)
            db.session.execute(state['t'].insert().values(
                pos_id=pid, terminal=row['terminal'], linha=row['line'], estacao=row['station'], status=row['status'],
                qtd_eventos=len(events), qtd_fotos=len(photos), excluido_por=session.get('user_id'),
                excluido_em=datetime.utcnow(), snapshot=snap))
            db.session.execute(text('DELETE FROM v876_pos_metro_photos WHERE event_id IN (SELECT id FROM v874_pos_metro_events WHERE pos_id=:i)'), {'i': pid})
            db.session.execute(text('DELETE FROM v874_pos_metro_events WHERE pos_id=:i'), {'i': pid})
            db.session.execute(text('DELETE FROM v874_pos_metro WHERE id=:i'), {'i': pid})
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        return redirect('/field/troca-pos-metro')

    @app.after_request
    def v88_pos_delete_inject(resp):
        try:
            if request.path != '/field/troca-pos-metro' or request.method != 'GET' or resp.status_code != 200:
                return resp
            if not (resp.mimetype or '').startswith('text/html') or not session.get('user_id') or not can(PERM):
                return resp
            html = resp.get_data(as_text=True)
            if 'pos_delete_v88.js' in html or '</body>' not in html:
                return resp
            html = html.replace('</body>', '<script defer src="/static/pos_delete_v88.js?v=88.2"></script></body>', 1)
            resp.set_data(html)
        except Exception:
            pass
        return resp


def install_mobile_menu_fix(app):
    """V88.0 REV2 — injeta o CSS que corrige o submenu (Field etc.) no celular, sem alterar base.html."""
    @app.after_request
    def v88_mobile_menu_css(resp):
        try:
            if request.method != 'GET' or resp.status_code != 200 or not (resp.mimetype or '').startswith('text/html'):
                return resp
            html = resp.get_data(as_text=True)
            if 'mainNavV424' not in html or 'menu_mobile_v88.css' in html or '</head>' not in html:
                return resp
            resp.set_data(html.replace('</head>', '<link rel="stylesheet" href="/static/menu_mobile_v88.css?v=88.2"></head>', 1))
        except Exception:
            pass
        return resp


def install_rev5_ui(app, db, User, SystemProfile):
    """V88.0 REV5 — injeta (1) herança de datas na APT e (2) nome do perfil em Usuários, sem alterar templates."""
    import json as _json

    @app.after_request
    def v88_rev5_inject(resp):
        try:
            if request.method != 'GET' or resp.status_code != 200 or not (resp.mimetype or '').startswith('text/html') or not session.get('user_id'):
                return resp
            path = request.path
            if path == '/rh/apt':
                html = resp.get_data(as_text=True)
                if 'apt_herdar_v88.js' in html or 'aptEditDialog' not in html or '</body>' not in html:
                    return resp
                resp.set_data(html.replace('</body>', '<script defer src="/static/apt_herdar_v88.js?v=88.5"></script></body>', 1))
            elif path == '/usuarios':
                html = resp.get_data(as_text=True)
                if 'users_profile_v88.js' in html or 'userDataRow' not in html or '</body>' not in html:
                    return resp
                rows = (db.session.query(User.id, SystemProfile.id, SystemProfile.name)
                        .join(SystemProfile, SystemProfile.id == User.system_profile_id)
                        .filter(User.archived_at.is_(None)).all())
                data = {str(u): {'id': pid, 'name': name or ''} for u, pid, name in rows}
                payload = _json.dumps(data, ensure_ascii=False).replace('<', '\\u003c')
                tag = ('<script>window.__V88_USER_PROFILES=' + payload + ';</script>'
                       '<script defer src="/static/users_profile_v88.js?v=88.5"></script>')
                resp.set_data(html.replace('</body>', tag + '</body>', 1))
        except Exception:
            pass
        return resp
