// V87.2 fallback para dropdown renderizado via JavaScript.
(()=>{function insert(){if(document.querySelector('a[href="/engenharia/estoque"]'))return;
 const anchors=[...document.querySelectorAll('a,button,[role="menuitem"]')];
 const coding=anchors.find(x=>x.textContent.trim()==='Codificação');
 if(!coding)return;
 const a=document.createElement('a');a.href='/engenharia/estoque';a.className='xp-stock-menu-link';a.textContent='📦 Estoque Central';
 coding.insertAdjacentElement('afterend',a);
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',insert);else insert();
 const obs=new MutationObserver(insert);obs.observe(document.body,{subtree:true,childList:true});
})();
