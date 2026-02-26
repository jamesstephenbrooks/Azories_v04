import { useState, useEffect } from 'react';
import { FiX, FiShare, FiPlusSquare } from 'react-icons/fi';

/**
 * PWA Home Screen Prompt
 * Shows a one-time banner prompting mobile users to add the app to their home screen
 * for a full-screen reading experience without browser UI
 */
export default function PWAPrompt() {
  const [showPrompt, setShowPrompt] = useState(false);
  const [isIOS, setIsIOS] = useState(false);
  
  useEffect(() => {
    // Only show on mobile devices
    const isMobile = typeof window !== 'undefined' && 
      (window.innerWidth < 768 || 'ontouchstart' in window);
    
    // Check if already dismissed
    const dismissed = localStorage.getItem('azories-pwa-prompt-dismissed');
    
    // Check if already installed as PWA (standalone mode)
    const isStandalone = window.matchMedia?.('(display-mode: standalone)')?.matches ||
                         (navigator as any).standalone === true;
    
    // Detect iOS for specific instructions
    const userAgent = typeof navigator !== 'undefined' ? navigator.userAgent || '' : '';
    const iOS = /iPad|iPhone|iPod/.test(userAgent) && !(window as any).MSStream;
    setIsIOS(iOS);
    
    // Show prompt after a short delay if conditions are met
    if (isMobile && !dismissed && !isStandalone) {
      const timer = setTimeout(() => setShowPrompt(true), 2000);
      return () => clearTimeout(timer);
    }
  }, []);
  
  const handleDismiss = () => {
    setShowPrompt(false);
    localStorage.setItem('azories-pwa-prompt-dismissed', 'true');
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
            <FiPlusSquare className="w-5 h-5" />
          </div>
          
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-sm mb-1">
              Get the Full Screen Experience
            </h3>
            <p className="text-xs text-white/80 leading-relaxed">
              {isIOS ? (
                <>Tap <FiShare className="inline w-3 h-3 mx-0.5" /> then "Add to Home Screen" for the best reading experience without browser bars.</>
              ) : (
                <>Add Azories to your home screen for immersive reading without browser UI.</>
              )}
            </p>
          </div>
          
          <button
            onClick={handleDismiss}
            className="flex-shrink-0 w-8 h-8 flex items-center justify-center hover:bg-white/20 rounded-full transition-colors"
            aria-label="Dismiss"
          >
            <FiX className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
