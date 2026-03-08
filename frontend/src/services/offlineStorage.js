/**
 * Offline Storage Service for Azories
 * Uses IndexedDB to store book content for offline reading
 */

const DB_NAME = 'azories-offline';
const DB_VERSION = 1;
const STORE_BOOKS = 'books';
const STORE_PAGES = 'pages';
const STORE_AUDIO = 'audio';

class OfflineStorageService {
  constructor() {
    this.db = null;
    this.isSupported = 'indexedDB' in window;
  }

  async init() {
    if (!this.isSupported) {
      console.warn('IndexedDB not supported');
      return false;
    }

    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => {
        console.error('Failed to open IndexedDB:', request.error);
        reject(request.error);
      };

      request.onsuccess = () => {
        this.db = request.result;
        resolve(true);
      };

      request.onupgradeneeded = (event) => {
        const db = event.target.result;

        // Books metadata store
        if (!db.objectStoreNames.contains(STORE_BOOKS)) {
          const booksStore = db.createObjectStore(STORE_BOOKS, { keyPath: 'id' });
          booksStore.createIndex('savedAt', 'savedAt', { unique: false });
        }

        // Pages store (images and text)
        if (!db.objectStoreNames.contains(STORE_PAGES)) {
          const pagesStore = db.createObjectStore(STORE_PAGES, { keyPath: 'id' });
          pagesStore.createIndex('bookId', 'bookId', { unique: false });
        }

        // Audio store (narration)
        if (!db.objectStoreNames.contains(STORE_AUDIO)) {
          const audioStore = db.createObjectStore(STORE_AUDIO, { keyPath: 'id' });
          audioStore.createIndex('bookId', 'bookId', { unique: false });
        }
      };
    });
  }

  async ensureDb() {
    if (!this.db) {
      await this.init();
    }
    return this.db;
  }

  /**
   * Save a book for offline reading (including narration audio)
   * @param {Object} book - Book data with pages array
   * @param {Function} onProgress - Progress callback (current, total, message)
   * @param {Object} options - Options { includeAudio: true/false }
   * @returns {Promise<Object>} - Result with success status
   */
  async saveBookForOffline(book, onProgress = () => {}, options = { includeAudio: true }) {
    await this.ensureDb();

    const bookId = book.id;
    const pages = book.pages || [];
    const includeAudio = options.includeAudio !== false;
    
    // Count total items: cover + pages + audio (if included)
    const audioPages = includeAudio ? pages.filter(p => p.audio_url) : [];
    const totalItems = 1 + pages.length + audioPages.length; // cover + pages + audio
    let savedItems = 0;
    let totalBytes = 0;

    try {
      // Save cover image first
      let coverBlob = null;
      if (book.cover_image) {
        try {
          onProgress(savedItems, totalItems, 'Downloading cover...');
          const coverResponse = await fetch(book.cover_image);
          coverBlob = await coverResponse.blob();
          totalBytes += coverBlob.size;
        } catch (e) {
          console.warn('Failed to fetch cover image:', e);
        }
      }
      savedItems++;
      onProgress(savedItems, totalItems, 'Cover saved');

      // Save each page
      const pageData = [];
      for (let i = 0; i < pages.length; i++) {
        const page = pages[i];
        let imageBlob = null;

        // Fetch and store page image
        const imageUrl = page.image_url || page.illustration_url;
        if (imageUrl) {
          try {
            onProgress(savedItems, totalItems, `Downloading page ${i + 1} image...`);
            const response = await fetch(imageUrl);
            imageBlob = await response.blob();
            totalBytes += imageBlob.size;
          } catch (e) {
            console.warn(`Failed to fetch image for page ${i + 1}:`, e);
          }
        }

        pageData.push({
          id: `${bookId}_page_${page.page_number || i}`,
          bookId: bookId,
          pageNumber: page.page_number || i,
          imageBlob: imageBlob,
          imageUrl: imageUrl,
          textContent: page.text_content || page.text || '',
          title: page.title || '',
          hasAudio: !!page.audio_url,
        });

        savedItems++;
        onProgress(savedItems, totalItems, `Page ${i + 1}/${pages.length} saved`);
      }

      // Save audio for each page that has narration
      if (includeAudio && audioPages.length > 0) {
        for (let i = 0; i < audioPages.length; i++) {
          const page = audioPages[i];
          const pageNumber = page.page_number || pages.indexOf(page);
          
          try {
            onProgress(savedItems, totalItems, `Downloading narration ${i + 1}/${audioPages.length}...`);
            const audioResponse = await fetch(page.audio_url);
            const audioBlob = await audioResponse.blob();
            totalBytes += audioBlob.size;
            
            // Save audio to audio store
            const audioTx = this.db.transaction(STORE_AUDIO, 'readwrite');
            const audioStore = audioTx.objectStore(STORE_AUDIO);
            
            await new Promise((resolve, reject) => {
              const request = audioStore.put({
                id: `${bookId}_audio_${pageNumber}`,
                bookId: bookId,
                pageNumber: pageNumber,
                audioBlob: audioBlob,
                audioUrl: page.audio_url,
                savedAt: Date.now()
              });
              request.onsuccess = resolve;
              request.onerror = () => reject(request.error);
            });
          } catch (e) {
            console.warn(`Failed to cache audio for page ${pageNumber}:`, e);
          }
          
          savedItems++;
          onProgress(savedItems, totalItems, `Narration ${i + 1}/${audioPages.length} saved`);
        }
      }

      // Store pages in IndexedDB
      const tx = this.db.transaction([STORE_BOOKS, STORE_PAGES], 'readwrite');
      const booksStore = tx.objectStore(STORE_BOOKS);
      const pagesStore = tx.objectStore(STORE_PAGES);

      // Save book metadata
      const bookMetadata = {
        id: bookId,
        title: book.title,
        coverBlob: coverBlob,
        coverUrl: book.cover_image,
        pageCount: pages.length,
        audioPageCount: audioPages.length,
        hasNarration: audioPages.length > 0,
        authorName: book.author_name || book.child_name,
        childName: book.child_name,
        savedAt: Date.now(),
        sizeBytes: totalBytes,
        status: 'complete'
      };

      await new Promise((resolve, reject) => {
        const bookRequest = booksStore.put(bookMetadata);
        bookRequest.onsuccess = resolve;
        bookRequest.onerror = () => reject(bookRequest.error);
      });

      // Save all pages
      for (const page of pageData) {
        await new Promise((resolve, reject) => {
          const pageRequest = pagesStore.put(page);
          pageRequest.onsuccess = resolve;
          pageRequest.onerror = () => reject(pageRequest.error);
        });
      }

      onProgress(totalItems, totalItems, 'Complete!');

      return {
        success: true,
        bookId: bookId,
        pageCount: pages.length,
        audioPageCount: audioPages.length,
        sizeBytes: totalBytes,
        sizeMB: (totalBytes / (1024 * 1024)).toFixed(2)
      };
    } catch (error) {
      console.error('Failed to save book offline:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Check if a book is saved for offline
   */
  async isBookOffline(bookId) {
    await this.ensureDb();

    return new Promise((resolve) => {
      const tx = this.db.transaction(STORE_BOOKS, 'readonly');
      const store = tx.objectStore(STORE_BOOKS);
      const request = store.get(bookId);

      request.onsuccess = () => {
        const book = request.result;
        resolve(book && book.status === 'complete');
      };

      request.onerror = () => {
        resolve(false);
      };
    });
  }

  /**
   * Get offline book metadata
   */
  async getOfflineBook(bookId) {
    await this.ensureDb();

    return new Promise((resolve) => {
      const tx = this.db.transaction(STORE_BOOKS, 'readonly');
      const store = tx.objectStore(STORE_BOOKS);
      const request = store.get(bookId);

      request.onsuccess = () => resolve(request.result || null);
      request.onerror = () => resolve(null);
    });
  }

  /**
   * Get offline pages for a book
   */
  async getOfflinePages(bookId) {
    await this.ensureDb();

    return new Promise((resolve) => {
      const tx = this.db.transaction(STORE_PAGES, 'readonly');
      const store = tx.objectStore(STORE_PAGES);
      const index = store.index('bookId');
      const request = index.getAll(bookId);

      request.onsuccess = () => {
        const pages = request.result || [];
        // Sort by page number
        pages.sort((a, b) => a.pageNumber - b.pageNumber);
        resolve(pages);
      };

      request.onerror = () => resolve([]);
    });
  }

  /**
   * Get all offline books
   */
  async getAllOfflineBooks() {
    await this.ensureDb();

    return new Promise((resolve) => {
      const tx = this.db.transaction(STORE_BOOKS, 'readonly');
      const store = tx.objectStore(STORE_BOOKS);
      const request = store.getAll();

      request.onsuccess = () => {
        const books = request.result || [];
        resolve(books.filter(b => b.status === 'complete'));
      };

      request.onerror = () => resolve([]);
    });
  }

  /**
   * Remove a book from offline storage
   */
  async removeBookOffline(bookId) {
    await this.ensureDb();

    try {
      const tx = this.db.transaction([STORE_BOOKS, STORE_PAGES, STORE_AUDIO], 'readwrite');
      const booksStore = tx.objectStore(STORE_BOOKS);
      const pagesStore = tx.objectStore(STORE_PAGES);
      const audioStore = tx.objectStore(STORE_AUDIO);

      // Remove book metadata
      booksStore.delete(bookId);

      // Remove all pages for this book
      const pagesIndex = pagesStore.index('bookId');
      const pagesRequest = pagesIndex.getAllKeys(bookId);
      
      pagesRequest.onsuccess = () => {
        const keys = pagesRequest.result;
        keys.forEach(key => pagesStore.delete(key));
      };

      // Remove all audio for this book
      const audioIndex = audioStore.index('bookId');
      const audioRequest = audioIndex.getAllKeys(bookId);
      
      audioRequest.onsuccess = () => {
        const keys = audioRequest.result;
        keys.forEach(key => audioStore.delete(key));
      };

      return { success: true };
    } catch (error) {
      console.error('Failed to remove book offline:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Get storage statistics
   */
  async getStorageStats() {
    await this.ensureDb();

    const books = await this.getAllOfflineBooks();
    const totalBytes = books.reduce((sum, book) => sum + (book.sizeBytes || 0), 0);

    // Try to get storage quota info
    let quotaInfo = null;
    if (navigator.storage && navigator.storage.estimate) {
      try {
        quotaInfo = await navigator.storage.estimate();
      } catch (e) {
        console.warn('Could not get storage estimate:', e);
      }
    }

    return {
      bookCount: books.length,
      totalBytes: totalBytes,
      totalMB: (totalBytes / (1024 * 1024)).toFixed(2),
      quota: quotaInfo ? {
        used: quotaInfo.usage,
        total: quotaInfo.quota,
        usedMB: (quotaInfo.usage / (1024 * 1024)).toFixed(2),
        totalMB: (quotaInfo.quota / (1024 * 1024)).toFixed(2),
        percentUsed: ((quotaInfo.usage / quotaInfo.quota) * 100).toFixed(1)
      } : null
    };
  }

  /**
   * Save audio for offline playback (Phase 3)
   * @param {string} bookId - Book ID
   * @param {number} pageNumber - Page number
   * @param {string|Blob} audioData - Either a URL to fetch or a Blob directly
   */
  async saveAudioForOffline(bookId, pageNumber, audioData) {
    await this.ensureDb();

    try {
      let audioBlob;
      
      // Check if audioData is already a Blob
      if (audioData instanceof Blob) {
        audioBlob = audioData;
      } else {
        // It's a URL, fetch it
        const response = await fetch(audioData);
        audioBlob = await response.blob();
      }

      const tx = this.db.transaction(STORE_AUDIO, 'readwrite');
      const store = tx.objectStore(STORE_AUDIO);

      await new Promise((resolve, reject) => {
        const request = store.put({
          id: `${bookId}_audio_${pageNumber}`,
          bookId: bookId,
          pageNumber: pageNumber,
          audioBlob: audioBlob,
          savedAt: Date.now()
        });
        request.onsuccess = resolve;
        request.onerror = () => reject(request.error);
      });

      return { success: true };
    } catch (error) {
      console.error('Failed to save audio offline:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Get offline audio for a page
   */
  async getOfflineAudio(bookId, pageNumber) {
    await this.ensureDb();

    return new Promise((resolve) => {
      const tx = this.db.transaction(STORE_AUDIO, 'readonly');
      const store = tx.objectStore(STORE_AUDIO);
      const request = store.get(`${bookId}_audio_${pageNumber}`);

      request.onsuccess = () => {
        const audio = request.result;
        if (audio && audio.audioBlob) {
          const url = URL.createObjectURL(audio.audioBlob);
          resolve({ success: true, url: url, blob: audio.audioBlob });
        } else {
          resolve({ success: false });
        }
      };

      request.onerror = () => resolve({ success: false });
    });
  }
}

// Singleton instance
const offlineStorage = new OfflineStorageService();

export default offlineStorage;
export { OfflineStorageService };
