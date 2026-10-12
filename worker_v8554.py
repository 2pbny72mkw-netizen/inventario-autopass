"""Worker independente para relatórios V85.54.
Executar em serviço Render Background Worker: python worker_v8554.py
Não executa dentro do processo web; necessita DATABASE_URL e demais variáveis do app.
"""
import csv
import io
import os
import time
from datetime import datetime, timedelta
from app import app, db, V8554ReportJob, ManagementTask

def safe_cell(value):
    text = str(value if value is not None else '')
    return "'" + text if text.startswith(('=', '+', '-', '@', '\t', '\r')) else text

def run_one():
    with app.app_context():
        # Bloqueio de linha evita que dois workers executem o mesmo job.
        job=(db.session.query(V8554ReportJob)
                 .filter(V8554ReportJob.status=='PENDING')
                 .order_by(V8554ReportJob.id)
                 .with_for_update(skip_locked=True).first())
        if job is None:return False
        job.status='RUNNING'
        job.started_at=datetime.utcnow()
        jid=job.id
        db.session.commit()
        try:
            stream=io.StringIO()
            writer=csv.writer(stream,lineterminator='\n')
            writer.writerow(['ID','Titulo','Projeto','Departamento','Prioridade','Status','Responsavel_ID','Prazo','ATM','Criado_em'])
            with app.app_context():
                rows=(ManagementTask.query.order_by(ManagementTask.id)
                      .limit(10000).all())
                for t in rows:
                    writer.writerow([safe_cell(x) for x in
                        (t.id,t.title,t.project,t.department,t.priority,t.status,
                         t.assigned_to,t.due_at.isoformat() if t.due_at else '',
                         t.atm_id,t.created_at.isoformat() if t.created_at else '')])
                job=db.session.get(V8554ReportJob,jid)
                job.result_csv=stream.getvalue()
                job.status='DONE'
                job.finished_at=datetime.utcnow()
                db.session.commit()
        except Exception as exc:
            db.session.rollback()
            job=db.session.get(V8554ReportJob,jid)
            job.status='FAILED'
            job.error=str(exc)[:450]
            job.finished_at=datetime.utcnow()
            db.session.commit()
        return True

if __name__=='__main__':
    interval=max(2,int(os.environ.get('REPORT_WORKER_POLL_SECONDS','5')))
    with app.app_context():
        db.create_all()
    while True:
        try:
            if not run_one():time.sleep(interval)
        except Exception:
            time.sleep(interval)
