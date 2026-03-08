/**
 * InstallPrompt - Prompts users to install the PWA for offline access
 */

import { useState, useEffect } from 'react';
import { FiDownload, FiX, FiSmartphone } from 'react-icons/fi';
import { Button } from './ui/button';

export default function InstallPrompt() {
  const [showPrompt, setShowPrompt] = useState(false);
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [isIOS, setIsIOS] = useState(false);
  const [isStandalone, setIsStandalone] = useState(false);

  useEffect(() => {
    // Check if already installed (standalone mode)
    const standalone = window.matchMedia('(display-mode: standalone)').matches || 
                       window.navigator.standalone === true;
    setIsStandalone(standalone);
    
    // Check if iOS
    const iOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    setIsIOS(iOS);
    
    // Don't show if already installed
    if (standalone) return;
    
    // Check if user has dismissed before (within last 7 days)
    const dismissed = localStorage.getItem('azories-install-dismissed');
    if (dismissed) {
      const dismissedDate = new Date(parseInt(dismissed));
      const daysSinceDismissed = (Date.now() - dismissedDate) / (1000 * 60 * 60 * 24);
      if (daysSinceDismissed < 7) return;
    }
    
    // For Android/Desktop, listen for beforeinstallprompt
    const handleBeforeInstall = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      // Show prompt after a delay (don't interrupt initial experience)
      setTimeout(() => setShowPrompt(true), 30000); // 30 seconds
    };
    
    window.addEventListener('beforeinstallprompt', handleBeforeInstall);
    
    // For iOS, show manual instruction prompt after delay
    if (iOS && !standalone) {
      setTimeout(() => setShowPrompt(true), 60000); // 1 minute
    }
    
    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstall);
    };
  }, []);

  const handleInstall = async () => {
    if (deferredPrompt) {
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      if (outcome === 'accepted') {
        setShowPrompt(false);
      }
      setDeferredPrompt(null);
    }
  };

  const handleDismiss = () => {
    setShowPrompt(false);
    localStorage.setItem('azories-install-dismissed', Date.now().toString());
  };

  if (!showPrompt || isStandalone) return null;

  return (
    <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-96 z-50 animate-in slide-in-from-bottom-4 duration-300">
      <div className="bg-gradient-to-r from-purple-900 to-purple-800 rounded-2xl shadow-2xl border border-purple-700/50 p-4">
        <button 
          onClick={handleDismiss}
          className="absolute top-2 right-2 text-white/60 hover:text-white p-1"
          aria-label="Dismiss"
        >
          <FiX className="w-5 h-5" />
        </button>
        
        <div className="flex items-start gap-3">
          <div className="w-12 h-12 rounded-xl bg-purple-600 flex items-center justify-center flex-shrink-0">
            <FiSmartphone className="w-6 h-6 text-white" />
          </div>
          
          <div className="flex-1 pr-6">
            <h3 className="font-semibold text-white text-sm mb-1">
              Read Offline Anytime
            </h3>
            <p className="text-purple-200 text-xs mb-3">
              {isIOS 
                ? "Add Azories to your home screen for offline access to saved books." 
                : "Install Azories for offline reading and a better experience."}
            </p>
            
            {isIOS ? (
              <div className="text-purple-200 text-xs space-y-1">
                <p>Tap the <span className="inline-flex items-center mx-1 px-1 bg-purple-700 rounded">
                  <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" />
                    <polyline points="16 6 12 2 8 6" />
                    <line x1="12" y1="2" x2="12" y2="15" />
                  </svg>
                </span> Share button, then "Add to Home Screen"</p>
              </div>
            ) : (
              <Button 
                onClick={handleInstall}
                size="sm"
                className="bg-white text-purple-900 hover:bg-purple-100 font-medium"
              >
                <FiDownload className="w-4 h-4 mr-2" />
                Install App
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
