/* V88.0 REV10 — rótulos de acessibilidade em campos sem rótulo (só atributos; não muda layout nem comportamento). */
(function(){
  function has(e){
    if(e.getAttribute('aria-label')||e.getAttribute('aria-labelledby')||e.getAttribute('title')) return true;
    if(e.id&&document.querySelector('label[for="'+(window.CSS&&CSS.escape?CSS.escape(e.id):e.id)+'"]')) return true;
    if(e.closest('label')) return true;
    return false;
  }
  function guess(e){
    var p=e.getAttribute('placeholder'); if(p) return p;
    var prev=e.previousElementSibling; if(prev&&/^(LABEL|SPAN|B|STRONG|SMALL)$/.test(prev.tagName)&&!prev.querySelector("input,select,textarea")){var t=(prev.textContent||'').trim(); if(t&&t.length<60) return t}
    var par=e.parentElement; if(par&&par!==document.body&&par.querySelectorAll('input:not([type=hidden]),select,textarea').length===1){var lb=par.querySelector(':scope > label, :scope > span, :scope > b'); if(lb&&lb!==e){var t2=(lb.textContent||'').trim(); if(t2&&t2.length<60) return t2}}
    var n=e.getAttribute('name')||e.id||''; n=n.replace(/[_\-]+/g,' ').replace(/([a-z])([A-Z])/g,'$1 $2').trim();
    return n? n.charAt(0).toUpperCase()+n.slice(1) : '';
  }
  function run(){
    var list=document.querySelectorAll('input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=reset]):not([type=image]), select, textarea');
    for(var i=0;i<list.length;i++){var e=list[i]; if(has(e)) continue; var g=guess(e); if(g) e.setAttribute('aria-label',g)}
    var b=document.querySelectorAll('button:not([aria-label]):not([title])');
    for(var j=0;j<b.length;j++){ if(!(b[j].textContent||'').trim()){ var t=b[j].getAttribute('data-title')||b[j].getAttribute('name')||b[j].id; if(t) b[j].setAttribute('aria-label',t) } }
  }
  function go(){ try{run()}catch(e){} setTimeout(function(){try{run()}catch(e){}},1500) }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',go); else go();
})();
