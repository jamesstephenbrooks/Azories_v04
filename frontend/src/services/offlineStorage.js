/**
 * Offline Storage Service for Azories
 * Uses IndexedDB to store book content for offline reading
 *
 * FIXES in this version:
 * 1. Blobs converted to ArrayBuffer for iOS Safari compatibility
 * 2. Single atomic transaction for books + pages (no split state)
 * 3. removeBookOffline properly awaits transaction completion
 * 4. ensureDb() guards against concurrent init race condition
 * 5. All ArrayBuffers converted back to Blob on read
 */

const DB_NAME = 'azories-offline';
const DB_VERSION = 2; // Bumped to trigger onupgradeneeded for schema fix
const STORE_BOOKS = 'books';
const STORE_PAGES = 'pages';
const STORE_AUDIO = 'audio';

// FIX 1: iOS Safari cannot reliably store Blobs in IndexedDB.
// Convert to ArrayBuffer before storing, back to Blob when reading.
async function blobToArrayBuffer(blob) {
  if (!blob) return null;
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(reader.error);
    reader.readAsArrayBuffer(blob);
  });
}

function arrayBufferToBlob(buffer, mimeType = 'application/octet-stream') {
  if (!buffer) return null;
  return new Blob([buffer], { type: mimeType });
}

class OfflineStorageService {
  constructor() {
    this.db = null;
    this.isSupported = 'indexedDB' in window;
    this._initPromise = null; // FIX 4: guard against concurrent init
  }

  async init() {
    if (!this.isSupported) {
      console.warn('IndexedDB not supported');
      return false;
    }

    // FIX 4: If init is already running, return the same promise
    if (this._initPromise) return this._initPromise;

    this._initPromise = new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => {
        console.error('Failed to open IndexedDB:', request.error);
        this._initPromise = null;
        reject(request.error);
      };

      request.onsuccess = () => {
        this.db = request.result;
        resolve(true);
      };

      // FIX 5: Handle both fresh install (v1) and upgrade from v1 -> v2
      request.onupgradeneeded = (event) => {
        const db = event.target.result;

        if (!db.objectStoreNames.contains(STORE_BOOKS)) {
          const booksStore = db.createObjectStore(STORE_BOOKS, { keyPath: 'id' });
          booksStore.createIndex('savedAt', 'savedAt', { unique: false });
        }

        if (!db.objectStoreNames.contains(STORE_PAGES)) {
          const pagesStore = db.createObjectStore(STORE_PAGES, { keyPath: 'id' });
          pagesStore.createIndex('bookId', 'bookId', { unique: false });
        }

        if (!db.objectStoreNames.contains(STORE_AUDIO)) {
          const audioStore = db.createObjectStore(STORE_AUDIO, { keyPath: 'id' });
          audioStore.createIndex('bookId', 'bookId', { unique: false });
        }
      };
    });

    return this._initPromise;
  }

  async ensureDb() {
    if (!this.db) {
      await this.init();
    }
    if (!this.db) throw new Error('IndexedDB unavailable');
    return this.db;
  }

  /**
   * Save a book for offline reading
   */
  async saveBookForOffline(book, onProgress = () => {}, options = { includeAudio: true }) {
    await this.ensureDb();

    const bookId = book.id;
    const pages = book.pages || [];
    const includeAudio = options.includeAudio !== false;

    const audioPages = includeAudio ? pages.filter(p => p.audio_url) : [];
    const totalItems = 1 + pages.length + audioPages.length;
    let savedItems = 0;
    let totalBytes = 0;

    try {
      // --- Step 1: Fetch cover image ---
      let coverBuffer = null;
      let coverMime = 'image/jpeg';
      if (book.cover_image) {
        try {
          onProgress(savedItems, totalItems, 'Downloading cover...');
          const coverResponse = await fetch(book.cover_image);
          const blob = await coverResponse.blob();
          coverMime = blob.type || 'image/jpeg';
          // FIX 1: Store as ArrayBuffer
          coverBuffer = await blobToArrayBuffer(blob);
          totalBytes += coverBuffer.byteLength;
        } catch (e) {
          console.warn('Failed to fetch cover image:', e);
        }
      }
      savedItems++;
      onProgress(savedItems, totalItems, 'Cover saved');

      // --- Step 2: Fetch page images ---
      const pageData = [];
      for (let i = 0; i < pages.length; i++) {
        const page = pages[i];
        let imageBuffer = null;
        let imageMime = 'image/jpeg';
        const imageUrl = page.image_url || page.illustration_url;

        if (imageUrl) {
          try {
            onProgress(savedItems, totalItems, `Downloading page ${i + 1} image...`);
            const response = await fetch(imageUrl);
            const blob = await response.blob();
            imageMime = blob.type || 'image/jpeg';
            // FIX 1: Store as ArrayBuffer
            imageBuffer = await blobToArrayBuffer(blob);
            totalBytes += imageBuffer.byteLength;
          } catch (e) {
            console.warn(`Failed to fetch image for page ${i + 1}:`, e);
          }
        }

        pageData.push({
          id: `${bookId}_page_${page.page_number ?? i}`,
          bookId: bookId,
          pageNumber: page.page_number ?? i,
          imageBuffer: imageBuffer,   // ArrayBuffer instead of Blob
          imageMime: imageMime,
          imageUrl: imageUrl,
          textContent: page.text_content || page.text || '',
          title: page.title || '',
          hasAudio: !!page.audio_url,
        });

        savedItems++;
        onProgress(savedItems, totalItems, `Page ${i + 1}/${pages.length} saved`);
      }

      // --- Step 3: Fetch audio ---
      // FIX 2: Audio saved in its own transaction, still before main tx
      // but now we collect all audio data first before any DB writes
      const audioData = [];
      if (includeAudio && audioPages.length > 0) {
        for (let i = 0; i < audioPages.length; i++) {
          const page = audioPages[i];
          const pageNumber = page.page_number ?? pages.indexOf(page);

          try {
            onProgress(savedItems, totalItems, `Downloading narration ${i + 1}/${audioPages.length}...`);
            const audioResponse = await fetch(page.audio_url);
            const audioBlob = await audioResponse.blob();
            const audioBuffer = await blobToArrayBuffer(audioBlob);
            totalBytes += audioBuffer.byteLength;

            audioData.push({
              id: `${bookId}_audio_${pageNumber}`,
              bookId: bookId,
              pageNumber: pageNumber,
              audioBuffer: audioBuffer,   // ArrayBuffer instead of Blob
              audioMime: audioBlob.type || 'audio/mpeg',
              audioUrl: page.audio_url,
              savedAt: Date.now()
            });
          } catch (e) {
            console.warn(`Failed to cache audio for page ${pageNumber}:`, e);
          }

          savedItems++;
          onProgress(savedItems, totalItems, `Narration ${i + 1}/${audioPages.length} saved`);
        }
      }

      // --- Step 4: Write everything to IndexedDB atomically ---
      // FIX 2: Single transaction for books + pages ensures consistency
      await new Promise((resolve, reject) => {
        const tx = this.db.transaction([STORE_BOOKS, STORE_PAGES], 'readwrite');
        const booksStore = tx.objectStore(STORE_BOOKS);
        const pagesStore = tx.objectStore(STORE_PAGES);

        tx.oncomplete = resolve;
        tx.onerror = () => reject(tx.error);
        tx.onabort = () => reject(new Error('Transaction aborted'));

        // Save book metadata
        booksStore.put({
          id: bookId,
          title: book.title,
          coverBuffer: coverBuffer,
          coverMime: coverMime,
          coverUrl: book.cover_image,
          pageCount: pages.length,
          audioPageCount: audioPages.length,
          hasNarration: audioPages.length > 0,
          authorName: book.author_name || book.child_name,
          childName: book.child_name,
          savedAt: Date.now(),
          sizeBytes: totalBytes,
          status: 'complete'
        });

        // Save all pages
        for (const page of pageData) {
          pagesStore.put(page);
        }
      });

      // Save audio in a separate transaction (audio store is separate)
      if (audioData.length > 0) {
        await new Promise((resolve, reject) => {
          const tx = this.db.transaction(STORE_AUDIO, 'readwrite');
          const audioStore = tx.objectStore(STORE_AUDIO);

          tx.oncomplete = resolve;
          tx.onerror = () => reject(tx.error);

          for (const audio of audioData) {
            audioStore.put(audio);
          }
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
      request.onerror = () => resolve(false);
    });
  }

  /**
   * Get offline book metadata
   * FIX 1: Converts stored ArrayBuffer back to Blob for coverBlob compatibility
   */
  async getOfflineBook(bookId) {
    await this.ensureDb();

    return new Promise((resolve) => {
      const tx = this.db.transaction(STORE_BOOKS, 'readonly');
      const store = tx.objectStore(STORE_BOOKS);
      const request = store.get(bookId);

      request.onsuccess = () => {
        const book = request.result;
        if (!book) return resolve(null);

        // Convert ArrayBuffer back to Blob for consumers expecting coverBlob
        if (book.coverBuffer) {
          book.coverBlob = arrayBufferToBlob(book.coverBuffer, book.coverMime || 'image/jpeg');
        }
        resolve(book);
      };
      request.onerror = () => resolve(null);
    });
  }

  /**
   * Get offline pages for a book
   * FIX 1: Converts stored ArrayBuffer back to Blob for imageBlob compatibility
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

        // Convert ArrayBuffer back to Blob for each page
        const converted = pages.map(page => {
          if (page.imageBuffer) {
            page.imageBlob = arrayBufferToBlob(page.imageBuffer, page.imageMime || 'image/jpeg');
          }
          return page;
        });

        converted.sort((a, b) => a.pageNumber - b.pageNumber);
        resolve(converted);
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
        // Don't return raw buffers in the list — just metadata
        const metadata = books
          .filter(b => b.status === 'complete')
          .map(({ coverBuffer, coverMime, ...rest }) => rest);
        resolve(metadata);
      };

      request.onerror = () => resolve([]);
    });
  }

  /**
   * Remove a book from offline storage
   * FIX 3: Properly awaits transaction completion before returning
   */
  async removeBookOffline(bookId) {
    await this.ensureDb();

    try {
      // Delete pages
      await new Promise((resolve, reject) => {
        const tx = this.db.transaction(STORE_PAGES, 'readwrite');
        const pagesStore = tx.objectStore(STORE_PAGES);
        const index = pagesStore.index('bookId');

        tx.oncomplete = resolve;
        tx.onerror = () => reject(tx.error);

        const request = index.getAllKeys(bookId);
        request.onsuccess = () => {
          request.result.forEach(key => pagesStore.delete(key));
        };
      });

      // Delete audio
      await new Promise((resolve, reject) => {
        const tx = this.db.transaction(STORE_AUDIO, 'readwrite');
        const audioStore = tx.objectStore(STORE_AUDIO);
        const index = audioStore.index('bookId');

        tx.oncomplete = resolve;
        tx.onerror = () => reject(tx.error);

        const request = index.getAllKeys(bookId);
        request.onsuccess = () => {
          request.result.forEach(key => audioStore.delete(key));
        };
      });

      // Delete book metadata last
      await new Promise((resolve, reject) => {
        const tx = this.db.transaction(STORE_BOOKS, 'readwrite');
        const booksStore = tx.objectStore(STORE_BOOKS);

        tx.oncomplete = resolve;
        tx.onerror = () => reject(tx.error);

        booksStore.delete(bookId);
      });

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
   * Save audio for offline playback
   * FIX 1: Stores as ArrayBuffer for iOS Safari compatibility
   */
  async saveAudioForOffline(bookId, pageNumber, audioData) {
    await this.ensureDb();

    try {
      let audioBlob;
      if (audioData instanceof Blob) {
        audioBlob = audioData;
      } else {
        const response = await fetch(audioData);
        audioBlob = await response.blob();
      }

      // FIX 1: Convert to ArrayBuffer
      const audioBuffer = await blobToArrayBuffer(audioBlob);
      const audioMime = audioBlob.type || 'audio/mpeg';

      await new Promise((resolve, reject) => {
        const tx = this.db.transaction(STORE_AUDIO, 'readwrite');
        const store = tx.objectStore(STORE_AUDIO);

        tx.oncomplete = resolve;
        tx.onerror = () => reject(tx.error);

        store.put({
          id: `${bookId}_audio_${pageNumber}`,
          bookId: bookId,
          pageNumber: pageNumber,
          audioBuffer: audioBuffer,
          audioMime: audioMime,
          savedAt: Date.now()
        });
      });

      return { success: true };
    } catch (error) {
      console.error('Failed to save audio offline:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Get offline audio for a page
   * FIX 1: Converts ArrayBuffer back to Blob before creating object URL
   */
  async getOfflineAudio(bookId, pageNumber) {
    await this.ensureDb();

    return new Promise((resolve) => {
      const tx = this.db.transaction(STORE_AUDIO, 'readonly');
      const store = tx.objectStore(STORE_AUDIO);
      const request = store.get(`${bookId}_audio_${pageNumber}`);

      request.onsuccess = () => {
        const audio = request.result;
        if (audio && audio.audioBuffer) {
          const blob = arrayBufferToBlob(audio.audioBuffer, audio.audioMime || 'audio/mpeg');
          const url = URL.createObjectURL(blob);
          resolve({ success: true, url: url, blob: blob });
        } else if (audio && audio.audioBlob) {
          // Backwards compat: handle old records that stored Blobs directly
          const url = URL.createObjectURL(audio.audioBlob);
          resolve({ success: true, url: url, blob: audio.audioBlob });
        } else {
          resolve({ success: false });
        }
      };

      request.onerror = () => resolve({ success: false });
    });
  }

  /**
   * Clear all offline data (useful for debugging / reset)
   */
  async clearAll() {
    await this.ensureDb();

    await new Promise((resolve, reject) => {
      const tx = this.db.transaction([STORE_BOOKS, STORE_PAGES, STORE_AUDIO], 'readwrite');
      tx.oncomplete = resolve;
      tx.onerror = () => reject(tx.error);
      tx.objectStore(STORE_BOOKS).clear();
      tx.objectStore(STORE_PAGES).clear();
      tx.objectStore(STORE_AUDIO).clear();
    });

    return { success: true };
  }
}

// Singleton instance
const offlineStorage = new OfflineStorageService();

export default offlineStorage;
export { OfflineStorageService };
