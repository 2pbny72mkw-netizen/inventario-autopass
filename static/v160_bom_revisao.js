/* V88.0 REV67 — Engenharia › BOM: selos de revisão (Mecânica, Hardware, Estoque e valores por Estoque/Compras).
   Mostra, ao abrir a BOM, quem revisou e quando; a API valida a liberação de cada área. */
(function(){
  "use strict";
  if(window.__v160Rev) return; window.__v160Rev=true;
  var $=function(id){return document.getElementById(id)};
  var esc=function(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})};
  var cache={}, busy=false;

  var css='.v160Box{border:1px solid #c7d8e7;border-radius:12px;background:#fff;padding:10px 12px;margin:10px 0}'+
    '.v160Head{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:8px}'+
    '.v160Head b{color:#0b2d45}.v160Head small{color:#526c84}.v160Grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:8px}'+
    '.v160Seal{display:flex;gap:10px;align-items:flex-start;border:1px solid #d6e2ee;border-left:5px solid #94a3b8;border-radius:10px;padding:9px 10px;background:#f8fafc}'+
    '.v160Seal.ok{border-left-color:#0E7A5A;background:#effaf5}.v160Seal.desatualizada{border-left-color:#F2A900;background:#fff8e6}'+
    '.v160Seal input{width:20px;height:20px;margin:2px 0 0;flex:none;accent-color:#0E7A5A;cursor:pointer}.v160Seal input:disabled{cursor:not-allowed}'+
    '.v160Seal .t{display:flex;flex-direction:column;gap:2px;min-width:0}.v160Seal .t b{font-size:.9rem;color:#0f172a}'+
    '.v160Seal .t span{font-size:.8rem;color:#334155}.v160Seal.ok .t span{color:#0E7A5A;font-weight:700}.v160Seal.desatualizada .t span{color:#8A5A00;font-weight:700}'+
    '.v160Seal .t em{font-style:normal;font-size:.74rem;color:#64748b}'+
    '.v160Link{background:none;border:0;color:#0B5FB3;font-weight:700;cursor:pointer;padding:2px 4px}.v160Err{color:#C23B2E;font-size:.82rem;margin-top:6px}'+
    '.v160Dlg{position:fixed;inset:0;background:rgba(15,30,61,.45);display:flex;align-items:center;justify-content:center;z-index:9999;padding:16px}'+
    '.v160DlgCard{background:#fff;border-radius:12px;max-width:760px;width:100%;max-height:80vh;overflow:auto;padding:16px}'+
    '.v160DlgCard table{width:100%;border-collapse:collapse}.v160DlgCard th,.v160DlgCard td{padding:6px 8px;border-bottom:1px solid #e2e8f0;text-align:left;font-size:.85rem}'+
    '.v160DlgCard thead th{position:sticky;top:0;background:#0b2d45;color:#fff}';
  var st=document.createElement('style'); st.textContent=css; document.head.appendChild(st);

  var SYM={ok:'✓',desatualizada:'⚠',pendente:'○',desmarcada:'○'};
  function statusText(a){
    if(a.estado==='ok') return SYM.ok+' Revisado por '+esc(a.by)+' em '+esc(a.at);
    if(a.estado==='desatualizada') return SYM.desatualizada+' Revisado por '+esc(a.by)+' em '+esc(a.at)+' — '+(a.tipo==='valores'?'valores mudaram':'estrutura mudou')+' depois; revisar de novo';
    if(a.estado==='desmarcada') return SYM.desmarcada+' Não revisado (desmarcado por '+esc(a.by)+' em '+esc(a.at)+')';
    return SYM.pendente+' Não revisado';
  }
  function seal(a){
    var lbl={mecanica:'Revisado pela Engenharia Mecânica',hardware:'Revisado pela Engenharia de Hardware',estoque:'Revisado pelo Estoque',
      valores:'Valores revisados por Estoque / Compras'}[a.area]||a.label;
    var tip=a.can_mark?'':' title="Sem liberação para marcar esta revisão"';
    return '<label class="v160Seal '+a.estado+'"'+tip+'><input type="checkbox" data-area="'+a.area+'"'+(a.approved?' checked':'')+(a.can_mark?'':' disabled')+
      ' aria-label="'+esc(lbl)+'"><span class="t"><b>'+esc(lbl)+'</b><span>'+statusText(a)+'</span>'+
      (a.can_mark?'':'<em>Somente quem tem a liberação desta área pode marcar.</em>')+'</span></label>';
  }
  function render(host, bid, d, which){
    var areas=(d.areas||[]).filter(function(a){return which==='valores'?a.tipo==='valores':true});
    var ok=areas.filter(function(a){return a.estado==='ok'}).length;
    host.innerHTML='<div class="v160Head"><div><b>'+(which==='valores'?'Revisão dos valores da BOM':'Revisões da BOM')+'</b> <small>'+ok+' de '+areas.length+' em dia</small></div>'+
      '<button type="button" class="v160Link" data-hist>Histórico de revisões</button></div><div class="v160Grid">'+areas.map(seal).join('')+'</div><div class="v160Err" hidden></div>';
    host.querySelectorAll('input[data-area]').forEach(function(inp){
      inp.addEventListener('change',function(){ mark(host,bid,inp,which); });
    });
    host.querySelector('[data-hist]').addEventListener('click',function(){ history(d); });
  }
  function err(host,msg){var e=host.querySelector('.v160Err'); if(e){e.textContent=msg; e.hidden=!msg;}}
  async function mark(host,bid,inp,which){
    if(busy){inp.checked=!inp.checked;return}
    var want=inp.checked;
    if(!want && !confirm('Desmarcar esta revisão? O nome e a data da revisão anterior ficam no histórico.')){inp.checked=true;return}
    busy=true; host.querySelectorAll('input[data-area]').forEach(function(x){x.dataset.was=x.disabled; x.disabled=true});
    try{
      var r=await fetch('/api/engineering/boms/'+bid+'/revisoes',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'same-origin',
        body:JSON.stringify({area:inp.dataset.area,approved:want})});
      var d=await r.json().catch(function(){return {ok:false,error:'Resposta inválida do servidor.'}});
      if(!r.ok||!d.ok) throw new Error(d.error||'Não foi possível gravar a revisão.');
      cache[bid]=d; refreshAll();
    }catch(e){
      inp.checked=!want; host.querySelectorAll('input[data-area]').forEach(function(x){x.disabled=x.dataset.was==='true'});
      err(host,e.message||String(e));
    }finally{busy=false}
  }
  function history(d){
    var rows=(d.historico||[]).map(function(h){return '<tr><td>'+esc(h.at)+'</td><td>'+esc(h.area)+'</td><td>'+(h.approved?'✓ Revisado':'○ Desmarcado')+'</td><td>'+esc(h.by)+'</td></tr>'}).join('');
    var dlg=document.createElement('div'); dlg.className='v160Dlg';
    dlg.innerHTML='<div class="v160DlgCard" role="dialog" aria-modal="true" aria-label="Histórico de revisões"><div class="v160Head"><b>Histórico de revisões</b><button type="button" class="v160Link" data-x>Fechar ×</button></div>'+
      (rows?'<div class="table-responsive"><table data-ap-table><thead><tr><th>Data / hora</th><th>Área</th><th>Situação</th><th>Por</th></tr></thead><tbody>'+rows+'</tbody></table></div>':'<p>Nenhuma revisão marcada nesta BOM ainda.</p>')+'</div>';
    function close(){dlg.remove(); document.removeEventListener('keydown',onKey)}
    function onKey(e){if(e.key==='Escape')close()}
    dlg.addEventListener('click',function(e){if(e.target===dlg||e.target.hasAttribute('data-x'))close()});
    document.addEventListener('keydown',onKey); document.body.appendChild(dlg); dlg.querySelector('[data-x]').focus();
  }
  async function load(host,bid,which,force){
    if(!bid){host.hidden=true;return}
    host.hidden=false;
    if(cache[bid]&&!force){render(host,bid,cache[bid],which);return}
    if(!host.innerHTML) host.innerHTML='<small style="color:#64748b">Carregando revisões…</small>';
    try{
      var r=await fetch('/api/engineering/boms/'+bid+'/revisoes',{credentials:'same-origin'});
      var d=await r.json();
      if(!r.ok||!d.ok) throw new Error(d.error||'Erro ao ler as revisões.');
      cache[bid]=d; if(host.dataset.bid==String(bid)) render(host,bid,d,which);
    }catch(e){ if(r&&r.status===403){host.hidden=true;return} host.innerHTML='<div class="v160Err">'+esc(e.message||e)+'</div>'; }
  }
  function slot(id,anchor,where){
    var h=$(id); if(h) return h;
    if(!anchor) return null;
    h=document.createElement('div'); h.id=id; h.className='v160Box'; h.hidden=true;
    anchor.insertAdjacentElement(where,h); return h;
  }
  function bomHost(){ var ws=$('engBomWorkspace'); return ws?slot('v160BomReviews',ws.querySelector('.engBomTitle'),'afterend'):null; }
  function priceHost(){ var ws=$('engPricingWorkspace'); return ws?slot('v160PriceReviews',ws.firstElementChild,'beforebegin'):null; }
  function refreshBom(force){ var h=bomHost(), s=$('engBomSelect'); if(!h||!s) return; var bid=s.value; h.dataset.bid=bid; load(h,bid,'todas',force); }
  function refreshPrice(force){ var h=priceHost(), s=$('engPriceBom'); if(!h||!s) return; var bid=s.value; h.dataset.bid=bid; load(h,bid,'valores',force); }
  function refreshAll(){ refreshBom(false); refreshPrice(false); }

  var tBom=null, tPrice=null;
  function init(){
    var rows=$('engBomRows');
    if(rows) new MutationObserver(function(){ clearTimeout(tBom); tBom=setTimeout(function(){ var s=$('engBomSelect'); if(s&&s.value) delete cache[s.value]; refreshBom(true); },400); }).observe(rows,{childList:true});
    var ps=$('engPriceBom'); if(ps) ps.addEventListener('change',function(){ refreshPrice(true); });
    var pw=$('engPricingWorkspace');
    if(pw) new MutationObserver(function(){ clearTimeout(tPrice); tPrice=setTimeout(function(){ refreshPrice(true); },300); }).observe(pw,{attributes:true,attributeFilter:['hidden']});
    refreshBom(true); refreshPrice(true);
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init); else init();
})();
