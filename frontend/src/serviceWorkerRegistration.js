/**
 * Service Worker Registration for Azories PWA
 * Enables offline support on iOS Safari and other browsers
 */

const isLocalhost = Boolean(
  window.location.hostname === 'localhost' ||
  window.location.hostname === '[::1]' ||
  window.location.hostname.match(/^127(?:\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}$/)
);

export function register(config) {
  if ('serviceWorker' in navigator) {
    const publicUrl = new URL(process.env.PUBLIC_URL || '', window.location.href);
    if (publicUrl.origin !== window.location.origin) {
      console.warn('[Azories SW] Different origin, skipping registration');
      return;
    }

    // Register immediately, don't wait for load
    const swUrl = `${process.env.PUBLIC_URL || ''}/service-worker.js`;
    
    if (isLocalhost) {
      checkValidServiceWorker(swUrl, config);
    } else {
      registerValidSW(swUrl, config);
    }
    
    // Also try to register on load for redundancy
    window.addEventListener('load', () => {
      registerValidSW(swUrl, config);
    });
  } else {
    console.warn('[Azories SW] Service workers not supported');
  }
}

function registerValidSW(swUrl, config) {
  navigator.serviceWorker
    .register(swUrl, { scope: '/' })
    .then((registration) => {
      console.log('[Azories SW] Registered successfully');
      
      // Force update check on registration
      registration.update();
      
      // Check for updates every 30 minutes
      setInterval(() => {
        registration.update();
      }, 30 * 60 * 1000);
      
      registration.onupdatefound = () => {
        const installingWorker = registration.installing;
        if (!installingWorker) return;
        
        installingWorker.onstatechange = () => {
          if (installingWorker.state === 'installed') {
            if (navigator.serviceWorker.controller) {
              // New content available
              console.log('[Azories SW] New version available - refresh to update');
              
              // Auto-update: tell the waiting SW to take over
              if (registration.waiting) {
                registration.waiting.postMessage({ type: 'SKIP_WAITING' });
              }
              
              if (config?.onUpdate) {
                config.onUpdate(registration);
              }
            } else {
              // First install
              console.log('[Azories SW] Content cached for offline use');
              if (config?.onSuccess) {
                config.onSuccess(registration);
              }
            }
          }
        };
      };
      
      // If there's a waiting worker, activate it immediately
      if (registration.waiting) {
        registration.waiting.postMessage({ type: 'SKIP_WAITING' });
      }
    })
    .catch((error) => {
      console.error('[Azories SW] Registration failed:', error);
    });

  // Listen for controller changes and reload
  let refreshing = false;
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (!refreshing) {
      refreshing = true;
      console.log('[Azories SW] Controller changed, reloading...');
      window.location.reload();
    }
  });
}

function checkValidServiceWorker(swUrl, config) {
  fetch(swUrl, { headers: { 'Service-Worker': 'script' } })
    .then((response) => {
      const contentType = response.headers.get('content-type');
      if (
        response.status === 404 ||
        (contentType && !contentType.includes('javascript'))
      ) {
        // No service worker found, unregister
        navigator.serviceWorker.ready.then((registration) => {
          registration.unregister().then(() => {
            window.location.reload();
          });
        });
      } else {
        registerValidSW(swUrl, config);
      }
    })
    .catch(() => {
      console.log('[Azories SW] Offline mode - using cached version');
    });
}

export function unregister() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready
      .then((registration) => {
        registration.unregister();
      })
      .catch((error) => {
        console.error('[Azories SW] Unregister error:', error);
      });
  }
}

// Force service worker update
export function update() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready.then((registration) => {
      registration.update();
    });
  }
}

// Clear cache and reinstall
export function clearCacheAndReload() {
  if ('caches' in window) {
    caches.keys().then((names) => {
      names.forEach((name) => {
        caches.delete(name);
      });
    }).then(() => {
      window.location.reload(true);
    });
  }
}
