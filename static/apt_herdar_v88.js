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
