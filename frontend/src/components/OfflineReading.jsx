import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { FiDownload, FiTrash2, FiWifiOff, FiCheck, FiLoader, FiCloud, FiCloudOff } from 'react-icons/fi';
import { toast } from 'sonner';

// Hook for managing offline books
export function useOfflineBooks() {
  const [cachedBooks, setCachedBooks] = useState([]);
  const [isOnline, setIsOnline] = useState(typeof navigator !== 'undefined' ? navigator.onLine : true);
  const [isSupported, setIsSupported] = useState(false);

  useEffect(() => {
    // Check if service worker is supported
    const swSupported = typeof navigator !== 'undefined' && 'serviceWorker' in navigator;
    setIsSupported(swSupported);
    
    // Register service worker
    if (swSupported) {
      navigator.serviceWorker.register('/service-worker.js').catch(console.error);
      
      // Listen for messages from service worker
      navigator.serviceWorker.addEventListener('message', (event) => {
        if (event.data.type === 'CACHED_BOOKS') {
          setCachedBooks(event.data.books || []);
        }
        if (event.data.type === 'BOOK_CACHED') {
          toast.success('Book saved for offline reading!');
          getCachedBooks();
        }
        if (event.data.type === 'BOOK_REMOVED') {
          toast.success('Book removed from offline storage');
          getCachedBooks();
        }
      });
      
      // Get initial cached books
      getCachedBooks();
    }
    
    // Online/offline listeners
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => {
      setIsOnline(false);
      toast.warning('You are offline. Some features may be limited.');
    };
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const getCachedBooks = useCallback(() => {
    if (typeof navigator !== 'undefined' && 'serviceWorker' in navigator && navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.postMessage({ type: 'GET_CACHED_BOOKS' });
    }
  }, []);

  const cacheBook = useCallback((book) => {
    if (typeof navigator === 'undefined' || !('serviceWorker' in navigator) || !navigator.serviceWorker.controller) {
      toast.error('Offline reading not available');
      return;
    }
    
    navigator.serviceWorker.controller.postMessage({
      type: 'CACHE_BOOK',
      bookId: book.id,
      pages: book.pages
    });
  }, []);

  const removeCachedBook = useCallback((bookId) => {
    if (typeof navigator === 'undefined' || !('serviceWorker' in navigator) || !navigator.serviceWorker.controller) return;
    
    navigator.serviceWorker.controller.postMessage({
      type: 'REMOVE_CACHED_BOOK',
      bookId
    });
  }, []);

  const isBookCached = useCallback((bookId) => {
    return cachedBooks.some((b) => b.id === bookId);
  }, [cachedBooks]);

  return {
    cachedBooks,
    isOnline,
    isSupported,
    cacheBook,
    removeCachedBook,
    isBookCached,
    refreshCachedBooks: getCachedBooks
  };
}

// Offline indicator component
export function OfflineIndicator() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  if (isOnline) return null;

  return (
    <motion.div
      initial={{ y: -50, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="fixed top-0 left-0 right-0 z-[100] bg-amber-500 text-white py-2 px-4 text-center text-sm flex items-center justify-center gap-2"
    >
      <FiWifiOff className="w-4 h-4" />
      You're offline. Some features may be limited.
    </motion.div>
  );
}

// Download for offline button
export function DownloadForOfflineButton({ book, size = 'default' }) {
  const { isSupported, cacheBook, removeCachedBook, isBookCached } = useOfflineBooks();
  const [isLoading, setIsLoading] = useState(false);
  
  const isCached = isBookCached(book?.id);

  const handleClick = async () => {
    if (!book) return;
    
    setIsLoading(true);
    
    try {
      if (isCached) {
        removeCachedBook(book.id);
      } else {
        cacheBook(book);
      }
    } finally {
      setTimeout(() => setIsLoading(false), 1000);
    }
  };

  if (!isSupported) return null;

  if (size === 'icon') {
    return (
      <Button
        variant="ghost"
        size="icon"
        onClick={handleClick}
        disabled={isLoading}
        className={isCached ? 'text-green-500' : ''}
        title={isCached ? 'Remove from offline' : 'Save for offline'}
      >
        {isLoading ? (
          <FiLoader className="w-4 h-4 animate-spin" />
        ) : isCached ? (
          <FiCheck className="w-4 h-4" />
        ) : (
          <FiDownload className="w-4 h-4" />
        )}
      </Button>
    );
  }

  return (
    <Button
      variant={isCached ? 'secondary' : 'outline'}
      onClick={handleClick}
      disabled={isLoading}
      className="gap-2"
    >
      {isLoading ? (
        <>
          <FiLoader className="w-4 h-4 animate-spin" />
          {isCached ? 'Removing...' : 'Saving...'}
        </>
      ) : isCached ? (
        <>
          <FiCheck className="w-4 h-4 text-green-500" />
          Saved Offline
        </>
      ) : (
        <>
          <FiDownload className="w-4 h-4" />
          Save for Offline
        </>
      )}
    </Button>
  );
}

// Cached books list
export function CachedBooksList() {
  const { cachedBooks, removeCachedBook, isOnline } = useOfflineBooks();

  if (cachedBooks.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <FiCloudOff className="w-12 h-12 mx-auto mb-4 opacity-50" />
        <p>No books saved for offline reading</p>
        <p className="text-sm mt-2">Download books to read them without internet</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-medium flex items-center gap-2">
          <FiCloud className="w-4 h-4" />
          Offline Library
        </h3>
        <span className="text-xs text-muted-foreground">
          {cachedBooks.length} book{cachedBooks.length !== 1 ? 's' : ''} saved
        </span>
      </div>
      
      <div className="space-y-2">
        {cachedBooks.map((book) => (
          <div 
            key={book.id}
            className="flex items-center justify-between p-3 bg-muted/50 rounded-lg"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-14 bg-gradient-to-br from-purple-500 to-pink-500 rounded flex items-center justify-center text-white text-xs">
                {book.pages?.length || '?'}p
              </div>
              <div>
                <p className="font-medium text-sm">{book.id}</p>
                <p className="text-xs text-muted-foreground">
                  {isOnline ? 'Available online & offline' : 'Available offline'}
                </p>
              </div>
            </div>
            
            <Button
              variant="ghost"
              size="icon"
              onClick={() => removeCachedBook(book.id)}
              className="text-red-500 hover:text-red-600 hover:bg-red-500/10"
            >
              <FiTrash2 className="w-4 h-4" />
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}
