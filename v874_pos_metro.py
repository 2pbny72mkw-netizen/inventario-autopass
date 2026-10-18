"""V87.4 incremental: atividade POS Metrô. Não altera tabelas legadas."""
from datetime import datetime
from io import BytesIO
from functools import wraps
from flask import request,session,abort,redirect,jsonify,render_template,send_file
from sqlalchemy import func, or_
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
  if search:q=q.filter(or_(POS.terminal.ilike('%'+search+'%'),POS.serial.ilike('%'+search+'%'),POS.asset.ilike('%'+search+'%')))
  return q
 @app.get('/field/troca-pos-metro')
 @guard('field.pos_metro')
 def pos_page():
  q=selected();items=q.order_by(POS.line,POS.station,POS.terminal).limit(500).all()
  overall=POS.query
  total=overall.count();done=overall.filter(POS.status=='Concluído').count();ongoing=overall.filter(POS.status=='Em andamento').count()
  lines=[x[0] for x in db.session.query(POS.line).distinct().order_by(POS.line)]
  stations_q=db.session.query(POS.station)
  if request.args.get('linha'):stations_q=stations_q.filter(POS.line==request.args['linha'])
  stations=[x[0] for x in stations_q.distinct().order_by(POS.station)]
  station_name=(request.args.get('estacao') or '').strip()
  station_q=POS.query.filter(POS.station==station_name) if station_name else None
  if station_q is not None and request.args.get('linha'):station_q=station_q.filter(POS.line==request.args['linha'])
  st_total=station_q.count() if station_q is not None else 0
  st_done=station_q.filter(POS.status=='Concluído').count() if station_q is not None else 0
  st_ongoing=station_q.filter(POS.status=='Em andamento').count() if station_q is not None else 0
  return render_template('v874_pos_metro.html',items=items,total=total,done=done,ongoing=ongoing,lines=lines,stations=stations,can_pos=can,st_total=st_total,st_done=st_done,st_ongoing=st_ongoing,filtered_count=q.count())
 @app.post('/field/troca-pos-metro/importar')
 @guard('field.pos_metro.import')
 def pos_import():
  f=request.files.get('arquivo')
  if not f or not (f.filename or '').lower().endswith('.xlsx'):return jsonify(error='Arquivo XLSX necessário'),400
  raw=f.read(5_000_001)
  if len(raw)>5_000_000:return jsonify(error='Arquivo excede 5 MB'),413
  try:wb=load_workbook(BytesIO(raw),read_only=True,data_only=True)
  except Exception:return jsonify(error='Planilha inválida'),400
  if 'Metrô' not in wb:return jsonify(error='Aba Metrô não encontrada'),400
  sheet=wb['Metrô']; rows=sheet.iter_rows(values_only=True)
  header=next(rows,None)
  if not header:return jsonify(error='Planilha vazia'),400
  def norm(v):
   import unicodedata
   return ''.join(c for c in unicodedata.normalize('NFKD',str(v or '').strip().upper()) if not unicodedata.combining(c)).replace('º','').replace('°','').replace('°','').replace(' ','').replace('N','N')
  columns={norm(v):i for i,v in enumerate(header)}
  required=['TERMINAL','LINHA','ESTACAO']
  if any(k not in columns for k in required):return jsonify(error='Colunas obrigatórias ausentes: TERMINAL, LINHA, ESTAÇÃO'),400
  def val(r,k):
   i=columns.get(k)
   return str(r[i]).strip() if i is not None and i<len(r) and r[i] is not None else ''
  records={}
  for r in rows:
   terminal=val(r,'TERMINAL')[:90];line=val(r,'LINHA')[:100];station=val(r,'ESTACAO')[:150]
   if not terminal or not line or not station:continue
   if terminal in records:return jsonify(error='Terminal duplicado na planilha: '+terminal),400
   records[terminal]=(line,station,val(r,'MODELO')[:120],val(r,'NSERIE')[:120],val(r,'PATRIMONIO')[:120],val(r,'FABRICANTE')[:120])
  if not records:return jsonify(error='Nenhum POS válido encontrado'),400
  try:
   existing={p.terminal:p for p in POS.query.filter(POS.terminal.in_(list(records))).all()}
   for terminal,(line,station,model,serial,asset,manufacturer) in records.items():
    obj=existing.get(terminal)
    if obj is None:
     obj=POS(terminal=terminal,status='Pendente');db.session.add(obj)
    obj.line=line;obj.station=station
    # Importações subsequentes não sobrescrevem informações executadas em campo.
    if obj.id is None or not db.session.query(Event.id).filter(Event.pos_id==obj.id).first():
     if model:obj.model=model
     if serial:obj.serial=serial
     if asset:obj.asset=asset
     if manufacturer:obj.manufacturer=manufacturer
   db.session.commit()
  except Exception:
   db.session.rollback();raise
  finally:wb.close()
  from flask import flash
  flash(f'Importação concluída: {len(records)} terminais processados.', 'success')
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
