"""V88.0 REV7 — box "Precisa de APT? (S/N)" no Cadastro de Usuários (criar e editar), sem trocar templates.
Só os usuários marcados (S) aparecem em RH › APT, nos filtros e nos seletores; os desmarcados (N) não geram vínculo de APT."""
import re
from flask import request, session


def _box(checked):
    return ('<div class="full needsAptBox" style="border:1px solid #d7e1ee;border-radius:10px;padding:10px 12px;background:#f8fbff">'
            '<input type="hidden" name="needs_apt_present" value="1">'
            '<label style="display:flex;gap:8px;align-items:center;font-weight:700;cursor:pointer">'
            '<input type="checkbox" name="needs_apt" value="1"' + (' checked' if checked else '') + '> Precisa de APT? (S/N)</label>'
            '<div style="font-size:12px;color:#64748b;margin-top:4px">Marcado (S): o colaborador aparece em RH › APT, nos filtros e no vínculo de APT. '
            'Desmarcado (N): não aparece nessa tela nem recebe vínculo de APT.</div></div>')


def install_apt_flag(app, db, User):
    edit_re = re.compile(r'^/usuarios/(\d+)/editar-form$')

    @app.after_request
    def v88_apt_flag_inject(resp):
        try:
            if request.method != 'GET' or resp.status_code != 200 or not (resp.mimetype or '').startswith('text/html') or not session.get('user_id'):
                return resp
            path = request.path
            m = edit_re.match(path)
            if not m and path != '/usuarios':
                return resp
            html = resp.get_data(as_text=True)
            if 'needsAptBox' in html:
                return resp
            if m:
                uid = int(m.group(1))
                row = db.session.query(User.needs_apt).filter(User.id == uid).first()
                box = _box(bool(row and row[0]))
                i = html.find('<div class="full accessBox"')
                if i < 0:
                    i = html.rfind('</form>')
            else:
                box = _box(False)
                f = html.find('id="userForm"')
                if f < 0:
                    return resp
                i = html.find('<div class="full accessBox"', f)
                if i < 0:
                    i = html.find('</form>', f)
            if i < 0:
                return resp
            resp.set_data(html[:i] + box + html[i:])
        except Exception:
            pass
        return resp
