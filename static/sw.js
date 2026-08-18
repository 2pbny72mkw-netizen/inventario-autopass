const VERSION='autopass-v39-1';
const SHELL=`${VERSION}-shell`;
const OFFLINE='/offline';
const STATIC_SHELL=[OFFLINE,'/static/app.css?v=v39-1','/static/autopass-logo.png'];
self.addEventListener('install',event=>event.waitUntil((async()=>{
  const c=await caches.open(SHELL);
  for(const u of STATIC_SHELL){try{const r=await fetch(u,{cache:'reload'});if(r&&r.ok)await c.put(u,r.clone())}catch(_){}}
  await self.skipWaiting();
})()));
self.addEventListener('activate',event=>event.waitUntil((async()=>{
  for(const key of await caches.keys()) if(key!==SHELL) await caches.delete(key);
  await self.clients.claim();
})()));
self.addEventListener('fetch',event=>{
  const req=event.request; let url; try{url=new URL(req.url)}catch(_){return}
  if(req.method!=='GET'||url.origin!==self.location.origin) return;
  // API e páginas autenticadas: sempre rede. Evita tela/sessão antiga servida por cache.
  if(url.pathname.startsWith('/api/')||req.mode==='navigate') {
    event.respondWith((async()=>{try{return await fetch(req,{cache:'no-store'})}catch(_){
      if(req.mode==='navigate') return (await caches.match(OFFLINE))||new Response('Sem conexão',{status:503});
      return new Response(JSON.stringify({offline:true,error:'Sem conexão'}),{status:503,headers:{'Content-Type':'application/json'}});
    }})()); return;
  }
  if(url.pathname.startsWith('/static/')){
    event.respondWith((async()=>{
      const hit=await caches.match(req); if(hit) return hit;
      try{const r=await fetch(req); if(r&&r.ok){const c=await caches.open(SHELL); await c.put(req,r.clone())} return r}catch(_){return new Response('',{status:503})}
    })());
  }
});
