(()=>{
 const seen=new Set();
 async function enhance(){
  const nodes=[...document.querySelectorAll('h1,h2,h3,strong,b,div')];
  for(const n of nodes){const m=(n.textContent||'').match(/Editar atividade\s*#(\d+)/i);if(!m)continue;
   const id=m[1]; if(seen.has(id))continue;
   const host=n.closest('[role="dialog"],.modal,.modal-content,.dialog')||n.parentElement; if(!host)continue;
   seen.add(id);
   try{const r=await fetch(`/api/arrow/${id}/evidencias`,{credentials:'same-origin'});const d=await r.json();if(!d.ok||!d.photos?.length)continue;
    const box=document.createElement('section');box.className='card';box.style.margin='12px 18px';box.innerHTML=`<h3 style="margin:0 0 8px">Evidências (${d.count})</h3><div style="display:flex;gap:10px;flex-wrap:wrap"></div>`;
    const row=box.querySelector('div');d.photos.forEach((ph,i)=>{const a=document.createElement('a');a.href=ph.url;a.target='_blank';a.rel='noopener';a.title=ph.name||`Foto ${i+1}`;const im=document.createElement('img');im.src=ph.url;im.alt=ph.name||`Evidência ${i+1}`;im.loading='lazy';im.style.cssText='width:110px;height:90px;object-fit:cover;border-radius:10px;border:1px solid #ccd6e0';a.appendChild(im);row.appendChild(a)});host.appendChild(box)
   }catch(e){seen.delete(id)}
  }
 }
 new MutationObserver(()=>enhance()).observe(document.documentElement,{childList:true,subtree:true});enhance();
})();