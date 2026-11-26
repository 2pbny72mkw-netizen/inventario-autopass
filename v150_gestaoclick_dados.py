# -*- coding: utf-8 -*-
"""V88.0 REV65 — GestãoClick (sistema anterior da Assistência): carga das planilhas exportadas e telas.

Planilhas aceitas (exportadas dos relatórios do GestãoClick em Excel, reconhecidas pelo título da 1ª linha):
- "Relatório de ordens de serviços"   -> v150_gc_os        (OS: cliente, datas, equipamento/série, situação, garagem...)
- "Notas fiscais (NF-e)"              -> v150_gc_nfe       (NF-e: destinatário, natureza, total, impostos, situação)
- "Relatório de estoque"              -> v150_gc_produtos  (saldo, mínimo, máximo, custo, preços)
- "Relatório de produtos"             -> v150_gc_produtos  (código, nome, custo, varejo)
- "Relatório de produtos comprados"   -> v150_gc_compras   (por período: quantidade, valor unitário, total)
- "Relatório de fornecedores"         -> v150_gc_fornecedores

Telas:
- /gestao/gestaoclick                          carga das planilhas (Gestor)
- /portal-cliente/assistencia-tecnica/gestaoclick  histórico de OS (equipe do Portal), paginado no servidor
- /portal-cliente/assistencia-tecnica/gestaoclick-nfe  NF-e (mesma senha da área financeira)
- /engenharia/estoque/apoio-compras            apoio a compras: saldo x compras do período, sugestão
"""
import io
import json
import re
import unicodedata
from datetime import date, datetime

KINDS = [  # (prefixo do título normalizado, tipo)
    ("RELATORIO DE ORDENS DE SERVICOS", "os"),
    ("NOTAS FISCAIS (NF-E)", "nfe"),
    ("RELATORIO DE PRODUTOS COMPRADOS", "compras"),
    ("RELATORIO DE ESTOQUE", "estoque"),
    ("RELATORIO DE PRODUTOS", "produtos"),
    ("RELATORIO DE FORNECEDORES", "fornecedores"),
]
KIND_LABEL = {"xml": "XMLs de NF-e (faturamento por item)", "os": "Ordens de serviço", "nfe": "NF-e", "compras": "Produtos comprados", "estoque": "Estoque de produtos",
              "produtos": "Produtos", "fornecedores": "Fornecedores"}


def fold(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode("ascii")
    return " ".join(s.upper().split())


def skey(s):
    return re.sub(r"[^A-Z0-9]", "", fold(s))[:120]


def num(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("R$", "").strip()
    if not s or set(s) <= {"-"}:
        return None
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def txt(v, n=300):
    if v is None:
        return None
    s = str(v).strip()
    if not s or set(s) <= {"-"}:
        return None
    return s[:n]


def dt(v):
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    s = str(v or "").strip()
    m = re.match(r"^(\d{2})/(\d{2})/(\d{4})", s)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            return None
    return None


def period_of(cell):
    m = re.findall(r"(\d{2}/\d{2}/\d{4})", str(cell or ""))
    return (dt(m[0]), dt(m[1])) if len(m) >= 2 else (None, None)


def serial_of(equip):
    """'VALIDADOR - LUNA - B80 - 1221' -> '1221'; 'Validador B80 - 0001749' -> '0001749'."""
    s = str(equip or "").strip()
    if not s:
        return None
    parte = s.split(",")[0].split(" - ")[-1].strip()
    return parte[:120] or None


def read_sheet(raw):
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    ws = wb.worksheets[0]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    wb.close()
    return rows


def detect(rows):
    if not rows:
        return None
    t = fold(rows[0][0] if rows[0] else "")
    for pref, k in KINDS:
        if t.startswith(pref):
            return k
    return None


def ensure(engine):
    from sqlalchemy import text
    stmts = [
        "CREATE TABLE IF NOT EXISTS v150_gc_os (codigo VARCHAR(30) PRIMARY KEY, loja VARCHAR(80), cliente VARCHAR(200), data DATE,"
        " previsao DATE, equipamento VARCHAR(300), serial VARCHAR(120), serial_key VARCHAR(120), situacao VARCHAR(80), custo FLOAT,"
        " total FLOAT, garagem VARCHAR(120), dt_atendimento DATE, os_retorno VARCHAR(80), tecnico_reinc VARCHAR(120), carregado_em TIMESTAMP)",
        "CREATE INDEX IF NOT EXISTS ix_v150_os_serial ON v150_gc_os (serial_key)",
        "CREATE INDEX IF NOT EXISTS ix_v150_os_data ON v150_gc_os (data)",
        "CREATE TABLE IF NOT EXISTS v150_gc_nfe (numero VARCHAR(30), tipo VARCHAR(20), data DATE, cliente VARCHAR(200), documento VARCHAR(30),"
        " natureza VARCHAR(160), total FLOAT, icms FLOAT, ipi FLOAT, pis FLOAT, cofins FLOAT, situacao VARCHAR(40), carregado_em TIMESTAMP,"
        " PRIMARY KEY (numero, tipo))",
        "CREATE TABLE IF NOT EXISTS v150_gc_produtos (codigo VARCHAR(40) PRIMARY KEY, nome VARCHAR(300), unidade VARCHAR(20), estoque FLOAT,"
        " estoque_min FLOAT, estoque_max FLOAT, custo_unit FLOAT, custo_total FLOAT, revenda FLOAT, varejo FLOAT, custo_cadastro FLOAT,"
        " carregado_em TIMESTAMP)",
        "CREATE TABLE IF NOT EXISTS v150_gc_compras (codigo VARCHAR(40), periodo_ini DATE, periodo_fim DATE, nome VARCHAR(300), quantidade FLOAT,"
        " valor_unit FLOAT, valor_total FLOAT, carregado_em TIMESTAMP, PRIMARY KEY (codigo, periodo_ini, periodo_fim))",
        "CREATE TABLE IF NOT EXISTS v150_gc_fornecedores (chave VARCHAR(220) PRIMARY KEY, tipo VARCHAR(40), nome VARCHAR(220), documento VARCHAR(30),"
        " telefone VARCHAR(60), email VARCHAR(160), cidade VARCHAR(100), uf VARCHAR(4), carregado_em TIMESTAMP)",
        "CREATE TABLE IF NOT EXISTS v150_gc_cargas (id BIGINT PRIMARY KEY, arquivo VARCHAR(255), tipo VARCHAR(20), periodo VARCHAR(60), linhas INTEGER,"
        " criado_em TIMESTAMP, usuario VARCHAR(180))",
    ]
    with engine.begin() as c:
        for s in stmts:
            c.execute(text(s))


def _upsert(c, table, keys, rows):
    """Apaga as chaves presentes e insere de novo (portável PostgreSQL/SQLite), em lotes."""
    from sqlalchemy import text
    if not rows:
        return
    cols = list(rows[0].keys())
    ins = text("INSERT INTO %s (%s) VALUES (%s)" % (table, ",".join(cols), ",".join(":" + k for k in cols)))
    for i in range(0, len(rows), 400):
        part = rows[i:i + 400]
        if len(keys) == 1:
            k = keys[0]
            c.execute(text("DELETE FROM %s WHERE %s IN (%s)" % (table, k, ",".join(":k%d" % j for j in range(len(part))))),
                      {"k%d" % j: r[k] for j, r in enumerate(part)})
        else:
            for r in part:
                c.execute(text("DELETE FROM %s WHERE %s" % (table, " AND ".join("%s=:%s" % (k, k) for k in keys))), {k: r[k] for k in keys})
        c.execute(ins, part)


def _data_rows(rows, head_idx=1):
    """Linhas de dados entre o cabeçalho (linha 2) e os totais do rodapé ('Total ...:', 'Valor Total:' etc.)."""
    out = []
    for r in rows[head_idx + 1:]:
        if not r or all(v in (None, "") for v in r):
            continue
        a = str(r[0] or "").strip()
        if a.endswith(":") and all(v in (None, "") for v in r[1:-1]):
            continue
        out.append(r)
    return out


def import_file(engine, raw, filename, user_name):
    from sqlalchemy import text
    rows = read_sheet(raw)
    kind = detect(rows)
    if not kind:
        raise ValueError("Planilha não reconhecida: use os relatórios do GestãoClick exportados em Excel (OS, NF-e, estoque, produtos, produtos comprados ou fornecedores).")
    head = [fold(h) for h in (rows[1] if len(rows) > 1 else [])]
    idx = {h: i for i, h in enumerate(head)}
    g = lambda r, name: r[idx[name]] if name in idx and idx[name] < len(r) else None
    data = _data_rows(rows)
    now = datetime.utcnow()
    p_ini, p_fim = period_of(rows[0][1] if len(rows[0]) > 1 else "")
    out = []
    if kind == "os":
        for r in data:
            cod = txt(g(r, "CODIGO"), 30)
            if not cod or not re.match(r"^\d+$", cod):
                continue
            eq = txt(g(r, "EQUIPAMENTOS"), 300)
            ser = serial_of(eq)
            out.append({"codigo": cod, "loja": txt(g(r, "LOJA"), 80), "cliente": txt(g(r, "CLIENTE"), 200), "data": dt(g(r, "DATA")),
                        "previsao": dt(g(r, "PREVISAO DE ENTREGA")), "equipamento": eq, "serial": ser, "serial_key": skey(ser) if ser else None,
                        "situacao": txt(g(r, "SITUACAO"), 80), "custo": num(g(r, "VALOR CUSTO")), "total": num(g(r, "VALOR TOTAL")),
                        "garagem": txt(g(r, "GARAGEM"), 120), "dt_atendimento": dt(g(r, "DT ATENDIMENTO O.S.")),
                        "os_retorno": txt(g(r, "OS DE RETORNO"), 80), "tecnico_reinc": txt(g(r, "TECNICO REINCIDENCIA"), 120), "carregado_em": now})
        table, keys = "v150_gc_os", ["codigo"]
    elif kind == "nfe":
        for r in data:
            n = txt(g(r, "NO"), 30)
            if not n or not re.match(r"^\d+$", n):
                continue
            out.append({"numero": n, "tipo": txt(g(r, "TIPO"), 20) or "", "data": dt(g(r, "DATA")), "cliente": txt(g(r, "RAZAO SOCIAL/NOME"), 200),
                        "documento": txt(g(r, "CNPJ/CPF"), 30), "natureza": txt(g(r, "NATUREZA"), 160), "total": num(g(r, "TOTAL")),
                        "icms": num(g(r, "ICMS")), "ipi": num(g(r, "IPI")), "pis": num(g(r, "PIS")), "cofins": num(g(r, "COFINS")),
                        "situacao": txt(g(r, "SITUACAO"), 40), "carregado_em": now})
        table, keys = "v150_gc_nfe", ["numero", "tipo"]
    elif kind == "estoque":
        for r in data:
            cod = txt(g(r, "COD. INTERNO"), 40)
            if not cod:
                continue
            out.append({"codigo": cod, "nome": txt(g(r, "NOME"), 300), "unidade": txt(g(r, "UNIDADE"), 20), "estoque": num(g(r, "ESTOQUE")),
                        "estoque_min": num(g(r, "ESTOQUE MIN.")), "estoque_max": num(g(r, "ESTOQUE MAX.")), "custo_unit": num(g(r, "CUSTO UNIT.")),
                        "custo_total": num(g(r, "CUSTO TOTAL")), "revenda": num(g(r, "REVENDA")), "varejo": num(g(r, "VAREJO"))})
        table, keys = "v150_gc_produtos", ["codigo"]
    elif kind == "produtos":
        for r in data:
            cod = txt(g(r, "COD. INTERNO"), 40)
            if not cod:
                continue
            out.append({"codigo": cod, "nome": txt(g(r, "NOME"), 300), "custo_cadastro": num(g(r, "VALOR DE CUSTO")), "varejo": num(g(r, "VR. VAREJO"))})
        table, keys = "v150_gc_produtos", ["codigo"]
    elif kind == "compras":
        if not p_ini:
            raise ValueError("Relatório de produtos comprados sem período na 1ª linha.")
        for r in data:
            cod = txt(g(r, "CODIGO"), 40)
            if not cod:
                continue
            out.append({"codigo": cod, "periodo_ini": p_ini, "periodo_fim": p_fim, "nome": txt(g(r, "NOME DO PRODUTO"), 300),
                        "quantidade": num(g(r, "QUANTIDADE")), "valor_unit": num(g(r, "VALOR UNITARIO")), "valor_total": num(g(r, "VALOR TOTAL")),
                        "carregado_em": now})
        table, keys = "v150_gc_compras", ["codigo", "periodo_ini", "periodo_fim"]
    else:  # fornecedores
        for r in data:
            nome = txt(g(r, "NOME/RAZAO SOCIAL"), 220)
            if not nome:
                continue
            doc = txt(g(r, "DOCUMENTO"), 30)
            out.append({"chave": (re.sub(r"\D", "", doc or "") or skey(nome))[:220], "tipo": txt(g(r, "TIPO"), 40), "nome": nome, "documento": doc,
                        "telefone": txt(g(r, "TELEFONE/CELULAR"), 60), "email": txt(g(r, "E-MAIL"), 160), "cidade": txt(g(r, "CIDADE"), 100),
                        "uf": txt(g(r, "ESTADO"), 4), "carregado_em": now})
        seen, ded = set(), []
        for o in out:
            if o["chave"] not in seen:
                seen.add(o["chave"]); ded.append(o)
        out = ded
        table, keys = "v150_gc_fornecedores", ["chave"]
    ensure(engine)
    with engine.begin() as c:
        if kind in ("estoque", "produtos") and out:
            # mescla: estoque e cadastro de produtos completam a mesma linha sem apagar o que o outro trouxe
            existing = {}
            codes = [o["codigo"] for o in out]
            for i in range(0, len(codes), 400):
                part = codes[i:i + 400]
                for rr in c.execute(text("SELECT * FROM v150_gc_produtos WHERE codigo IN (%s)" % ",".join(":k%d" % j for j in range(len(part)))),
                                    {"k%d" % j: v for j, v in enumerate(part)}):
                    existing[rr._mapping["codigo"]] = dict(rr._mapping)
            base = {k: None for k in ("codigo", "nome", "unidade", "estoque", "estoque_min", "estoque_max", "custo_unit", "custo_total", "revenda",
                                      "varejo", "custo_cadastro", "carregado_em")}
            merged = []
            for o in out:
                m = dict(base); m.update(existing.get(o["codigo"]) or {})
                m.update({k: v for k, v in o.items() if v is not None})
                m["carregado_em"] = now
                merged.append(m)
            out = merged
        _upsert(c, table, keys, out)
        _CACHE.update(at=0.0, rows=None)
        c.execute(text("INSERT INTO v150_gc_cargas (id, arquivo, tipo, periodo, linhas, criado_em, usuario) VALUES (:i,:a,:t,:p,:l,:c,:u)"),
                  {"i": int(now.timestamp() * 1000000), "a": (filename or "")[:255], "t": kind,
                   "p": ("%s a %s" % (p_ini.strftime("%d/%m/%Y"), p_fim.strftime("%d/%m/%Y"))) if p_ini and p_fim else None,
                   "l": len(out), "c": now, "u": (user_name or "")[:180]})
    return {"arquivo": filename, "tipo": kind, "rotulo": KIND_LABEL[kind], "linhas": len(out),
            "periodo": ("%s a %s" % (p_ini.strftime("%d/%m/%Y"), p_fim.strftime("%d/%m/%Y"))) if p_ini and p_fim else None}


def gc_reincidencia(engine, sk, desde):
    """OS do GestãoClick da mesma série (exata) a partir de 'desde' — usada pela checagem de reincidência da Assistência."""
    from sqlalchemy import text
    if not sk:
        return []
    try:
        with engine.connect() as c:
            return [tuple(r) for r in c.execute(text("SELECT codigo, data, situacao, equipamento FROM v150_gc_os WHERE serial_key=:k AND data >= :d"
                                                      " ORDER BY data DESC LIMIT 5"), {"k": sk, "d": desde}).fetchall()]
    except Exception:
        return []


def install_gestaoclick_dados(app, H):
    """H: login_required, gestor() -> resposta de erro/None, portal_staff(), fin_liberado(), can(perm), engine, render(tpl,**kw),
    audit(evento, detalhe), user_name()."""
    from flask import jsonify, request, abort
    from sqlalchemy import text
    login_required, engine = H["login_required"], H["engine"]

    def _ensure():
        ensure(engine)

    # ---------------- carga ----------------
    @app.post("/api/gestaoclick/carga")
    @login_required
    def v150_gc_carga():
        g = H["gestor"]()
        if g:
            return g
        files = request.files.getlist("arquivos") or request.files.getlist("file")
        if not files:
            return jsonify({"ok": False, "error": "Escolha ao menos uma planilha."}), 400
        res = []
        for f in files[:12]:
            raw = f.read()
            try:
                nome = (f.filename or "").lower()
                if nome.endswith(".zip") or nome.endswith(".xml"):
                    H["fat_ensure"]()
                    r = import_nfe_xmls(engine, raw, f.filename, H["user_name"]())
                else:
                    r = import_file(engine, raw, f.filename, H["user_name"]())
                res.append({"ok": True, **r})
            except ValueError as exc:
                res.append({"ok": False, "arquivo": f.filename, "error": str(exc)})
            except Exception:
                app.logger.exception("REV65: falha na carga GestãoClick %s", f.filename)
                res.append({"ok": False, "arquivo": f.filename, "error": "Falha ao ler a planilha."})
        try:
            H["audit"]("GESTAOCLICK_CARGA", "; ".join("%s: %s" % (x.get("arquivo"), x.get("linhas", x.get("error"))) for x in res))
        except Exception:
            pass
        return jsonify({"ok": any(x["ok"] for x in res), "resultados": res})

    @app.get("/api/gestaoclick/cargas")
    @login_required
    def v150_gc_cargas():
        g = H["gestor"]()
        if g:
            return g
        _ensure()
        with engine.connect() as c:
            rows = [dict(r._mapping) for r in c.execute(text("SELECT * FROM v150_gc_cargas ORDER BY criado_em DESC LIMIT 30"))]
            tot = {t: c.execute(text("SELECT COUNT(*) FROM %s" % t)).scalar() for t in
                   ("v150_gc_os", "v150_gc_nfe", "v150_gc_produtos", "v150_gc_compras", "v150_gc_fornecedores")}
        for r in rows:
            r["criado_em"] = r["criado_em"].isoformat() + "Z" if hasattr(r["criado_em"], "isoformat") else r["criado_em"]
            r["rotulo"] = KIND_LABEL.get(r["tipo"], r["tipo"])
        return jsonify({"ok": True, "cargas": rows, "totais": tot})

    # ---------------- OS (histórico) ----------------
    @app.get("/portal-cliente/assistencia-tecnica/gestaoclick")
    @login_required
    def v150_gc_os_page():
        if not H["portal_staff"]():
            abort(403)
        return H["render"]("gestaoclick_os_v150.html")

    def _os_where():
        a = request.args
        w, p = ["1=1"], {}
        if a.get("de"):
            w.append("data >= :de"); p["de"] = a.get("de")
        if a.get("ate"):
            w.append("data <= :ate"); p["ate"] = a.get("ate")
        if a.get("cliente"):
            w.append("cliente = :cli"); p["cli"] = a.get("cliente")
        if a.get("situacao"):
            w.append("situacao = :sit"); p["sit"] = a.get("situacao")
        if a.get("garagem"):
            w.append("garagem = :gar"); p["gar"] = a.get("garagem")
        if a.get("mes"):
            w.append("data >= :m1 AND data < :m2"); y, m = map(int, a.get("mes").split("-"))
            p["m1"] = date(y, m, 1); p["m2"] = date(y + (m == 12), m % 12 + 1, 1)
        if a.get("abertas") == "1":
            w.append("UPPER(COALESCE(situacao,'')) NOT IN ('FINALIZADO','LIBERADO','CANCELADO','ENTREGUE','CONCLUIDO')")
        if a.get("retorno") == "1":
            w.append("os_retorno IS NOT NULL")
        q = (a.get("q") or "").strip()
        if q:
            w.append("(UPPER(equipamento) LIKE :q OR serial_key LIKE :qs OR codigo = :qc OR UPPER(cliente) LIKE :q)")
            p["q"] = "%" + q.upper() + "%"; p["qs"] = "%" + skey(q) + "%"; p["qc"] = q
        return " AND ".join(w), p

    @app.get("/api/gestaoclick/os")
    @login_required
    def v150_gc_os_api():
        if not H["portal_staff"]():
            return jsonify({"ok": False, "error": "Sem permissão"}), 403
        _ensure()
        where, p = _os_where()
        sort_map = {"codigo": "CAST(codigo AS INTEGER)", "data": "data", "cliente": "cliente", "equipamento": "equipamento", "situacao": "situacao",
                    "garagem": "garagem", "previsao": "previsao", "custo": "custo", "dt_atendimento": "dt_atendimento"}
        sort = sort_map.get(request.args.get("ordem") or "data", "data")
        direc = "ASC" if request.args.get("dir") == "asc" else "DESC"
        page = max(1, int(request.args.get("pagina") or 1)); size = min(200, max(10, int(request.args.get("por") or 50)))
        with engine.connect() as c:
            total = c.execute(text("SELECT COUNT(*) FROM v150_gc_os WHERE " + where), p).scalar() or 0
            rows = [dict(r._mapping) for r in c.execute(text(
                "SELECT codigo, cliente, data, previsao, equipamento, serial, situacao, garagem, dt_atendimento, os_retorno, tecnico_reinc, custo"
                " FROM v150_gc_os WHERE " + where + " ORDER BY " + sort + " " + direc + ", CAST(codigo AS INTEGER) DESC LIMIT :lim OFFSET :off"),
                dict(p, lim=size, off=(page - 1) * size))]
            resumo = None
            if request.args.get("resumo") == "1":
                def agg(col, lim=12):
                    return [list(r) for r in c.execute(text("SELECT COALESCE(%s,'(vazio)') k, COUNT(*) n FROM v150_gc_os WHERE %s GROUP BY k ORDER BY n DESC LIMIT %d"
                                                            % (col, where, lim)), p)]
                meses = [[str(r[0]), r[1]] for r in c.execute(text(
                    "SELECT SUBSTR(CAST(data AS VARCHAR(10)),1,7) m, COUNT(*) FROM v150_gc_os WHERE " + where + " AND data IS NOT NULL GROUP BY m ORDER BY m"), p)]
                abertas = c.execute(text("SELECT COUNT(*) FROM v150_gc_os WHERE " + where + " AND UPPER(COALESCE(situacao,'')) NOT IN"
                                         " ('FINALIZADO','LIBERADO','CANCELADO','ENTREGUE','CONCLUIDO')"), p).scalar()
                retorno = c.execute(text("SELECT COUNT(*) FROM v150_gc_os WHERE " + where + " AND os_retorno IS NOT NULL"), p).scalar()
                series = c.execute(text("SELECT COUNT(DISTINCT serial_key) FROM v150_gc_os WHERE " + where), p).scalar()
                filtros = {
                    "clientes": [r[0] for r in c.execute(text("SELECT DISTINCT cliente FROM v150_gc_os WHERE cliente IS NOT NULL ORDER BY cliente"))],
                    "situacoes": [r[0] for r in c.execute(text("SELECT DISTINCT situacao FROM v150_gc_os WHERE situacao IS NOT NULL ORDER BY situacao"))],
                    "garagens": [r[0] for r in c.execute(text("SELECT DISTINCT garagem FROM v150_gc_os WHERE garagem IS NOT NULL ORDER BY garagem"))],
                }
                resumo = {"total": total, "abertas": abertas, "retorno": retorno, "series": series, "por_mes": meses,
                          "por_cliente": agg("cliente", 10), "por_situacao": agg("situacao", 12), "por_garagem": agg("garagem", 10), "filtros": filtros}
        for r in rows:
            for k in ("data", "previsao", "dt_atendimento"):
                r[k] = r[k].isoformat() if hasattr(r[k], "isoformat") else (str(r[k])[:10] if r[k] else None)
        return jsonify({"ok": True, "total": total, "pagina": page, "por": size, "rows": rows, "resumo": resumo})

    @app.get("/api/gestaoclick/os/exportar")
    @login_required
    def v150_gc_os_export():
        if not H["portal_staff"]():
            abort(403)
        import openpyxl
        from flask import send_file
        _ensure()
        where, p = _os_where()
        wb = openpyxl.Workbook(); ws = wb.active; ws.title = "OS GestaoClick"
        cols = ["codigo", "cliente", "data", "previsao", "equipamento", "serial", "situacao", "garagem", "dt_atendimento", "os_retorno", "tecnico_reinc"]
        ws.append(["OS", "Cliente", "Entrada", "Previsão", "Equipamento", "Série", "Situação", "Garagem", "Atendimento", "OS de retorno", "Técnico reincidência"])
        with engine.connect() as c:
            for r in c.execute(text("SELECT " + ",".join(cols) + " FROM v150_gc_os WHERE " + where + " ORDER BY data DESC LIMIT 50000"), p):
                ws.append([v.strftime("%d/%m/%Y") if hasattr(v, "strftime") else v for v in r])
        out = io.BytesIO(); wb.save(out); out.seek(0)
        return send_file(out, as_attachment=True, download_name="os_gestaoclick.xlsx",
                         mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # ---------------- NF-e (área financeira) ----------------
    @app.get("/portal-cliente/assistencia-tecnica/gestaoclick-nfe")
    @login_required
    def v150_gc_nfe_page():
        if not H["portal_staff"]():
            abort(403)
        return H["render"]("gestaoclick_nfe_v150.html")

    @app.get("/api/gestaoclick/nfe")
    @login_required
    def v150_gc_nfe_api():
        if not H["portal_staff"]():
            return jsonify({"ok": False, "error": "Sem permissão"}), 403
        if not H["fin_liberado"]():
            return jsonify({"ok": False, "bloqueado": True, "error": "Digite a senha da área financeira na tela de Faturamento de peças."}), 401
        _ensure()
        with engine.connect() as c:
            rows = [dict(r._mapping) for r in c.execute(text(
                "SELECT numero, tipo, data, cliente, documento, natureza, total, icms, ipi, pis, cofins, situacao FROM v150_gc_nfe ORDER BY data DESC, numero DESC LIMIT 20000"))]
        for r in rows:
            r["data"] = r["data"].isoformat() if hasattr(r["data"], "isoformat") else (str(r["data"])[:10] if r["data"] else None)
        return jsonify({"ok": True, "rows": rows})

    # ---------------- Apoio a compras ----------------
    @app.get("/engenharia/estoque/apoio-compras")
    @login_required
    def v150_gc_compras_page():
        if not H["can"]("engineering.stock.view"):
            abort(403)
        return H["render"]("gestaoclick_compras_v150.html")

    @app.get("/api/gestaoclick/apoio-compras")
    @login_required
    def v150_gc_compras_api():
        if not H["can"]("engineering.stock.view"):
            return jsonify({"ok": False, "error": "Sem permissão"}), 403
        _ensure()
        with engine.connect() as c:
            per = c.execute(text("SELECT periodo_ini, periodo_fim FROM v150_gc_compras GROUP BY periodo_ini, periodo_fim ORDER BY periodo_fim DESC, periodo_ini LIMIT 1")).first()
            comp = {}
            if per:
                for r in c.execute(text("SELECT codigo, nome, quantidade, valor_unit, valor_total FROM v150_gc_compras WHERE periodo_ini=:a AND periodo_fim=:b"),
                                   {"a": per[0], "b": per[1]}):
                    comp[r[0]] = {"nome": r[1], "qtd": r[2] or 0, "unit": r[3], "total": r[4] or 0}
            prods = [dict(r._mapping) for r in c.execute(text("SELECT codigo, nome, unidade, estoque, estoque_min, estoque_max, custo_unit, custo_cadastro, custo_total"
                                                              " FROM v150_gc_produtos"))]
            carga = c.execute(text("SELECT MAX(criado_em) FROM v150_gc_cargas WHERE tipo IN ('estoque','compras')")).scalar()
        ini, fim = (per[0], per[1]) if per else (None, None)
        if ini and not isinstance(ini, date):
            ini, fim = date.fromisoformat(str(ini)[:10]), date.fromisoformat(str(fim)[:10])
        if carga and not isinstance(carga, datetime):
            try:
                carga = datetime.fromisoformat(str(carga)[:19])
            except ValueError:
                carga = None
        ref_fim = min(fim, carga.date()) if (fim and carga) else fim
        meses = max(1.0, ((ref_fim - ini).days + 1) / 30.4) if ini and ref_fim else None
        out, seen = [], set()
        for p in prods:
            cp = comp.get(p["codigo"]) or {}
            seen.add(p["codigo"])
            out.append(_linha(p["codigo"], p["nome"] or cp.get("nome"), p, cp, meses))
        for cod, cp in comp.items():
            if cod not in seen:
                out.append(_linha(cod, cp.get("nome"), {}, cp, meses))
        return jsonify({"ok": True, "rows": out, "periodo": {"ini": ini.isoformat() if ini else None, "fim": fim.isoformat() if fim else None,
                                                             "meses": round(meses, 1) if meses else None},
                        "carga": carga.isoformat() + "Z" if hasattr(carga, "isoformat") else carga})


def _linha(cod, nome, p, cp, meses):
    est = p.get("estoque")
    qtd = cp.get("qtd") or 0
    media = (qtd / meses) if (meses and qtd) else 0.0
    cob = (est / media) if (media and est is not None) else None
    mn = p.get("estoque_min") or 0
    sug = 0.0
    motivo = None
    if est is not None and mn and est < mn:
        sug = max(sug, mn - est); motivo = "abaixo do mínimo"
    if media and est is not None and est < 2 * media:
        alvo = 2 * media - est
        if alvo > sug:
            sug = alvo; motivo = "cobertura menor que 2 meses"
    custo = p.get("custo_unit") or cp.get("unit") or p.get("custo_cadastro")
    return {"codigo": cod, "nome": nome, "unidade": p.get("unidade"), "estoque": est, "minimo": p.get("estoque_min"), "maximo": p.get("estoque_max"),
            "comprado": qtd, "media_mes": round(media, 2), "cobertura_meses": round(cob, 1) if cob is not None else None,
            "custo_unit": custo, "valor_estoque": p.get("custo_total"), "sugestao": round(sug, 2) if sug else 0, "motivo": motivo,
            "valor_sugestao": round(sug * custo, 2) if sug and custo else 0}


# ---------------- REV66: tela única (GestãoClick até o corte + Bhom depois) ----------------
GC_CORTE = date(2026, 10, 1)   # OS do GestãoClick com entrada ANTES desta data; a partir dela vale o Bhom
_FIM = {"LIBERADO", "FINALIZADO", "ENTREGUE", "CONCLUIDO"}
_CACHE = {"at": 0.0, "rows": None}


def _status(sit):
    s = fold(sit)
    if s in _FIM:
        return "FATURADA", "PROCESSO FINALIZADO"
    if s.startswith("CANCEL"):
        return "CANCELADA", "CANCELADA"
    if s in ("ORCAMENTO", "EM ABERTO"):
        return "ABERTA", "AGUARDANDO ORCAMENTO"
    if "APROVACAO" in s or s == "AGUARDANDO APROVACAO":
        return "ABERTA", "AGUARDANDO APROVACAO"
    return "ABERTA", "AGUARDANDO EXECUCAO"


def gc_rows_v120(engine, ttl=120):
    """OS do GestãoClick no formato das linhas da Assistência (v120), só as anteriores ao corte. Cache curto."""
    import time as _t
    from sqlalchemy import text
    if _CACHE["rows"] is not None and _t.time() - _CACHE["at"] < ttl:
        return _CACHE["rows"]
    out = []
    try:
        with engine.connect() as c:
            for r in c.execute(text("SELECT o.codigo, o.cliente, o.data, o.previsao, o.dt_atendimento, o.equipamento, o.serial, o.serial_key, o.situacao,"
                                    " o.garagem, o.os_retorno, m.company_id FROM v150_gc_os o LEFT JOIN v120_at_clients m ON m.name=o.cliente"
                                    " WHERE o.data < :c"), {"c": GC_CORTE}):
                d = dict(r._mapping)
                st, det = _status(d["situacao"])
                ab = d["data"] if isinstance(d["data"], date) else (date.fromisoformat(str(d["data"])[:10]) if d["data"] else None)
                fe = d["dt_atendimento"] or d["previsao"]
                fe = fe if isinstance(fe, date) or fe is None else date.fromisoformat(str(fe)[:10])
                out.append({"os_number": "GC-" + str(d["codigo"]), "client_install": d["cliente"], "status_os": st, "status_det": det,
                            "substatus": "FINALIZADO" if st == "FATURADA" else (d["situacao"] or "").upper(), "opened": ab,
                            "closed": fe if st == "FATURADA" else None, "serial": d["serial"], "serial_key": d["serial_key"], "technician": None,
                            "fault_short": None, "fault": None, "cause": None, "solution": None, "company_id": d["company_id"],
                            "origem": "GestãoClick", "equipamento": d["equipamento"]})
    except Exception:
        out = []
    _CACHE.update(at=_t.time(), rows=out)
    return out


def gc_cache_clear():
    _CACHE.update(at=0.0, rows=None)


# ---------------- REV66: faturamento por item a partir dos XMLs das NF-e do GestãoClick ----------------
_CFOP_VENDA = re.compile(r"^[56][14]\d\d$")


def _x(el, path, ns):
    if el is None:
        return None
    f = el.find(path, ns)
    return f.text if f is not None else None


def _xf(el, path, ns):
    try:
        return float(_x(el, path, ns) or 0)
    except ValueError:
        return 0.0


def parse_nfe_xml(raw):
    """Devolve (cabecalho, itens) de um XML de NF-e (nfeProc ou NFe). Itens só com CFOP de venda."""
    import xml.etree.ElementTree as ET
    root = ET.fromstring(raw)
    ns = {"n": "http://www.portalfiscal.inf.br/nfe"}
    inf = root.find(".//n:infNFe", ns)
    if inf is None:
        return None, []
    prot = root.find(".//n:protNFe/n:infProt/n:cStat", ns)
    if prot is not None and prot.text not in ("100", "150"):
        return None, []
    ide = inf.find("n:ide", ns)
    if _x(ide, "n:tpNF", ns) == "0":  # entrada
        return None, []
    nnf = _x(ide, "n:nNF", ns)
    dh = (_x(ide, "n:dhEmi", ns) or _x(ide, "n:dEmi", ns) or "")[:10]
    try:
        d = date.fromisoformat(dh)
    except ValueError:
        d = None
    cli = _x(inf, "n:dest/n:xNome", ns)
    itens = []
    for det in inf.findall("n:det", ns):
        prod = det.find("n:prod", ns)
        cfop = _x(prod, "n:CFOP", ns) or ""
        if not _CFOP_VENDA.match(cfop):
            continue
        imp = det.find("n:imposto", ns)
        icms = sum(float(e.text or 0) for e in imp.iter("{http://www.portalfiscal.inf.br/nfe}vICMS")) if imp is not None else 0.0
        st = sum(float(e.text or 0) for e in imp.iter("{http://www.portalfiscal.inf.br/nfe}vICMSST")) if imp is not None else 0.0
        ipi = _xf(imp, "n:IPI/n:IPITrib/n:vIPI", ns)
        pis = sum(float(e.text or 0) for e in imp.find("n:PIS", ns).iter("{http://www.portalfiscal.inf.br/nfe}vPIS")) if imp is not None and imp.find("n:PIS", ns) is not None else 0.0
        cof = sum(float(e.text or 0) for e in imp.find("n:COFINS", ns).iter("{http://www.portalfiscal.inf.br/nfe}vCOFINS")) if imp is not None and imp.find("n:COFINS", ns) is not None else 0.0
        venda = _xf(prod, "n:vProd", ns) - _xf(prod, "n:vDesc", ns)
        itens.append({"codigo": (_x(prod, "n:cProd", ns) or "")[:60], "descricao": (_x(prod, "n:xProd", ns) or "")[:300], "cfop": cfop,
                      "qtde": _xf(prod, "n:qCom", ns), "preco_unit": _xf(prod, "n:vUnCom", ns), "venda": round(venda, 2),
                      "icms": round(icms, 2), "pis": round(pis, 2), "cofins": round(cof, 2), "ipi_st": round(ipi + st, 2),
                      "valor_nf": round(venda + ipi + st, 2)})
    return {"nf": nnf, "data": d, "cliente": cli}, itens


def import_nfe_xmls(engine, raw, filename, user_name):
    """Aceita um .zip com XMLs (ou um .xml). Grava no faturamento de peças (v132_fat_itens) só notas ANTES do corte (o Bhom cobre depois)."""
    import zipfile
    from sqlalchemy import text
    blobs = []
    if raw[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for n in z.namelist():
                if n.lower().endswith(".xml"):
                    blobs.append(z.read(n))
                elif n.lower().endswith(".zip"):
                    with zipfile.ZipFile(io.BytesIO(z.read(n))) as z2:
                        blobs += [z2.read(m) for m in z2.namelist() if m.lower().endswith(".xml")]
    else:
        blobs.append(raw)
    with engine.connect() as c:
        custos = {r[0]: (r[1] or r[2]) for r in c.execute(text("SELECT codigo, custo_unit, custo_cadastro FROM v150_gc_produtos"))}
    now = datetime.utcnow()
    load_id = int(now.timestamp() * 1000)
    linhas, nfs, ignoradas, depois = [], set(), 0, 0
    for b in blobs:
        try:
            cab, itens = parse_nfe_xml(b)
        except Exception:
            ignoradas += 1
            continue
        if not cab or not itens or not cab["nf"]:
            ignoradas += 1
            continue
        if cab["data"] and cab["data"] >= GC_CORTE:
            depois += 1
            continue
        nfs.add(cab["nf"])
        for i, it in enumerate(itens, 1):
            cu = custos.get(it["codigo"])
            linhas.append({"nf": str(cab["nf"])[:20], "linha": i, "data": cab["data"], "cliente": (cab["cliente"] or "")[:200],
                           "custo_unit": cu or 0.0, "custo": round((cu or 0.0) * it["qtde"], 2),
                           "origem_custo": ("GESTAOCLICK CADASTRO" if cu else "SEM CUSTO")[:30], "load_id": load_id, "updated_at": now, **it})
    if not linhas:
        raise ValueError("Nenhuma nota de venda (CFOP 51xx/54xx/61xx/64xx) anterior a %s encontrada nos XMLs." % GC_CORTE.strftime("%d/%m/%Y"))
    cols = ["nf", "linha", "data", "cfop", "cliente", "codigo", "descricao", "qtde", "preco_unit", "venda", "custo_unit", "custo", "icms", "pis",
            "cofins", "ipi_st", "valor_nf", "origem_custo", "load_id", "updated_at"]
    nl = sorted(nfs)
    with engine.begin() as c:
        for i in range(0, len(nl), 400):
            part = nl[i:i + 400]
            c.execute(text("DELETE FROM v132_fat_itens WHERE nf IN (%s)" % ",".join(":k%d" % j for j in range(len(part)))), {"k%d" % j: v for j, v in enumerate(part)})
        c.execute(text("INSERT INTO v132_fat_itens (%s) VALUES (%s)" % (",".join(cols), ",".join(":" + k for k in cols))), [{k: l[k] for k in cols} for l in linhas])
        c.execute(text("INSERT INTO v150_gc_cargas (id, arquivo, tipo, periodo, linhas, criado_em, usuario) VALUES (:i,:a,'xml',NULL,:l,:c,:u)"),
                  {"i": int(now.timestamp() * 1000000), "a": (filename or "")[:255], "l": len(linhas), "c": now, "u": (user_name or "")[:180]})
    sem = sum(1 for l in linhas if not l["custo_unit"])
    return {"arquivo": filename, "tipo": "xml", "rotulo": "XMLs de NF-e (faturamento por item)", "linhas": len(linhas),
            "periodo": None, "detalhe": "%d notas de venda, %d itens%s%s%s" % (len(nfs), len(linhas), (", %d itens sem custo no cadastro" % sem) if sem else "",
                                                                                 (", %d notas a partir de %s ignoradas (Bhom)" % (depois, GC_CORTE.strftime("%d/%m"))) if depois else "",
                                                                                 (", %d XMLs que não são venda/autorizada" % ignoradas) if ignoradas else "")}
