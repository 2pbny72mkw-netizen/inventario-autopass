/* V88.0 REV68 — Engenharia › BOM: status de cotação por item (coluna "Cotação" da árvore).
   Linhas diretas da BOM aberta: lista para escolher (com liberação). Linhas herdadas de subestrutura: só leitura.
   Contador no topo com filtro por status. */
(function(){
  "use strict";
  if(window.__v168Cot) return; window.__v168Cot=true;
  var $=function(id){return document.getElementById(id)};
  var esc=function(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})};
  var ST=[['NAO_COTADO','Não cotado','○'],['EM_COTACAO','Em cotação','⏳'],['COTADO','Cotado','✓'],['AGUARDANDO_DEFINICAO','Aguardando definição','?']];
  var LBL={},SYM={}; ST.forEach(function(s){LBL[s[0]]=s[1];SYM[s[0]]=s[2]});
  var data={itens:{},can_edit:false}, filtro='', busy=false;

  var css='.v168Sel{font-size:.78rem;font-weight:700;border-radius:999px;padding:3px 8px;border:1px solid #cbd5e1;min-width:178px;max-width:200px}'+
    '.v168Badge{display:inline-block;font-size:.76rem;font-weight:700;border-radius:999px;padding:3px 9px;white-space:nowrap}'+
    '.v168-NAO_COTADO{background:#fde8e6!important;color:#C23B2E!important;border-color:#f3b9b2!important}'+
    '.v168-EM_COTACAO{background:#e6f0fb!important;color:#0B5FB3!important;border-color:#b5d0ef!important}'+
    '.v168-COTADO{background:#e3f5ee!important;color:#0E7A5A!important;border-color:#a9dcc8!important}'+
    '.v168-AGUARDANDO_DEFINICAO{background:#fff4d6!important;color:#8A5A00!important;border-color:#f2d58a!important}'+
    '.v168Bar{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:8px 0;padding:8px 10px;border:1px solid #d6e2ee;border-radius:10px;background:#fff}'+
    '.v168Bar b{color:#0b2d45;margin-right:4px}.v168Bar button{border:1px solid #cbd5e1;border-radius:999px;padding:4px 10px;font-weight:700;font-size:.8rem;cursor:pointer;background:#f8fafc}'+
    '.v168Bar button[aria-pressed="true"]{outline:3px solid #0F1E3D;outline-offset:1px}.v168Bar small{color:#64748b;margin-left:auto}.v168Err{color:#C23B2E;font-size:.8rem}';
  var st=document.createElement('style'); st.textContent=css; document.head.appendChild(st);

  function cells(){ return Array.prototype.slice.call(document.querySelectorAll('#engBomRows td.engQuoteCell')); }
  function stOf(bi){ var it=data.itens[bi]; return it?it.s:'NAO_COTADO'; }
  function tip(bi){ var it=data.itens[bi]; return it?'Por '+it.by+' em '+it.at:'Sem status registrado'; }
  function paint(td){
    var bi=td.dataset.bi, s=stOf(bi), ed=td.dataset.ed==='1'&&data.can_edit;
    if(ed){
      td.innerHTML='<select class="v168Sel v168-'+s+'" data-bi="'+esc(bi)+'" title="'+esc(tip(bi))+'" aria-label="Status de cotação">'+
        ST.map(function(o){return '<option value="'+o[0]+'"'+(o[0]===s?' selected':'')+'>'+o[2]+' '+o[1]+'</option>'}).join('')+'</select>';
    }else{
      td.innerHTML='<span class="v168Badge v168-'+s+'" title="'+esc(tip(bi))+'">'+SYM[s]+' '+LBL[s]+'</span>';
    }
  }
  function bar(){
    var tbl=$('engBomRows'); if(!tbl) return;
    var host=$('v168Bar');
    if(!host){ host=document.createElement('div'); host.id='v168Bar'; host.className='v168Bar';
      var wrap=tbl.closest('.table-responsive')||tbl.closest('table'); wrap.parentNode.insertBefore(host,wrap); }
    var diretos=cells().filter(function(td){return td.dataset.ed==='1'});
    if(!diretos.length){ host.hidden=true; return; } host.hidden=false;
    var cnt={}; ST.forEach(function(s){cnt[s[0]]=0}); diretos.forEach(function(td){cnt[stOf(td.dataset.bi)]++});
    host.innerHTML='<b>Cotação</b>'+ST.map(function(s){return '<button type="button" class="v168-'+s[0]+'" data-f="'+s[0]+'" aria-pressed="'+(filtro===s[0])+'">'+s[2]+' '+cnt[s[0]]+' '+s[1].toLowerCase()+'</button>'}).join('')+
      (filtro?'<button type="button" data-f="">Mostrar todos</button>':'')+'<small>itens diretos desta BOM · clique para filtrar</small><span class="v168Err" hidden></span>';
    host.querySelectorAll('button[data-f]').forEach(function(b){ b.addEventListener('click',function(){ filtro=(filtro===b.dataset.f?'':b.dataset.f); apply(); bar(); }); });
  }
  function apply(){
    document.querySelectorAll('#engBomRows tr').forEach(function(tr){
      var td=tr.querySelector('td.engQuoteCell');
      if(!filtro){ tr.style.display=''; return; }
      tr.style.display=(td&&td.dataset.ed==='1'&&stOf(td.dataset.bi)===filtro)?'':'none';
      if(tr.classList.contains('engBomRoot')) tr.style.display='';
    });
  }
  function err(msg){ var e=document.querySelector('#v168Bar .v168Err'); if(e){e.textContent=msg;e.hidden=!msg} else if(msg) alert(msg); }
  async function load(){
    var list=cells(); if(!list.length){ var h=$('v168Bar'); if(h) h.hidden=true; return; }
    var boms=Array.from(new Set(list.map(function(td){return td.dataset.sb}))).join(',');
    try{
      var r=await fetch('/api/engineering/cotacao?boms='+encodeURIComponent(boms),{credentials:'same-origin'}); var d=await r.json();
      if(!r.ok||!d.ok) throw new Error(d.error||'Erro ao ler status de cotação.');
      data={itens:d.itens||{},can_edit:!!d.can_edit};
    }catch(e){ list.forEach(function(td){td.innerHTML='<span class="v168Err">—</span>'}); return; }
    list.forEach(paint); bar(); apply();
  }
  document.addEventListener('change',async function(e){
    var sel=e.target; if(!sel.matches||!sel.matches('select.v168Sel')) return;
    var bi=sel.dataset.bi, novo=sel.value, antes=stOf(bi);
    if(busy){ sel.value=antes; return; } busy=true; sel.disabled=true;
    try{
      var r=await fetch('/api/engineering/cotacao',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({bom_item_id:Number(bi),status:novo})});
      var d=await r.json().catch(function(){return {ok:false,error:'Resposta inválida do servidor.'}});
      if(!r.ok||!d.ok) throw new Error(d.error||'Não foi possível gravar o status.');
      data.itens[bi]=d.item; err('');
    }catch(x){ err(x.message||String(x)); }
    finally{ busy=false; cells().filter(function(td){return td.dataset.bi===bi}).forEach(paint); bar(); apply(); }
  });
  // usado pelo selo "Valores revisados por Estoque / Compras" (REV67): itens diretos ainda não cotados
  window.__v168Pendentes=function(){ return cells().filter(function(td){return td.dataset.ed==='1'&&stOf(td.dataset.bi)!=='COTADO'}).length; };

  var t=null;
  function init(){
    var rows=$('engBomRows'); if(!rows) return;
    new MutationObserver(function(){ clearTimeout(t); t=setTimeout(function(){ filtro=''; load(); },250); }).observe(rows,{childList:true});
    load();
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init); else init();
})();
