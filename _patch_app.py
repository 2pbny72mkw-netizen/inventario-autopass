# -*- coding: utf-8 -*-
"""Ajuste do app.py do SEU repositorio (a versao no ar), sem substitui-lo: registra o modulo novo e atualiza o rotulo da versao.
Executado por aplicar_versao.py. Seguro para rodar de novo (nao duplica)."""
import re

ANCHOR = "install_v86(app, db, User, _has_access)"
ADD = ("\nfrom v103_estoque_foto import install_estoque_foto  # V88.0 REV15 - foto do material (camera/galeria/trocar)\n"
       "install_estoque_foto(app, db, text, _has_access)\n")
RELEASE = "V88.0 REV15"


def patch(src):
    notes = []
    if "install_estoque_foto(" not in src:
        i = src.find(ANCHOR)
        if i < 0:
            raise RuntimeError("nao achei '" + ANCHOR + "' no app.py - me avise, nao faca o deploy")
        j = src.index("\n", i)
        src = src[:j] + ADD.rstrip("\n") + src[j:]
        notes.append("modulo v103_estoque_foto registrado")
    new, n = re.subn(r'(APP_RELEASE\s*=\s*")[^"]+(")', r'\g<1>' + RELEASE + r'\g<2>', src, count=1)
    if n:
        if new != src:
            notes.append("APP_RELEASE = " + RELEASE)
        src = new
    else:
        raise RuntimeError("nao achei APP_RELEASE no app.py")
    return src, notes
