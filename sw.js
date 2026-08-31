// V50.6 — cache seguro: páginas, dashboards e APIs nunca são interceptados.
const CACHE = 'autopass-v71-2-hf1-static';
const PRECACHE = ['/static/autopass-icon-192.png','/static/autopass-icon-512.png'];
self.addEventListener('install', event => {
  event.waitUntil((async()=>{const cache=await caches.open(CACHE);await cache.addAll(PRECACHE);await self.skipWaiting();})());
});
self.addEventListener('activate', event => {
  event.waitUntil((async()=>{const keys=await caches.keys();await Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)));await self.clients.claim();})());
});
self.addEventListener('fetch', event => {
  const request=event.request;
  if(request.method!=='GET') return;
  const url=new URL(request.url);
  if(url.origin!==self.location.origin) return;
  // Não interceptar navegação, HTML, APIs ou rotas autenticadas.
  if(request.mode==='navigate') return;
  if(!url.pathname.startsWith('/static/')) return;
  // Somente estáticos: rede primeiro; cache apenas como fallback offline.
  event.respondWith((async()=>{
    try{
      const response=await fetch(request,{cache:'no-store'});
      if(response && response.ok){const cache=await caches.open(CACHE);await cache.put(request,response.clone());}
      return response;
    }catch(error){
      const cached=await caches.match(request);
      if(cached) return cached;
      throw error;
    }
  })());
});
