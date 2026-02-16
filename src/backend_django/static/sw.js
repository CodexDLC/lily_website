const CACHE_NAME = 'lily-admin-v1';
const STATIC_CACHE = 'lily-static-v1';

// Файлы для кэширования при установке
const STATIC_ASSETS = [
  '/admin/',
  '/static/css/app.css',
  '/static/js/base.js',
  '/static/img/logo_lily.webp',
  '/static/img/favicon/icon-192x192.png',
  '/static/img/favicon/icon-512x512.png',
  '/static/admin/offline.html'
];

// Установка Service Worker
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing...');
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
  console.log('[Service Worker] Activating...');
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

  // Игнорируем chrome-extension и другие протоколы
  if (!url.protocol.startsWith('http')) {
    return;
  }

  // Network-first для admin API и динамического контента
  if (url.pathname.startsWith('/admin/') && !url.pathname.match(/\.(css|js|png|jpg|jpeg|webp|svg|woff2?|ttf|eot|ico)$/)) {
    event.respondWith(
      fetch(request)
        .then(response => {
          // Кэшируем успешные GET запросы
          if (request.method === 'GET' && response.status === 200) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then(cache => {
              cache.put(request, responseClone);
            });
          }
          return response;
        })
        .catch(() => {
          return caches.match(request)
            .then(cached => {
              return cached || caches.match('/static/admin/offline.html');
            });
        })
    );
    return;
  }

  // Cache-first для статических ресурсов
  event.respondWith(
    caches.match(request)
      .then(cached => {
        if (cached) {
          return cached;
        }

        return fetch(request).then(response => {
          // Кэшируем только успешные GET запросы
          if (request.method === 'GET' && response.status === 200) {
            const responseClone = response.clone();
            caches.open(STATIC_CACHE).then(cache => {
              cache.put(request, responseClone);
            });
          }
          return response;
        });
      })
      .catch(() => {
        // Возвращаем offline страницу для HTML запросов
        if (request.headers.get('accept').includes('text/html')) {
          return caches.match('/static/admin/offline.html');
        }
      })
  );
});

// Обработка сообщений от клиентов
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
