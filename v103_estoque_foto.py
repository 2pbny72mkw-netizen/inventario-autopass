# -*- coding: utf-8 -*-
"""V88.0 REV15 - Estoque Central: adicionar/trocar/remover a foto do material e escolher entre câmera e galeria.

- POST   /api/engenharia/estoque/materiais/<id>/foto   (multipart, campo "photo"): troca a foto (fica uma só por material)
- DELETE /api/engenharia/estoque/materiais/<id>/foto   : remove a foto
- Tela /engenharia/estoque (injeção): botões "Tirar foto" e "Escolher da galeria" no cadastro de material e no painel do material
  selecionado; a foto é reduzida no navegador (máx. 1600 px, JPEG) para caber nos 2 MB.
Usa a tabela existente v86_material_photos; cada troca/remoção entra no histórico do material (kind EDICAO).
"""
import re

MAX_BYTES = 2 * 1024 * 1024
MIMES = {"image/jpeg", "image/png", "image/webp"}


def sniff(data):
    """Tipo real pelo conteúdo (não confia só no cabeçalho do navegador)."""
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


SCRIPT = r"""
<script data-v103-foto="1">
(function(){
if(window.__v103foto)return;window.__v103foto=1;
function $(i){return document.getElementById(i)}
function el(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e}
var MAXD=1600,LIMIT=1900000;
function shrink(file){return new Promise(function(res,rej){
  if(!file)return rej(new Error('Nenhuma foto escolhida.'));
  function plain(){ if(file.size<=2*1024*1024-1024)res(file); else rej(new Error('Não consegui reduzir esta foto. Tente outra (JPG, PNG ou WebP).')) }
  if(!window.createImageBitmap||!document.createElement('canvas').toBlob){return plain()}
  createImageBitmap(file).then(function(bm){
    var w=bm.width,h=bm.height,k=Math.min(1,MAXD/Math.max(w,h));
    if(k===1&&file.size<=LIMIT&&/jpeg|png|webp/.test(file.type)){return res(file)}
    var c=document.createElement('canvas');c.width=Math.max(1,Math.round(w*k));c.height=Math.max(1,Math.round(h*k));
    var g=c.getContext('2d');g.fillStyle='#fff';g.fillRect(0,0,c.width,c.height);g.drawImage(bm,0,0,c.width,c.height);
    var q=.85;(function tryq(){c.toBlob(function(b){
      if(!b)return plain();
      if(b.size>LIMIT&&q>.45){q-=.1;return tryq()}
      if(b.size>2*1024*1024-1024)return rej(new Error('A foto continua grande demais.'));
      res(new File([b],'foto.jpg',{type:'image/jpeg'}))},'image/jpeg',q)})()
  }).catch(function(){plain()})})}
function buttons(onFile){
  var box=el('div','v103-btns');
  function mk(label,capture){
    var inp=document.createElement('input');inp.type='file';inp.accept='image/jpeg,image/png,image/webp';if(capture)inp.setAttribute('capture','environment');inp.hidden=true;
    var b=el('button','v103-btn',label);b.type='button';b.onclick=function(){inp.value='';inp.click()};
    inp.onchange=function(){var f=inp.files&&inp.files[0];if(f)onFile(f)};
    box.append(inp,b);return b}
  var cam=mk('📷 Tirar foto',true),gal=mk('🖼 Escolher da galeria',false);
  box.setAttribute('data-ap-v','neutral');
  return {box:box,cam:cam,gal:gal}}
function css(){if($('v103css'))return;var s=el('style');s.id='v103css';
 s.textContent='.v103-btns{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0}.v103-btn{margin:0;font:inherit;font-size:13px;border:1px solid #c9d3e0;background:#fff;color:#16335c;border-radius:8px;padding:7px 12px;cursor:pointer}.v103-btn[disabled]{opacity:.5;cursor:default}.v103-btn.dng{color:#a02020;border-color:#e0b4b4}'+
 '.v103-box{border:1px solid #dbe3ee;background:#f8fafd;border-radius:10px;padding:10px 12px;margin:10px 0;display:flex;gap:12px;align-items:flex-start;flex-wrap:wrap}.v103-prev{width:96px;height:96px;border:1px solid #dbe3ee;border-radius:8px;background:#edf3f8 center/contain no-repeat;display:flex;align-items:center;justify-content:center;color:#8a97a8;font-size:26px;overflow:hidden;flex:none}.v103-prev img{width:100%;height:100%;object-fit:contain}'+
 '.v103-msg{font-size:12px;min-height:16px;color:#5b6b80}.v103-msg.err{color:#a02020}.v103-msg.ok{color:#0e6b4b}';
 document.head.append(s)}
css();
/* ---------- cadastro de material ---------- */
function setupNew(){
  var form=$('stNewForm');if(!form||form.__v103)return;var inp=form.querySelector('input[name=photo]');if(!inp)return;form.__v103=1;
  inp.removeAttribute('capture');inp.hidden=true;
  var lab=inp.closest('label');if(lab){lab.style.display='block';lab.firstChild.textContent='Foto do material (opcional; reduzida automaticamente)'}
  var prev=el('div','v103-prev','▧'),msg=el('div','v103-msg');
  function onFile(f){msg.className='v103-msg';msg.textContent='Preparando foto…';
    shrink(f).then(function(ff){var dt=new DataTransfer();dt.items.add(ff);inp.files=dt.files;
      prev.replaceChildren();var im=new Image();im.src=URL.createObjectURL(ff);prev.append(im);msg.className='v103-msg ok';msg.textContent='Foto pronta ('+Math.round(ff.size/1024)+' KB). Será enviada ao cadastrar.'})
    .catch(function(e){msg.className='v103-msg err';msg.textContent=e.message})}
  var bs=buttons(onFile);var clr=el('button','v103-btn','Limpar foto');clr.type='button';clr.onclick=function(){inp.value='';prev.replaceChildren(document.createTextNode('▧'));msg.textContent=''};bs.box.append(clr);
  var wrap=el('div','v103-box');var r=el('div');r.append(bs.box,msg);wrap.append(prev,r);
  (lab||inp).after(wrap);
  form.addEventListener('reset',function(){clr.click()})}
/* ---------- painel do material selecionado ---------- */
var cache={};var curCode=null;
function loadList(){return fetch('/api/engenharia/estoque',{credentials:'same-origin'}).then(function(r){return r.json()}).then(function(d){cache={};(d.items||[]).forEach(function(x){cache[x.code]=x});return cache})}
function findItem(code){return cache[code]?Promise.resolve(cache[code]):loadList().then(function(c){return c[code]||null})}
function setupSel(){
  var sel=$('stSelected');if(!sel||sel.__v103)return;sel.__v103=1;
  var box=el('div','v103-box');box.id='v103Photo';
  var prev=el('div','v103-prev','▧'),right=el('div'),title=el('b','', 'Foto do material'),msg=el('div','v103-msg');
  var state={id:null,has:false};
  function render(){prev.replaceChildren();
    if(state.id&&state.has){var im=new Image();im.src='/api/engenharia/estoque/fotos/'+state.id+'?v='+Date.now();im.alt='Foto do material';prev.append(im)}else prev.textContent='▧';
    rm.style.display=state.has?'':'none';bs.cam.textContent=state.has?'📷 Trocar (câmera)':'📷 Tirar foto';bs.gal.textContent=state.has?'🖼 Trocar (galeria)':'🖼 Escolher da galeria'}
  function busy(b){[bs.cam,bs.gal,rm].forEach(function(x){x.disabled=b})}
  function done(){var rl=$('stReload');if(rl)setTimeout(function(){rl.click()},400)}
  function send(f){if(!state.id)return;busy(true);msg.className='v103-msg';msg.textContent='Preparando foto…';
    shrink(f).then(function(ff){msg.textContent='Enviando…';var fd=new FormData();fd.append('photo',ff,ff.name||'foto.jpg');
      return fetch('/api/engenharia/estoque/materiais/'+state.id+'/foto',{method:'POST',body:fd,credentials:'same-origin'}).then(function(r){return r.json().catch(function(){return{ok:false,error:'Resposta inválida ('+r.status+')'}})})})
    .then(function(j){if(!j.ok)throw new Error(j.error||'Não foi possível salvar a foto.');state.has=true;if(cache[curCode])cache[curCode].photo_url='/api/engenharia/estoque/fotos/'+state.id;render();msg.className='v103-msg ok';msg.textContent='Foto salva.';done()})
    .catch(function(e){msg.className='v103-msg err';msg.textContent=e.message||'Erro ao enviar a foto.'}).then(function(){busy(false)})}
  var bs=buttons(send);
  var rm=el('button','v103-btn dng','Remover foto');rm.type='button';rm.onclick=function(){
    if(!state.id||!confirm('Remover a foto deste material?'))return;busy(true);
    fetch('/api/engenharia/estoque/materiais/'+state.id+'/foto',{method:'DELETE',credentials:'same-origin'}).then(function(r){return r.json()}).then(function(j){if(!j.ok)throw new Error(j.error||'Erro');state.has=false;if(cache[curCode])delete cache[curCode].photo_url;render();msg.className='v103-msg ok';msg.textContent='Foto removida.';done()})
    .catch(function(e){msg.className='v103-msg err';msg.textContent=e.message}).then(function(){busy(false)})};
  bs.box.append(rm);right.append(title,bs.box,msg);box.append(prev,right);
  var d=$('stSelectedDetail');(d||$('stSelectedTitle')).after(box);
  function sync(){var m=/^\s*(\S+)\s·/.exec(($('stSelectedDetail')||{}).textContent||'');var code=m&&m[1];if(!code)return;
    if(code===curCode&&state.id)return;curCode=code;state.id=null;state.has=false;render();msg.textContent='';
    findItem(code).then(function(it){if(curCode!==code)return;if(it){state.id=it.id;state.has=!!it.photo_url}render()})}
  render();var mo=new MutationObserver(sync);if($('stSelectedDetail'))mo.observe($('stSelectedDetail'),{childList:true,characterData:true,subtree:true});if($('stSelectedTitle'))mo.observe($('stSelectedTitle'),{childList:true,characterData:true,subtree:true});sync()}
function boot(){setupNew();setupSel()}
boot();new MutationObserver(boot).observe(document.body,{childList:true,subtree:true});
})();
</script>
"""


def install_estoque_foto(app, db, text, can):
    from flask import jsonify, request, session, abort

    def _auth():
        if not session.get("user_id"):
            return jsonify(ok=False, error="Autenticação necessária"), 401
        if not (can("engineering.stock.classify") or can("engineering.stock.create")):
            abort(403)
        return None

    def _material(mid):
        row = db.session.execute(text("SELECT id, active FROM v86_materials WHERE id=:i"), {"i": mid}).first()
        return row if row and row[1] else None

    def _log(mid, note):
        db.session.execute(text(
            "INSERT INTO v86_stock_movements (warehouse_id, material_id, user_id, kind, quantity, before_qty, after_qty, note, created_at) "
            "VALUES (0, :m, :u, 'EDICAO', 0, 0, 0, :n, CURRENT_TIMESTAMP)"), {"m": mid, "u": session.get("user_id"), "n": note[:500]})

    @app.post("/api/engenharia/estoque/materiais/<int:mid>/foto")
    def v103_foto_salvar(mid):
        g = _auth()
        if g:
            return g
        f = request.files.get("photo")
        if not f or not f.filename:
            return jsonify(ok=False, error="Escolha uma foto."), 400
        data = f.read(MAX_BYTES + 1)
        if not data:
            return jsonify(ok=False, error="Arquivo vazio."), 400
        if len(data) > MAX_BYTES:
            return jsonify(ok=False, error="Foto deve ter até 2 MB."), 400
        mime = sniff(data)
        if mime not in MIMES:
            return jsonify(ok=False, error="Foto deve ser JPG, PNG ou WebP."), 400
        try:
            if not _material(mid):
                return jsonify(ok=False, error="Material não encontrado."), 404
            had = db.session.execute(text("SELECT 1 FROM v86_material_photos WHERE material_id=:m LIMIT 1"), {"m": mid}).first() is not None
            _v107 = app.extensions.get("v107")  # REV17: foto no R2; a antiga sai do R2 depois do commit
            old_keys = _v107.keys_where("v86_material_photos", "material_id=:m", {"m": mid}) if _v107 else []
            db.session.execute(text("DELETE FROM v86_material_photos WHERE material_id=:m"), {"m": mid})
            db.session.execute(text("INSERT INTO v86_material_photos (material_id, mime, data, created_at) VALUES (:m, :t, :d, CURRENT_TIMESTAMP)"),
                               {"m": mid, "t": mime, "d": data})
            if _v107:
                new_id = db.session.execute(text("SELECT MAX(id) FROM v86_material_photos WHERE material_id=:m"), {"m": mid}).scalar()
                _v107.store("v86_material_photos", new_id, data, mime)
            _log(mid, "Foto " + ("trocada" if had else "adicionada") + " (" + str(max(1, len(data) // 1024)) + " KB)")
            db.session.commit()
            if _v107 and old_keys:
                _v107.delete_keys(old_keys)
            return jsonify(ok=True, substituida=had, kb=max(1, len(data) // 1024), photo_url="/api/engenharia/estoque/fotos/" + str(mid))
        except Exception:
            db.session.rollback()
            app.logger.exception("REV15 foto estoque")
            return jsonify(ok=False, error="Não foi possível salvar a foto."), 500

    @app.delete("/api/engenharia/estoque/materiais/<int:mid>/foto")
    def v103_foto_remover(mid):
        g = _auth()
        if g:
            return g
        try:
            if not _material(mid):
                return jsonify(ok=False, error="Material não encontrado."), 404
            _v107 = app.extensions.get("v107")
            old_keys = _v107.keys_where("v86_material_photos", "material_id=:m", {"m": mid}) if _v107 else []
            n = db.session.execute(text("DELETE FROM v86_material_photos WHERE material_id=:m"), {"m": mid}).rowcount
            if n:
                _log(mid, "Foto removida")
            db.session.commit()
            if _v107 and old_keys:
                _v107.delete_keys(old_keys)
            return jsonify(ok=True, removida=bool(n))
        except Exception:
            db.session.rollback()
            app.logger.exception("REV15 foto estoque remover")
            return jsonify(ok=False, error="Não foi possível remover a foto."), 500

    @app.after_request
    def v103_inject(response):
        if request.path != "/engenharia/estoque" or response.status_code != 200 or response.mimetype != "text/html" or response.direct_passthrough:
            return response
        try:
            html = response.get_data(as_text=True)
        except Exception:
            return response
        if "stNewForm" not in html or "data-v103-foto" in html:
            return response
        i = html.rfind("</body>")
        html = html[:i] + SCRIPT + html[i:] if i >= 0 else html + SCRIPT
        response.set_data(html)
        return response
    return None


def install_auto(app, db, text, release="V88.0 REV61.1"):  # rótulo da versão no ar
    """Registro sem editar o app.py: chamado por v101_cleanup.install_cleanup. Busca _has_access e APP_RELEASE no módulo principal."""
    import sys

    def _main():
        return sys.modules.get("app") or sys.modules.get("__main__")

    def can(permission):
        m = _main()
        return bool(m._has_access(permission))
    m = _main()
    if m is not None and hasattr(m, "APP_RELEASE"):
        m.APP_RELEASE = release
    try:  # REV15.2: modelos extras na lista do agendamento do cliente
        from v104_portal_modelos import install_models
        install_models(app)
    except Exception:
        app.logger.exception("REV15.2 modelos do portal nao registrados")
    return install_estoque_foto(app, db, text, can)
