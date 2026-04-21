const CACHE_NAME = 'lily-site-v7';
const STATIC_CACHE = 'lily-static-v7';

// Файлы для кэширования при установке
const STATIC_ASSETS = [
  '/static/css/app.css',
  '/static/js/base.js',
  '/static/img/logo_lily.webp',
  '/static/img/favicon/web-app-manifest-192x192.png',
  '/static/img/favicon/web-app-manifest-512x512.png',
  '/static/offline.html'
];

// Установка Service Worker
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing v6...');
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('[Service Worker] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('[Service Worker] Skip waiting');
        return self.skipWaiting();
      })
      .catch(err => console.error('[Service Worker] Installation failed:', err))
  );
});

// Активация и очистка старых кэшей
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating v6...');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames
          .filter(name => name !== CACHE_NAME && name !== STATIC_CACHE)
          .map(name => {
            console.log('[Service Worker] Deleting old cache:', name);
            return caches.delete(name);
          })
      );
    }).then(() => {
      console.log('[Service Worker] Claiming clients');
      return self.clients.claim();
    })
  );
});

// Fetch стратегия
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Игнорируем не-http запросы (chrome-extension и т.д.)
  if (!url.protocol.startsWith('http')) {
    return;
  }

  // 1. Игнорируем АДМИНКУ и КАБИНЕТ ПОЛНОСТЬЮ (Network Only)
  // Это критически важные разделы, которые должны работать напрямую с сервером
  // чтобы избежать ошибок кэширования и проблем с редиректами (ERR_FAILED)
  if (url.pathname.startsWith('/admin/') || url.pathname.startsWith('/cabinet/')) {
    return;
  }

  // 2. API — всегда свежие данные (Network Only)
  if (url.pathname.startsWith('/api/')) {
    return;
  }

  // 3. Cache-first для статики (CSS, JS, шрифты, картинки)
  const isStaticAsset = url.pathname.startsWith('/static/') &&
    /\.(css|js|woff2?|ttf|eot|png|jpg|jpeg|webp|svg|ico)(\?.*)?$/.test(url.pathname);

  if (isStaticAsset) {
    event.respondWith(
      caches.match(request).then(cached => {
        if (cached) return cached;
        return fetch(request).then(response => {
          if (request.method === 'GET' && response.status === 200) {
            const responseClone = response.clone();
            caches.open(STATIC_CACHE).then(cache => cache.put(request, responseClone));
          }
          return response;
        });
      })
    );
    return;
  }

  // 4. Network First для HTML-страниц (Навигация по сайту)
  if (request.mode === 'navigate' || (request.headers.get('accept') && request.headers.get('accept').includes('text/html'))) {
    event.respondWith(
      fetch(request) // Убрали redirect: follow, браузер сам разберется
        .catch(error => {
          console.error('[Service Worker] Fetch failed for navigation:', error);

          // Показываем офлайн только если реально нет сети
          if (!navigator.onLine) {
             return caches.match('/static/offline.html');
          }

          // Если сеть есть, но fetch упал, пробуем отдать из кэша или показываем заглушку
          return caches.match(request).then(cached => {
            return cached || caches.match('/static/offline.html');
          });
        })
    );
    return;
  }
});

// Обработка сообщений
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys().then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => caches.delete(cacheName))
        );
      }).then(() => {
        return self.clients.matchAll();
      }).then(clients => {
        clients.forEach(client => client.postMessage({
          type: 'CACHE_CLEARED'
        }));
      })
    );
  }
});
