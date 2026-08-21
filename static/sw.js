const CACHE='autopass-v50-static';
const STATIC=['/offline','/static/app.css','/static/autopass-logo.png'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(STATIC)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil((async()=>{for(const k of await caches.keys())if(k!==CACHE)await caches.delete(k);await self.clients.claim();})()));
self.addEventListener('fetch',e=>{
  const r=e.request;if(r.method!=='GET')return;
  const u=new URL(r.url);
  if(u.origin!==location.origin)return;
  if(u.pathname.startsWith('/static/')){e.respondWith(caches.match(r).then(c=>c||fetch(r).then(res=>{const copy=res.clone();caches.open(CACHE).then(x=>x.put(r,copy));return res;})));return;}
  if(r.mode==='navigate'){e.respondWith(fetch(r).catch(()=>caches.match('/offline')));}
});
