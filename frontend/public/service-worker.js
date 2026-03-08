/**
 * Azories Service Worker
 * Enables offline support by caching the app shell and handling offline requests
 */

const CACHE_NAME = 'azories-v2';
const OFFLINE_URL = '/offline.html';

// Core app shell files to pre-cache
const APP_SHELL = [
  '/',
  '/index.html',
  '/offline.html',
  '/manifest.json',
  '/favicon.ico'
];

// Install event - cache the app shell and all initial assets
self.addEventListener('install', (event) => {
  console.log('[Azories SW] Installing service worker v2');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(async (cache) => {
        console.log('[Azories SW] Caching app shell');
        
        // Cache static files first
        await Promise.allSettled(
          APP_SHELL.map(url => 
            cache.add(url).catch(err => {
              console.warn(`[Azories SW] Failed to cache ${url}:`, err.message);
            })
          )
        );
        
        // Fetch and cache the main page to get JS/CSS bundle URLs
        try {
          const response = await fetch('/');
          if (response.ok) {
            const html = await response.text();
            
            // Extract JS and CSS URLs from the HTML
            const jsMatches = html.match(/\/static\/js\/[^"']+\.js/g) || [];
            const cssMatches = html.match(/\/static\/css\/[^"']+\.css/g) || [];
            
            const allAssets = [...new Set([...jsMatches, ...cssMatches])];
            console.log('[Azories SW] Found assets to cache:', allAssets.length);
            
            // Cache all discovered assets
            await Promise.allSettled(
              allAssets.map(url => 
                cache.add(url).catch(err => {
                  console.warn(`[Azories SW] Failed to cache asset ${url}:`, err.message);
                })
              )
            );
          }
        } catch (e) {
          console.warn('[Azories SW] Could not fetch index for asset discovery:', e);
        }
        
        console.log('[Azories SW] App shell cached successfully');
        return self.skipWaiting();
      })
  );
});

// Activate event - clean up old caches and take control immediately
self.addEventListener('activate', (event) => {
  console.log('[Azories SW] Activating service worker');
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((cacheName) => cacheName.startsWith('azories-') && cacheName !== CACHE_NAME)
            .map((cacheName) => {
              console.log('[Azories SW] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            })
        );
      })
      .then(() => {
        console.log('[Azories SW] Service worker activated');
        return self.clients.claim();
      })
  );
});

// Fetch event - smart caching strategy
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // Skip non-GET requests
  if (event.request.method !== 'GET') {
    return;
  }
  
  // Skip API requests - always go to network for fresh data
  if (url.pathname.startsWith('/api')) {
    return;
  }
  
  // Skip external URLs (Cloudinary, etc.) - except for cached offline book images
  if (url.origin !== self.location.origin) {
    return;
  }
  
  // For navigation requests (HTML pages), use network-first with offline fallback
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          // Cache successful HTML responses for offline
          if (response.ok) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then(cache => {
              cache.put(event.request, responseClone);
            });
          }
          return response;
        })
        .catch(async () => {
          // Offline - try to serve cached version
          const cached = await caches.match(event.request);
          if (cached) return cached;
          
          // Try the index page
          const indexCached = await caches.match('/');
          if (indexCached) return indexCached;
          
          // Last resort - offline page
          return caches.match('/offline.html');
        })
    );
    return;
  }
  
  // For static assets (JS, CSS, fonts, images), use cache-first strategy
  // This is crucial for offline functionality
  const isStaticAsset = url.pathname.startsWith('/static/') || 
                        url.pathname.endsWith('.js') || 
                        url.pathname.endsWith('.css') ||
                        url.pathname.endsWith('.woff2') ||
                        url.pathname.endsWith('.woff') ||
                        url.pathname.match(/\.(png|jpg|jpeg|gif|svg|ico|webp)$/);
  
  if (isStaticAsset) {
    event.respondWith(
      caches.match(event.request)
        .then(cached => {
          if (cached) {
            // Return cached version immediately, but update cache in background
            fetch(event.request).then(response => {
              if (response.ok) {
                caches.open(CACHE_NAME).then(cache => {
                  cache.put(event.request, response);
                });
              }
            }).catch(() => {});
            return cached;
          }
          
          // Not in cache, fetch and cache
          return fetch(event.request)
            .then(response => {
              if (response.ok) {
                const responseClone = response.clone();
                caches.open(CACHE_NAME).then(cache => {
                  cache.put(event.request, responseClone);
                });
              }
              return response;
            })
            .catch(() => {
              // Return a placeholder for images if offline
              if (url.pathname.match(/\.(png|jpg|jpeg|gif|svg|webp)$/)) {
                return new Response('', { status: 404 });
              }
              return new Response('Offline', { status: 503 });
            });
        })
    );
    return;
  }
  
  // Default: network-first for everything else
  event.respondWith(
    fetch(event.request)
      .then(response => {
        if (response.ok) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, responseClone);
          });
        }
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});

// Handle messages from the app
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  // Allow the app to request caching of specific URLs
  if (event.data && event.data.type === 'CACHE_URLS') {
    const urls = event.data.urls || [];
    caches.open(CACHE_NAME).then(cache => {
      urls.forEach(url => {
        cache.add(url).catch(err => {
          console.warn(`[Azories SW] Failed to cache requested URL ${url}:`, err.message);
        });
      });
    });
  }
});
