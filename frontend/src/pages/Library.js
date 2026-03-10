import { useState, useEffect, lazy, Suspense, useRef, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { FiSearch, FiBook, FiHeadphones, FiUser, FiStar, FiAward, FiTrendingUp, FiGrid, FiInfo, FiRefreshCw, FiBookOpen, FiWifiOff, FiDownload } from 'react-icons/fi';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { toast } from 'sonner';
import Navbar from '@/components/Navbar';
import BookRecommendations from '@/components/BookRecommendations';
import { getThumbnailUrl, preloadImages, AZORIES_PLACEHOLDER, handleImageError } from '@/utils/imageOptimizer';
import { AZORA_ASSETS } from '@/components/AzoraMascot';
import { useAuth } from '@/context/AuthContext';
import useOffline from '@/hooks/useOffline';
import SaveOfflineButton from '@/components/SaveOfflineButton';

// ============================================
// THUMBNAIL CACHING UTILITIES
// ============================================

// Cache for preloaded images (persists during session)
const imageCache = new Map();

// Optimized Cloudinary URL generator with aggressive compression
const getOptimizedThumbnailUrl = (url, width = 300) => {
  if (!url) return url;
  if (url.includes('res.cloudinary.com')) {
    // Super aggressive optimization for fast loading:
    // f_auto = best format (webp/avif)
    // q_auto:eco = economy quality (smaller files, still looks good)
    // w_X = resize to width
    // c_limit = don't upscale
    // fl_progressive = progressive loading
    // dpr_1.0 = force 1x DPI (prevents 2x/3x on retina)
    return url.replace('/upload/', `/upload/f_auto,q_auto:eco,w_${width},c_limit,fl_progressive,dpr_1.0/`);
  }
  return url;
};

// Preload image and cache it
const preloadAndCacheImage = (url, width = 250) => {
  if (!url || imageCache.has(url)) return Promise.resolve();

  const optimizedUrl = getOptimizedThumbnailUrl(url, width);

  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      imageCache.set(url, true);
      resolve();
    };
    img.onerror = () => resolve(); // Don't fail on error
    img.src = optimizedUrl;
  });
};

// Session storage cache for book data
const CACHE_KEY = 'azories_library_cache';
const CACHE_VERSION = 'v2'; // Increment to invalidate old caches
const CACHE_EXPIRY = 5 * 60 * 1000; // 5 minutes

const getBookCache = () => {
  try {
    const cached = sessionStorage.getItem(CACHE_KEY);
    if (cached) {
      const parsed = JSON.parse(cached);
      // Check version and expiry
      if (parsed.version === CACHE_VERSION &&
          parsed.timestamp &&
          Date.now() - parsed.timestamp < CACHE_EXPIRY) {
        return parsed.data;
      }
      // Invalid cache - clear it
      sessionStorage.removeItem(CACHE_KEY);
    }
  } catch (e) {
    // Corrupted cache - clear it
    try { sessionStorage.removeItem(CACHE_KEY); } catch {}
  }
  return null;
};

const setBookCache = (data) => {
  try {
    sessionStorage.setItem(CACHE_KEY, JSON.stringify({
      version: CACHE_VERSION,
      data,
      timestamp: Date.now()
    }));
  } catch (e) {
    // Ignore cache errors
  }
};

// ============================================
// LAZY IMAGE COMPONENT WITH CACHING
// ============================================

// Lazy-loaded image component with blur-up placeholder, caching, and purple shimmer
const LazyImage = ({ src, alt, className, placeholderColor, thumbnailWidth = 250, priority = false }) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);
  const imgRef = useRef(null);

  // Check if already cached for instant display
  const isCached = useMemo(() => imageCache.has(src), [src]);

  // Get optimized thumbnail URL with aggressive Cloudinary optimization
  const optimizedSrc = useMemo(() => {
    return getOptimizedThumbnailUrl(src, thumbnailWidth);
  }, [src, thumbnailWidth]);

  // Tiny placeholder for blur-up effect (20px wide, heavily compressed)
  const tinyPlaceholder = useMemo(() => {
    if (!src || !src.includes('res.cloudinary.com')) return null;
    return src.replace('/upload/', '/upload/f_auto,q_10,w_20,e_blur:500/');
  }, [src]);

  // Handle successful image load
  const handleLoad = useCallback(() => {
    setIsLoaded(true);
    imageCache.set(src, true);
  }, [src]);

  // Generate a color based on the alt text for consistent placeholder
  const getPlaceholderGradient = useCallback(() => {
    if (placeholderColor) return placeholderColor;
    const colors = [
      'from-purple-500/40 to-pink-500/40',
      'from-purple-400/40 to-indigo-500/40',
      'from-violet-500/40 to-purple-400/40',
      'from-indigo-400/40 to-purple-500/40',
      'from-purple-600/40 to-violet-400/40',
      'from-fuchsia-400/40 to-purple-500/40',
    ];
    const index = alt ? alt.charCodeAt(0) % colors.length : 0;
    return colors[index];
  }, [alt, placeholderColor]);

  return (
    <div ref={imgRef} className={`relative ${className}`}>
      {/* Blur-up placeholder or shimmer skeleton - only show if not cached */}
      {!isLoaded && !hasError && !isCached && (
        <>
          {tinyPlaceholder ? (
            <img
              src={tinyPlaceholder}
              alt=""
              className="absolute inset-0 w-full h-full object-cover scale-105 blur-sm"
              aria-hidden="true"
            />
          ) : (
            <div className={`absolute inset-0 bg-gradient-to-br ${getPlaceholderGradient()} overflow-hidden`}>
              <div className="absolute inset-0 -translate-x-full animate-[shimmer_1.5s_infinite] bg-gradient-to-r from-transparent via-white/20 to-transparent" />
              <div className="absolute inset-0 flex items-center justify-center">
                <FiBook className="w-10 h-10 text-white/40" />
              </div>
            </div>
          )}
        </>
      )}

      {/* Actual image - always render, use native lazy loading or eager for priority */}
      {!hasError && (
        <img
          src={optimizedSrc}
          alt={alt}
          className={`w-full h-full object-cover transition-opacity duration-200 ${isLoaded || isCached ? 'opacity-100' : 'opacity-0'}`}
          onLoad={handleLoad}
          onError={() => setHasError(true)}
          loading={priority ? "eager" : "lazy"}
          decoding="async"
          fetchPriority={priority ? "high" : "auto"}
        />
      )}

      {/* Error fallback - Azories branded placeholder */}
      {hasError && (
        <img
          src={AZORIES_PLACEHOLDER}
          alt={alt}
          className="absolute inset-0 w-full h-full object-cover"
        />
      )}
    </div>
  );
};

// Lazy load the 3D component
// 3D Library - Re-enabled
const ImmersiveLibrary3D = lazy(() => import('@/components/ImmersiveLibrary3D'));

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Custom hook for debounced value
const useDebounce = (value, delay = 300) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
};

export default function Library() {
  const [books, setBooks] = useState([]);
  const [featuredBooks, setFeaturedBooks] = useState([]);
  const [bestOfWeek, setBestOfWeek] = useState([]);
  const [newlyAddedBooks, setNewlyAddedBooks] = useState([]);
  const [comingSoonBooks, setComingSoonBooks] = useState([]);
  const [continueReadingBooks, setContinueReadingBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [initialLoadComplete, setInitialLoadComplete] = useState(false);
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 300); // Debounce search input
  const [genre, setGenre] = useState('All');
  const [ageRange, setAgeRange] = useState('All');
  const [genres, setGenres] = useState([]);
  const [activeTab, setActiveTab] = useState('all');
  const [viewMode, setViewMode] = useState('grid'); // 'grid', '3d', or 'immersive'
  const [selectedBook, setSelectedBook] = useState(null);
  const [summaryBook, setSummaryBook] = useState(null);
  const [showBackToTop, setShowBackToTop] = useState(false);
  const [showOfflineOnly, setShowOfflineOnly] = useState(false); // Offline filter
  const navigate = useNavigate();
  const { user, token } = useAuth();

  // Offline support
  const {
    isOnline,
    offlineBooks,
    isBookOffline,
    saveBookOffline,
    removeBookOffline,
    hasOfflineNarration,
    getOfflineBook
  } = useOffline();

  // State for offline books with cover URLs (created from blobs)
  const [offlineBooksWithCovers, setOfflineBooksWithCovers] = useState([]);
  const offlineCoverUrlsRef = useRef(new Map()); // Track created URLs for cleanup

  // Load offline books with cover images when showOfflineOnly is enabled or offlineBooks changes
  useEffect(() => {
    async function loadOfflineBooksWithCovers() {
      if (offlineBooks.length === 0) {
        setOfflineBooksWithCovers([]);
        return;
      }

      const booksWithCovers = await Promise.all(
        offlineBooks.map(async (book) => {
          try {
            // Get full offline book data including coverBlob/coverBuffer
            const fullOfflineBook = await getOfflineBook(book.id);

            let coverUrl = book.coverUrl; // Fallback to stored URL

            // getOfflineBook (fixed version) converts coverBuffer -> coverBlob automatically.
            // Also handle legacy records that stored coverBlob directly.
            const coverBlob = fullOfflineBook?.coverBlob;
            if (coverBlob) {
              // Revoke old URL if exists
              if (offlineCoverUrlsRef.current.has(book.id)) {
                URL.revokeObjectURL(offlineCoverUrlsRef.current.get(book.id));
              }
              coverUrl = URL.createObjectURL(coverBlob);
              offlineCoverUrlsRef.current.set(book.id, coverUrl);
            }

            return {
              id: book.id,
              title: book.title,
              cover_image: coverUrl,
              author_name: book.authorName,
              child_name: book.childName,
              pageCount: book.pageCount,
              hasNarration: book.hasNarration,
              savedAt: book.savedAt,
              sizeBytes: book.sizeBytes,
              // Mark as offline-loaded for display purposes
              _isOfflineBook: true
            };
          } catch (err) {
            console.warn(`Failed to load cover for offline book ${book.id}:`, err);
            return {
              id: book.id,
              title: book.title,
              cover_image: book.coverUrl,
              author_name: book.authorName,
              _isOfflineBook: true
            };
          }
        })
      );

      setOfflineBooksWithCovers(booksWithCovers);
    }

    loadOfflineBooksWithCovers();

    // Cleanup Object URLs on unmount
    return () => {
      offlineCoverUrlsRef.current.forEach((url) => URL.revokeObjectURL(url));
      offlineCoverUrlsRef.current.clear();
    };
  }, [offlineBooks, getOfflineBook]);

  // Fetch Continue Reading books for logged-in users
  const fetchContinueReading = useCallback(async () => {
    if (!user || !token) {
      setContinueReadingBooks([]);
      return;
    }
    try {
      const res = await axios.get(`${API}/continue-reading`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setContinueReadingBooks(res.data.books || []);
    } catch (error) {
      console.error('Error fetching continue reading:', error);
      setContinueReadingBooks([]);
    }
  }, [user, token]);

  // Fetch continue reading when user logs in
  useEffect(() => {
    if (user && token) {
      fetchContinueReading();
    }
  }, [user, token, fetchContinueReading]);

  // Handle scroll to show/hide back to top button
  useEffect(() => {
    const handleScroll = () => {
      // Check both window scroll and body scroll for compatibility
      const scrollPos = window.scrollY || document.documentElement.scrollTop || document.body.scrollTop;
      setShowBackToTop(scrollPos > 500);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    document.body.addEventListener('scroll', handleScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', handleScroll);
      document.body.removeEventListener('scroll', handleScroll);
    };
  }, []);

  // Scroll to top function
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    document.body.scrollTo({ top: 0, behavior: 'smooth' });
    document.documentElement.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Age range options
  const AGE_RANGES = ['All', '0-3', '4-6', '7-9', '10-12', '13+'];

  // Reusable function to fetch library data
  const fetchLibraryData = useCallback(async (skipCache = false) => {
    // Check cache first for instant display - but ONLY if it has valid books
    if (!skipCache) {
      const cached = getBookCache();
      const hasValidCache = cached &&
                           cached.books &&
                           Array.isArray(cached.books) &&
                           cached.books.length > 0;

      if (hasValidCache) {
        setBooks(cached.books);
        setFeaturedBooks(cached.featuredBooks || []);
        setBestOfWeek(cached.bestOfWeek || []);
        setNewlyAddedBooks(cached.newlyAddedBooks || []);
        setComingSoonBooks(cached.comingSoonBooks || []);
        setGenres(cached.genres || ['All']);
        setLoading(false);
        setLoadError(false);
        setInitialLoadComplete(true);

        // Preload images from cache
        const allCoverUrls = [
          ...(cached.books || []).map(b => b.cover_image),
          ...(cached.featuredBooks || []).map(b => b.cover_image),
          ...(cached.newlyAddedBooks || []).map(b => b.cover_image),
        ].filter(Boolean).slice(0, 12);
        allCoverUrls.forEach(url => preloadAndCacheImage(url, 300));

        return; // Use cache, skip network fetch
      }
    }

    // No valid cache or skip cache - fetch from server
    setLoading(true);
    setLoadError(false);

    try {
      // OPTIMIZATION: Fetch main books first for instant display, then others
      // This reduces perceived load time significantly
      const mainBooksPromise = axios.get(`${API}/books?published_only=true&limit=50`);
      const secondaryPromises = Promise.allSettled([
          axios.get(`${API}/books/featured`),
          axios.get(`${API}/books/newly-added`),
          axios.get(`${API}/books/coming-soon`),
          axios.get(`${API}/genres`)
        ]);

      const cacheData = {};

      // Process main books IMMEDIATELY when they arrive
      try {
        const mainBooksRes = await mainBooksPromise;
        const booksData = mainBooksRes.data || [];
        setBooks(booksData);
        cacheData.books = booksData;
        // Set loading false AS SOON AS main books arrive
        setLoading(false);
        // Preload first 8 cover images
        booksData.slice(0, 8).forEach(b => {
          if (b.cover_image) preloadAndCacheImage(b.cover_image, 300);
        });
      } catch (mainError) {
        console.error('Main books fetch failed:', mainError);
        setLoadError(true);
      }

      // Process secondary data in background (doesn't block initial render)
      const results = await secondaryPromises;

        if (results[0].status === 'fulfilled') {
          const featuredData = results[0].value.data || [];
          const featured = featuredData.filter(b => b.is_featured);
          const bestWeek = featuredData.filter(b => b.is_best_of_week);
          setFeaturedBooks(featured);
          setBestOfWeek(bestWeek);
          cacheData.featuredBooks = featured;
          cacheData.bestOfWeek = bestWeek;
          // Preload featured images
          featured.slice(0, 4).forEach(b => {
            if (b.cover_image) preloadAndCacheImage(b.cover_image, 300);
          });
        }

        if (results[1].status === 'fulfilled') {
          const newlyAdded = results[1].value.data || [];
          setNewlyAddedBooks(newlyAdded);
          cacheData.newlyAddedBooks = newlyAdded;
          // Preload newly added images
          newlyAdded.slice(0, 4).forEach(b => {
            if (b.cover_image) preloadAndCacheImage(b.cover_image, 300);
          });
        }

        if (results[2].status === 'fulfilled') {
          const comingSoon = results[2].value.data || [];
          setComingSoonBooks(comingSoon);
          cacheData.comingSoonBooks = comingSoon;
        }

        if (results[3].status === 'fulfilled' && results[3].value.data?.genres) {
          const genresData = ['All', ...results[3].value.data.genres];
          setGenres(genresData);
          cacheData.genres = genresData;
        } else {
          setGenres(['All']); // Fallback
          cacheData.genres = ['All'];
        }

        // Only cache if we got valid books data
        if (cacheData.books && cacheData.books.length > 0) {
          setBookCache(cacheData);
          setLoadError(false);
        } else if (books.length === 0) {
          // No books loaded at all - show error state
          setLoadError(true);
        }

      } catch (error) {
        console.error('Error loading library data:', error);
        // On error, try a simple fallback fetch
        try {
          const fallbackRes = await axios.get(`${API}/books?published_only=true&limit=50`);
          if (fallbackRes.data && fallbackRes.data.length > 0) {
            setBooks(fallbackRes.data);
            setLoadError(false);
          } else {
            setLoadError(true);
          }
        } catch (fallbackError) {
          console.error('Fallback fetch also failed:', fallbackError);
          setLoadError(true);
        }
      } finally {
        // Loading already set to false when main books arrived
        // Just ensure initialLoadComplete is set
        setInitialLoadComplete(true);
      }
  }, []);

  // Initial data fetch - runs once on mount
  useEffect(() => {
    fetchLibraryData();
  }, [fetchLibraryData]);

  // Retry handler for when loading fails
  const handleRetry = useCallback(() => {
    // Clear cache and refetch
    try { sessionStorage.removeItem('azories_library_cache'); } catch {}
    toast.info('Refreshing library...');
    fetchLibraryData(true); // Skip cache
  }, [fetchLibraryData]);

  // Search/filter changes - only run after initial load is complete
  useEffect(() => {
    if (!initialLoadComplete) return; // Skip if initial load not done
    if (activeTab !== 'all') return; // Only fetch when on 'all' tab

    // Skip if all filters are at default values (initial load already fetched this)
    const hasActiveFilters = debouncedSearch || genre !== 'All' || ageRange !== 'All';
    if (!hasActiveFilters) return;

    const fetchFilteredBooks = async () => {
      try {
        setLoading(true);
        const params = new URLSearchParams();
        if (debouncedSearch) params.append('search', debouncedSearch);
        if (genre && genre !== 'All') params.append('genre', genre);
        if (ageRange && ageRange !== 'All') params.append('age_rating', ageRange);
        params.append('published_only', 'true');
        params.append('limit', '12');

        const res = await axios.get(`${API}/books?${params.toString()}`);
        setBooks(res.data || []);
      } catch (error) {
        console.error('Error fetching filtered books:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchFilteredBooks();
  }, [debouncedSearch, genre, ageRange, activeTab, initialLoadComplete]);

  // Check if a book is new (published in last 7 days)
  const isNewBook = (book) => {
    if (!book.published_at && !book.created_at) return false;
    const publishDate = new Date(book.published_at || book.created_at);
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
    return publishDate > sevenDaysAgo;
  };

  // Filter books based on offline toggle
  const displayBooks = useMemo(() => {
    if (showOfflineOnly) return offlineBooksWithCovers;
    // When offline, patch cover URLs for saved books so thumbnails show from IndexedDB
    if (!isOnline && offlineBooksWithCovers.length > 0) {
      const offlineCoverMap = new Map(offlineBooksWithCovers.map(b => [b.id, b.cover_image]));
      return books.map(b => {
        const offlineCover = offlineCoverMap.get(b.id);
        return offlineCover ? { ...b, cover_image: offlineCover } : b;
      });
    }
    return books;
  }, [books, showOfflineOnly, offlineBooksWithCovers, isOnline]);

  // Filter featured, newly added, etc. based on offline toggle
  const displayFeaturedBooks = useMemo(() => {
    if (!showOfflineOnly) return featuredBooks;
    // When offline only, don't show featured section - just show all offline books in main grid
    return [];
  }, [featuredBooks, showOfflineOnly]);

  const displayNewlyAddedBooks = useMemo(() => {
    if (!showOfflineOnly) return newlyAddedBooks;
    return [];
  }, [newlyAddedBooks, showOfflineOnly]);

  const displayBestOfWeek = useMemo(() => {
    if (!showOfflineOnly) return bestOfWeek;
    return [];
  }, [bestOfWeek, showOfflineOnly]);

  const BookCard = ({ book, index, isFeatured = false, isComingSoon = false }) => {
    const isNew = isNewBook(book);

    const handleClick = () => {
      if (isComingSoon) {
        toast.info('This story is almost ready — check back soon! 🐉');
        return;
      }
      navigate(`/read/${book.id}`);
    };

    return (
      <div
        className="book-card group cursor-pointer"
        onClick={handleClick}
        data-testid={`book-card-${book.id}`}
      >
        <div className="book-perspective">
          <div className={`relative bg-card rounded-3xl overflow-hidden border border-border book-3d ${isFeatured ? 'ring-2 ring-primary/50' : ''} ${isComingSoon ? 'opacity-90' : ''}`}>
          {/* Summary/Back cover button - Top Right (always visible, not just hover) */}
          {!isComingSoon && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                e.preventDefault();
                setSummaryBook(book);
              }}
              className="absolute top-3 right-3 z-30 w-10 h-10 rounded-full bg-black/60 hover:bg-black/80 active:bg-black/90 active:scale-95 text-white flex items-center justify-center transition-all duration-200 touch-manipulation cursor-pointer"
              style={{ 
                pointerEvents: 'auto',
                touchAction: 'manipulation',
                WebkitTapHighlightColor: 'transparent'
              }}
              title="View Summary"
              aria-label="View book summary"
              data-testid={`summary-btn-${book.id}`}
            >
              <FiInfo className="w-5 h-5" />
            </button>
          )}

          {/* NEW badge for recently published - positioned below info button */}
          {isNew && !isComingSoon && (
            <div className="absolute top-12 right-3 z-20">
              <span className="px-2 py-1 rounded-full bg-green-500 text-white text-xs font-bold animate-pulse">
                NEW
              </span>
            </div>
          )}

          {/* Coming Soon overlay */}
          {isComingSoon && (
            <div className="absolute inset-0 z-30 flex items-center justify-center bg-black/40 backdrop-blur-sm">
              <div className="text-center">
                <span className="px-4 py-2 rounded-full bg-purple-600 text-white text-sm font-bold">
                  Coming Soon
                </span>
                {book.coming_soon_label && (
                  <p className="mt-2 text-white/80 text-xs">{book.coming_soon_label}</p>
                )}
              </div>
            </div>
          )}

          {/* Featured/Best badges */}
          {(book.is_featured || book.is_best_of_week) && !isComingSoon && (
            <div className="absolute top-3 left-3 z-10 flex gap-2">
              {book.is_featured && (
                <span className="px-3 py-1 rounded-full bg-primary text-primary-foreground text-xs font-ui flex items-center gap-1">
                  <FiStar className="w-3 h-3" /> Featured
                </span>
              )}
              {book.is_best_of_week && (
                <span className="px-3 py-1 rounded-full bg-secondary text-secondary-foreground text-xs font-ui flex items-center gap-1">
                  <FiAward className="w-3 h-3" /> Best of Week
                </span>
              )}
            </div>
          )}

          {/* Offline indicator - show if book is saved offline */}
          {isBookOffline(book.id) && !isComingSoon && (
            <div className="absolute top-3 right-12 z-20 flex gap-1">
              <span className="px-2 py-1 rounded-full bg-purple-600/90 text-white text-xs font-medium flex items-center gap-1" title="Available offline">
                <FiWifiOff className="w-3 h-3" />
              </span>
              {hasOfflineNarration(book.id) && (
                <span className="px-2 py-1 rounded-full bg-green-600/90 text-white text-xs font-medium flex items-center gap-1" title="Narration cached">
                  <FiHeadphones className="w-3 h-3" />
                </span>
              )}
            </div>
          )}

          {/* Book Cover */}
          <div className={`aspect-[3/4] relative overflow-hidden bg-muted/30 ${isComingSoon ? 'filter blur-[4px]' : ''}`}>
            {book.cover_image ? (
              <LazyImage
                src={book.cover_image}
                alt={book.title}
                className="w-full h-full"
                thumbnailWidth={250}
                priority={index < 8} // Eagerly load first 8 books for faster initial render
              />
            ) : (
              <div className="w-full h-full bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center">
                <div className="text-center p-4">
                  <FiBook className="w-12 h-12 mx-auto text-primary/40 mb-2" />
                  <span className="font-heading text-lg text-primary/60">{book.cover_title || book.title}</span>
                </div>
              </div>
            )}

            {/* Hover overlay */}
            <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center gap-4">
              <Button
                className="rounded-full"
                onClick={(e) => {
                  e.stopPropagation();
                  navigate(`/read/${book.id}`);
                }}
                data-testid={`read-btn-${book.id}`}
              >
                <FiBook className="mr-2" />
                Read
              </Button>
              <Button
                variant="secondary"
                className="rounded-full"
                onClick={(e) => {
                  e.stopPropagation();
                  navigate(`/read/${book.id}?audio=true`);
                }}
                data-testid={`listen-btn-${book.id}`}
              >
                <FiHeadphones className="mr-2" />
                Listen
              </Button>
            </div>
          </div>

          {/* Book Info */}
          <div className="p-5 space-y-2">
            <h3 className="font-heading text-lg font-semibold line-clamp-1">
              {book.title}
            </h3>
            <p className="font-body text-sm text-muted-foreground line-clamp-2">
              {book.description || 'A magical story awaits...'}
            </p>
            <div className="flex items-center justify-between pt-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <FiUser className="w-4 h-4" />
                <span className="font-ui">{book.author_name}</span>
              </div>
              <span className="text-xs px-3 py-1 rounded-full bg-primary/10 text-primary font-ui">
                {book.genre}
              </span>
            </div>

            {/* Save for Offline Button - Centered on mobile */}
            {!isComingSoon && (
              <div className="mt-3 flex justify-center" onClick={(e) => e.stopPropagation()}>
                <SaveOfflineButton
                  book={book}
                  isOffline={isBookOffline(book.id)}
                  onSave={saveBookOffline}
                  onRemove={removeBookOffline}
                  compact={false}
                  showLabel={true}
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
    );
  };

  // Skeleton loader for book cards
  const BookCardSkeleton = () => (
    <div className="book-card">
      <div className="book-perspective">
        <div className="relative bg-card rounded-3xl overflow-hidden border border-border">
          <div className="relative aspect-[3/4] bg-gradient-to-br from-purple-400/20 to-pink-400/20 animate-pulse">
            <div className="absolute inset-0 flex items-center justify-center">
              <FiBook className="w-10 h-10 text-white/30" />
            </div>
          </div>
          <div className="p-4 space-y-2">
            <div className="h-4 bg-muted/50 rounded animate-pulse" />
            <div className="h-3 bg-muted/30 rounded w-2/3 animate-pulse" />
          </div>
        </div>
      </div>
    </div>
  );

  // Skeleton section for horizontal scroll
  const SectionSkeleton = ({ title, icon }) => (
    <div className="mb-12">
      <div className="flex items-center gap-3 mb-6">
        <span className="text-2xl">{icon}</span>
        <div className="h-6 w-32 bg-muted/50 rounded animate-pulse" />
      </div>
      <div className="flex gap-6 overflow-x-auto pb-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="flex-shrink-0 w-48">
            <BookCardSkeleton />
          </div>
        ))}
      </div>
    </div>
  );

  const FeaturedSection = ({ title, icon, books: sectionBooks, emptyMessage }) => {
    // Show skeleton while loading on initial load
    if (loading && sectionBooks.length === 0) {
      return (
        <div className="mb-16">
          <div className="flex items-center gap-3 mb-6">
            {icon}
            <h2 className="font-heading text-2xl font-bold">{title}</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <BookCardSkeleton key={i} />
            ))}
          </div>
        </div>
      );
    }

    return (
      <div className="mb-16">
        <div className="flex items-center gap-3 mb-6">
          {icon}
          <h2 className="font-heading text-2xl font-bold">{title}</h2>
        </div>
        {sectionBooks.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {sectionBooks.map((book, index) => (
              <BookCard key={book.id} book={book} index={index} isFeatured />
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center text-center py-12 bg-muted/30 rounded-3xl">
            <motion.img
              src={AZORA_ASSETS.readingCozy}
              alt="Azora reading"
              className="w-32 h-40 object-contain mb-4 opacity-70"
              animate={{ y: [0, -5, 0] }}
              transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
            />
            <p className="text-muted-foreground font-body">{emptyMessage}</p>
          </div>
        )}
      </div>
    );
  };

  // Newly Added Section - Horizontal scroll row
  const NewlyAddedSection = () => {
    // Show skeleton while loading
    if (loading && displayNewlyAddedBooks.length === 0) {
      return <SectionSkeleton title="Newly Added" icon="🆕" />;
    }

    if (displayNewlyAddedBooks.length === 0) return null;

    return (
      <div className="mb-12">
        <div className="flex items-center gap-3 mb-6">
          <span className="text-2xl">🆕</span>
          <h2 className="font-heading text-2xl font-bold">Newly Added</h2>
          <span className="text-sm text-muted-foreground">({displayNewlyAddedBooks.length} new stories)</span>
        </div>
        <div className="relative">
          <div className="flex gap-6 overflow-x-auto pb-4 scrollbar-thin scrollbar-thumb-primary/30 scrollbar-track-transparent">
            {displayNewlyAddedBooks.map((book, index) => (
              <div key={book.id} className="flex-shrink-0 w-48">
                <BookCard book={book} index={index} />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  // Coming Soon Section - Horizontal scroll row with blurred cards
  const ComingSoonSection = () => {
    // Show skeleton while loading
    if (loading && comingSoonBooks.length === 0) {
      return <SectionSkeleton title="Coming Soon" icon="👀" />;
    }

    if (comingSoonBooks.length === 0) return null;

    return (
      <div className="mb-12">
        <div className="flex items-center gap-3 mb-6">
          <span className="text-2xl">👀</span>
          <h2 className="font-heading text-2xl font-bold">Coming Soon</h2>
          <span className="text-sm text-muted-foreground">Sneak peek at upcoming stories!</span>
        </div>
        <div className="relative">
          <div className="flex gap-6 overflow-x-auto pb-4 scrollbar-thin scrollbar-thumb-primary/30 scrollbar-track-transparent">
            {comingSoonBooks.map((book, index) => (
              <div key={book.id} className="flex-shrink-0 w-48">
                <BookCard book={book} index={index} isComingSoon />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      {/* Header - no opacity animation to prevent purple flash */}
      <div className="pt-32 pb-8 px-6 md:px-12">
        <div className="max-w-7xl mx-auto">
          <div>
            <h1 className="font-heading text-4xl md:text-5xl font-bold mb-4">
              Explore the Library
            </h1>
            <p className="font-body text-lg text-muted-foreground mb-8">
              Discover magical stories created by young authors
            </p>
          </div>
        </div>
      </div>

      {/* Tabs and Content */}
      <div className="px-6 md:px-12 pb-20">
        <div className="max-w-7xl mx-auto">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="mb-8 bg-muted/50 p-1 rounded-full inline-flex flex-wrap sm:flex-nowrap gap-1">
              <TabsTrigger
                value="all"
                className="rounded-full px-3 sm:px-6 text-sm sm:text-base data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
                data-testid="tab-all-books"
              >
                All Books
              </TabsTrigger>
              <TabsTrigger
                value="featured"
                className="rounded-full px-3 sm:px-6 text-sm sm:text-base data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
                data-testid="tab-featured"
              >
                <FiStar className="mr-1 sm:mr-2 w-3 h-3 sm:w-4 sm:h-4" />
                Featured
              </TabsTrigger>
              <TabsTrigger
                value="best"
                className="rounded-full px-3 sm:px-6 text-sm sm:text-base data-[state=active]:bg-primary data-[state=active]:text-primary-foreground whitespace-nowrap"
                data-testid="tab-best-week"
              >
                <FiAward className="mr-1 sm:mr-2 w-3 h-3 sm:w-4 sm:h-4" />
                <span className="sm:hidden">Top</span>
                <span className="hidden sm:inline">Best of Week</span>
              </TabsTrigger>
            </TabsList>

            <TabsContent value="all">
              {/* Search, Filters, and View Toggle */}
              <div className="flex flex-col sm:flex-row gap-4 mb-8">
                <div className="relative flex-1 max-w-md">
                  <FiSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    type="text"
                    placeholder="Search by title or author..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-12 rounded-full border-2 h-12"
                    data-testid="library-search-input"
                  />
                </div>

                <Select value={genre} onValueChange={setGenre}>
                  <SelectTrigger
                    className="w-full sm:w-48 rounded-full border-2 h-12"
                    data-testid="genre-select"
                  >
                    <SelectValue placeholder="Genre" />
                  </SelectTrigger>
                  <SelectContent>
                    {genres.map((g) => (
                      <SelectItem key={g} value={g} data-testid={`genre-option-${g}`}>
                        {g}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                {/* Age Range Filter */}
                <Select value={ageRange} onValueChange={setAgeRange}>
                  <SelectTrigger
                    className="w-full sm:w-40 rounded-full border-2 h-12"
                    data-testid="age-range-select"
                  >
                    <SelectValue placeholder="Age Range" />
                  </SelectTrigger>
                  <SelectContent>
                    {AGE_RANGES.map((age) => (
                      <SelectItem key={age} value={age} data-testid={`age-option-${age}`}>
                        {age === 'All' ? 'All Ages' : `${age} years`}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                {/* Offline Filter Toggle */}
                {offlineBooks.length > 0 && (
                  <Button
                    variant={showOfflineOnly ? 'default' : 'outline'}
                    onClick={() => setShowOfflineOnly(!showOfflineOnly)}
                    className={`rounded-full h-12 px-4 gap-2 ${showOfflineOnly ? 'bg-purple-600 hover:bg-purple-700' : ''}`}
                    data-testid="offline-filter-btn"
                    title={showOfflineOnly ? 'Show all books' : 'Show offline books only'}
                  >
                    <FiWifiOff className="w-4 h-4" />
                    <span className="hidden sm:inline">Offline</span>
                    <span className="text-xs bg-white/20 px-1.5 py-0.5 rounded-full">{offlineBooks.length}</span>
                  </Button>
                )}

                {/* View Mode Toggle */}
                <div className="flex gap-2 bg-muted/50 p-1 rounded-full items-center">
                  <Button
                    variant={viewMode === 'grid' ? 'default' : 'ghost'}
                    size="icon"
                    onClick={() => setViewMode('grid')}
                    className="rounded-full w-10 h-10"
                    data-testid="view-grid-btn"
                    title="Grid View"
                  >
                    <FiGrid className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* 3D Grand Library Promotional Card - Only show in grid view when not searching */}
              {viewMode === 'grid' && !debouncedSearch && (
                <div
                  className="mb-8 relative overflow-hidden rounded-3xl cursor-pointer group"
                  onClick={() => setViewMode('immersive')}
                  data-testid="grand-library-promo"
                >
                  <div className="relative h-40 sm:h-48 md:h-64 overflow-hidden">
                    {/* Background Image */}
                    <img
                      src="https://res.cloudinary.com/dlbmjqmoy/image/upload/v1772378060/azories/library/grand_library_entrance.jpg"
                      alt="Grand Library"
                      className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                    />
                    {/* Gradient Overlay */}
                    <div className="absolute inset-0 bg-gradient-to-r from-black/80 via-black/50 to-transparent" />

                    {/* Content */}
                    <div className="absolute inset-0 flex items-center p-4 sm:p-8 md:p-12">
                      <div className="max-w-lg">
                        <div className="flex items-center gap-2 mb-2 sm:mb-3">
                          <span className="px-2 sm:px-3 py-1 bg-purple-500/30 backdrop-blur-sm rounded-full text-purple-300 text-[10px] sm:text-xs font-medium">
                            IMMERSIVE
                          </span>
                        </div>
                        <h3 className="text-lg sm:text-2xl md:text-4xl font-serif font-bold text-white mb-1 sm:mb-3">
                          Enter the Grand Library
                        </h3>
                        <p className="text-white/70 text-xs sm:text-sm md:text-base mb-2 sm:mb-4 max-w-md line-clamp-2 sm:line-clamp-none">
                          Walk through towering bookshelves in our magical 3D library.
                        </p>
                        <Button
                          size="sm"
                          className="rounded-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white shadow-lg shadow-purple-500/30 group-hover:scale-105 transition-transform text-xs sm:text-sm"
                        >
                          <FiBook className="mr-1 sm:mr-2 w-3 h-3 sm:w-4 sm:h-4" />
                          Explore
                        </Button>
                      </div>
                    </div>

                    {/* Floating particles effect */}
                    <div className="absolute inset-0 pointer-events-none">
                      <div className="absolute top-1/4 right-1/4 w-2 h-2 bg-yellow-400/60 rounded-full animate-pulse" />
                      <div className="absolute top-1/2 right-1/3 w-1 h-1 bg-purple-400/60 rounded-full animate-ping" style={{ animationDelay: '0.5s' }} />
                      <div className="absolute bottom-1/3 right-1/2 w-1.5 h-1.5 bg-pink-400/60 rounded-full animate-pulse" style={{ animationDelay: '1s' }} />
                    </div>
                  </div>
                </div>
              )}

              {/* Immersive 3D Gothic Library View */}
              {viewMode === 'immersive' ? (
                <Suspense fallback={
                  <div className="w-full h-[700px] rounded-3xl bg-black flex items-center justify-center">
                    <div className="text-center space-y-4">
                      <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
                      <p className="text-white text-lg">Loading Gothic Library...</p>
                      <p className="text-white/60 text-sm">Preparing an immersive experience</p>
                    </div>
                  </div>
                }>
                  <ImmersiveLibrary3D
                    books={books}
                    onClose={() => setViewMode('grid')}
                    onSelectBook={(book) => navigate(`/read/${book.id}`)}
                  />
                </Suspense>
              ) : (
              /* Books Grid with Recommendations */
              <>
              {/* Continue Reading Section - Show only for logged-in users with progress */}
              {!debouncedSearch && user && continueReadingBooks.length > 0 && (
                <div className="mb-10" data-testid="continue-reading-section">
                  <div className="flex items-center gap-3 mb-5">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center">
                      <FiBookOpen className="w-5 h-5 text-white" />
                    </div>
                    <h2 className="text-xl sm:text-2xl font-heading font-bold">Continue Reading</h2>
                  </div>

                  {/* Horizontal scroll container */}
                  <div className="relative">
                    <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-hide snap-x snap-mandatory">
                      {continueReadingBooks.map((item, index) => (
                        <div
                          key={item.book_id}
                          className="flex-shrink-0 w-48 sm:w-56 snap-start cursor-pointer group"
                          onClick={() => navigate(`/read/${item.book_id}`)}
                          data-testid={`continue-book-${item.book_id}`}
                        >
                          <div className="relative rounded-2xl overflow-hidden bg-card border border-border shadow-lg transition-all duration-300 group-hover:shadow-xl group-hover:-translate-y-1">
                            {/* Cover Image */}
                            <div className="aspect-[3/4] relative">
                              <img
                                src={getOptimizedThumbnailUrl(item.cover_image, 220)}
                                alt={item.title}
                                className="w-full h-full object-cover"
                                loading={index < 3 ? 'eager' : 'lazy'}
                              />
                              {/* Progress overlay */}
                              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 via-black/60 to-transparent p-3 pt-8">
                                <div className="w-full bg-white/20 rounded-full h-1.5 mb-1">
                                  <div
                                    className="bg-gradient-to-r from-emerald-400 to-teal-400 h-1.5 rounded-full transition-all"
                                    style={{ width: `${item.progress_percent}%` }}
                                  />
                                </div>
                                <p className="text-white/80 text-xs">
                                  Page {item.current_page + 1} of {item.total_pages}
                                </p>
                              </div>
                            </div>

                            {/* Book Info */}
                            <div className="p-3">
                              <h3 className="font-semibold text-sm line-clamp-1 mb-0.5">{item.title}</h3>
                              <p className="text-xs text-muted-foreground line-clamp-1">{item.author_name}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Newly Added Section - Show at top when not searching */}
              {!debouncedSearch && (
                <NewlyAddedSection />
              )}

              {/* Coming Soon Section - Show after Newly Added */}
              {!debouncedSearch && (
                <ComingSoonSection />
              )}

              {/* Recommendations Section - Hide when searching */}
              {!debouncedSearch && (
                <div className="mb-12">
                  <BookRecommendations />
                </div>
              )}

              {/* Search Results Header - Show when searching */}
              {debouncedSearch && (
                <div className="mb-6">
                  <h2 className="text-xl font-semibold text-foreground">
                    Search results for "{debouncedSearch}"
                  </h2>
                  <p className="text-muted-foreground text-sm mt-1">
                    {books.length} {books.length === 1 ? 'book' : 'books'} found
                  </p>
                </div>
              )}

              {/* Books Grid */}
              {loading ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
                  {[...Array(8)].map((_, i) => (
                    <div key={i} className="rounded-3xl overflow-hidden">
                      <div className="aspect-[3/4] shimmer" />
                      <div className="p-5 space-y-3">
                        <div className="h-6 w-3/4 shimmer rounded" />
                        <div className="h-4 w-full shimmer rounded" />
                        <div className="h-4 w-1/2 shimmer rounded" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : displayBooks.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
                  {displayBooks.map((book, index) => (
                    <BookCard key={book.id} book={book} index={index} />
                  ))}
                </div>
              ) : (
                <div className="text-center py-20">
                  <motion.img
                    src={AZORA_ASSETS.readingCozy}
                    alt="Azora searching"
                    className="w-36 h-44 object-contain mx-auto mb-4 opacity-70"
                    animate={{ y: [0, -8, 0] }}
                    transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                  />
                  <h3 className="font-heading text-xl text-muted-foreground">
                    {loadError ? 'Oops! Something went wrong' : showOfflineOnly ? 'No offline books' : 'No books found'}
                  </h3>
                  <p className="font-body text-muted-foreground mt-2">
                    {loadError
                      ? 'We couldn\'t load the library. Please try again.'
                      : showOfflineOnly
                        ? 'Save some books for offline reading first!'
                        : 'Try adjusting your search or filters'
                    }
                  </p>
                  {loadError && (
                    <Button
                      onClick={handleRetry}
                      className="mt-4 gap-2"
                      data-testid="retry-load-btn"
                    >
                      <FiRefreshCw className="w-4 h-4" />
                      Retry
                    </Button>
                  )}
                </div>
              )}
              </>
              )}
            </TabsContent>

            <TabsContent value="featured">
              <FeaturedSection
                title="Featured Books"
                icon={<FiStar className="w-6 h-6 text-primary" />}
                books={featuredBooks}
                emptyMessage="No featured books at the moment. Check back soon!"
              />
            </TabsContent>

            <TabsContent value="best">
              <FeaturedSection
                title="Best of the Week"
                icon={<FiAward className="w-6 h-6 text-secondary" />}
                books={bestOfWeek}
                emptyMessage="Best of the week books will appear here!"
              />
            </TabsContent>
          </Tabs>
        </div>
      </div>

      {/* Summary/Back Cover Popup Dialog */}
      <Dialog open={!!summaryBook} onOpenChange={() => setSummaryBook(null)}>
        <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-heading text-2xl flex items-center gap-2">
              <FiBook className="text-primary" />
              {summaryBook?.title}
            </DialogTitle>
            <DialogDescription className="font-body text-sm">
              By {summaryBook?.author_name} • {summaryBook?.genre}
            </DialogDescription>
          </DialogHeader>
          <div className="pt-4 space-y-4">
            {/* Layout: Image on left, Summary on right for larger screens */}
            <div className="flex flex-col md:flex-row gap-4">
              {/* Back cover image if exists */}
              {summaryBook?.back_cover_image && (
                <div className="md:w-1/3 flex-shrink-0">
                  <div className="rounded-xl overflow-hidden aspect-[3/4]">
                    <LazyImage
                      src={summaryBook.back_cover_image}
                      alt="Back cover"
                      className="w-full h-full"
                    />
                  </div>
                </div>
              )}

              {/* Summary text */}
              <div className={`flex-1 ${summaryBook?.back_cover_image ? '' : 'w-full'}`}>
                <div className="p-4 rounded-xl bg-muted/50 space-y-3 h-full">
                  <h4 className="font-heading font-semibold text-sm text-muted-foreground uppercase tracking-wide">Summary</h4>
                  <p 
                    className="font-body text-base leading-relaxed select-text cursor-text"
                    style={{ userSelect: 'text', WebkitUserSelect: 'text' }}
                  >
                    {summaryBook?.back_cover_text || summaryBook?.description || 'A magical story awaits you...'}
                  </p>
                </div>
              </div>
            </div>

            {/* Quick info */}
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              {summaryBook?.age_rating && summaryBook.age_rating !== 'All Ages' && (
                <span className="px-3 py-1 rounded-full bg-primary/10 text-primary font-ui">
                  {summaryBook.age_rating}
                </span>
              )}
              <span className="font-ui flex items-center gap-1">
                <FiUser className="w-4 h-4" />
                {summaryBook?.author_name}
              </span>
            </div>

            {/* Action buttons */}
            <div className="flex gap-3 pt-2">
              <Button
                className="flex-1 rounded-full hidden sm:flex"
                onClick={() => {
                  setSummaryBook(null);
                  navigate(`/read/${summaryBook?.id}`);
                }}
                data-testid="summary-read-btn"
              >
                <FiBook className="mr-2" />
                Start Reading
              </Button>
              <Button
                variant="outline"
                className="flex-1 rounded-full hidden sm:flex"
                onClick={() => {
                  setSummaryBook(null);
                  navigate(`/read/${summaryBook?.id}?audio=true`);
                }}
                data-testid="summary-listen-btn"
              >
                <FiHeadphones className="mr-2" />
                Listen
              </Button>
              {/* Mobile: Single centered button to read */}
              <Button
                className="w-full rounded-full sm:hidden"
                onClick={() => {
                  setSummaryBook(null);
                  navigate(`/read/${summaryBook?.id}`);
                }}
                data-testid="summary-read-mobile-btn"
              >
                <FiBook className="mr-2" />
                Read Story
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Back to Top Button */}
      {showBackToTop && (
        <motion.button
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.8 }}
          onClick={scrollToTop}
          className="fixed bottom-20 sm:bottom-8 right-4 sm:right-8 z-50 p-3 sm:p-4 bg-purple-600 hover:bg-purple-700 text-white rounded-full shadow-lg transition-colors"
          data-testid="back-to-top-btn"
          aria-label="Back to top"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5 sm:h-6 sm:w-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
          </svg>
        </motion.button>
      )}
    </div>
  );
}
