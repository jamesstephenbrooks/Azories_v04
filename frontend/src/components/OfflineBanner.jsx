/**
 * OfflineBanner - Shows when user is offline
 */

import { FiWifiOff, FiX } from 'react-icons/fi';
import { useState } from 'react';

function OfflineBanner({ isOffline, offlineBookCount = 0 }) {
  const [dismissed, setDismissed] = useState(false);

  if (!isOffline || dismissed) return null;

  return (
    <div className="fixed top-16 left-0 right-0 z-50 bg-gradient-to-r from-orange-600 to-red-600 text-white px-4 py-2 shadow-lg">
      <div className="max-w-4xl mx-auto flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <FiWifiOff className="w-5 h-5 flex-shrink-0" />
          <div>
            <span className="font-medium">You're offline</span>
            {offlineBookCount > 0 ? (
              <span className="text-white/80 ml-2">
                — {offlineBookCount} book{offlineBookCount !== 1 ? 's' : ''} available to read
              </span>
            ) : (
              <span className="text-white/80 ml-2">
                — Save books for offline reading when connected
              </span>
            )}
          </div>
        </div>
        <button
          onClick={() => setDismissed(true)}
          className="p-1 hover:bg-white/20 rounded-full transition-colors touch-manipulation"
        >
          <FiX className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}

export default OfflineBanner;
