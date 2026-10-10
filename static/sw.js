// V85.44 REV9 — PWA/cache expandido para navegação geral.
// Toda navegação GET autenticada visitada com sucesso fica disponível como fallback offline.
// Estáticos usam network-first. POST/PUT/PATCH/DELETE e APIs dinâmicas não são cacheados.
// A fila offline de Bobinas permanece no IndexedDB da própria tela.
const STATIC_CACHE='autopass-v85-46-static';
const PRIVATE_CACHE='autopass-v85-46-private';
const PRECACHE=['/static/autopass-icon-192.png','/static/autopass-icon-512.png','/static/autopass-logo.png','/offline'];
const OFFLINE_GET_APIS=['/api/bobinas/options','/api/bobinas/atm-status'];
self.addEventListener('install',event=>event.waitUntil((async()=>{const c=await caches.open(STATIC_CACHE);await c.addAll(PRECACHE);await self.skipWaiting();})()));
self.addEventListener('activate',event=>event.waitUntil((async()=>{const keys=await caches.keys();await Promise.all(keys.filter(k=>k!==STATIC_CACHE&&k!==PRIVATE_CACHE).map(k=>caches.delete(k)));await self.clients.claim();})()));
async function networkFirst(request,cacheName){
  const cache=await caches.open(cacheName);
  try{const response=await fetch(request,{cache:'no-store'});if(response&&response.ok){await cache.put(request,response.clone());}return response;}
  catch(err){const cached=await cache.match(request);if(cached)return cached;throw err;}
}
self.addEventListener('fetch',event=>{
  const request=event.request;if(request.method!=='GET')return;
  const url=new URL(request.url);if(url.origin!==self.location.origin)return;
  if(url.pathname.startsWith('/static/')){event.respondWith(networkFirst(request,STATIC_CACHE));return;}
  // REV9: qualquer página GET visitada online pode ser reaberta offline.
  // A resposta só entra no cache após sucesso HTTP; APIs e mutações permanecem fora desta regra.
  if(request.mode==='navigate'){
    event.respondWith((async()=>{
      try{return await networkFirst(request,PRIVATE_CACHE)}
      catch(_e){return (await caches.match(request))||(await caches.match('/offline'))||Response.error()}
    })());return;
  }
  if(OFFLINE_GET_APIS.some(p=>url.pathname===p)){
    event.respondWith(networkFirst(request,PRIVATE_CACHE));return;
  }
});
self.addEventListener('message',event=>{
  const d=event.data||{};
  if(d.type==='CLEAR_PRIVATE_CACHE'){event.waitUntil(caches.delete(PRIVATE_CACHE));return;}
  if(d.type==='SHOW_NOTIFICATION'){self.registration.showNotification(d.title||'Sistema de Gestão',{body:d.body||'',icon:'/static/autopass-icon-192.png',badge:'/static/autopass-icon-192.png',tag:d.tag||'autopass-v8544r9',renotify:true,data:{url:d.url||'/notificacoes'}});}
});
self.addEventListener('notificationclick',event=>{event.notification.close();const url=event.notification.data?.url||'/notificacoes';event.waitUntil(clients.matchAll({type:'window',includeUncontrolled:true}).then(ws=>{for(const w of ws){if('focus' in w){w.navigate(url);return w.focus();}}return clients.openWindow(url);}));});
