"""V86.1 — Estoque Central multi-localidade (Web responsiva)."""
from datetime import datetime
from functools import wraps
from io import BytesIO
import base64, json, re, uuid
from flask import request, session, jsonify, abort, redirect, url_for, render_template, send_file
from sqlalchemy import func
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill


def install_v86(app, db, User, can):
    class Warehouse(db.Model):
        __tablename__='v86_warehouses'
        id=db.Column(db.Integer,primary_key=True)
        name=db.Column(db.String(120),nullable=False,unique=True)
        active=db.Column(db.Boolean,default=True,nullable=False)

    class Material(db.Model):
        __tablename__='v86_materials'
        id=db.Column(db.Integer,primary_key=True)
        code=db.Column(db.String(80),unique=True,index=True)
        description=db.Column(db.String(300),nullable=False)
        original_description=db.Column(db.String(300),nullable=False)
        unit=db.Column(db.String(24),default='UN',nullable=False)
        classified=db.Column(db.Boolean,default=False,nullable=False)
        active=db.Column(db.Boolean,default=True,nullable=False)
        created_by=db.Column(db.Integer,nullable=False)
        created_at=db.Column(db.DateTime,default=datetime.utcnow,nullable=False)

    class Photo(db.Model):
        __tablename__='v86_material_photos'
        id=db.Column(db.Integer,primary_key=True)
        material_id=db.Column(db.Integer,db.ForeignKey('v86_materials.id'),nullable=False,index=True)
        mime=db.Column(db.String(60),nullable=False)
        data=db.Column(db.LargeBinary,nullable=False)
        created_at=db.Column(db.DateTime,default=datetime.utcnow,nullable=False)

    class Balance(db.Model):
        __tablename__='v86_stock_balances'
        id=db.Column(db.Integer,primary_key=True)
        warehouse_id=db.Column(db.Integer,db.ForeignKey('v86_warehouses.id'),nullable=False)
        material_id=db.Column(db.Integer,db.ForeignKey('v86_materials.id'),nullable=False)
        quantity=db.Column(db.Integer,default=0,nullable=False)
        __table_args__=(db.UniqueConstraint('warehouse_id','material_id',name='uq_v86_wh_mat'),)

    class Movement(db.Model):
        __tablename__='v86_stock_movements'
        id=db.Column(db.Integer,primary_key=True)
        warehouse_id=db.Column(db.Integer,nullable=False)
        material_id=db.Column(db.Integer,nullable=False)
        user_id=db.Column(db.Integer,nullable=False)
        kind=db.Column(db.String(30),nullable=False)
        quantity=db.Column(db.Integer,nullable=False)
        before_qty=db.Column(db.Integer,nullable=False)
        after_qty=db.Column(db.Integer,nullable=False)
        note=db.Column(db.String(500))
        created_at=db.Column(db.DateTime,default=datetime.utcnow,nullable=False)

    initialized=False
    def setup():
        nonlocal initialized
        if initialized:return
        for cls in (Warehouse,Material,Photo,Balance,Movement):
            cls.__table__.create(bind=db.engine,checkfirst=True)
        # Migração incremental: preserva todas as linhas e fotos existentes.
        from sqlalchemy import inspect, text
        columns={x['name'] for x in inspect(db.engine).get_columns('v86_materials')}
        if 'active' not in columns:
            with db.engine.begin() as con:
                con.execute(text('ALTER TABLE v86_materials ADD COLUMN active BOOLEAN NOT NULL DEFAULT TRUE'))
        if not Warehouse.query.first():
            db.session.add_all([Warehouse(name='Liberdade'),Warehouse(name='Guardiã')]);db.session.commit()
        initialized=True

    def guard(permission):
        def outer(fn):
            @wraps(fn)
            def inner(*args,**kwargs):
                if not session.get('user_id'):
                    if request.path.startswith('/api/'):
                        return jsonify(ok=False,error='Autenticação necessária'),401
                    return redirect(url_for('login'))
                if not can(permission):abort(403)
                setup()
                return fn(*args,**kwargs)
            return inner
        return outer

    def payload_material(m):
        return {'id':m.id,'code':m.code,'description':m.description,'original_description':m.original_description,
                'unit':m.unit,'classified':m.classified,'active':m.active,'photo_url':('/api/engenharia/estoque/fotos/'+str(m.id)) if Photo.query.filter_by(material_id=m.id).first() else None}

    @app.get('/engenharia/estoque')
    @guard('engineering.stock.view')
    def v86_stock_page():
        return render_template('v86_stock.html',app_release='V87.1',can_stock=can)

    @app.get('/api/engenharia/estoque')
    @guard('engineering.stock.view')
    def v86_stock_list():
        wid=request.args.get('warehouse_id',type=int)
        q=(request.args.get('q') or '').strip()[:100]
        wh=Warehouse.query.filter_by(active=True).order_by(Warehouse.name).all()
        materials=Material.query.filter_by(active=True)
        if q:
            pattern='%'+q.replace('%','\\%').replace('_','\\_')+'%'
            materials=materials.filter(db.or_(Material.description.ilike(pattern),Material.code.ilike(pattern),Material.original_description.ilike(pattern)))
        mats=materials.order_by(Material.description).limit(400).all()
        balances=Balance.query.filter(Balance.material_id.in_([m.id for m in mats])).all() if mats else []
        bm={(b.material_id,b.warehouse_id):b.quantity for b in balances}
        result=[]
        for m in mats:
            d=payload_material(m)
            d['quantity']=sum(b.quantity for b in balances if b.material_id==m.id and (not wid or b.warehouse_id==wid))
            d['by_warehouse']={str(w.id):bm.get((m.id,w.id),0) for w in wh}
            result.append(d)
        movements=Movement.query.filter_by(warehouse_id=wid).count() if wid else Movement.query.count()
        counts={'items':sum(x['quantity']>0 for x in result),'units':sum(x['quantity'] for x in result),'unclassified':sum(x['quantity']>0 and not x['classified'] for x in result),
                'movements':movements}
        return jsonify(ok=True,warehouses=[{'id':w.id,'name':w.name,'active':w.active} for w in wh],items=result,counts=counts)

    @app.post('/api/engenharia/estoque/localidades')
    @guard('engineering.stock.locations')
    def v86_warehouse_add():
        d=request.get_json(silent=True) or {}; name=str(d.get('name') or '').strip()[:120]
        if len(name)<2:return jsonify(ok=False,error='Informe o nome da localidade.'),400
        if Warehouse.query.filter(func.lower(Warehouse.name)==name.lower()).first():return jsonify(ok=False,error='Localidade já cadastrada.'),409
        db.session.add(Warehouse(name=name));db.session.commit()
        return jsonify(ok=True)

    @app.patch('/api/engenharia/estoque/localidades/<int:wid>')
    @guard('engineering.stock.locations')
    def v861_warehouse_edit(wid):
        w=db.session.get(Warehouse,wid)
        if not w:abort(404)
        d=request.get_json(silent=True) or {}
        name=str(d.get('name') or '').strip()[:120]
        if len(name)<2:return jsonify(ok=False,error='Informe o nome da localidade.'),400
        duplicate=Warehouse.query.filter(Warehouse.id!=wid,func.lower(Warehouse.name)==name.lower()).first()
        if duplicate:return jsonify(ok=False,error='Localidade já cadastrada.'),409
        w.name=name
        db.session.commit()
        return jsonify(ok=True)

    @app.delete('/api/engenharia/estoque/localidades/<int:wid>')
    @guard('engineering.stock.locations')
    def v861_warehouse_remove(wid):
        w=db.session.get(Warehouse,wid)
        if not w:abort(404)
        if Balance.query.filter_by(warehouse_id=wid).first() or Movement.query.filter_by(warehouse_id=wid).first():
            w.active=False
            db.session.commit()
            return jsonify(ok=True,inactivated=True,message='Localidade inativada: histórico preservado.')
        db.session.delete(w)
        db.session.commit()
        return jsonify(ok=True,inactivated=False)

    @app.patch('/api/engenharia/estoque/materiais/<int:mid>')
    @guard('engineering.stock.classify')
    def v861_material_edit(mid):
        m=db.session.get(Material,mid)
        if not m or not m.active:abort(404)
        d=request.get_json(silent=True) or {}
        description=str(d.get('description') or '').strip()[:300]
        code=str(d.get('code') or '').strip().upper()[:80]
        if len(description)<3:return jsonify(ok=False,error='Descrição deve ter ao menos 3 caracteres.'),400
        if code:
            duplicate=Material.query.filter(Material.id!=mid,func.upper(Material.code)==code).first()
            if duplicate:return jsonify(ok=False,error='Código já utilizado.'),409
        previous=f'{m.code} | {m.description}'
        m.description=description
        if code:
            m.code=code
            m.classified=not code.startswith('PROV-')
        db.session.add(Movement(warehouse_id=0,material_id=mid,user_id=session['user_id'],
            kind='EDICAO',quantity=0,before_qty=0,after_qty=0,
            note=f'{previous} -> {m.code} | {m.description}'[:500]))
        db.session.commit()
        return jsonify(ok=True,item=payload_material(m))

    @app.delete('/api/engenharia/estoque/materiais/<int:mid>')
    @guard('engineering.stock.classify')
    def v861_material_remove(mid):
        m=db.session.get(Material,mid)
        if not m or not m.active:abort(404)
        has_history=Movement.query.filter_by(material_id=mid).first() is not None
        has_balance=Balance.query.filter_by(material_id=mid).first() is not None
        if has_history or has_balance:
            positive=Balance.query.filter(Balance.material_id==mid,Balance.quantity!=0).first()
            if positive:return jsonify(ok=False,error='Material possui saldo. Zere o saldo por movimentação auditável antes de inativar.'),409
            m.active=False
            db.session.add(Movement(warehouse_id=0,material_id=mid,user_id=session['user_id'],kind='INATIVACAO',
                quantity=0,before_qty=0,after_qty=0,note='Cadastro inativado, histórico preservado'))
            db.session.commit()
            return jsonify(ok=True,inactivated=True)
        Photo.query.filter_by(material_id=mid).delete()
        db.session.delete(m)
        db.session.commit()
        return jsonify(ok=True,inactivated=False)

    def save_photo(m, file):
        if not file or not file.filename:return
        mime=file.mimetype or ''
        if mime not in ('image/jpeg','image/png','image/webp'):raise ValueError('Foto deve ser JPG, PNG ou WebP.')
        data=file.read(2*1024*1024+1)
        if not data or len(data)>2*1024*1024:raise ValueError('Foto deve ter até 2 MB.')
        db.session.add(Photo(material_id=m.id,mime=mime,data=data))

    @app.post('/api/engenharia/estoque/materiais')
    @guard('engineering.stock.create')
    def v86_material_add():
        name=(request.form.get('description') or '').strip()[:300]
        if len(name)<3:return jsonify(ok=False,error='Informe a descrição do item.'),400
        m=Material(description=name,original_description=name,unit='UN',classified=False,created_by=session['user_id'])
        try:
            db.session.add(m);db.session.flush();m.code='PROV-'+str(m.id).zfill(6)
            save_photo(m,request.files.get('photo'))
            db.session.commit()
            return jsonify(ok=True,item=payload_material(m))
        except ValueError as e:
            db.session.rollback();return jsonify(ok=False,error=str(e)),400

    @app.post('/api/engenharia/estoque/materiais/<int:mid>/classificar')
    @guard('engineering.stock.classify')
    def v86_material_classify(mid):
        m=db.session.get(Material,mid)
        if not m:abort(404)
        d=request.get_json(silent=True) or {}
        name=str(d.get('description') or '').strip()[:300]
        code=str(d.get('code') or '').strip().upper()[:80]
        if not name or not code:return jsonify(ok=False,error='Código e descrição obrigatórios.'),400
        duplicate=Material.query.filter(Material.id!=mid,func.upper(Material.code)==code).first()
        if duplicate:return jsonify(ok=False,error='Código já cadastrado.'),409
        m.code=code;m.description=name;m.classified=True
        db.session.add(Movement(warehouse_id=0,material_id=mid,user_id=session['user_id'],kind='CLASSIFICACAO',quantity=0,before_qty=0,after_qty=0,note='Código/descrição revisados'))
        db.session.commit();return jsonify(ok=True,item=payload_material(m))

    @app.get('/api/engenharia/estoque/fotos/<int:mid>')
    @guard('engineering.stock.view')
    def v86_material_photo(mid):
        photo=Photo.query.filter_by(material_id=mid).order_by(Photo.id).first()
        if not photo:abort(404)
        response=send_file(BytesIO(photo.data),mimetype=photo.mime,download_name='material-'+str(mid)+'.jpg')
        response.headers['Cache-Control']='private, max-age=300'
        return response

    @app.post('/api/engenharia/estoque/movimentar')
    @guard('engineering.stock.move')
    def v86_stock_move():
        d=request.get_json(silent=True) or {}
        try: wid=int(d.get('warehouse_id'));mid=int(d.get('material_id'));qty=int(d.get('quantity'))
        except (ValueError,TypeError):return jsonify(ok=False,error='Localidade, item e quantidade são obrigatórios.'),400
        kind=str(d.get('kind') or '').upper()
        if kind not in ('CONTAGEM','ENTRADA','RETIRADA'):return jsonify(ok=False,error='Tipo de movimento inválido.'),400
        if qty<0 or (kind!='CONTAGEM' and qty==0):return jsonify(ok=False,error='Quantidade inválida.'),400
        if not Warehouse.query.filter_by(id=wid,active=True).first() or not Material.query.filter_by(id=mid,active=True).first():return jsonify(ok=False,error='Item ou localidade inexistente.'),404
        try:
            # Lock de localidade serializa as alterações de saldo, inclusive quando ainda não há linha de balanço.
            Warehouse.query.filter_by(id=wid).with_for_update().first()
            b=Balance.query.filter_by(warehouse_id=wid,material_id=mid).with_for_update().first()
            if not b:
                b=Balance(warehouse_id=wid,material_id=mid,quantity=0);db.session.add(b);db.session.flush()
            before=b.quantity
            after=qty if kind=='CONTAGEM' else before+(qty if kind=='ENTRADA' else -qty)
            if after<0:return jsonify(ok=False,error='Saldo insuficiente para retirada.'),409
            # Contagem com divergência é registrada como conferência pendente, sem alterar saldo.
            if kind=='CONTAGEM' and before!=after and before!=0:
                db.session.add(Movement(warehouse_id=wid,material_id=mid,user_id=session['user_id'],kind='CONTAGEM_DIVERGENTE',quantity=qty,before_qty=before,after_qty=before,note=str(d.get('note') or '')[:500]))
                db.session.commit();return jsonify(ok=True,pending_review=True,before=before,counted=qty)
            b.quantity=after
            db.session.add(Movement(warehouse_id=wid,material_id=mid,user_id=session['user_id'],kind=kind,quantity=qty,before_qty=before,after_qty=after,note=str(d.get('note') or '')[:500]))
            db.session.commit();return jsonify(ok=True,before=before,after=after)
        except Exception:
            db.session.rollback();raise

    @app.get('/api/engenharia/estoque/movimentacoes')
    @guard('engineering.stock.view')
    def v86_stock_history():
        wid=request.args.get('warehouse_id',type=int)
        query=Movement.query
        if wid:query=query.filter_by(warehouse_id=wid)
        rows=query.order_by(Movement.id.desc()).limit(300).all()
        return jsonify(ok=True,rows=[{'id':r.id,'date':r.created_at.isoformat(),'warehouse_id':r.warehouse_id,'material_id':r.material_id,'user_id':r.user_id,'kind':r.kind,'quantity':r.quantity,'before':r.before_qty,'after':r.after_qty,'note':r.note} for r in rows])

    @app.get('/api/engenharia/estoque/exportar')
    @guard('engineering.stock.export')
    def v86_stock_export():
        wb=Workbook();ws=wb.active;ws.title='Estoque Atual'
        ws.append(['Código','Descrição','Descrição original','Localidade','Quantidade','Unidade','Classificado','Foto (link interno)'])
        for m in Material.query.order_by(Material.description).all():
            for b in Balance.query.filter_by(material_id=m.id).all():
                w=db.session.get(Warehouse,b.warehouse_id)
                ws.append([m.code,m.description,m.original_description,w.name if w else '',b.quantity,m.unit,'Sim' if m.classified else 'Não',request.host_url.rstrip('/')+'/api/engenharia/estoque/fotos/'+str(m.id)])
        hs=wb.create_sheet('Movimentações');hs.append(['Data','Localidade ID','Item ID','Usuário ID','Tipo','Quantidade','Antes','Depois','Observação'])
        for r in Movement.query.order_by(Movement.id.desc()).limit(20000).all():
            hs.append([r.created_at.strftime('%d/%m/%Y %H:%M'),r.warehouse_id,r.material_id,r.user_id,r.kind,r.quantity,r.before_qty,r.after_qty,r.note])
        for sh in wb:
            sh.freeze_panes='A2';sh.auto_filter.ref=sh.dimensions
            for c in sh[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='16456D')
        buff=BytesIO();wb.save(buff);buff.seek(0)
        return send_file(buff,mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',as_attachment=True,download_name='Estoque_Central_V86.xlsx')
