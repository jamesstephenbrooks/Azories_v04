/**
 * useOffline Hook - Manages offline state and book caching
 */

import { useState, useEffect, useCallback } from 'react';
import offlineStorage from '../services/offlineStorage';

export function useOffline() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [offlineBooks, setOfflineBooks] = useState([]);
  const [offlineBookIds, setOfflineBookIds] = useState(new Set());
  const [storageStats, setStorageStats] = useState(null);
  const [isInitialized, setIsInitialized] = useState(false);

  // Initialize and load offline books
  useEffect(() => {
    async function init() {
      try {
        await offlineStorage.init();
        await refreshOfflineBooks();
        setIsInitialized(true);
      } catch (error) {
        console.error('Failed to initialize offline storage:', error);
        setIsInitialized(true);
      }
    }
    init();
  }, []);

  // Listen for online/offline events
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

  // Refresh offline books list
  const refreshOfflineBooks = useCallback(async () => {
    try {
      const books = await offlineStorage.getAllOfflineBooks();
      setOfflineBooks(books);
      setOfflineBookIds(new Set(books.map(b => b.id)));
      
      const stats = await offlineStorage.getStorageStats();
      setStorageStats(stats);
    } catch (error) {
      console.error('Failed to refresh offline books:', error);
    }
  }, []);

  // Check if a specific book is available offline
  const isBookOffline = useCallback((bookId) => {
    return offlineBookIds.has(bookId);
  }, [offlineBookIds]);

  // Save a book for offline reading
  const saveBookOffline = useCallback(async (book, onProgress) => {
    try {
      const result = await offlineStorage.saveBookForOffline(book, onProgress);
      if (result.success) {
        await refreshOfflineBooks();
      }
      return result;
    } catch (error) {
      console.error('Failed to save book offline:', error);
      return { success: false, error: error.message };
    }
  }, [refreshOfflineBooks]);

  // Remove a book from offline storage
  const removeBookOffline = useCallback(async (bookId) => {
    try {
      const result = await offlineStorage.removeBookOffline(bookId);
      if (result.success) {
        await refreshOfflineBooks();
      }
      return result;
    } catch (error) {
      console.error('Failed to remove book offline:', error);
      return { success: false, error: error.message };
    }
  }, [refreshOfflineBooks]);

  // Get offline book data
  const getOfflineBook = useCallback(async (bookId) => {
    return offlineStorage.getOfflineBook(bookId);
  }, []);

  // Get offline pages for a book
  const getOfflinePages = useCallback(async (bookId) => {
    return offlineStorage.getOfflinePages(bookId);
  }, []);

  // Get offline audio for a page
  const getOfflineAudio = useCallback(async (bookId, pageNumber) => {
    return offlineStorage.getOfflineAudio(bookId, pageNumber);
  }, []);

  // Save audio for offline playback
  const saveAudioOffline = useCallback(async (bookId, pageNumber, audioUrl) => {
    return offlineStorage.saveAudioForOffline(bookId, pageNumber, audioUrl);
  }, []);

  // Check if offline book has narration cached
  const hasOfflineNarration = useCallback((bookId) => {
    const book = offlineBooks.find(b => b.id === bookId);
    return book?.hasNarration || false;
  }, [offlineBooks]);

  return {
    isOnline,
    isOffline: !isOnline,
    isInitialized,
    offlineBooks,
    offlineBookIds,
    storageStats,
    isBookOffline,
    saveBookOffline,
    removeBookOffline,
    getOfflineBook,
    getOfflinePages,
    getOfflineAudio,
    saveAudioOffline,
    hasOfflineNarration,
    refreshOfflineBooks
  };
}

export default useOffline;
