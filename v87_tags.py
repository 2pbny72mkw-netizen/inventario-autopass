"""REV25: TAGs/Produtos — banco próprio, importação pré-validada e exportação."""
from datetime import datetime
from functools import wraps
from io import BytesIO
import re, unicodedata, json
from flask import request, session, jsonify, abort, redirect, url_for, render_template, send_file
from sqlalchemy import func
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font, PatternFill

def norm(s):
    s=unicodedata.normalize('NFKD',str(s or '')).encode('ascii','ignore').decode().upper()
    return re.sub(r'[^A-Z0-9]+','_',s).strip('_')
FIELDS=['serial','patrimonio','produto','lote','empresa','localidade','finalidade','status','nf_entrada','nf_saida','caixa','observacao']
ALIASES={
 'serial':['N_SERIE','N_DE_SERIE','NUMERO_DE_SERIE','NUMERO_SERIE','SERIE','SERIAL','TAG','N_SERIE_TAG','N_SERIE_BF80','N_S','NSERIE'],
 'patrimonio':['PATRIMONIO','N_PATRIMONIO'], 'produto':['PRODUTO','MODELO','EQUIPAMENTO'],
 'lote':['LOTE','PRODUCAO','N_PRODUCAO','FABRICACAO'],
 'empresa':['EMPRESA','PROPRIETARIO','EMPRESA_PROPRIETARIA'],
 'localidade':['LOCAL_PROJETO','LOCALIDADE','LOCAL','PROJETO','DESTINO','ENDERECAMENTO'],
 'finalidade':['FINALIDADE','TIPO_OPERACAO'],
 'status':['STATUS','STATUS_OPERACIONAL','SITUACAO'],
 'nf_entrada':['NF_ENTRADA','NOTA_FISCAL_ENTRADA','NF_DE_ENTRADA'],
 'nf_saida':['NF_SAIDA','NOTA_FISCAL_SAIDA','NF_DE_SAIDA'],
 'caixa':['CAIXA','N_CAIXA'], 'observacao':['OBSERVACAO','OBSERVACOES','OBS']}
ALIASES={k:set([norm(k)]+[norm(x) for x in v]) for k,v in ALIASES.items()}

def install_tags(app,db,can):
 class Tag(db.Model):
    __tablename__='v87_product_tags'
    id=db.Column(db.Integer,primary_key=True)
    serial=db.Column(db.String(160),nullable=False)
    produto=db.Column(db.String(160),nullable=False,default='BF80')
    patrimonio=db.Column(db.String(160),default='')
    lote=db.Column(db.String(120),default='')
    empresa=db.Column(db.String(160),default='')
    localidade=db.Column(db.String(200),default='')
    finalidade=db.Column(db.String(120),default='')
    status=db.Column(db.String(120),default='')
    nf_entrada=db.Column(db.String(120),default='')
    nf_saida=db.Column(db.String(120),default='')
    caixa=db.Column(db.String(120),default='')
    observacao=db.Column(db.Text,default='')
    created_at=db.Column(db.DateTime,default=datetime.utcnow)
    updated_at=db.Column(db.DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)
    __table_args__=(db.UniqueConstraint('produto','serial',name='uq_v87_tags_product_serial'),)
 class Audit(db.Model):
    __tablename__='v87_product_tag_audit'
    id=db.Column(db.Integer,primary_key=True)
    tag_id=db.Column(db.Integer,nullable=False)
    user_id=db.Column(db.Integer,nullable=False)
    action=db.Column(db.String(30),nullable=False)
    before_json=db.Column(db.Text)
    after_json=db.Column(db.Text)
    created_at=db.Column(db.DateTime,default=datetime.utcnow)
 class ImportIssue(db.Model):
    __tablename__='v87_product_tag_import_issues'
    id=db.Column(db.Integer,primary_key=True)
    produto=db.Column(db.String(160),nullable=False)
    serial=db.Column(db.String(160),nullable=False)
    lines=db.Column(db.String(300),default='')
    detail=db.Column(db.Text,default='')
    file_name=db.Column(db.String(255),default='')
    user_id=db.Column(db.Integer,nullable=False)
    created_at=db.Column(db.DateTime,default=datetime.utcnow)
    resolved_at=db.Column(db.DateTime,nullable=True)
 initialized=False
 def guard(write=False):
    def outer(fn):
     @wraps(fn)
     def inner(*a,**kw):
      nonlocal initialized
      if not session.get('user_id'):
       return (jsonify(ok=False,error='Autenticação necessária'),401) if request.path.startswith('/api/') else redirect(url_for('login'))
      if not can('engineering.stock.view') or (write and not (can('engineering.stock.create') or can('engineering.stock.classify'))): abort(403)
      if not initialized:
       Tag.__table__.create(bind=db.engine,checkfirst=True)
       Audit.__table__.create(bind=db.engine,checkfirst=True)
       ImportIssue.__table__.create(bind=db.engine,checkfirst=True)
       initialized=True
      return fn(*a,**kw)
     return inner
    return outer
 def asdict(t):return {k:str(getattr(t,k) or '') for k in FIELDS}|{'id':t.id,'updated_at':t.updated_at.isoformat() if t.updated_at else ''}
 def query_filtered():
    q=Tag.query
    for field in ['produto','empresa','localidade','finalidade','status','lote']:
     val=request.args.get(field,'').strip()
     if val:q=q.filter(getattr(Tag,field)==val)
    search=request.args.get('q','').strip()
    if search:q=q.filter(db.or_(Tag.serial.ilike('%'+search+'%'),Tag.patrimonio.ilike('%'+search+'%'),Tag.localidade.ilike('%'+search+'%')))
    return q
 @app.get('/engenharia/tags')
 @guard()
 def tags_page():return render_template('v87_tags.html')
 @app.get('/api/engenharia/tags')
 @guard()
 def tags_list():
    q=query_filtered(); total=q.count()
    sort=request.args.get('sort','serial');sort=sort if sort in FIELDS else 'serial'
    col=getattr(Tag,sort)
    q=q.order_by(col.desc() if request.args.get('dir')=='desc' else col.asc(),Tag.id.asc())
    page=max(1,int(request.args.get('page',1)));limit=min(200,max(1,int(request.args.get('limit',30))))
    items=q.offset((page-1)*limit).limit(limit).all()
    all_rows=query_filtered().all()
    groups={}
    for key in ['produto','empresa','localidade','finalidade','status','lote']:
     counts={}
     for row in all_rows:
      v=getattr(row,key) or 'Não informado';counts[v]=counts.get(v,0)+1
     groups[key]=[{'name':k,'count':v} for k,v in sorted(counts.items(),key=lambda x:(-x[1],x[0]))]
    return jsonify(ok=True,total=total,page=page,limit=limit,items=[asdict(t) for t in items],groups=groups,
      summary={'total':total,'locacao':sum(1 for t in all_rows if 'LOC' in norm(t.finalidade)),
      'venda':sum(1 for t in all_rows if 'VEND' in norm(t.finalidade)),
      'estoque':sum(1 for t in all_rows if 'ESTOQUE' in norm(t.finalidade)),
      'localidades':len({t.localidade for t in all_rows if t.localidade}),
      'sem_nf':sum(1 for t in all_rows if not t.nf_entrada),
      'sem_patrimonio':sum(1 for t in all_rows if not t.patrimonio),
      'divergencias':ImportIssue.query.filter(ImportIssue.resolved_at.is_(None), ImportIssue.produto.in_([t.produto for t in all_rows] or [request.args.get('produto') or 'BF80'])).count()})
 @app.get('/api/engenharia/tags/modelo')
 @guard()
 def tags_model():
    wb=Workbook();ws=wb.active;ws.title='TAGs';ws.append(['Número de Série (TAG)','Patrimônio','Produto','Produção / Lote','Empresa','Local / Projeto','Finalidade','Status Operacional','NF Entrada','NF Saída','Caixa','Observação'])
    ws.append(['BF80-EXEMPLO-001','','BF80','1ª Produção','Autopass','BELÉM','Locação','Instalado','','','','EXEMPLO — excluir antes de importar'])
    for c in ws[1]:c.fill=PatternFill('solid',fgColor='17345D');c.font=Font(color='FFFFFF',bold=True)
    ws.freeze_panes='A2';ws.auto_filter.ref='A1:L2'
    for col in 'ABCDEFGHIJKL':ws.column_dimensions[col].width=22
    b=BytesIO();wb.save(b);b.seek(0)
    return send_file(b,as_attachment=True,download_name='Modelo_TAGs_Produtos.xlsx',mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
 @app.get('/api/engenharia/tags/exportar')
 @guard()
 def tags_export():
    rows=query_filtered().order_by(Tag.produto,Tag.serial).all();wb=Workbook();ws=wb.active;ws.title='TAGs'
    ws.append(['Nº Série (TAG)','Patrimônio','Produto','Produção/Lote','Empresa','Local/Projeto','Finalidade','Status','NF Entrada','NF Saída','Caixa','Observação'])
    for t in rows:ws.append([getattr(t,k) or '' for k in FIELDS])
    for c in ws[1]:c.fill=PatternFill('solid',fgColor='17345D');c.font=Font(color='FFFFFF',bold=True)
    ws.freeze_panes='A2';ws.auto_filter.ref=f'A1:L{max(2,ws.max_row)}'
    for col in 'ABCDEFGHIJKL':ws.column_dimensions[col].width=23
    summary=wb.create_sheet('Resumo');summary.append(['Indicador','Quantidade']);summary.append(['TAGs',len(rows)])
    for k in ['produto','lote','localidade','finalidade']:
     summary.append([]);summary.append([k.upper(),'Quantidade']);counts={}
     for t in rows:counts[getattr(t,k) or 'Não informado']=counts.get(getattr(t,k) or 'Não informado',0)+1
     for name,n in sorted(counts.items(),key=lambda v:-v[1]):summary.append([name,n])
    summary.column_dimensions['A'].width=40;summary.column_dimensions['B'].width=18
    b=BytesIO();wb.save(b);b.seek(0)
    return send_file(b,as_attachment=True,download_name='Controle_TAGs_Produtos.xlsx',mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
 def parse_xlsx(upload):
    if not upload or not upload.filename.lower().endswith('.xlsx'):raise ValueError('Envie um arquivo .xlsx válido.')
    raw=upload.read()
    if len(raw)>15*1024*1024:raise ValueError('Arquivo acima do limite de 15 MB.')
    wb=load_workbook(BytesIO(raw),read_only=True,data_only=True)
    try:
     best=None
     for ws in wb.worksheets:
      for ix,row in enumerate(ws.iter_rows(min_row=1,max_row=min(ws.max_row,35),values_only=True),1):
       mapping={}
       for j,cell in enumerate(row):
        h=norm(cell)
        for key,alias in ALIASES.items():
         if h in alias and key not in mapping:mapping[key]=j
       if 'serial' in mapping and (best is None or len(mapping)>len(best[2])):best=(ws,ix,mapping)
     if best is None:raise ValueError('Coluna de número de série não identificada. Utilize o modelo padrão de importação.')
     ws,start,mapping=best
     rows=[];errors=[];seen={};duplicates={}
     for ix,row in enumerate(ws.iter_rows(min_row=start+1,values_only=True),start+1):
      def val(k):
       j=mapping.get(k);v=row[j] if j is not None and j<len(row) else None
       if v is None:return ''
       if isinstance(v,(int,float)) and float(v).is_integer():return str(int(v))
       return str(v).strip()
      item={k:val(k) for k in FIELDS};item['produto']=item['produto'] or request.form.get('produto','BF80').strip() or 'BF80'
      if not any(item.values()) or not item['serial']:continue
      key=(item['produto'].casefold(),item['serial'].casefold())
      if key in seen:
       duplicates.setdefault(key,{'produto':item['produto'],'serial':item['serial'],'linhas':[seen[key]],'detalhes':[]})['linhas'].append(ix)
      else:seen[key]=ix
      rows.append(item)
      if len(rows)>20000:raise ValueError('Limite de 20.000 TAGs por importação.')
     return rows,[{'produto':v['produto'],'serial':v['serial'],'linhas':v['linhas']} for v in duplicates.values()]
    finally:wb.close()
 @app.get('/api/engenharia/tags/divergencias')
 @guard()
 def tags_issues():
    q=ImportIssue.query.filter(ImportIssue.resolved_at.is_(None))
    product=request.args.get('produto','').strip()
    if product:q=q.filter(ImportIssue.produto==product)
    rows=q.order_by(ImportIssue.created_at.desc()).limit(1000).all()
    return jsonify(ok=True,total=len(rows),items=[dict(id=x.id,produto=x.produto,serial=x.serial,linhas=x.lines,descricao=x.detail,detalhes_json=x.detail if x.detail.startswith('[') else '[]',arquivo=x.file_name,data=x.created_at.isoformat()) for x in rows])
 @app.post('/api/engenharia/tags/divergencias/<int:issue_id>/resolver')
 @guard(True)
 def tags_resolve_issue(issue_id):
    issue=ImportIssue.query.get_or_404(issue_id)
    if issue.resolved_at is not None:return jsonify(ok=False,error='Divergência já tratada.'),409
    payload=request.get_json(silent=True) or {}
    action=payload.get('acao')
    if action not in ('same','correct'):return jsonify(ok=False,error='Informe o tipo de tratamento.'),400
    uid=int(session['user_id'])
    if action=='correct':
     corrected=str(payload.get('serial_corrigido') or '').strip()
     if not corrected or corrected.casefold()==issue.serial.casefold():return jsonify(ok=False,error='A TAG corrigida deve ser diferente da original.'),400
     if len(corrected)>160:return jsonify(ok=False,error='TAG excede o tamanho permitido.'),400
     exists=Tag.query.filter(db.func.lower(Tag.produto)==issue.produto.lower(),db.func.lower(Tag.serial)==corrected.lower()).first()
     if exists:return jsonify(ok=False,error='TAG corrigida já cadastrada. Confira antes de prosseguir.'),409
     # Registro mínimo, pois as linhas conflitantes originais não foram armazenadas na REV25.
     tag=Tag(produto=issue.produto,serial=corrected)
     db.session.add(tag);db.session.flush()
     db.session.add(Audit(tag_id=tag.id,user_id=uid,action='INSERT',before_json=None,after_json=json.dumps({'produto':issue.produto,'serial':corrected,'origem':'tratamento de divergência','issue_id':issue.id},ensure_ascii=False)))
    issue.resolved_at=datetime.utcnow()
    db.session.commit()
    return jsonify(ok=True,acao=action,complementar_dados=(action=='correct'))
 @app.post('/api/engenharia/tags/importar')
 @guard(True)
 def tags_import():
    try:rows,errors=parse_xlsx(request.files.get('arquivo'))
    except Exception as e:return jsonify(ok=False,error=str(e)),400
    if not rows:return jsonify(ok=False,error='Nenhuma TAG encontrada.'),400
    duplicate_keys={(d['produto'].casefold(),d['serial'].casefold()) for d in errors}
    valid=[x for x in rows if (x['produto'].casefold(),x['serial'].casefold()) not in duplicate_keys]
    existing={ (t.produto.casefold(),t.serial.casefold()):t for t in Tag.query.filter(Tag.produto.in_({x['produto'] for x in valid})).all() }
    inserts=sum((x['produto'].casefold(),x['serial'].casefold()) not in existing for x in valid)
    updates=len(valid)-inserts
    preview=dict(ok=True,preview=True,inserts=inserts,updates=updates,total=len(rows),validos=len(valid),divergencias=errors,divergencias_count=len(errors),ignorados=len(rows)-len(valid))
    if request.form.get('confirmar')!='sim':return jsonify(**preview)
    if errors and request.form.get('ignorar_divergencias')!='sim':
     return jsonify(ok=False,error='Confirme explicitamente a importação parcial: TAGs duplicadas serão isoladas para conferência.'),409
    uid=int(session['user_id'])
    try:
     for item in valid:
      key=(item['produto'].casefold(),item['serial'].casefold());t=existing.get(key)
      before=json.dumps(asdict(t),ensure_ascii=False) if t else None
      if not t:
       t=Tag(serial=item['serial'],produto=item['produto']);db.session.add(t);db.session.flush();existing[key]=t
      for k in FIELDS:
       if k in ('serial','produto'):continue
       # Em atualização, células vazias não apagam informações existentes.
       if item[k]:setattr(t,k,item[k])
      db.session.add(Audit(tag_id=t.id,user_id=uid,action='UPDATE' if before else 'INSERT',before_json=before,after_json=json.dumps(asdict(t),ensure_ascii=False)))
     for issue in errors:
      # Preserva histórico; repetição da mesma planilha não cria alertas duplicados.
      found=ImportIssue.query.filter_by(produto=issue['produto'],serial=issue['serial'],file_name=(request.files.get('arquivo').filename or '')[:255],resolved_at=None).first()
      if not found:db.session.add(ImportIssue(produto=issue['produto'],serial=issue['serial'],lines=', '.join(map(str,issue['linhas'])),detail='TAG repetida dentro do Excel; não importada automaticamente',file_name=(request.files.get('arquivo').filename or '')[:255],user_id=uid))
     db.session.commit()
    except Exception:
     db.session.rollback();app.logger.exception('Erro importação TAGs');return jsonify(ok=False,error='Falha ao gravar. Nenhuma alteração foi confirmada.'),500
    return jsonify(ok=True,inserted=inserts,updated=updates,total=len(valid),divergencias_count=len(errors),ignorados=len(rows)-len(valid))


