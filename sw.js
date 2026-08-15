const VERSION='autopass-v10';
const SHELL=`${VERSION}-shell`;
const DATA=`${VERSION}-data`;
const APP_SHELL=['/offline','/static/app.css?v=v10','/static/autopass-logo.png','/static/technician.js?v=v10'];
self.addEventListener('install',event=>{event.waitUntil(caches.open(SHELL).then(c=>c.addAll(APP_SHELL)).then(()=>self.skipWaiting()));});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>!k.startsWith(VERSION)).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',event=>{
 const req=event.request,url=new URL(req.url); if(req.method!=='GET'||url.origin!==self.location.origin)return;
 if(url.pathname.startsWith('/static/')){event.respondWith(fetch(req).then(resp=>{if(resp.ok){const copy=resp.clone();caches.open(SHELL).then(c=>c.put(req,copy));}return resp;}).catch(()=>caches.match(req)));return;}
 if(url.pathname.startsWith('/api/locations')||url.pathname.includes('/assets')||url.pathname.includes('/inventory')){event.respondWith(fetch(req).then(resp=>{const copy=resp.clone();caches.open(DATA).then(c=>c.put(req,copy));return resp;}).catch(()=>caches.match(req)));return;}
 if(url.pathname==='/tecnico'){event.respondWith(fetch(req).then(resp=>{const copy=resp.clone();caches.open(SHELL).then(c=>c.put(req,copy));return resp;}).catch(()=>caches.match(req).then(r=>r||caches.match('/offline'))));return;}
 event.respondWith(fetch(req).catch(()=>caches.match(req)));
});
