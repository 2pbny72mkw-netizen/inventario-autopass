const VERSION='autopass-v52-2';
const SHELL=`${VERSION}-shell`; const DATA=`${VERSION}-data`;
const OFFLINE='/offline';
const APP_SHELL=[OFFLINE,'/tecnico','/static/app.css?v=v34-1','/static/autopass-logo.png','/static/technician.js?v=v34-1'];
self.addEventListener('install',event=>event.waitUntil((async()=>{const c=await caches.open(SHELL);for(const u of APP_SHELL){try{const r=await fetch(u,{cache:'reload'});if(r&&r.ok)await c.put(u,r.clone())}catch(_){}}await self.skipWaiting()})()));
self.addEventListener('activate',event=>event.waitUntil((async()=>{for(const key of await caches.keys())if(!key.startsWith(VERSION))await caches.delete(key);await self.clients.claim()})()));
async function safeFetch(req,fallback){try{const r=await fetch(req);if(r)return r}catch(_){} if(fallback){const c=await caches.match(fallback);if(c)return c} const hit=await caches.match(req);if(hit)return hit;return new Response('Sem conexão',{status:503,headers:{'Content-Type':'text/plain; charset=utf-8'}})}
self.addEventListener('fetch',event=>{const req=event.request;let url;try{url=new URL(req.url)}catch(_){return} if(req.method!=='GET'||url.origin!==self.location.origin)return;
 if(url.pathname.startsWith('/static/')){event.respondWith((async()=>{try{const r=await fetch(req);if(r&&r.ok){const c=await caches.open(SHELL);await c.put(req,r.clone())}return r}catch(_){return (await caches.match(req))||new Response('',{status:503})}})());return}
 if(url.pathname.startsWith('/api/locations')||url.pathname.includes('/assets')||url.pathname.includes('/inventory')){event.respondWith((async()=>{try{const r=await fetch(req);if(r&&r.ok){const c=await caches.open(DATA);await c.put(req,r.clone())}return r}catch(_){return (await caches.match(req))||new Response(JSON.stringify({offline:true,error:'Dados não disponíveis neste aparelho'}),{status:503,headers:{'Content-Type':'application/json'}})}})());return}
 if(url.pathname==='/tecnico'||url.pathname==='/lancamento'){event.respondWith(safeFetch(req,'/tecnico'));return}
 if(req.mode==='navigate'){event.respondWith(safeFetch(req,OFFLINE));return}
 event.respondWith(safeFetch(req,null));
});