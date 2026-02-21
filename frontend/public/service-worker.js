/* eslint-disable no-restricted-globals */

const CACHE_NAME = 'azories-v1';
const OFFLINE_URL = '/offline.html';

// Assets to cache on install
const PRECACHE_ASSETS = [
  '/',
  '/index.html',
  '/static/js/main.js',
  '/static/css/main.css',
  '/manifest.json',
];

// Install event - cache core assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('Caching core assets');
      return cache.addAll(PRECACHE_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});

// Fetch event - network first, then cache
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') return;

  // Skip API requests (let them fail naturally if offline)
  if (url.pathname.startsWith('/api')) {
    event.respondWith(
      fetch(request).catch(() => {
        return new Response(
          JSON.stringify({ error: 'You are offline', offline: true }),
          { headers: { 'Content-Type': 'application/json' } }
        );
      })
    );
    return;
  }

  // For book images - cache first, then network
  if (request.url.includes('book-images') || request.url.includes('cover')) {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached;
        
        return fetch(request).then((response) => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, clone);
            });
          }
          return response;
        });
      })
    );
    return;
  }

  // For everything else - network first, cache fallback
  event.respondWith(
    fetch(request)
      .then((response) => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, clone);
          });
        }
        return response;
      })
      .catch(() => {
        return caches.match(request).then((cached) => {
          if (cached) return cached;
          
          // Return offline page for navigation requests
          if (request.mode === 'navigate') {
            return caches.match(OFFLINE_URL);
          }
          
          return new Response('Offline', { status: 503 });
        });
      })
  );
});

// Listen for messages from the app
self.addEventListener('message', (event) => {
  if (event.data.type === 'CACHE_BOOK') {
    const { bookId, pages } = event.data;
    
    caches.open(CACHE_NAME).then((cache) => {
      // Cache book data
      const bookData = JSON.stringify({ id: bookId, pages, cached: true });
      cache.put(
        new Request(`/offline-book/${bookId}`),
        new Response(bookData, { headers: { 'Content-Type': 'application/json' } })
      );
      
      // Cache all page images
      pages.forEach((page) => {
        if (page.image) {
          fetch(page.image).then((response) => {
            if (response.ok) {
              cache.put(new Request(page.image), response);
            }
          });
        }
      });
      
      // Notify the app
      event.source.postMessage({ type: 'BOOK_CACHED', bookId });
    });
  }
  
  if (event.data.type === 'GET_CACHED_BOOKS') {
    caches.open(CACHE_NAME).then((cache) => {
      cache.keys().then((keys) => {
        const bookKeys = keys.filter((k) => k.url.includes('/offline-book/'));
        Promise.all(bookKeys.map((k) => cache.match(k).then((r) => r.json()))).then((books) => {
          event.source.postMessage({ type: 'CACHED_BOOKS', books });
        });
      });
    });
  }
  
  if (event.data.type === 'REMOVE_CACHED_BOOK') {
    const { bookId } = event.data;
    caches.open(CACHE_NAME).then((cache) => {
      cache.delete(new Request(`/offline-book/${bookId}`));
      event.source.postMessage({ type: 'BOOK_REMOVED', bookId });
    });
  }
});
