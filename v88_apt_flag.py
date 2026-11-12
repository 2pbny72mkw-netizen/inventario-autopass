"""V88.0 REV7 — box "Precisa de APT? (S/N)" no Cadastro de Usuários (criar e editar), sem trocar templates.
Só os usuários marcados (S) aparecem em RH › APT, nos filtros e nos seletores; os desmarcados (N) não geram vínculo de APT."""
import re
from flask import request, session


_CSS = ('<style>.needsAptBox{grid-column:1/-1;border:1px solid #d7e1ee;border-left:4px solid #1d4ed8;border-radius:12px;padding:12px 14px;background:#f8fbff}'
        '.needsAptBox label.naRow{display:flex!important;flex-direction:row!important;align-items:center!important;gap:12px!important;margin:0!important;cursor:pointer;width:100%}'
        '.needsAptBox .naSw{position:relative;flex:none;width:46px;height:26px;border-radius:999px;background:#cbd5e1;transition:background .15s}'
        '.needsAptBox .naSw:after{content:"";position:absolute;top:3px;left:3px;width:20px;height:20px;border-radius:50%;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,.3);transition:left .15s}'
        '.needsAptBox input.naCk{position:absolute!important;opacity:0!important;width:1px!important;height:1px!important;margin:0!important;padding:0!important;border:0!important}'
        '.needsAptBox input.naCk:checked+.naSw{background:#16a34a}.needsAptBox input.naCk:checked+.naSw:after{left:23px}'
        '.needsAptBox input.naCk:focus-visible+.naSw{outline:3px solid #93c5fd;outline-offset:2px}'
        '.needsAptBox .naTx{flex:1;min-width:0;display:flex;flex-direction:column;gap:2px}.needsAptBox .naTx b{font-size:14px;color:#0f172a}'
        '.needsAptBox .naTx small{font-size:12px;color:#64748b;line-height:1.35}'
        '.needsAptBox .naSt{flex:none;font-weight:800;font-size:12px;padding:4px 12px;border-radius:999px;background:#e2e8f0;color:#475569}'
        '.needsAptBox input.naCk:checked~.naSt{background:#dcfce7;color:#166534}'
        '.needsAptBox .naSt:before{content:"N — Não"}.needsAptBox input.naCk:checked~.naSt:before{content:"S — Sim"}</style>')


def _box(checked):
    return (_CSS + '<div class="full needsAptBox"><input type="hidden" name="needs_apt_present" value="1">'
            '<label class="naRow"><input type="checkbox" class="naCk" name="needs_apt" value="1"' + (' checked' if checked else '') + '>'
            '<span class="naSw" aria-hidden="true"></span>'
            '<span class="naTx"><b>Precisa de APT?</b><small>Sim: aparece em RH › APT, nos filtros e no vínculo de APT. '
            'Não: não aparece nessa tela nem recebe vínculo de APT.</small></span>'
            '<span class="naSt"></span></label></div>')


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
