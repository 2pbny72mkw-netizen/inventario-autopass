const VERSION='autopass-v8-0-1';
const SHELL=`${VERSION}-shell`;
const DATA=`${VERSION}-data`;
const APP_SHELL=[
  '/offline',
  '/static/app.css',
  '/static/autopass-logo.png',
  '/static/technician.js'
];

self.addEventListener('install',event=>{
  event.waitUntil(caches.open(SHELL).then(cache=>cache.addAll(APP_SHELL)).then(()=>self.skipWaiting()));
});
self.addEventListener('activate',event=>{
  event.waitUntil(
    caches.keys().then(keys=>Promise.all(keys.filter(k=>!k.startsWith(VERSION)).map(k=>caches.delete(k))))
      .then(()=>self.clients.claim())
  );
});
self.addEventListener('fetch',event=>{
  const req=event.request;
  const url=new URL(req.url);
  if(req.method!=='GET'||url.origin!==self.location.origin) return;

  // Dynamic field data: network first, cached fallback.
  if(url.pathname.startsWith('/api/locations')||
     url.pathname.includes('/assets')||
     url.pathname.includes('/inventory')){
    event.respondWith(
      fetch(req).then(resp=>{
        const copy=resp.clone();
        caches.open(DATA).then(c=>c.put(req,copy));
        return resp;
      }).catch(()=>caches.match(req))
    );
    return;
  }

  // Technician shell: network first to respect session, offline fallback.
  if(url.pathname==='/tecnico'){
    event.respondWith(
      fetch(req).then(resp=>{
        const copy=resp.clone();
        caches.open(SHELL).then(c=>c.put(req,copy));
        return resp;
      }).catch(()=>caches.match(req).then(r=>r||caches.match('/offline')))
    );
    return;
  }

  event.respondWith(
    caches.match(req).then(cached=>cached||fetch(req).then(resp=>{
      if(resp.ok && (url.pathname.startsWith('/static/'))){
        const copy=resp.clone(); caches.open(SHELL).then(c=>c.put(req,copy));
      }
      return resp;
    }))
  );
});
