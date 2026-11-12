/* V88.0 REV5 — "Incluir PT": traz NR10, NR35, ASO e Integração da APT base do colaborador. */
(function(){
  var F=[['aeNr10','nr10_valid_until'],['aeNr35','nr35_valid_until'],['aeAsoSched','aso_scheduled_at'],['aeAsoValid','aso_valid_until'],['aeIntSched','integration_scheduled_at'],['aeIntValid','integration_valid_until']];
  var $=function(i){return document.getElementById(i)};
  var dlg=$('aptEditDialog'), sel=$('aeUser'), seq=0;
  if(!dlg||!sel) return;
  function note(){var n=$('aeHerdaNote');if(!n){n=document.createElement('div');n.id='aeHerdaNote';n.className='muted';n.style.cssText='font-size:12px;margin:6px 0;display:none';var host=$('aeNr10'); (host&&host.closest('label')?host.closest('label').parentNode:dlg).insertBefore(n,(host&&host.closest('label'))||null);}return n}
  function unlock(){F.forEach(function(f){var e=$(f[0]);if(e){e.readOnly=false;e.style.background='';e.title='';if(e.dataset.herdado&&e.dataset.herdado===e.value)e.value='';delete e.dataset.herdado}});var n=$('aeHerdaNote');if(n)n.style.display='none'}
  function sync(){
    var uid=sel.value, isNew=!(($('aeId')||{}).value);
    unlock();
    if(!uid||!isNew||!dlg.open) return;
    var my=++seq;
    fetch('/api/rh/apt/user/'+encodeURIComponent(uid)+'/shared',{credentials:'same-origin',headers:{'Accept':'application/json'}})
      .then(function(r){return r.ok?r.json():null}).then(function(d){
        if(!d||!d.ok||my!==seq||sel.value!==uid) return;
        var n=0;
        F.forEach(function(f){var e=$(f[0]),v=d[f[1]];if(e&&v){e.value=v;e.dataset.herdado=v;e.readOnly=true;e.style.background='#f1f5f9';e.title='Herdado da APT base do colaborador';n++}});
        if(n){var m=note();m.textContent='Datas de NR10, NR35, ASO e Integração herdadas da APT base de '+(d.name||'colaborador')+'. Para alterá-las, edite a APT base.';m.style.display='block'}
      }).catch(function(){});
  }
  sel.addEventListener('change',function(){setTimeout(sync,0)});
  new MutationObserver(function(){if(dlg.open) setTimeout(sync,30); else unlock();}).observe(dlg,{attributes:true,attributeFilter:['open']});
  dlg.addEventListener('close',unlock);
})();

/* V88.0 REV9 — Colaborador: digitar ou escolher na lista de quem está marcado "Precisa de APT?" */
(function(){
  var sel=document.getElementById('aeUser'); if(!sel) return;
  var people=[].slice.call(sel.options).filter(function(o){return o.value}).map(function(o){return {id:o.value,name:o.dataset.name||'',company:o.dataset.company||''}});
  if(!people.length) return;
  function dl(id){var d=document.createElement('datalist');d.id=id;people.forEach(function(p){var o=document.createElement('option');o.value=p.name;o.label=p.company?(p.name+' · '+p.company):p.name;d.appendChild(o)});document.body.appendChild(d);return d}
  dl('aptPeopleDL');
  var q=document.querySelector('#aptFilters input[name="q"]');
  if(q){q.setAttribute('list','aptPeopleDL');q.setAttribute('autocomplete','off');q.placeholder='Colaborador (digite ou escolha), APT, empresa ou linha'}
  var nm=document.getElementById('aeName'), dlg=document.getElementById('aptEditDialog');
  if(!nm||!dlg) return;
  var hint=document.createElement('div');hint.style.cssText='font-size:12px;color:#64748b;margin-top:2px;display:none';
  hint.textContent='Digite ou escolha um colaborador marcado “Precisa de APT?” no Cadastro de Usuários.';
  nm.parentNode.appendChild(hint);
  function mode(){
    var isNew=!((document.getElementById('aeId')||{}).value);
    if(isNew){nm.readOnly=false;nm.setAttribute('list','aptPeopleDL');nm.setAttribute('autocomplete','off');nm.placeholder='Digite ou escolha o colaborador';hint.style.display='block'}
    else{nm.readOnly=true;nm.removeAttribute('list');hint.style.display='none'}
  }
  function norm(v){return (v||'').toString().trim().toLowerCase()}
  nm.addEventListener('input',function(){
    if(nm.readOnly) return;
    var v=norm(nm.value), hit=people.filter(function(p){return norm(p.name)===v});
    if(hit.length===1 && sel.value!==hit[0].id){sel.value=hit[0].id;sel.dispatchEvent(new Event('change',{bubbles:true}))}
    else if(!hit.length && sel.value){sel.value='';sel.dispatchEvent(new Event('change',{bubbles:true}));var c=document.getElementById('aeCompany');if(c) c.value=''}
  });
  new MutationObserver(function(){if(dlg.open) setTimeout(mode,40)}).observe(dlg,{attributes:true,attributeFilter:['open']});
  sel.addEventListener('change',function(){setTimeout(function(){if(!nm.readOnly){var p=people.filter(function(x){return x.id===sel.value})[0];if(p) nm.value=p.name}},20)});
})();
