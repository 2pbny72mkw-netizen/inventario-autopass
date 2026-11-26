/* V88.0 REV63.9 — seletor de dashboard no celular (o script original saiu na limpeza do REV32).
   Monta a lista a partir do menu lateral (dashboards e personalizadas) e troca a dashboard pelo mesmo clique do menu. */
(()=>{
 const btn=document.getElementById('v72MobileDashButton'),menu=document.getElementById('v72MobileDashMenu'),cur=document.getElementById('v72MobileDashCurrent'),side=document.getElementById('v23Sidebar');
 if(!btn||!menu||!side)return;
 const itens=()=>[...side.querySelectorAll('.v23Nav')].filter(e=>e.offsetParent!==null||getComputedStyle(e).display!=='none');
 const rotulo=e=>(e.textContent||'').replace(/\s+/g,' ').trim();
 function atual(){const a=side.querySelector('.v23Nav.active')||side.querySelector('.v23Nav.v62SideLink[aria-current]');cur.textContent=a?rotulo(a).replace(/^\W+\s*/,''):'Selecionar'}
 function monta(){menu.replaceChildren();let grupo='';
  side.querySelectorAll('.v42SideGroup,.v23Nav').forEach(e=>{
   if(e.classList.contains('v42SideGroup')){grupo=rotulo(e);const h=document.createElement('div');h.textContent=grupo;h.style.cssText='font-size:.72rem;font-weight:800;letter-spacing:.06em;color:#5b6f85;padding:8px 10px 4px';menu.append(h);return}
   const b=document.createElement('button');b.type='button';b.textContent=rotulo(e);if(e.classList.contains('active'))b.classList.add('active');
   b.onclick=()=>{fecha();if(e.tagName==='A'&&e.href){location.href=e.href;return}e.click();atual();window.scrollTo({top:0,behavior:'smooth'})};
   menu.append(b)})}
 function abre(){monta();menu.hidden=false;btn.setAttribute('aria-expanded','true')}
 function fecha(){menu.hidden=true;btn.setAttribute('aria-expanded','false')}
 btn.addEventListener('click',e=>{e.stopPropagation();menu.hidden?abre():fecha()});
 document.addEventListener('click',e=>{if(!menu.hidden&&!e.target.closest('#v72MobileDashSwitch'))fecha()});
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!menu.hidden){fecha();e.preventDefault()}});
 side.addEventListener('click',()=>setTimeout(atual,0));
 atual();
 if(itens().length){const st=document.createElement('style');st.textContent='@media (max-width:768px){#v23Sidebar{display:none!important}}';document.head.append(st)}
})();
