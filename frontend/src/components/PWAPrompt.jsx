import { useState, useEffect, useRef } from 'react';
import { FiX, FiShare, FiPlusSquare, FiDownload } from 'react-icons/fi';

/**
 * PWA Home Screen Prompt
 * Shows a one-time banner prompting mobile users to add the app to their home screen
 * - Chrome/Android: Uses native beforeinstallprompt for automatic install dialog
 * - iOS Safari: Shows manual instructions (Apple doesn't allow auto-prompts)
 */
export default function PWAPrompt() {
  const [showPrompt, setShowPrompt] = useState(false);
  const [isIOS, setIsIOS] = useState(false);
  const [canInstall, setCanInstall] = useState(false);
  const deferredPromptRef = useRef(null);
  
  useEffect(() => {
    // Only show on mobile devices
    const isMobile = typeof window !== 'undefined' && 
      (window.innerWidth < 768 || 'ontouchstart' in window);
    
    // Check if already dismissed
    const dismissed = localStorage.getItem('azories-pwa-prompt-dismissed');
    
    // Check if already installed as PWA (standalone mode)
    let isStandalone = false;
    try {
      isStandalone = window.matchMedia?.('(display-mode: standalone)')?.matches || false;
      if (typeof navigator !== 'undefined' && 'standalone' in navigator) {
        isStandalone = isStandalone || navigator.standalone === true;
      }
    } catch (e) {
      // Ignore errors from unsupported APIs
    }
    
    // Detect iOS - ALL iOS browsers use WebKit, so check user agent for iOS device
    // This catches Safari, Chrome, Firefox, and any other browser on iOS
    let iOS = false;
    try {
      const userAgent = typeof navigator !== 'undefined' ? navigator.userAgent || '' : '';
      // Check for iPhone, iPad, iPod in user agent
      iOS = /iPad|iPhone|iPod/.test(userAgent);
      // Also check for iPad running iPadOS 13+ which reports as Mac
      if (!iOS && /Macintosh/.test(userAgent) && 'ontouchend' in document) {
        iOS = true;
      }
      console.log('[PWAPrompt] iOS detected:', iOS, 'UserAgent:', userAgent.substring(0, 100));
    } catch (e) {
      console.log('[PWAPrompt] Error detecting iOS:', e);
    }
    setIsIOS(iOS);
    
    // Listen for Chrome's beforeinstallprompt event (only fires on Android Chrome, never on iOS)
    const handleBeforeInstallPrompt = (e) => {
      e.preventDefault();
      deferredPromptRef.current = e;
      setCanInstall(true);
      console.log('[PWAPrompt] beforeinstallprompt captured');
    };
    
    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    
    // Listen for successful installation
    const handleAppInstalled = () => {
      console.log('[PWAPrompt] App installed successfully');
      setShowPrompt(false);
      deferredPromptRef.current = null;
      setCanInstall(false);
    };
    window.addEventListener('appinstalled', handleAppInstalled);
    
    // Show prompt after a short delay if conditions are met
    console.log('[PWAPrompt] Conditions:', { isMobile, dismissed, isStandalone });
    if (isMobile && !dismissed && !isStandalone) {
      const timer = setTimeout(() => {
        console.log('[PWAPrompt] Showing prompt');
        setShowPrompt(true);
      }, 2000);
      return () => {
        clearTimeout(timer);
        window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
        window.removeEventListener('appinstalled', handleAppInstalled);
      };
    }
    
    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);
  
  const handleDismiss = () => {
    setShowPrompt(false);
    localStorage.setItem('azories-pwa-prompt-dismissed', 'true');
  };
  
  const handleInstall = async () => {
    // Chrome/Android: Use the native install prompt
    if (deferredPromptRef.current) {
      try {
        // Show the native install prompt
        deferredPromptRef.current.prompt();
        
        // Wait for user choice
        const { outcome } = await deferredPromptRef.current.userChoice;
        console.log('[PWAPrompt] User choice:', outcome);
        
        if (outcome === 'accepted') {
          setShowPrompt(false);
          localStorage.setItem('azories-pwa-prompt-dismissed', 'true');
        }
        
        // Clear the deferred prompt
        deferredPromptRef.current = null;
        setCanInstall(false);
      } catch (error) {
        console.error('[PWAPrompt] Install error:', error);
      }
    }
  };
  
  if (!showPrompt) return null;
  
  return (
    <div 
      className="fixed bottom-20 left-4 right-4 z-[100] animate-in slide-in-from-bottom duration-300"
      style={{ maxWidth: '400px', margin: '0 auto' }}
    >
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-2xl shadow-2xl p-4 text-white">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
            {canInstall ? <FiDownload className="w-5 h-5" /> : <FiPlusSquare className="w-5 h-5" />}
          </div>
          
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-sm mb-1">
              Get the Full Screen Experience
            </h3>
            <p className="text-xs text-white/80 leading-relaxed mb-3">
              {isIOS ? (
                <>Tap <FiShare className="inline w-3 h-3 mx-0.5" /> then "Add to Home Screen" for the best reading experience.</>
              ) : canInstall ? (
                <>Install Azories for immersive reading without browser UI.</>
              ) : (
                <>Add Azories to your home screen for the best reading experience.</>
              )}
            </p>
            
            {/* Action buttons */}
            <div className="flex gap-2">
              {canInstall && !isIOS && (
                <button
                  onClick={handleInstall}
                  className="flex-1 py-2 px-4 bg-white text-purple-600 font-semibold text-sm rounded-lg hover:bg-white/90 transition-colors flex items-center justify-center gap-2"
                >
                  <FiDownload className="w-4 h-4" />
                  Install App
                </button>
              )}
              <button
                onClick={handleDismiss}
                className={`${canInstall && !isIOS ? 'px-4' : 'flex-1 px-4'} py-2 bg-white/20 text-white text-sm rounded-lg hover:bg-white/30 transition-colors`}
              >
                {canInstall && !isIOS ? 'Later' : 'Dismiss'}
              </button>
            </div>
          </div>
          
          <button
            onClick={handleDismiss}
            className="flex-shrink-0 w-6 h-6 flex items-center justify-center hover:bg-white/20 rounded-full transition-colors"
            aria-label="Dismiss"
          >
            <FiX className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
