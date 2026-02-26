import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import { FiX, FiCheck, FiSettings } from 'react-icons/fi';

const CookieConsent = () => {
  const [visible, setVisible] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [preferences, setPreferences] = useState({
    necessary: true,
    analytics: true,
    marketing: false
  });

  useEffect(() => {
    // Check if user has already made a choice
    const consent = localStorage.getItem('azories-cookie-consent');
    if (!consent) {
      // Show banner after a short delay
      setTimeout(() => setVisible(true), 1000);
    }
  }, []);

  const handleAcceptAll = () => {
    const allConsent = { necessary: true, analytics: true, marketing: true, timestamp: new Date().toISOString() };
    localStorage.setItem('azories-cookie-consent', JSON.stringify(allConsent));
    setVisible(false);
  };

  const handleAcceptSelected = () => {
    const consent = { ...preferences, timestamp: new Date().toISOString() };
    localStorage.setItem('azories-cookie-consent', JSON.stringify(consent));
    setVisible(false);
  };

  const handleRejectAll = () => {
    const minimalConsent = { necessary: true, analytics: false, marketing: false, timestamp: new Date().toISOString() };
    localStorage.setItem('azories-cookie-consent', JSON.stringify(minimalConsent));
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ y: 100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: 100, opacity: 0 }}
        className="fixed bottom-0 left-0 right-0 z-50 p-2 sm:p-4"
      >
        <div className="max-w-4xl mx-auto bg-white rounded-xl sm:rounded-2xl shadow-2xl border border-gray-200 overflow-hidden max-h-[50vh] sm:max-h-none overflow-y-auto">
          <div className="p-4 sm:p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center">
                <span className="text-2xl mr-3">🍪</span>
                <h3 className="text-lg font-bold text-gray-900">We use cookies</h3>
              </div>
              <button
                onClick={handleRejectAll}
                className="text-gray-400 hover:text-gray-600"
              >
                <FiX className="text-xl" />
              </button>
            </div>

            <p className="text-gray-600 mb-3 sm:mb-4 text-sm sm:text-base">
              We use cookies to improve your experience on our site. By clicking "Accept All", you consent to our use of cookies. 
              You can manage your preferences or learn more in our{' '}
              <Link to="/privacy" className="text-purple-600 hover:underline">Privacy Policy</Link>.
            </p>

            {showDetails && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                className="border-t border-gray-200 pt-4 mb-4"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between py-2">
                    <div>
                      <div className="font-medium text-gray-900">Necessary Cookies</div>
                      <p className="text-sm text-gray-500">Required for the site to function properly</p>
                    </div>
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        checked={preferences.necessary}
                        disabled
                        className="w-5 h-5 text-purple-600 rounded"
                      />
                      <span className="ml-2 text-xs text-gray-400">Always on</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between py-2">
                    <div>
                      <div className="font-medium text-gray-900">Analytics Cookies</div>
                      <p className="text-sm text-gray-500">Help us understand how visitors use our site</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={preferences.analytics}
                      onChange={e => setPreferences(p => ({ ...p, analytics: e.target.checked }))}
                      className="w-5 h-5 text-purple-600 rounded cursor-pointer"
                    />
                  </div>

                  <div className="flex items-center justify-between py-2">
                    <div>
                      <div className="font-medium text-gray-900">Marketing Cookies</div>
                      <p className="text-sm text-gray-500">Used to personalize ads and content</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={preferences.marketing}
                      onChange={e => setPreferences(p => ({ ...p, marketing: e.target.checked }))}
                      className="w-5 h-5 text-purple-600 rounded cursor-pointer"
                    />
                  </div>
                </div>
              </motion.div>
            )}

            <div className="flex flex-wrap gap-2 sm:gap-3">
              <button
                onClick={() => setShowDetails(!showDetails)}
                className="flex items-center px-3 sm:px-4 py-2 text-sm sm:text-base text-gray-600 hover:text-gray-900 border border-gray-300 rounded-lg transition-colors"
              >
                <FiSettings className="mr-1 sm:mr-2" />
                {showDetails ? 'Hide' : 'Manage'}
              </button>
              
              {showDetails ? (
                <button
                  onClick={handleAcceptSelected}
                  className="flex items-center px-4 sm:px-6 py-2 text-sm sm:text-base bg-purple-600 hover:bg-purple-500 text-white rounded-lg transition-colors"
                >
                  <FiCheck className="mr-1 sm:mr-2" />
                  Save
                </button>
              ) : (
                <>
                  <button
                    onClick={handleRejectAll}
                    className="px-3 sm:px-4 py-2 text-sm sm:text-base text-gray-600 hover:text-gray-900 border border-gray-300 rounded-lg transition-colors"
                  >
                    Reject All
                  </button>
                  <button
                    onClick={handleAcceptAll}
                    className="flex items-center px-4 sm:px-6 py-2 text-sm sm:text-base bg-purple-600 hover:bg-purple-500 text-white rounded-lg transition-colors"
                  >
                    <FiCheck className="mr-1 sm:mr-2" />
                    Accept All
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export default CookieConsent;
