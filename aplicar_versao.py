#!/usr/bin/env python3
"""Autopass - aplicar pacote de versao no repositorio local e conferir antes do deploy.

Uso (PowerShell, na pasta do repositorio ou informando o caminho):
    python aplicar_versao.py PASTA_DO_PACOTE [PASTA_DO_REPOSITORIO] [--commit]

O que faz:
  1. Copia cada arquivo do pacote (app.py, templates/, static/...) para o repositorio, mantendo as pastas.
  2. Confere que cada arquivo copiado ficou IDENTICO ao do pacote (SHA-256) e que nada do pacote ficou de fora.
  3. Verifica que todo arquivo estatico citado pelos templates existe (pega o erro "esqueci a pasta static").
  4. Compila o app.py e abre todos os templates no Jinja (se o jinja2 estiver instalado).
  5. Mostra o resumo e, com --commit, faz o commit local (NUNCA envia ao GitHub: o push continua manual).
Nao apaga nem altera nada fora dos arquivos do pacote.
"""
import hashlib, os, py_compile, re, shutil, subprocess, sys, tempfile

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()

def main(argv):
    flags = [a for a in argv if a.startswith('--')]
    args = [a for a in argv if not a.startswith('--')]
    if not args:
        print(__doc__); return 2
    pkg = os.path.abspath(args[0]); repo = os.path.abspath(args[1] if len(args) > 1 else os.getcwd())
    if not os.path.isdir(pkg): print('ERRO: pasta do pacote nao existe:', pkg); return 2
    if not os.path.isfile(os.path.join(repo, 'app.py')): print('ERRO: nao achei app.py em', repo, '- informe a pasta do repositorio.'); return 2
    problems, copied = [], []
    for dp, _, fns in os.walk(pkg):
        for fn in fns:
            src = os.path.join(dp, fn); rel = os.path.relpath(src, pkg).replace('\\', '/')
            if rel.upper().startswith('LEIA-ME') or rel.lower().endswith(('.sha256.txt', '.zip')): continue
            dst = os.path.join(repo, rel); os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst); copied.append(rel)
            if sha(src) != sha(dst): problems.append('copia diferente do pacote: ' + rel)
    if not copied: print('ERRO: o pacote esta vazio.'); return 2
    print(f'[1/4] Copiados e conferidos {len(copied)} arquivos.')
    if not any(c.startswith('static/') for c in copied):
        print('      aviso: este pacote nao traz arquivos em static/ (normal em versoes so de servidor).')
    # 3. estaticos citados pelos templates
    missing = set(); tdir = os.path.join(repo, 'templates')
    pat = re.compile(r"url_for\(\s*['\"]static['\"]\s*,\s*filename\s*=\s*['\"]([^'\"]+)['\"]")
    if os.path.isdir(tdir):
        for fn in os.listdir(tdir):
            if fn.endswith('.html'):
                txt = open(os.path.join(tdir, fn), encoding='utf-8', errors='ignore').read()
                for m in pat.findall(txt):
                    if not os.path.isfile(os.path.join(repo, 'static', m)): missing.add(f'{m} (citado em templates/{fn})')
    if missing: problems += ['arquivo estatico ausente: ' + m for m in sorted(missing)]
    print('[2/4] Arquivos estaticos citados pelos templates: ' + ('TODOS presentes.' if not missing else f'{len(missing)} AUSENTE(S)!'))
    # 4. compilacao e Jinja
    try:
        py_compile.compile(os.path.join(repo, 'app.py'), cfile=os.path.join(tempfile.gettempdir(), 'autopass_app.pyc'), doraise=True)
        print('[3/4] app.py compila sem erro.')
    except py_compile.PyCompileError as e:
        problems.append('app.py nao compila: ' + str(e)[:300]); print('[3/4] app.py COM ERRO de sintaxe.')
    try:
        import jinja2
        env = jinja2.Environment(); bad = 0; n = 0
        for fn in sorted(os.listdir(tdir)) if os.path.isdir(tdir) else []:
            if fn.endswith('.html'):
                n += 1
                try: env.parse(open(os.path.join(tdir, fn), encoding='utf-8').read())
                except Exception as e: bad += 1; problems.append(f'template com erro: {fn}: {str(e)[:200]}')
        print(f'[4/4] Templates abertos no Jinja: {n - bad}/{n} ok.')
    except ImportError:
        print('[4/4] jinja2 nao instalado: etapa de templates pulada (rode: pip install jinja2).')
    if problems:
        print('\nPROBLEMAS ENCONTRADOS - NAO FACA O DEPLOY:'); [print('  -', p) for p in problems]; return 1
    print('\nTUDO CERTO. Arquivos alterados:'); [print('  ', c) for c in copied]
    if '--commit' in flags:
        try:
            ver = re.search(r'APP_RELEASE\s*=\s*"([^"]+)"', open(os.path.join(repo, 'app.py'), encoding='utf-8').read())
            msg = (ver.group(1) if ver else 'versao') + ' - aplicada com aplicar_versao.py'
            subprocess.run(['git', '-C', repo, 'add', '--'] + copied, check=True)
            subprocess.run(['git', '-C', repo, 'commit', '-m', msg], check=True)
            print('Commit local feito:', msg, '\nPara publicar, faca o push manualmente (git push).')
        except Exception as e:
            print('Nao consegui commitar:', e); return 1
    else:
        print('\nProximo passo: revise com "git status" / "git diff", faca o commit e o push como de costume.')
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
