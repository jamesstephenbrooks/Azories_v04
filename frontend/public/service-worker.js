/**
 * Azories Service Worker v3 - iOS Safari PWA Compatible
 * Properly caches app shell for true offline support
 */

const CACHE_NAME = 'azories-v3';
const OFFLINE_URL = '/offline.html';

// Install event - Pre-cache essential files
self.addEventListener('install', (event) => {
  console.log('[Azories SW v3] Installing...');
  
  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE_NAME);
      
      // First, cache the offline fallback page
      try {
        await cache.add(new Request(OFFLINE_URL, { cache: 'reload' }));
      } catch (e) {
        console.warn('[Azories SW] Could not cache offline page:', e);
      }
      
      // Cache the main HTML page - critical for offline PWA
      try {
        const indexResponse = await fetch('/', { cache: 'reload' });
        if (indexResponse.ok) {
          await cache.put('/', indexResponse.clone());
          await cache.put('/index.html', indexResponse.clone());
          
          // Parse HTML to find all JS/CSS assets
          const html = await indexResponse.text();
          const assetUrls = [];
          
          // Find all script and link tags
          const scriptMatches = html.matchAll(/src=["']([^"']+\.(js|css))["']/g);
          const linkMatches = html.matchAll(/href=["']([^"']+\.css)["']/g);
          
          for (const match of scriptMatches) {
            if (match[1].startsWith('/') || match[1].startsWith('./')) {
              assetUrls.push(match[1].replace('./', '/'));
            }
          }
          
          for (const match of linkMatches) {
            if (match[1].startsWith('/') || match[1].startsWith('./')) {
              assetUrls.push(match[1].replace('./', '/'));
            }
          }
          
          // Also add common static assets
          const staticAssets = [
            '/manifest.json',
            '/favicon.ico'
          ];
          
          const allAssets = [...new Set([...assetUrls, ...staticAssets])];
          console.log('[Azories SW] Caching assets:', allAssets.length);
          
          // Cache each asset
          for (const url of allAssets) {
            try {
              const response = await fetch(url, { cache: 'reload' });
              if (response.ok) {
                await cache.put(url, response);
              }
            } catch (e) {
              console.warn('[Azories SW] Failed to cache:', url);
            }
          }
        }
      } catch (e) {
        console.error('[Azories SW] Failed to cache app shell:', e);
      }
      
      console.log('[Azories SW v3] Install complete');
      // Force this service worker to become active immediately
      await self.skipWaiting();
    })()
  );
});

// Activate event - Clean up old caches and take control immediately
self.addEventListener('activate', (event) => {
  console.log('[Azories SW v3] Activating...');
  
  event.waitUntil(
    (async () => {
      // Delete old caches
      const cacheNames = await caches.keys();
      await Promise.all(
        cacheNames
          .filter(name => name.startsWith('azories-') && name !== CACHE_NAME)
          .map(name => {
            console.log('[Azories SW] Deleting old cache:', name);
            return caches.delete(name);
          })
      );
      
      // Take control of all pages immediately
      await self.clients.claim();
      console.log('[Azories SW v3] Activated and controlling all clients');
    })()
  );
});

// Fetch event - Serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // Only handle GET requests
  if (event.request.method !== 'GET') {
    return;
  }
  
  // Skip API requests - always go to network
  if (url.pathname.startsWith('/api')) {
    return;
  }
  
  // Skip external requests
  if (url.origin !== self.location.origin) {
    return;
  }
  
  // Handle navigation requests (HTML pages) - CRITICAL FOR OFFLINE PWA
  if (event.request.mode === 'navigate') {
    event.respondWith(
      (async () => {
        try {
          // Try network first for navigation
          const networkResponse = await fetch(event.request);
          
          // Cache the response for future offline use
          if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(event.request, networkResponse.clone());
          }
          
          return networkResponse;
        } catch (error) {
          // Network failed - serve from cache
          console.log('[Azories SW] Network failed, serving from cache');
          
          const cachedResponse = await caches.match(event.request);
          if (cachedResponse) {
            return cachedResponse;
          }
          
          // Try to serve the main index.html for any navigation
          const indexResponse = await caches.match('/');
          if (indexResponse) {
            return indexResponse;
          }
          
          // Last resort - offline page
          const offlineResponse = await caches.match(OFFLINE_URL);
          if (offlineResponse) {
            return offlineResponse;
          }
          
          // Nothing cached - return error
          return new Response('Offline - Please connect to internet to load the app', {
            status: 503,
            headers: { 'Content-Type': 'text/plain' }
          });
        }
      })()
    );
    return;
  }
  
  // Handle static assets (JS, CSS, images) - Cache first strategy
  event.respondWith(
    (async () => {
      // Check cache first
      const cachedResponse = await caches.match(event.request);
      if (cachedResponse) {
        // Return cached version and update cache in background
        fetch(event.request).then(response => {
          if (response.ok) {
            caches.open(CACHE_NAME).then(cache => {
              cache.put(event.request, response);
            });
          }
        }).catch(() => {});
        
        return cachedResponse;
      }
      
      // Not in cache - try network
      try {
        const networkResponse = await fetch(event.request);
        
        // Cache successful responses
        if (networkResponse.ok) {
          const cache = await caches.open(CACHE_NAME);
          cache.put(event.request, networkResponse.clone());
        }
        
        return networkResponse;
      } catch (error) {
        // Network failed and not in cache
        console.warn('[Azories SW] Asset not available offline:', event.request.url);
        
        // For images, return a placeholder or empty response
        if (event.request.destination === 'image') {
          return new Response('', { status: 404 });
        }
        
        return new Response('Offline', { status: 503 });
      }
    })()
  );
});

// Handle messages from the app
self.addEventListener('message', (event) => {
  if (event.data?.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  // Force update cache
  if (event.data?.type === 'UPDATE_CACHE') {
    caches.open(CACHE_NAME).then(async cache => {
      try {
        const response = await fetch('/', { cache: 'reload' });
        if (response.ok) {
          await cache.put('/', response);
          console.log('[Azories SW] Updated main cache');
        }
      } catch (e) {
        console.warn('[Azories SW] Could not update cache');
      }
    });
  }
});
