"""V87.4 incremental: atividade POS Metrô. Não altera tabelas legadas."""
from datetime import datetime
from io import BytesIO
from functools import wraps
from flask import request,session,abort,redirect,jsonify,render_template,send_file
from sqlalchemy import func
from openpyxl import load_workbook,Workbook

def install_pos_metro(app,db,can):
 class POS(db.Model):
  __tablename__='v874_pos_metro'
  id=db.Column(db.Integer,primary_key=True)
  terminal=db.Column(db.String(90),unique=True,nullable=False)
  line=db.Column(db.String(100),nullable=False,default='')
  station=db.Column(db.String(150),nullable=False,default='')
  serial=db.Column(db.String(120))
  asset=db.Column(db.String(120))
  manufacturer=db.Column(db.String(120))
  model=db.Column(db.String(120))
  status=db.Column(db.String(25),nullable=False,default='Pendente')
  installed_on=db.Column(db.DateTime)
 class Event(db.Model):
  __tablename__='v874_pos_metro_events'
  id=db.Column(db.Integer,primary_key=True)
  pos_id=db.Column(db.Integer,db.ForeignKey('v874_pos_metro.id'),nullable=False,index=True)
  old_serial=db.Column(db.String(120))
  new_serial=db.Column(db.String(120))
  old_model=db.Column(db.String(120))
  new_model=db.Column(db.String(120))
  notes=db.Column(db.Text)
  user_id=db.Column(db.Integer,nullable=False)
  occurred_at=db.Column(db.DateTime,default=datetime.utcnow,nullable=False)
 def guard(permission):
  def deco(fn):
   @wraps(fn)
   def wrapped(*args,**kwargs):
    if not session.get('user_id'):return redirect('/login')
    if not can(permission):abort(403)
    POS.__table__.create(bind=db.engine,checkfirst=True)
    Event.__table__.create(bind=db.engine,checkfirst=True)
    return fn(*args,**kwargs)
   return wrapped
  return deco
 def selected():
  q=POS.query
  for arg,col in [('linha',POS.line),('estacao',POS.station),('status',POS.status)]:
   v=(request.args.get(arg) or '').strip()
   if v:q=q.filter(col==v)
  search=(request.args.get('q') or '').strip()
  if search:q=q.filter(POS.terminal.ilike('%'+search+'%'))
  return q
 @app.get('/field/troca-pos-metro')
 @guard('field.pos_metro')
 def pos_page():
  q=selected(); items=q.order_by(POS.line,POS.station,POS.terminal).limit(500).all()
  total=q.count(); done=q.filter(POS.status=='Concluído').count(); ongoing=q.filter(POS.status=='Em andamento').count()
  lines=[x[0] for x in db.session.query(POS.line).distinct().order_by(POS.line)]
  stations=[x[0] for x in db.session.query(POS.station).filter(POS.line==request.args.get('linha')).distinct().order_by(POS.station)] if request.args.get('linha') else []
  return render_template('v874_pos_metro.html',items=items,total=total,done=done,ongoing=ongoing,lines=lines,stations=stations,can_pos=can)
 @app.post('/field/troca-pos-metro/importar')
 @guard('field.pos_metro.import')
 def pos_import():
  f=request.files.get('arquivo')
  if not f or not f.filename.lower().endswith('.xlsx'):return jsonify(error='Arquivo XLSX necessário'),400
  wb=load_workbook(BytesIO(f.read(5_000_001)),read_only=True,data_only=True)
  if 'INSTALAÇÃO POS 2025_2026' not in wb:return jsonify(error='Aba de origem não encontrada'),400
  sheet=wb['INSTALAÇÃO POS 2025_2026']; n=0
  for r in sheet.iter_rows(min_row=6,values_only=True):
   if len(r)<15 or not r[3] or not r[5] or not r[6]:continue
   terminal=str(r[3]).strip()[:90]
   obj=POS.query.filter_by(terminal=terminal).first()
   if obj is None:obj=POS(terminal=terminal);db.session.add(obj)
   # Importação não apaga execuções nem regride status de atividades existentes.
   obj.line=str(r[5]).strip()[:100];obj.station=str(r[6]).strip()[:150]
   if obj.id is None or not db.session.query(Event.id).filter(Event.pos_id==obj.id).first():
    obj.serial=str(r[9] or '')[:120];obj.asset=str(r[10] or '')[:120];obj.manufacturer=str(r[11] or '')[:120];obj.model=str(r[12] or '')[:120]
    obj.status='Concluído' if str(r[13] or '').strip().upper()=='SIM' else 'Pendente'
    if isinstance(r[14],datetime):obj.installed_on=r[14]
   n+=1
  db.session.commit()
  return redirect('/field/troca-pos-metro')
 @app.post('/field/troca-pos-metro/<int:pid>/registrar')
 @guard('field.pos_metro.execute')
 def pos_register(pid):
  obj=db.session.get(POS,pid)
  if not obj:abort(404)
  serial=(request.form.get('serial') or '').strip()[:120]
  if not serial:return jsonify(error='Número de série obrigatório'),400
  event=Event(pos_id=pid,old_serial=obj.serial,old_model=obj.model,new_serial=serial,new_model=(request.form.get('modelo') or '')[:120],notes=(request.form.get('observacoes') or '')[:2000],user_id=session['user_id'])
  db.session.add(event);obj.serial=serial;obj.model=event.new_model;obj.status='Concluído';obj.installed_on=datetime.utcnow();db.session.commit()
  return redirect('/field/troca-pos-metro')
 @app.get('/field/troca-pos-metro/exportar')
 @guard('field.pos_metro.export')
 def pos_export():
  wb=Workbook();ws=wb.active;ws.title='POS Metrô';ws.append(['Linha','Estação','Terminal','Série','Patrimônio','Fabricante','Modelo','Status','Instalação'])
  for x in selected().order_by(POS.line,POS.station,POS.terminal):ws.append([x.line,x.station,x.terminal,x.serial,x.asset,x.manufacturer,x.model,x.status,x.installed_on])
  stream=BytesIO();wb.save(stream);stream.seek(0)
  return send_file(stream,as_attachment=True,download_name='pos_metro_filtrado.xlsx',mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
