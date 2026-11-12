# -*- coding: utf-8 -*-
"""V88.0 REV11 — Visão do Gerente de Projeto (Planejamento semanal).

Parte 1 (funções puras, sem Flask/SQL): farol por regra, progresso por peso igual, série histórica por título,
indicadores, qualidade dos dados e relatório. Parte 2 (install_pm): tabelas novas, rotas e página.
Nada daqui altera o comportamento do Planejamento semanal existente; só lê as tabelas v96_* / v99_* e grava
nos campos novos (projeto: objetivo/datas/fase/produto; atividade: rotina/horas estimadas) e nas tabelas v100_*.
"""
import io
import json
import re
import unicodedata
from datetime import date, datetime, timedelta

# ----------------------------------------------------------------------------------------------------------------
# Regras do farol (parâmetros únicos — aparecem na tela em "Como o farol é calculado")
# ----------------------------------------------------------------------------------------------------------------
RULES = {
    "late_red": 5,        # atraso acima de N dias => vermelho
    "late_yellow": 1,     # atraso de 1..N dias => amarelo
    "slip_red": 5,        # previsão N dias após o prazo => vermelho
    "stale_days": 3,      # parada/sem atualização há mais de N dias => amarelo
    "milestone_days": 7,  # marco vence em até N dias e projeto abaixo de 80% => amarelo
    "no_update_days": 7,  # projeto sem nenhuma atualização há N dias => alerta de qualidade
    "min_dates_pct": 50,  # menos de N% das atividades com prazo => cinza (dados insuficientes)
}
FAROL_TXT = {"vermelho": "Crítico", "amarelo": "Atenção", "verde": "No prazo", "cinza": "Sem dados", "ok": "Concluído"}
FAROL_ORDER = {"vermelho": 0, "amarelo": 1, "cinza": 2, "verde": 3, "ok": 4}
FAROL_COLOR = {"vermelho": "#d03b3b", "amarelo": "#c98a00", "verde": "#0a8f3c", "cinza": "#8a8984", "ok": "#0a8f3c"}


def norm_title(t):
    s = unicodedata.normalize("NFKD", str(t or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def _d(v):
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    try:
        return datetime.strptime(str(v)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _dt(v):
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v
    if isinstance(v, date):
        return datetime(v.year, v.month, v.day)
    try:
        return datetime.strptime(str(v)[:19].replace("T", " "), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            return datetime.strptime(str(v)[:10], "%Y-%m-%d")
        except ValueError:
            return None


def _iso(v):
    return v.isoformat() if v else None


# ----------------------------------------------------------------------------------------------------------------
# Séries: a mesma atividade em semanas diferentes (casadas por título normalizado)
# ----------------------------------------------------------------------------------------------------------------
def build_series(items):
    """items: lista de dicts (com week_start). Devolve lista de séries; cada uma traz a linha mais recente ('cur')."""
    groups = {}
    for it in items:
        groups.setdefault(norm_title(it["title"]), []).append(it)
    out = []
    for key, rows in groups.items():
        rows.sort(key=lambda r: (str(r["week_start"]), r["id"]))
        cur = rows[-1]
        dls = [_d(r.get("deadline")) for r in rows if _d(r.get("deadline"))]
        base = dls[0] if dls else None
        replans = sum(1 for a, b in zip(dls, dls[1:]) if a != b)
        out.append({"key": key, "cur": cur, "rows": rows, "baseline": base, "replans": replans,
                    "first_week": str(rows[0]["week_start"]), "weeks": len(rows)})
    return out


# ----------------------------------------------------------------------------------------------------------------
# Atividade: farol
# ----------------------------------------------------------------------------------------------------------------
def eval_activity(a, today, rules=RULES):
    """a: dict da linha atual. Devolve (farol, motivos[])."""
    if a["status"] == "ok":
        return "ok", []
    reasons, level = [], "verde"

    def bump(lv, why):
        nonlocal level
        reasons.append(why)
        if FAROL_ORDER[lv] < FAROL_ORDER[level]:
            level = lv

    dl, fc, st = _d(a.get("deadline")), _d(a.get("forecast_date")), _d(a.get("start_date"))
    late = (today - dl).days if dl and dl < today else 0
    if a["status"] == "blq":
        bump("vermelho", "Bloqueada" + (": " + a["stop_reason"] if a.get("stop_reason") else ""))
    if late > rules["late_red"]:
        bump("vermelho", "Atraso de %d dias" % late)
    elif late >= rules["late_yellow"]:
        bump("amarelo", "Atraso de %d dia%s" % (late, "" if late == 1 else "s"))
    if dl and fc and (fc - dl).days > rules["slip_red"]:
        bump("vermelho", "Previsão %d dias após o prazo" % (fc - dl).days)
    since = _dt(a.get("status_since")) if a["status"] in ("agu", "blq") else _dt(a.get("updated_at"))
    if since and a["status"] in ("and", "agu"):
        stale = (datetime.combine(today, datetime.min.time()) - since).days
        if stale > rules["stale_days"]:
            bump("amarelo", ("Aguardando há %d dias" if a["status"] == "agu" else "Sem atualização há %d dias") % stale)
    if a["status"] == "nao" and st and st < today:
        bump("amarelo", "Início previsto em %s e não iniciada" % st.strftime("%d/%m"))
    return level, reasons


def is_activity(a):
    """Entra no progresso: tipo atividade e não rotineira."""
    return a.get("kind", "ativ") == "ativ" and not a.get("routine")


# ----------------------------------------------------------------------------------------------------------------
# Projeto: progresso, farol, indicadores
# ----------------------------------------------------------------------------------------------------------------
def progress_of(acts):
    """Média simples (peso igual) do progresso das atividades; concluída = 100."""
    ps = [100 if a["status"] == "ok" else int(a.get("progress") or 0) for a in acts]
    return round(sum(ps) / len(ps), 1) if ps else None


def spi_of(acts, today):
    """SPI simplificado = (atividades concluídas, em fração) / (atividades com prazo até hoje). None se nada venceu."""
    planned = [a for a in acts if _d(a.get("deadline")) and _d(a["deadline"]) <= today]
    if not planned:
        return None
    earned = sum((100 if a["status"] == "ok" else int(a.get("progress") or 0)) / 100.0 for a in planned)
    return round(earned / len(planned), 2)


def eval_project(p, acts, pends, milestones, risks, today, rules=RULES):
    reasons, level = [], "verde"

    def bump(lv, why):
        nonlocal level
        reasons.append(why)
        if FAROL_ORDER[lv] < FAROL_ORDER[level]:
            level = lv

    open_acts = [a for a in acts if a["status"] != "ok"]
    prog = progress_of(acts)
    n_red = sum(1 for a in open_acts if a["farol"] == "vermelho")
    n_yel = sum(1 for a in open_acts if a["farol"] == "amarelo")
    if n_red:
        bump("vermelho", "%d atividade%s crítica%s" % (n_red, "" if n_red == 1 else "s", "" if n_red == 1 else "s"))
    end = _d(p.get("end_date"))
    if end and end < today and (prog is None or prog < 100):
        bump("vermelho", "Fim do projeto (%s) vencido sem 100%%" % end.strftime("%d/%m/%Y"))
    ms_late = [m for m in milestones if not m["done"] and _d(m["due"]) and _d(m["due"]) < today]
    if ms_late:
        bump("vermelho", "Marco vencido: " + ", ".join(m["name"] for m in ms_late[:2]))
    if n_yel:
        bump("amarelo", "%d atividade%s em atenção" % (n_yel, "" if n_yel == 1 else "s"))
    near = [m for m in milestones if not m["done"] and _d(m["due"]) and 0 <= (_d(m["due"]) - today).days <= rules["milestone_days"]]
    if near and (prog is None or prog < 80):
        bump("amarelo", "Marco em até %d dias com projeto abaixo de 80%%: %s" % (rules["milestone_days"], near[0]["name"]))
    open_p = [x for x in pends if x["status"] != "ok"]
    if open_p:
        bump("amarelo", "%d pendência%s aberta%s" % (len(open_p), "" if len(open_p) == 1 else "s", "" if len(open_p) == 1 else "s"))
    rk_late = [r for r in risks if r["status"] == "aberto" and _d(r["due"]) and _d(r["due"]) < today]
    if rk_late:
        bump("amarelo", "%d risco/decisão com prazo vencido" % len(rk_late))
    if not acts:
        if level == "verde":
            level = "cinza"
        reasons.append("Sem atividades vinculadas")
    else:
        with_dl = sum(1 for a in acts if _d(a.get("deadline")))
        if with_dl * 100.0 / len(acts) < rules["min_dates_pct"]:
            reasons.append("Só %d de %d atividades têm prazo" % (with_dl, len(acts)))
            if level == "verde":
                level = "cinza"
    if prog is not None and prog >= 100 and not open_acts and not open_p:
        level, reasons = "ok", ["Todas as atividades concluídas"]
    if not reasons:
        reasons = ["Sem desvios segundo as regras"]
    return level, reasons


def worst(levels):
    levels = [l for l in levels if l]
    if not levels:
        return "cinza"
    return min(levels, key=lambda l: FAROL_ORDER.get(l, 9))


# ----------------------------------------------------------------------------------------------------------------
# Portfólio completo
# ----------------------------------------------------------------------------------------------------------------
def compute_portfolio(projects, items, hours, milestones, risks, today, rules=RULES):
    """projects: [{id,code,name,responsible,active,parent_id,objective,start_date,end_date,phase}]
    items: todas as linhas semanais [{id,week_id,week_start,front,title,status,responsible,deadline,kind,progress,start_date,
           forecast_date,status_since,completed_at,stop_reason,predecessors(list),project_id,updated_at,created_at,routine,est_hours,obs}]
    hours: {item_id: horas}; milestones: [{id,project_id,name,due,done}]; risks: [{id,project_id,kind,title,owner,due,status,created_at}]."""
    series = build_series(items)
    pmap = {p["id"]: p for p in projects}
    acts_all = []
    for s in series:
        a = dict(s["cur"])
        a["series_key"] = s["key"]
        a["baseline"] = _iso(s["baseline"])
        a["replans"] = s["replans"]
        a["first_week"] = s["first_week"]
        cur_dl = _d(a.get("deadline"))
        a["slip_days"] = (cur_dl - s["baseline"]).days if cur_dl and s["baseline"] else 0
        a["hours"] = round(sum(hours.get(r["id"], 0.0) for r in s["rows"]), 2)
        a["farol"], a["reasons"] = eval_activity(a, today, rules)
        if not is_activity(a) and a.get("kind") == "ativ":
            a["farol"], a["reasons"] = ("ok" if a["status"] == "ok" else "verde"), []
        a["project_name"] = pmap[a["project_id"]]["name"] if a.get("project_id") in pmap else ""
        acts_all.append(a)

    children = {}
    for p in projects:
        children.setdefault(p.get("parent_id"), []).append(p["id"])

    def subtree(pid):
        ids = [pid]
        for c in children.get(pid, []):
            ids += subtree(c)
        return ids

    # semanas em ordem (para burndown)
    weeks = sorted({(str(r["week_start"]), r["week_id"]) for r in items})
    out_projects = []
    for p in projects:
        ids = set(subtree(p["id"]))
        mine = [a for a in acts_all if a.get("project_id") in ids]
        acts = [a for a in mine if is_activity(a)]
        pends = [a for a in mine if a.get("kind") == "pend"]
        ms = [m for m in milestones if m["project_id"] in ids]
        rks = [r for r in risks if r["project_id"] in ids]
        farol, reasons = eval_project(p, acts, pends, ms, rks, today, rules)
        prog = progress_of(acts)
        open_acts = [a for a in acts if a["status"] != "ok"]
        done_acts = [a for a in acts if a["status"] == "ok"]
        ends = [_d(a.get("forecast_date")) or _d(a.get("deadline")) for a in open_acts]
        ends = [e for e in ends if e]
        forecast_end = max(ends) if ends else None
        plan_end = _d(p.get("end_date"))
        # vazão: concluídas nos últimos 7 dias e nos 7 anteriores
        def _done_between(a, d0, d1):
            c = _dt(a.get("completed_at"))
            return bool(c and d0 <= c.date() < d1)
        thr_now = sum(1 for a in done_acts if _done_between(a, today - timedelta(days=7), today + timedelta(days=1)))
        thr_prev = sum(1 for a in done_acts if _done_between(a, today - timedelta(days=14), today - timedelta(days=7)))
        # burndown semanal (instantâneo de cada semana)
        burn = []
        mine_rows = [r for r in items if r.get("project_id") in ids and (r.get("kind", "ativ") == "ativ") and not r.get("routine")]
        for wk, wid in weeks:
            rows = [r for r in mine_rows if r["week_id"] == wid]
            if rows:
                burn.append({"week": wk, "total": len(rows), "done": sum(1 for r in rows if r["status"] == "ok"),
                             "open": sum(1 for r in rows if r["status"] != "ok")})
        # carga por pessoa
        load = {}
        for a in open_acts:
            k = (a.get("responsible") or "").strip() or "(sem responsável)"
            L = load.setdefault(k, {"name": k, "open": 0, "late": 0, "hours": 0.0})
            L["open"] += 1
            if a["farol"] == "vermelho" or (a.get("deadline") and _d(a["deadline"]) < today):
                L["late"] += 1
            L["hours"] = round(L["hours"] + a["hours"], 2)
        ages = [(today - (_dt(a.get("created_at")) or datetime.combine(today, datetime.min.time())).date()).days for a in pends if a["status"] != "ok"]
        upd = [_dt(a.get("updated_at")) for a in mine if a.get("updated_at")]
        last_upd = max(upd) if upd else None
        out_projects.append({
            "id": p["id"], "code": p.get("code") or "", "name": p["name"], "responsible": p.get("responsible") or "",
            "active": bool(p.get("active", True)), "parent_id": p.get("parent_id"), "objective": p.get("objective") or "",
            "phase": p.get("phase") or "exec", "start_date": _iso(_d(p.get("start_date"))), "end_date": _iso(plan_end),
            "has_children": bool(children.get(p["id"])), "farol": farol, "farol_txt": FAROL_TXT[farol], "reasons": reasons,
            "progress": prog, "spi": spi_of(acts, today),
            "n_acts": len(acts), "n_done": len(done_acts), "n_open": len(open_acts),
            "n_late": sum(1 for a in open_acts if a.get("deadline") and _d(a["deadline"]) < today),
            "n_blocked": sum(1 for a in open_acts if a["status"] == "blq"),
            "n_pend": sum(1 for a in pends if a["status"] != "ok"),
            "n_routine": sum(1 for a in mine if a.get("kind") == "ativ" and a.get("routine")),
            "forecast_end": _iso(forecast_end), "slip_end": (forecast_end - plan_end).days if forecast_end and plan_end else None,
            "replans": sum(a["replans"] for a in acts), "thr_now": thr_now, "thr_prev": thr_prev,
            "pend_age_avg": round(sum(ages) / len(ages), 1) if ages else None, "pend_age_max": max(ages) if ages else None,
            "hours": round(sum(a["hours"] for a in mine), 2), "est_hours": round(sum(float(a.get("est_hours") or 0) for a in acts), 1),
            "last_update": _iso(last_upd), "burn": burn, "load": sorted(load.values(), key=lambda x: -x["open"]),
            "act_ids": [a["id"] for a in mine],
        })
    return {"projects": out_projects, "activities": acts_all, "today": today.isoformat(), "rules": rules}


# ----------------------------------------------------------------------------------------------------------------
# Qualidade dos dados e alertas
# ----------------------------------------------------------------------------------------------------------------
def quality_checks(acts, projects_out, today, rules=RULES, product_suggestions=None):
    live = [a for a in acts if a["status"] != "ok" and not a.get("routine")]
    by_id = {a["id"]: a for a in acts}

    def dd(x):
        return _d(x.get("deadline"))

    checks = [
        ("sem_resp", "Sem responsável", [a["id"] for a in live if not (a.get("responsible") or "").strip()]),
        ("sem_prazo", "Sem prazo", [a["id"] for a in live if a.get("kind") == "ativ" and not dd(a)]),
        ("sem_projeto", "Sem projeto", [a["id"] for a in live if not a.get("project_id")]),
        ("parada", "Parada há mais de %d dias" % rules["stale_days"],
         [a["id"] for a in live if any(r.startswith(("Aguardando há", "Sem atualização há")) for r in a["reasons"])]),
        ("vence7", "Vence em até 7 dias", [a["id"] for a in live if dd(a) and 0 <= (dd(a) - today).days <= 7]),
        ("atrasada", "Atrasada", [a["id"] for a in live if dd(a) and dd(a) < today]),
        ("pred", "Bloqueada por predecessora",
         [a["id"] for a in live if any(by_id.get(pid) and by_id[pid]["status"] != "ok" for pid in (a.get("predecessors") or []))]),
    ]
    stale_proj = []
    for p in projects_out:
        if not p["active"] or p["n_open"] == 0:
            continue
        lu = _dt(p["last_update"])
        if not lu or (datetime.combine(today, datetime.min.time()) - lu).days > rules["no_update_days"]:
            stale_proj.append(p["id"])
    res = [{"code": c, "label": l, "ids": ids, "count": len(ids)} for c, l, ids in checks]
    res.append({"code": "proj_sem_update", "label": "Projeto sem atualização há mais de %d dias" % rules["no_update_days"],
                "ids": [], "project_ids": stale_proj, "count": len(stale_proj)})
    return {"checks": res, "product_suggestions": product_suggestions or []}


def suggest_products(acts, projects):
    """Sugere vincular atividades a produtos pelo nome do produto no título (ex.: 'terminal de consulta' → produto do SPTrans)."""
    prods = [p for p in projects if p.get("parent_id") and p.get("active", True)]
    out = []
    for a in acts:
        if a["status"] == "ok":
            continue
        t = norm_title(a["title"] + " " + (a.get("obs") or ""))
        for p in prods:
            if norm_title(p["name"]) and norm_title(p["name"]) in t and a.get("project_id") != p["id"]:
                out.append({"id": a["id"], "title": a["title"], "from_project_id": a.get("project_id"), "product_id": p["id"], "product": p["name"]})
                break
    return out


# ----------------------------------------------------------------------------------------------------------------
# Relatório automático por projeto (texto copiável)
# ----------------------------------------------------------------------------------------------------------------
def _br(iso):
    d = _d(iso)
    return d.strftime("%d/%m/%Y") if d else "—"


def project_report(p, acts, milestones, risks, today):
    L = []
    L.append("RELATÓRIO DE STATUS — %s%s" % (p["name"], (" (" + p["code"] + ")") if p.get("code") else ""))
    L.append("Data: %s · Responsável: %s · Fase: %s" % (today.strftime("%d/%m/%Y"), p.get("responsible") or "—", PHASES.get(p.get("phase"), p.get("phase") or "—")))
    L.append("Situação: %s — %s" % (FAROL_TXT[p["farol"]].upper(), "; ".join(p["reasons"])))
    L.append("Progresso: %s%% (%d de %d atividades concluídas)%s" % (
        ("%g" % p["progress"]) if p["progress"] is not None else "—", p["n_done"], p["n_acts"],
        (" · SPI " + ("%.2f" % p["spi"]).replace(".", ",")) if p.get("spi") is not None else ""))
    L.append("Período planejado: %s a %s · Previsão de término: %s%s" % (
        _br(p["start_date"]), _br(p["end_date"]), _br(p["forecast_end"]),
        (" (%+d dias)" % p["slip_end"]) if p.get("slip_end") is not None else ""))
    if p.get("objective"):
        L.append("Objetivo: " + p["objective"])
    L.append("")
    done = sorted([a for a in acts if a["status"] == "ok" and (_dt(a.get("completed_at")) or datetime.min).date() >= today - timedelta(days=7)],
                  key=lambda a: a["title"])
    L.append("CONCLUÍDO NA SEMANA (%d)" % len(done))
    L += ["• " + a["title"] for a in done] or ["• —"]
    L.append("")
    crit = [a for a in acts if a["status"] != "ok" and a["farol"] in ("vermelho", "amarelo")]
    crit.sort(key=lambda a: (FAROL_ORDER[a["farol"]], str(a.get("deadline") or "9999")))
    L.append("PONTOS DE ATENÇÃO (%d)" % len(crit))
    for a in crit:
        L.append("• [%s] %s — %s%s" % (FAROL_TXT[a["farol"]], a["title"], "; ".join(a["reasons"]),
                                        (" · resp.: " + a["responsible"]) if a.get("responsible") else ""))
    if not crit:
        L.append("• —")
    L.append("")
    nxt = [a for a in acts if a["status"] != "ok" and _d(a.get("deadline")) and today <= _d(a["deadline"]) <= today + timedelta(days=14)]
    nxt.sort(key=lambda a: str(a["deadline"]))
    L.append("PRÓXIMOS 14 DIAS (%d)" % len(nxt))
    L += ["• %s — %s%s" % (_br(a["deadline"]), a["title"], (" (" + a["responsible"] + ")") if a.get("responsible") else "") for a in nxt] or ["• —"]
    L.append("")
    ms = [m for m in milestones if not m["done"]]
    L.append("MARCOS ABERTOS (%d)" % len(ms))
    L += ["• %s — %s" % (_br(m["due"]), m["name"]) for m in sorted(ms, key=lambda m: str(m["due"] or "9999"))] or ["• —"]
    L.append("")
    rk = [r for r in risks if r["status"] == "aberto"]
    L.append("RISCOS, DECISÕES E PENDÊNCIAS ABERTOS (%d)" % len(rk))
    L += ["• [%s] %s — %s%s" % (RISK_KINDS.get(r["kind"], r["kind"]), r["title"], (r.get("owner") or "sem dono"),
                               (" · até " + _br(r["due"])) if r.get("due") else "") for r in rk] or ["• —"]
    return "\n".join(L)


PHASES = {"plan": "Planejamento", "exec": "Execução", "homol": "Homologação", "ent": "Entrega", "enc": "Encerrado", "pausa": "Pausado"}
RISK_KINDS = {"risco": "Risco", "decisao": "Decisão", "pend": "Pendência"}
RISK_ST = ("aberto", "fechado")


# ----------------------------------------------------------------------------------------------------------------
# Excel
# ----------------------------------------------------------------------------------------------------------------
def build_xlsx(port, quality):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
    wb = Workbook()
    ws = wb.active
    ws.title = "Portfólio"
    hdr = ["Projeto", "Código", "Produto de", "Responsável", "Farol", "Motivos", "Progresso %", "SPI", "Atividades", "Concluídas", "Atrasadas",
           "Bloqueadas", "Pendências", "Início", "Fim planejado", "Previsão de fim", "Desvio (dias)", "Replanejamentos", "Horas", "Última atualização"]
    names = {p["id"]: p["name"] for p in port["projects"]}
    rows = [[p["name"], p["code"], names.get(p["parent_id"], ""), p["responsible"], p["farol_txt"], "; ".join(p["reasons"]), p["progress"], p["spi"],
             p["n_acts"], p["n_done"], p["n_late"], p["n_blocked"], p["n_pend"], _br(p["start_date"]), _br(p["end_date"]), _br(p["forecast_end"]),
             p["slip_end"], p["replans"], p["hours"], (p["last_update"] or "")[:10]] for p in port["projects"]]

    def put(ws, hdr, rows):
        ws.append(hdr)
        for r in rows:
            ws.append(r)
        for c in ws[1]:
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = PatternFill("solid", fgColor="16335C")
            c.alignment = Alignment(wrap_text=True, vertical="center")
        for i, h in enumerate(hdr, 1):
            w = max([len(str(h))] + [len(str(r[i - 1] if r[i - 1] is not None else "")) for r in rows[:200]]) + 2
            ws.column_dimensions[get_column_letter(i)].width = min(60, max(10, w))
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

    put(ws, hdr, rows)
    ws2 = wb.create_sheet("Atividades")
    h2 = ["Projeto", "Atividade", "Tipo", "Rotina", "Status", "Farol", "Motivos", "Responsável", "Prazo original", "Prazo atual", "Previsão",
          "Desvio (dias)", "Replanejamentos", "Progresso %", "Horas", "Horas estimadas"]
    stn = {"nao": "Não iniciado", "and": "Em andamento", "agu": "Aguardando", "blq": "Bloqueado", "ok": "Concluído"}
    r2 = [[a["project_name"], a["title"], "Pendência" if a.get("kind") == "pend" else "Atividade", "Sim" if a.get("routine") else "", stn.get(a["status"], a["status"]),
           FAROL_TXT.get(a["farol"], ""), "; ".join(a["reasons"]), a.get("responsible") or "", _br(a.get("baseline")), _br(a.get("deadline")),
           _br(a.get("forecast_date")), a["slip_days"], a["replans"], 100 if a["status"] == "ok" else a.get("progress"), a["hours"], a.get("est_hours")]
          for a in sorted(port["activities"], key=lambda a: (a["project_name"], str(a.get("deadline") or "9999")))]
    put(ws2, h2, r2)
    ws3 = wb.create_sheet("Qualidade dos dados")
    r3 = []
    byid = {a["id"]: a for a in port["activities"]}
    for c in quality["checks"]:
        for i in c["ids"]:
            a = byid.get(i)
            if a:
                r3.append([c["label"], a["project_name"], a["title"], a.get("responsible") or ""])
        for pid in c.get("project_ids", []):
            r3.append([c["label"], names.get(pid, str(pid)), "", ""])
    put(ws3, ["Alerta", "Projeto", "Atividade", "Responsável"], r3)
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()


# ----------------------------------------------------------------------------------------------------------------
# Servidor
# ----------------------------------------------------------------------------------------------------------------
_PM = {"ready": False}


def install_pm(app, db, text, H):
    """H: dict com as funções do Planejamento semanal (gate, ensure, event, scope, in_scope, areas_of, clean_date, login_required)."""
    from flask import jsonify, request, render_template, abort, send_file, g, session

    gate, ensure, event, in_scope, areas_of, clean_date, login_required = (
        H["gate"], H["ensure"], H["event"], H["in_scope"], H["areas_of"], H["clean_date"], H["login_required"])

    def today_br():
        return (datetime.utcnow() - timedelta(hours=3)).date()

    def pm_ensure(conn):
        ensure(conn)
        if _PM["ready"]:
            return
        for ddl in (
            "ALTER TABLE v96_plan_projects ADD COLUMN IF NOT EXISTS parent_id INTEGER",
            "ALTER TABLE v96_plan_projects ADD COLUMN IF NOT EXISTS objective VARCHAR(500) NOT NULL DEFAULT ''",
            "ALTER TABLE v96_plan_projects ADD COLUMN IF NOT EXISTS start_date DATE",
            "ALTER TABLE v96_plan_projects ADD COLUMN IF NOT EXISTS end_date DATE",
            "ALTER TABLE v96_plan_projects ADD COLUMN IF NOT EXISTS phase VARCHAR(10) NOT NULL DEFAULT 'exec'",
            "ALTER TABLE v96_plan_items ADD COLUMN IF NOT EXISTS routine BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE v96_plan_items ADD COLUMN IF NOT EXISTS est_hours NUMERIC(6,1)",
            "CREATE TABLE IF NOT EXISTS v100_plan_milestones (id SERIAL PRIMARY KEY, project_id INTEGER NOT NULL, name VARCHAR(160) NOT NULL, due DATE, "
            "done BOOLEAN NOT NULL DEFAULT FALSE, done_at TIMESTAMP, created_by INTEGER, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)",
            "CREATE INDEX IF NOT EXISTS ix_v100_ms_project ON v100_plan_milestones (project_id)",
            "CREATE TABLE IF NOT EXISTS v100_plan_risks (id SERIAL PRIMARY KEY, project_id INTEGER NOT NULL, kind VARCHAR(8) NOT NULL DEFAULT 'risco', "
            "title VARCHAR(300) NOT NULL, owner VARCHAR(120) NOT NULL DEFAULT '', due DATE, status VARCHAR(8) NOT NULL DEFAULT 'aberto', "
            "impact VARCHAR(300) NOT NULL DEFAULT '', created_by INTEGER, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, closed_at TIMESTAMP)",
            "CREATE INDEX IF NOT EXISTS ix_v100_risks_project ON v100_plan_risks (project_id)",
            # "Terminal de consulta" é um produto do projeto SPTrans (decisão do administrador); cria uma vez, se ainda não existir
            "INSERT INTO v96_plan_projects (code, name, responsible, active, parent_id) "
            "SELECT '', 'Terminal de consulta', '', TRUE, p.id FROM v96_plan_projects p WHERE LOWER(p.name)='sptrans' AND p.parent_id IS NULL "
            "AND NOT EXISTS (SELECT 1 FROM v96_plan_projects x WHERE LOWER(x.name)='terminal de consulta') ORDER BY p.id LIMIT 1",
        ):
            conn.execute(text(ddl))
        _PM["ready"] = True

    def load(conn):
        pr = conn.execute(text("SELECT id, code, name, responsible, active, parent_id, objective, start_date, end_date, phase FROM v96_plan_projects ORDER BY LOWER(name)")).fetchall()
        projects = [{"id": r[0], "code": r[1], "name": r[2], "responsible": r[3], "active": bool(r[4]), "parent_id": r[5], "objective": r[6],
                     "start_date": r[7], "end_date": r[8], "phase": r[9]} for r in pr]
        it = conn.execute(text(
            "SELECT i.id, i.week_id, w.week_start, i.front, i.title, i.status, i.responsible, i.deadline, i.kind, i.progress, i.start_date, i.forecast_date, "
            "i.status_since, i.completed_at, i.stop_reason, i.predecessors, i.project_id, i.updated_at, i.created_at, i.routine, i.est_hours, i.obs, i.fronts_extra "
            "FROM v96_plan_items i JOIN v96_plan_weeks w ON w.id=i.week_id ORDER BY w.week_start, i.id LIMIT 6000")).fetchall()
        items = []
        for r in it:
            try:
                preds = [int(x) for x in json.loads(r[15] or "[]")]
            except Exception:
                preds = []
            items.append({"id": r[0], "week_id": r[1], "week_start": r[2], "front": r[3], "title": r[4], "status": r[5], "responsible": r[6] or "",
                          "deadline": r[7], "kind": r[8] or "ativ", "progress": r[9] or 0, "start_date": r[10], "forecast_date": r[11],
                          "status_since": r[12], "completed_at": r[13], "stop_reason": r[14] or "", "predecessors": preds, "project_id": r[16],
                          "updated_at": r[17], "created_at": r[18], "routine": bool(r[19]),
                          "est_hours": float(r[20]) if r[20] is not None else None, "obs": r[21] or "", "fronts_extra": r[22] or "[]"})
        hrs = {row[0]: float(row[1] or 0) for row in conn.execute(text("SELECT item_id, SUM(hours) FROM v99_plan_hours GROUP BY item_id")).fetchall()}
        ms = [{"id": r[0], "project_id": r[1], "name": r[2], "due": _iso(r[3]), "done": bool(r[4])}
              for r in conn.execute(text("SELECT id, project_id, name, due, done FROM v100_plan_milestones ORDER BY due NULLS LAST, id")).fetchall()]
        rk = [{"id": r[0], "project_id": r[1], "kind": r[2], "title": r[3], "owner": r[4], "due": _iso(r[5]), "status": r[6], "impact": r[7],
               "created_at": r[8]} for r in conn.execute(text("SELECT id, project_id, kind, title, owner, due, status, impact, created_at FROM v100_plan_risks ORDER BY id")).fetchall()]
        return projects, items, hrs, ms, rk

    def build(conn):
        projects, items, hrs, ms, rk = load(conn)
        today = today_br()
        port = compute_portfolio(projects, items, hrs, ms, rk, today)
        port["milestones"], port["risks"] = ms, [dict(r, created_at=_iso(_dt(r["created_at"]))) for r in rk]
        sug = suggest_products(port["activities"], projects)
        port["quality"] = quality_checks(port["activities"], port["projects"], today, RULES, sug)
        return port

    def clean(a):
        out = dict(a)
        for k in ("deadline", "start_date", "forecast_date", "week_start"):
            out[k] = _iso(_d(a.get(k)))
        for k in ("status_since", "completed_at", "updated_at", "created_at"):
            v = _dt(a.get(k))
            out[k] = v.isoformat(sep=" ") if v else None
        out.pop("fronts_extra", None)
        return out

    @app.get("/gestao/planejamento-semanal/projetos")
    @login_required
    def v100_pm_page():
        from flask import current_app
        ver, edit, adm = H["access"]()
        if not ver:
            abort(403)
        return render_template("planejamento_projetos.html", app_release=H["release"](), can_edit=edit, is_admin=adm,
                               full=(H["scope"]() is None), plan_on=bool(H["flags"]().get("planejamento_semanal")))

    @app.get("/api/pm/portfolio")
    @login_required
    def v100_pm_portfolio():
        gd, acc = gate()
        if gd:
            return gd
        with db.engine.begin() as conn:
            pm_ensure(conn)
            port = build(conn)
        port["activities"] = [clean(a) for a in port["activities"]]
        port["me"] = {"edit": bool(acc[1]), "admin": bool(acc[2]), "full": H["scope"]() is None}
        port["phases"], port["risk_kinds"] = PHASES, RISK_KINDS
        port["farol_color"] = FAROL_COLOR
        return jsonify({"ok": True, **port})

    @app.post("/api/pm/projeto")
    @login_required
    def v100_pm_project_save():
        gd, acc = gate(need_edit=True)
        if gd:
            return gd
        fg = H["full_gate"]()
        if fg:
            return fg
        d = request.get_json(silent=True) or {}
        name = (d.get("name") or "").strip()[:120]
        if not name:
            return jsonify({"ok": False, "error": "Informe o nome do projeto."}), 400
        try:
            pid = int(d["id"]) if d.get("id") not in (None, "", 0) else None
            parent = int(d["parent_id"]) if d.get("parent_id") not in (None, "", 0) else None
            sd, ed = clean_date(d.get("start_date")), clean_date(d.get("end_date"))
        except (TypeError, ValueError) as e:
            return jsonify({"ok": False, "error": str(e) if "Data" in str(e) else "Dados inválidos."}), 400
        if sd and ed and ed < sd:
            return jsonify({"ok": False, "error": "O fim planejado não pode ser anterior ao início."}), 400
        phase = d.get("phase") if d.get("phase") in PHASES else "exec"
        with db.engine.begin() as conn:
            pm_ensure(conn)
            if parent:
                pr = conn.execute(text("SELECT parent_id FROM v96_plan_projects WHERE id=:i"), {"i": parent}).first()
                if not pr:
                    return jsonify({"ok": False, "error": "Projeto-pai não encontrado."}), 400
                if pr[0] is not None:
                    return jsonify({"ok": False, "error": "Só há dois níveis: projeto → produto. O pai escolhido já é um produto."}), 400
                if pid and parent == pid:
                    return jsonify({"ok": False, "error": "Um projeto não pode ser produto dele mesmo."}), 400
            if pid and parent and conn.execute(text("SELECT 1 FROM v96_plan_projects WHERE parent_id=:i LIMIT 1"), {"i": pid}).first():
                return jsonify({"ok": False, "error": "Este projeto já tem produtos; não pode virar produto de outro."}), 400
            code = (d.get("code") or "").strip()[:20]
            dup = conn.execute(text("SELECT id FROM v96_plan_projects WHERE id<>:i AND LOWER(name)=LOWER(:n)"), {"i": pid or 0, "n": name}).first()
            if dup:
                return jsonify({"ok": False, "error": "Já existe um projeto com esse nome."}), 409
            vals = {"n": name, "c": code, "r": (d.get("responsible") or "").strip()[:120], "a": bool(d.get("active", True)), "p": parent,
                    "o": (d.get("objective") or "").strip()[:500], "sd": sd, "ed": ed, "ph": phase}
            if pid:
                conn.execute(text("UPDATE v96_plan_projects SET name=:n, code=:c, responsible=:r, active=:a, parent_id=:p, objective=:o, "
                                  "start_date=CAST(:sd AS DATE), end_date=CAST(:ed AS DATE), phase=:ph WHERE id=:i"), dict(vals, i=pid))
            else:
                pid = conn.execute(text("INSERT INTO v96_plan_projects (name, code, responsible, active, parent_id, objective, start_date, end_date, phase, created_by) "
                                        "VALUES (:n,:c,:r,:a,:p,:o,CAST(:sd AS DATE),CAST(:ed AS DATE),:ph,:u) RETURNING id"), dict(vals, u=session.get("user_id"))).scalar()
            event(conn, None, None, "pm_projeto", "%s (#%s)" % (name, pid))
        return jsonify({"ok": True, "id": pid})

    def _proj_ok(conn, pid):
        return bool(conn.execute(text("SELECT 1 FROM v96_plan_projects WHERE id=:i"), {"i": pid}).first())

    @app.post("/api/pm/marco")
    @login_required
    def v100_pm_milestone_save():
        gd, acc = gate(need_edit=True)
        if gd:
            return gd
        fg = H["full_gate"]()
        if fg:
            return fg
        d = request.get_json(silent=True) or {}
        name = (d.get("name") or "").strip()[:160]
        try:
            pid = int(d.get("project_id"))
            mid = int(d["id"]) if d.get("id") not in (None, "", 0) else None
            due = clean_date(d.get("due"))
        except (TypeError, ValueError) as e:
            return jsonify({"ok": False, "error": str(e) if "Data" in str(e) else "Dados inválidos."}), 400
        if not name:
            return jsonify({"ok": False, "error": "Informe o nome do marco."}), 400
        done = bool(d.get("done"))
        with db.engine.begin() as conn:
            pm_ensure(conn)
            if not _proj_ok(conn, pid):
                return jsonify({"ok": False, "error": "Projeto não encontrado."}), 404
            if mid:
                conn.execute(text("UPDATE v100_plan_milestones SET name=:n, due=CAST(:d AS DATE), done=:x, "
                                  "done_at=CASE WHEN :x AND done_at IS NULL THEN CURRENT_TIMESTAMP WHEN :x THEN done_at ELSE NULL END WHERE id=:i AND project_id=:p"),
                             {"n": name, "d": due, "x": done, "i": mid, "p": pid})
            else:
                mid = conn.execute(text("INSERT INTO v100_plan_milestones (project_id,name,due,done,done_at,created_by) VALUES (:p,:n,CAST(:d AS DATE),:x,"
                                        "CASE WHEN :x THEN CURRENT_TIMESTAMP ELSE NULL END,:u) RETURNING id"),
                                   {"p": pid, "n": name, "d": due, "x": done, "u": session.get("user_id")}).scalar()
            event(conn, None, None, "pm_marco", "%s (projeto #%s)" % (name, pid))
        return jsonify({"ok": True, "id": mid})

    @app.post("/api/pm/marco/<int:mid>/excluir")
    @login_required
    def v100_pm_milestone_del(mid):
        gd, acc = gate(need_edit=True)
        if gd:
            return gd
        fg = H["full_gate"]()
        if fg:
            return fg
        with db.engine.begin() as conn:
            pm_ensure(conn)
            conn.execute(text("DELETE FROM v100_plan_milestones WHERE id=:i"), {"i": mid})
            event(conn, None, None, "pm_marco_excluir", "#%s" % mid)
        return jsonify({"ok": True})

    @app.post("/api/pm/risco")
    @login_required
    def v100_pm_risk_save():
        gd, acc = gate(need_edit=True)
        if gd:
            return gd
        d = request.get_json(silent=True) or {}
        title = (d.get("title") or "").strip()[:300]
        kind = d.get("kind") if d.get("kind") in RISK_KINDS else "risco"
        status = d.get("status") if d.get("status") in RISK_ST else "aberto"
        try:
            pid = int(d.get("project_id"))
            rid = int(d["id"]) if d.get("id") not in (None, "", 0) else None
            due = clean_date(d.get("due"))
        except (TypeError, ValueError) as e:
            return jsonify({"ok": False, "error": str(e) if "Data" in str(e) else "Dados inválidos."}), 400
        if not title:
            return jsonify({"ok": False, "error": "Descreva o risco, a decisão ou a pendência."}), 400
        with db.engine.begin() as conn:
            pm_ensure(conn)
            if not _proj_ok(conn, pid):
                return jsonify({"ok": False, "error": "Projeto não encontrado."}), 404
            vals = {"p": pid, "k": kind, "t": title, "o": (d.get("owner") or "").strip()[:120], "d": due, "s": status, "im": (d.get("impact") or "").strip()[:300]}
            if rid:
                conn.execute(text("UPDATE v100_plan_risks SET kind=:k, title=:t, owner=:o, due=CAST(:d AS DATE), status=:s, impact=:im, "
                                  "closed_at=CASE WHEN :s='fechado' THEN COALESCE(closed_at, CURRENT_TIMESTAMP) ELSE NULL END WHERE id=:i AND project_id=:p"), dict(vals, i=rid))
            else:
                rid = conn.execute(text("INSERT INTO v100_plan_risks (project_id,kind,title,owner,due,status,impact,created_by) "
                                        "VALUES (:p,:k,:t,:o,CAST(:d AS DATE),:s,:im,:u) RETURNING id"), dict(vals, u=session.get("user_id"))).scalar()
            event(conn, None, None, "pm_risco", "%s: %s (projeto #%s)" % (kind, title[:80], pid))
        return jsonify({"ok": True, "id": rid})

    @app.post("/api/pm/risco/<int:rid>/excluir")
    @login_required
    def v100_pm_risk_del(rid):
        gd, acc = gate(need_edit=True)
        if gd:
            return gd
        with db.engine.begin() as conn:
            pm_ensure(conn)
            conn.execute(text("DELETE FROM v100_plan_risks WHERE id=:i"), {"i": rid})
            event(conn, None, None, "pm_risco_excluir", "#%s" % rid)
        return jsonify({"ok": True})

    @app.post("/api/pm/item/<int:iid>")
    @login_required
    def v100_pm_item_quick(iid):
        """Correção rápida dos campos que o gerente precisa: responsável, prazo, previsão, projeto/produto, rotina, horas estimadas."""
        gd, acc = gate(need_edit=True)
        if gd:
            return gd
        d = request.get_json(silent=True) or {}
        with db.engine.begin() as conn:
            pm_ensure(conn)
            r = conn.execute(text("SELECT week_id, front, fronts_extra, title FROM v96_plan_items WHERE id=:i"), {"i": iid}).first()
            if not r:
                return jsonify({"ok": False, "error": "Atividade não encontrada."}), 404
            if not in_scope(areas_of(r[1], r[2])):
                return jsonify({"ok": False, "error": "Esta atividade é de outra área; você não edita essa área."}), 403
            sets, vals, log = [], {"i": iid}, []
            try:
                if "responsible" in d:
                    vals["rs"] = (d.get("responsible") or "").strip()[:120]
                    sets.append("responsible=:rs"); log.append("responsável=" + (vals["rs"] or "—"))
                for key, col in (("deadline", "deadline"), ("forecast_date", "forecast_date"), ("start_date", "start_date")):
                    if key in d:
                        vals[col] = clean_date(d.get(key))
                        sets.append("%s=CAST(:%s AS DATE)" % (col, col)); log.append("%s=%s" % (key, vals[col] or "—"))
                if "project_id" in d:
                    pj = int(d["project_id"]) if d.get("project_id") not in (None, "", 0) else None
                    if pj and not _proj_ok(conn, pj):
                        return jsonify({"ok": False, "error": "Projeto não encontrado."}), 404
                    vals["pj"] = pj
                    sets.append("project_id=:pj"); log.append("projeto=%s" % (pj or "—"))
                if "routine" in d:
                    vals["ro"] = bool(d.get("routine"))
                    sets.append("routine=:ro"); log.append("rotina=%s" % ("sim" if vals["ro"] else "não"))
                if "est_hours" in d:
                    eh = d.get("est_hours")
                    vals["eh"] = None if eh in (None, "") else round(float(eh), 1)
                    if vals["eh"] is not None and not (0 <= vals["eh"] <= 9999):
                        return jsonify({"ok": False, "error": "Horas estimadas inválidas."}), 400
                    sets.append("est_hours=:eh"); log.append("horas estimadas=%s" % (vals["eh"] if vals["eh"] is not None else "—"))
            except (TypeError, ValueError) as e:
                return jsonify({"ok": False, "error": str(e) if "Data" in str(e) else "Valor inválido."}), 400
            if not sets:
                return jsonify({"ok": False, "error": "Nada para alterar."}), 400
            conn.execute(text("UPDATE v96_plan_items SET " + ", ".join(sets) + " WHERE id=:i"), vals)
            event(conn, r[0], iid, "pm_rapido", "; ".join(log))
        return jsonify({"ok": True})

    @app.get("/api/pm/exportar.xlsx")
    @login_required
    def v100_pm_xlsx():
        gd, acc = gate()
        if gd:
            return gd
        with db.engine.begin() as conn:
            pm_ensure(conn)
            port = build(conn)
        try:
            blob = build_xlsx(port, port["quality"])
        except Exception as exc:
            app.logger.exception("PM xlsx")
            return jsonify({"ok": False, "error": "Não foi possível gerar o Excel: " + str(exc)[:160]}), 500
        return send_file(io.BytesIO(blob), as_attachment=True, download_name="projetos-%s.xlsx" % today_br().isoformat(),
                         mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    @app.get("/api/pm/relatorio/<int:pid>")
    @login_required
    def v100_pm_report(pid):
        gd, acc = gate()
        if gd:
            return gd
        with db.engine.begin() as conn:
            pm_ensure(conn)
            port = build(conn)
        p = next((x for x in port["projects"] if x["id"] == pid), None)
        if not p:
            return jsonify({"ok": False, "error": "Projeto não encontrado."}), 404
        ids = set(p["act_ids"])
        acts = [a for a in port["activities"] if a["id"] in ids and is_activity(a)]
        sub = {x["id"] for x in port["projects"] if x["id"] == pid or x["parent_id"] == pid}
        ms = [m for m in port["milestones"] if m["project_id"] in sub]
        rk = [r for r in port["risks"] if r["project_id"] in sub]
        return jsonify({"ok": True, "text": project_report(p, acts, ms, rk, today_br())})

    @app.after_request
    def v100_pm_link(response):
        """Botão 'Visão do Gerente de Projeto' na barra do Planejamento semanal (sem alterar o template existente)."""
        if response.status_code != 200 or response.mimetype != "text/html" or response.direct_passthrough:
            return response
        if request.path != "/gestao/planejamento-semanal":
            return response
        html = response.get_data(as_text=True)
        if "data-v100-pm" in html:
            return response
        m = re.search(r'<div class="btns">', html)
        if not m:
            return response
        a = '<a class="b p" data-v100-pm="1" href="/gestao/planejamento-semanal/projetos" style="text-decoration:none;display:inline-block">Visão do Gerente de Projeto</a>'
        response.set_data(html[:m.end()] + a + html[m.end():])
        return response

    return pm_ensure
