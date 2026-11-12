/* V88.0 REV5 — Usuários: a coluna Perfil e o filtro passam a mostrar o perfil de acessos (personalizado). */
(function(){
  var P=window.__V88_USER_PROFILES||{}; var rows=document.querySelectorAll('tr.userDataRow'); if(!rows.length) return;
  var used={};
  rows.forEach(function(tr){
    var b=tr.querySelector('[data-target^="edit-user-"]'); if(!b) return;
    var uid=b.getAttribute('data-target').replace('edit-user-',''); var p=P[uid]; if(!p) return;
    if(tr.cells[3]) tr.cells[3].textContent=p.name;
    tr.setAttribute('data-role','custom:'+p.id); used[p.id]=p.name;
  });
  var sel=null; document.querySelectorAll('select').forEach(function(s){if(!sel&&s.options.length&&/perfis/i.test(s.options[0].textContent||'')) sel=s});
  if(sel){ Object.keys(used).sort(function(a,b){return used[a].localeCompare(used[b],'pt-BR')}).forEach(function(id){
      if([].some.call(sel.options,function(o){return o.value==='custom:'+id})) return;
      var o=document.createElement('option'); o.value='custom:'+id; o.textContent=used[id]+' (perfil)'; sel.appendChild(o); }); }
})();
