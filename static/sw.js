const VERSION = 'autopass-v22-2';
const SHELL = `${VERSION}-shell`;
const DATA = `${VERSION}-data`;
const APP_SHELL = [
  '/offline',
  '/static/app.css?v=v22-2',
  '/static/autopass-logo.png',
  '/static/autopass-icon-192.png',
  '/static/autopass-icon-512.png',
  '/static/technician.js?v=v22-2'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(SHELL)
      .then(cache => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => !k.startsWith(VERSION)).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

async function networkFirst(request, cacheName, fallbackPath) {
  try {
    const response = await fetch(request);
    if (response && response.ok) {
      const copy = response.clone();
      const cache = await caches.open(cacheName);
      await cache.put(request, copy);
    }
    return response;
  } catch (err) {
    const cached = await caches.match(request);
    if (cached) return cached;
    if (fallbackPath) {
      const fallback = await caches.match(fallbackPath);
      if (fallback) return fallback;
    }
    throw err;
  }
}

self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== self.location.origin) return;

  if (url.pathname.startsWith('/static/')) {
    event.respondWith(networkFirst(request, SHELL));
    return;
  }
  if (url.pathname.startsWith('/api/locations') || url.pathname.includes('/assets') || url.pathname.includes('/inventory')) {
    event.respondWith(networkFirst(request, DATA));
    return;
  }
  if (url.pathname === '/tecnico') {
    event.respondWith(networkFirst(request, SHELL, '/offline'));
    return;
  }
  // Rotas gerenciais/API críticas não são cacheadas pelo SW.
  event.respondWith(fetch(request));
});
