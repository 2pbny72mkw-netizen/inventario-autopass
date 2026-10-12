"""V85.51 — verificação conservadora, somente leitura, das janelas de coleta.

Não presume que um lançamento manual sem R0050 é um fechamento oficial.
Não altera transações, valores declarados, apurados nem programações.
"""
from collections import defaultdict
from datetime import datetime


def audit_cash_chronology_rows(rows):
    issues=[]
    total_events=0
    total_windows=0
    status_counts=defaultdict(int)
    affected=set()
    for row in rows:
        terminal=str(row.get('terminal') or '').strip()
        events=[]
        for item in (row.get('planned') or [])+(row.get('extra') or []):
            cycle=item.get('transaction_cycle') or {}
            if not cycle: continue
            total_events+=1
            audit=cycle.get('chronology_audit') or {}
            status=audit.get('status')
            if status:
                status_counts[status]+=1
                if status in ('REFERENCIA_ANTERIOR_CORRIGIDA','SEM_REFERENCIA_R0050','MANUAL_SEM_REFERENCIA'):
                    issues.append({'terminal':terminal,'type':status,'date':item.get('realized_date') or item.get('date'),
                                   'reference_at':cycle.get('initial_at'),
                                   'previous_reference_at':audit.get('previous_reference_at'),
                                   'selected_reference_at':audit.get('selected_reference_at')})
                    affected.add(terminal)
            if not cycle.get('available'): continue
            a,b=cycle.get('initial_at'),cycle.get('final_at')
            if not a or not b: continue
            try:
                start=datetime.fromisoformat(a); end=datetime.fromisoformat(b)
            except (ValueError,TypeError): continue
            total_windows+=1
            if start>=end:
                issues.append({'terminal':terminal,'type':'INTERVALO_INVALIDO','start':a,'end':b})
                affected.add(terminal)
            else:
                events.append((start,end,item.get('event_id'),item.get('date')))
        # Deduplicar janelas idênticas: a mesma coleta pode aparecer em
        # programação e no agrupamento extra sem representar sobreposição real.
        distinct={(a,b) for a,b,_,_ in events}
        ordered=sorted(distinct)
        for (_,prev_end),(start,end) in zip(ordered,ordered[1:]):
            if start<prev_end:
                issues.append({'terminal':terminal,'type':'JANELAS_SOBREPOSTAS',
                               'previous_end':prev_end.isoformat(),
                               'next_start':start.isoformat(),'next_end':end.isoformat()})
                affected.add(terminal)
    return {'atms_checked':len(rows),'events_checked':total_events,
            'windows_checked':total_windows,'atms_with_issues':len(affected),
            'status_counts':dict(status_counts),'issues':issues}
