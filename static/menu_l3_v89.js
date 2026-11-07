/* V89 — menu com terceiro nível (variante 2: painel ao lado no computador; lista que abre e fecha no celular).
   Só roda com a chave "menu_terceiro_nivel" ligada. Nunca cria acesso: só enfeita links que o servidor já entregou ao usuário. */
(()=>{try{
 if(!(window.AP_FLAGS&&window.AP_FLAGS.menu_terceiro_nivel))return;
 const SECS=window.AP_DIAG_SECS||[];
 const MAP={'/diagnostico':SECS.map(s=>({label:s.label,href:'/diagnostico#sec-'+s.k}))};
 const root=document.getElementById('mainNavV424');if(!root)return;
 const st=document.createElement('style');
 st.textContent='.apL3Item{position:relative;display:block}.apL3Item>a{display:block;padding-right:34px!important}'
 +'.apL3Toggle{position:absolute;right:4px;top:50%;transform:translateY(-50%);border:0!important;background:transparent!important;box-shadow:none!important;min-width:0!important;width:auto!important;height:auto!important;color:inherit;cursor:pointer;font-size:14px;padding:4px 8px!important;line-height:1;margin:0}'
 +'.apL3Panel{display:none;background:#F8FAFD;border-left:3px solid #2BA6A0}.apL3Panel a{display:block;padding:7px 14px;font-size:13px;white-space:nowrap}'
 +'.apL3Panel h4{margin:6px 14px 4px;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:#5A6478}'
 +'.apL3Item.open>.apL3Panel{display:block}'
 +'@media(min-width:761px){.apL3Panel{position:absolute;left:100%;top:0;min-width:270px;box-shadow:0 12px 28px #17345d33;border:1px solid #DDE3EE;border-left:3px solid #2BA6A0;z-index:90010;padding:6px 0}'
 +'.apL3Item:hover>.apL3Panel,.apL3Item:focus-within>.apL3Panel{display:block}.apL3Toggle{pointer-events:none}}'
 +'@media(max-width:760px){.apL3Panel{margin-left:14px}}';
 document.head.appendChild(st);
 for(const [href,items] of Object.entries(MAP)){
  for(const a of root.querySelectorAll('.navDropMenu a[href="'+href+'"]')){
   if(a.closest('.apL3Item'))continue;
   const wrap=document.createElement('div');wrap.className='apL3Item';a.parentNode.insertBefore(wrap,a);wrap.appendChild(a);
   const tg=document.createElement('button');tg.type='button';tg.className='apL3Toggle';tg.textContent='▸';tg.setAttribute('aria-label','Mostrar seções de '+(a.textContent||'').trim());tg.setAttribute('aria-expanded','false');
   const panel=document.createElement('div');panel.className='apL3Panel';
   const h=document.createElement('h4');h.textContent=(a.textContent||'').trim();panel.appendChild(h);
   for(const it of items){const l=document.createElement('a');l.href=it.href;l.textContent=it.label;panel.appendChild(l)}
   wrap.append(tg,panel);
   tg.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();const o=wrap.classList.toggle('open');tg.setAttribute('aria-expanded',o?'true':'false');tg.textContent=o?'▾':'▸'});
   a.addEventListener('keydown',e=>{if(e.key==='ArrowRight'){const f=panel.querySelector('a');if(f){e.preventDefault();wrap.classList.add('open');f.focus()}}});
   panel.addEventListener('keydown',e=>{if(e.key==='ArrowLeft'||e.key==='Escape'){e.preventDefault();wrap.classList.remove('open');a.focus()}});
  }
 }
}catch(e){console.error('MENU_L3_V89',e)}})();
