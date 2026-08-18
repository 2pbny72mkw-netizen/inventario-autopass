const VERSION='suporte-campo-v39-2-cleanup';
self.addEventListener('install',event=>event.waitUntil(self.skipWaiting()));
self.addEventListener('activate',event=>event.waitUntil((async()=>{
  try{for(const key of await caches.keys()) await caches.delete(key);}catch(_e){}
  try{await self.registration.unregister();}catch(_e){}
  try{const clients=await self.clients.matchAll({type:'window'});for(const c of clients)c.postMessage({type:'SW_DISABLED_V39_2'});}catch(_e){}
})()));
self.addEventListener('fetch',()=>{});
