"""V88.0 REV10 — desempenho e padronização sem trocar templates.
 1) Estáticos com versão por conteúdo (?h=<hash>) e cache longo (immutable) — só quando o link traz o hash.
 2) Cache curto (20 s, por usuário) dos contadores do menu que rodam em quase todas as telas.
 3) Título da aba padronizado ("Tela | Sistema de Gestão") e script de rótulos de acessibilidade."""
import hashlib, os, re, time
from flask import request, session, Response, make_response

_HASH = {}          # caminho relativo -> (mtime_ns, hash8)
_RE_ATTR = re.compile(r'(\b(?:href|src)=")(/static/[^"?#]+)((?:\?[^"#]*)?)(")')
_RE_TITLE = re.compile(r'<title>(.*?)</title>', re.I | re.S)
_SUFFIX = re.compile(r'\s*[|·\-–—]\s*(Inventário SP|Sistema de Gestão|Autopass|Inventário Autopass|AUTOPASS)\s*$', re.I)
_VERSION = re.compile(r'\s*[·\-–—|]?\s*\bV\d+(?:\.\d+)*(?:\s*REV\d+)?\b\s*$', re.I)
_CACHED_APIS = {'/api/notificacoes', '/api/v76/notificacoes', '/api/materials/pending-count', '/api/gestao/autorizacoes-jornada/count'}
_TTL = 20
_API_CACHE = {}     # (uid, path, query) -> (expira, bytes, mimetype)
_API_MAX = 2000


def _file_hash(app, rel):
    full = os.path.join(app.static_folder, rel)
    try:
        st = os.stat(full)
    except OSError:
        return None
    hit = _HASH.get(rel)
    if hit and hit[0] == st.st_mtime_ns:
        return hit[1]
    h = hashlib.sha1()
    with open(full, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    val = h.hexdigest()[:10]
    _HASH[rel] = (st.st_mtime_ns, val)
    return val


def _clean_title(t):
    t = re.sub(r'\s+', ' ', t).strip()
    base = t
    for _ in range(3):
        n = _SUFFIX.sub('', base)
        n = _VERSION.sub('', n)
        if n == base:
            break
        base = n
    base = base.strip(' |·-–—')
    return (base + ' | Sistema de Gestão') if base else 'Sistema de Gestão'


def install_perf(app):
    @app.before_request
    def v88_api_cache_get():
        try:
            if request.method != 'GET' or request.path not in _CACHED_APIS:
                return None
            uid = session.get('user_id')
            if not uid:
                return None
            hit = _API_CACHE.get((uid, request.path, request.query_string))
            if hit and hit[0] > time.monotonic():
                if hit[3] and hit[3] not in (request.headers.get('Accept-Encoding', '') or ''):
                    return None   # resposta guardada comprimida e o cliente não aceita: deixa passar
                resp = Response(hit[1], mimetype=hit[2])
                if hit[3]:
                    resp.headers['Content-Encoding'] = hit[3]
                    resp.headers['Vary'] = 'Accept-Encoding'
                resp.headers['Cache-Control'] = 'private, no-store'
                resp.headers['X-Cache-Badge'] = 'HIT'
                return resp
        except Exception:
            pass
        return None

    @app.after_request
    def v88_perf_after(resp):
        try:
            path = request.path
            if request.method in ('POST', 'PUT', 'PATCH', 'DELETE') and session.get('user_id'):
                _uid = session.get('user_id')   # qualquer gravação do usuário invalida os contadores dele
                for k in [k for k in _API_CACHE if k[0] == _uid]:
                    _API_CACHE.pop(k, None)
            if request.method == 'GET' and resp.status_code == 200:
                if path.startswith('/static/') and request.args.get('h'):
                    resp.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
                    return resp
                if path in _CACHED_APIS and session.get('user_id') and resp.mimetype == 'application/json' and not resp.direct_passthrough:
                    if len(_API_CACHE) > _API_MAX:
                        now = time.monotonic()
                        for k in [k for k, v in _API_CACHE.items() if v[0] <= now]:
                            _API_CACHE.pop(k, None)
                        if len(_API_CACHE) > _API_MAX:
                            _API_CACHE.clear()
                    _API_CACHE[(session['user_id'], path, request.query_string)] = (time.monotonic() + _TTL, resp.get_data(), resp.mimetype, resp.headers.get('Content-Encoding'), request.headers.get('Accept-Encoding', ''))
                    return resp
            if request.method != 'GET' or resp.status_code != 200 or not (resp.mimetype or '') == 'text/html' or resp.direct_passthrough:
                return resp
            html = resp.get_data(as_text=True)
            if '</head>' not in html.lower():
                return resp

            def _rewrite(m):
                rel = m.group(2)[len('/static/'):]
                q = m.group(3)
                if 'h=' in q:
                    return m.group(0)
                hv = _file_hash(app, rel)
                if not hv:
                    return m.group(0)
                q = (q + '&h=' + hv) if q else ('?h=' + hv)
                return m.group(1) + m.group(2) + q + m.group(4)
            html = _RE_ATTR.sub(_rewrite, html)
            tm = _RE_TITLE.search(html)
            if tm:
                html = html[:tm.start()] + '<title>' + _clean_title(re.sub(r'<[^>]+>', '', tm.group(1))) + '</title>' + html[tm.end():]
            if 'a11y_v88.js' not in html and '</body>' in html:
                hv = _file_hash(app, 'a11y_v88.js')
                if hv:
                    html = html.replace('</body>', '<script defer src="/static/a11y_v88.js?v=88.10&h=' + hv + '"></script></body>', 1)
            resp.set_data(html)
        except Exception:
            pass
        return resp
