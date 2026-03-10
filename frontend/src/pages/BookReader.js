import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { useAuth } from '@/context/AuthContext';
import { 
  FiArrowLeft, FiChevronLeft, FiChevronRight, FiChevronUp, FiChevronDown,
  FiMaximize2, FiMinimize2, FiPlay, FiPause, FiVolume2, FiVolumeX, 
  FiSun, FiMoon, FiLock, FiBook, FiAward, FiTrendingUp, FiMic, FiX,
  FiPrinter, FiDownload, FiShare2, FiHome, FiBookmark, FiPackage, FiWifiOff,
  FiEdit2, FiLoader
} from 'react-icons/fi';
import confetti from 'canvas-confetti';
import { useTheme } from '@/context/ThemeContext';
import AmbientSound from '@/components/AmbientSound';
import AIReadingBuddy from '@/components/AIReadingBuddy';
import { useSwipeGestures } from '@/hooks/useSwipeGestures';
import RealisticPageFlip from '@/components/RealisticPageFlip';
import PWAPrompt from '@/components/PWAPrompt';
import { AZORA_ASSETS } from '@/components/AzoraMascot';
import PrintOrderModal from '@/components/PrintOrderModal';
import useOffline from '@/hooks/useOffline';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function BookReader() {
  const { bookId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const { user, token, loading: authLoading, logout, refreshUser } = useAuth();
  const audioRef = useRef(null);
  
  // Offline support for audio caching
  const { isOnline, isBookOffline, getOfflineAudio, saveAudioOffline, getOfflineBook, getOfflinePages } = useOffline();
  const [isOfflineMode, setIsOfflineMode] = useState(false);
  
  const [book, setBook] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(-1); // -1 = front cover
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isFlipping, setIsFlipping] = useState(false);
  const [flipDirection, setFlipDirection] = useState('next');
  const [requiresAuth, setRequiresAuth] = useState(false);
  const [showRotatePrompt, setShowRotatePrompt] = useState(false);
  const [forceLandscapeTest, setForceLandscapeTest] = useState(false); // TEMP: For testing landscape mode
  const [showScrollIndicator, setShowScrollIndicator] = useState(false);
  const textScrollRef = useRef(null);
  const textScrollRefLandscape = useRef(null);
  
  // Continue Reading state
  const [showContinuePrompt, setShowContinuePrompt] = useState(false);
  const [savedPageNumber, setSavedPageNumber] = useState(0);
  
  // Audio state
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioLoading, setAudioLoading] = useState(false);
  const [audioElement, setAudioElement] = useState(null);
  const [volume, setVolume] = useState([75]);
  const [playbackSpeed, setPlaybackSpeed] = useState([1]);
  const [autoRead, setAutoRead] = useState(false);  // OFF by default - user clicks Read/Listen to enable
  const [narrationPreparing, setNarrationPreparing] = useState(false); // Show "Preparing narration..." message
  const [narrationReady, setNarrationReady] = useState(false); // First few pages are cached
  const [audioProgress, setAudioProgress] = useState(0); // 0 to 1 - for auto-scroll sync
  
  // IPAD FIX: Persistent audio element - created once on user interaction, reused for all pages
  // This preserves the "user interaction" permission that iPad Safari requires for autoplay
  const persistentAudioRef = useRef(null);
  const audioUnlockedRef = useRef(false); // Track if audio has been unlocked by user tap
  
  // Audio cache for pre-loading upcoming pages
  const audioCache = useRef(new Map()); // pageIndex -> audio base64
  const preloadingPages = useRef(new Set()); // pages currently being preloaded
  
  // Track which page audio has been played for - prevents duplicate playback
  const lastPlayedPageRef = useRef(-999);
  
  // Cleanup tracking refs
  const abortControllerRef = useRef(null);
  const activeTimeoutsRef = useRef(new Set());
  const mountedRef = useRef(true);
  
  // Helper to create tracked timeout
  const safeTimeout = useCallback((callback, delay) => {
    const timeoutId = setTimeout(() => {
      activeTimeoutsRef.current.delete(timeoutId);
      if (mountedRef.current) {
        callback();
      }
    }, delay);
    activeTimeoutsRef.current.add(timeoutId);
    return timeoutId;
  }, []);
  
  // Helper to clear all active timeouts
  const clearAllTimeouts = useCallback(() => {
    activeTimeoutsRef.current.forEach(id => clearTimeout(id));
    activeTimeoutsRef.current.clear();
  }, []);
  
  // Track blob URLs for cleanup
  const blobUrlsRef = useRef(new Map());
  
  // Helper to get image source - handles offline blobs
  const getImageSource = useCallback((page) => {
    if (!page) return null;
    
    // If we have an offline blob, create/reuse object URL
    if (page.offline_image_blob) {
      const pageKey = page.id || page.pageNumber;
      if (!blobUrlsRef.current.has(pageKey)) {
        const blobUrl = URL.createObjectURL(page.offline_image_blob);
        blobUrlsRef.current.set(pageKey, blobUrl);
      }
      return blobUrlsRef.current.get(pageKey);
    }
    
    // Otherwise use the regular URL
    return page.image_url || page.imageUrl;
  }, []);
  
  // Cleanup blob URLs on unmount
  useEffect(() => {
    return () => {
      blobUrlsRef.current.forEach(url => URL.revokeObjectURL(url));
      blobUrlsRef.current.clear();
    };
  }, []);
  
  // Comprehensive cleanup function (called on unmount AND before navigation)
  // This is CRITICAL for preventing memory leaks when navigating between books
  const performFullCleanup = useCallback(() => {
    console.log('[BookReader] Performing full cleanup...');
    
    // 1. Abort ALL pending API requests immediately
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      // Don't set to null - let the next useEffect create a fresh one
    }
    
    // 2. Stop audio but don't destroy persistent element (for iPad compatibility)
    if (audioElement) {
      try {
        audioElement.pause();
        audioElement.onended = null;
        audioElement.onerror = null;
        audioElement.oncanplay = null;
        audioElement.onloadeddata = null;
      } catch (e) {
        console.log('[BookReader] Audio cleanup error (safe to ignore):', e);
      }
    }
    
    // Also stop persistent audio if it exists
    if (persistentAudioRef.current) {
      try {
        persistentAudioRef.current.pause();
        persistentAudioRef.current.onended = null;
      } catch (e) {}
    }
    
    // 3. Clear ALL cached audio objects (these can hold memory)
    audioCache.current.forEach((cached) => {
      if (cached && cached.audio) {
        try {
          cached.audio.pause();
          cached.audio.src = '';
        } catch (e) {}
      }
    });
    audioCache.current.clear();
    preloadingPages.current.clear();
    
    // 4. Clear all timeouts
    clearAllTimeouts();
    
    // 5. Reset tracking refs to prevent stale callbacks
    lastPlayedPageRef.current = -999;
    
    console.log('[BookReader] Cleanup complete');
  }, [audioElement, clearAllTimeouts]);

  // Handler for navigating back to library - MUST cleanup before navigation
  const handleBackToLibrary = useCallback(() => {
    console.log('[BookReader] Back button clicked - cleaning up before navigation');
    performFullCleanup();
    // Small delay to ensure cleanup completes before React unmounts
    setTimeout(() => {
      navigate('/library');
    }, 10);
  }, [performFullCleanup, navigate]);

  const [allPages, setAllPages] = useState([]);
  const [narratorVoice, setNarratorVoice] = useState('');
  const [narratorVoiceLocked, setNarratorVoiceLocked] = useState(false);
  const [voices, setVoices] = useState([]);  // Available voices for selection
  
  // Reading progress
  const [readingProgress, setReadingProgress] = useState(0);
  const [readingStats, setReadingStats] = useState(null);
  
  // AI Reading Buddy
  const [showAIBuddy, setShowAIBuddy] = useState(false);
  
  // Hide controls (for iPad immersive mode)
  const [hideControls, setHideControls] = useState(false);
  
  // iOS audio unlock state
  const [iosAudioUnlocked, setIosAudioUnlocked] = useState(false);
  
  // Printable PDF state
  const [showPrintDialog, setShowPrintDialog] = useState(false);
  const [isPrinting, setIsPrinting] = useState(false);
  
  // Print-on-Demand order modal state (Gelato integration)
  const [showPrintOrderModal, setShowPrintOrderModal] = useState(false);
  
  // Book completion celebration state
  const [showCelebration, setShowCelebration] = useState(false);
  const hasShownCelebrationRef = useRef(false);
  
  // Realistic page flip mode - always enabled
  const realisticFlipRef = useRef(null);
  
  // Swipe state for visual feedback
  const [swipeHint, setSwipeHint] = useState(null);
  
  // Responsive window size for mobile/landscape
  const [windowSize, setWindowSize] = useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 1200,
    height: typeof window !== 'undefined' ? window.innerHeight : 800
  });
  
  // Dedicated orientation state using proper APIs for real device detection
  // This is a critical state that determines if we show split view vs two-page spread
  const [isLandscapeOrientation, setIsLandscapeOrientation] = useState(() => {
    if (typeof window === 'undefined') return false;
    // Use multiple detection methods and prefer dimension-based for reliability
    const matchMediaResult = window.matchMedia?.('(orientation: landscape)')?.matches;
    const dimensionResult = window.innerWidth > window.innerHeight;
    // On real devices, dimension check is most reliable after rotation completes
    console.log('[BookReader] Initial orientation:', { matchMediaResult, dimensionResult, width: window.innerWidth, height: window.innerHeight });
    return matchMediaResult ?? dimensionResult;
  });
  
  // Unique key to force re-render of page flip component on orientation change
  const [orientationKey, setOrientationKey] = useState(0);
  
  // iPad-specific detection - used to completely bypass react-pageflip
  // iPad has persistent issues with react-pageflip intercepting touch events
  // Solution: Use simple tap zones and buttons only on iPad
  const isIPad = useMemo(() => {
    if (typeof navigator === 'undefined') return false;
    const userAgent = navigator.userAgent || '';
    const platform = navigator.platform || '';
    const maxTouchPoints = navigator.maxTouchPoints || 0;
    
    // Detect iPad: explicit iPad user agent OR MacIntel with touch (iPad in desktop mode)
    const isIPadUA = /iPad/i.test(userAgent);
    const isIPadDesktopMode = platform === 'MacIntel' && maxTouchPoints > 1;
    
    const result = isIPadUA || isIPadDesktopMode;
    if (result) {
      console.log('[BookReader] iPad detected - using tap zones instead of swipe');
    }
    return result;
  }, []);
  
  // iPhone detection - need navigation buttons but can keep swipe enabled
  const isIPhone = useMemo(() => {
    if (typeof navigator === 'undefined') return false;
    const userAgent = navigator.userAgent || '';
    const result = /iPhone/i.test(userAgent);
    if (result) {
      console.log('[BookReader] iPhone detected - adding navigation buttons');
    }
    return result;
  }, []);
  
  // Listen to window resize for responsive book sizing
  useEffect(() => {
    const updateOrientation = () => {
      const newWidth = window.innerWidth;
      const newHeight = window.innerHeight;
      const matchMediaLandscape = window.matchMedia?.('(orientation: landscape)')?.matches ?? false;
      const dimensionLandscape = newWidth > newHeight;
      
      // Use dimension-based detection as primary (more reliable on real devices after rotation)
      // matchMedia can sometimes lag behind the actual viewport dimensions
      const isLandscape = dimensionLandscape;
      
      console.log('[BookReader] Orientation update:', { 
        matchMediaLandscape, 
        dimensionLandscape, 
        width: newWidth, 
        height: newHeight,
        finalIsLandscape: isLandscape 
      });
      
      setWindowSize({ width: newWidth, height: newHeight });
      setIsLandscapeOrientation(isLandscape);
      // Force re-render of pageflip component to recalculate dimensions
      setOrientationKey(prev => prev + 1);
    };
    
    // Debounced resize handler to avoid rapid updates during rotation
    let resizeTimeout;
    const handleResize = () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(updateOrientation, 100);
    };
    
    // Orientation change handler for real mobile devices
    // This fires when the device is physically rotated
    const handleOrientationChange = () => {
      console.log('[BookReader] orientationchange event fired');
      // On real devices, dimensions may not be updated immediately after orientationchange
      // Wait for the browser to complete the rotation animation
      setTimeout(updateOrientation, 150);
      // Also check again after a longer delay for slower devices
      setTimeout(updateOrientation, 350);
    };
    
    // Screen orientation API handler (modern browsers)
    const handleScreenOrientationChange = () => {
      try {
        console.log('[BookReader] screen.orientation change event fired:', screen?.orientation?.type);
      } catch (e) {
        console.log('[BookReader] screen.orientation change event fired');
      }
      setTimeout(updateOrientation, 150);
      setTimeout(updateOrientation, 350);
    };
    
    // matchMedia change handler (for DevTools and some browsers)
    const mediaQuery = window.matchMedia?.('(orientation: landscape)');
    const handleMediaChange = (e) => {
      console.log('[BookReader] matchMedia orientation change:', e.matches);
      updateOrientation();
    };
    
    // Add all event listeners
    window.addEventListener('resize', handleResize);
    window.addEventListener('orientationchange', handleOrientationChange);
    
    // Safely check for screen.orientation API
    try {
      if (typeof screen !== 'undefined' && screen.orientation && screen.orientation.addEventListener) {
        screen.orientation.addEventListener('change', handleScreenOrientationChange);
      }
    } catch (e) {
      // screen.orientation not available or throws
    }
    
    if (mediaQuery?.addEventListener) {
      mediaQuery.addEventListener('change', handleMediaChange);
    } else if (mediaQuery?.addListener) {
      mediaQuery.addListener(handleMediaChange);
    }
    
    // Initial check after mount (in case orientation changed during hydration)
    updateOrientation();
    
    return () => {
      clearTimeout(resizeTimeout);
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('orientationchange', handleOrientationChange);
      try {
        if (typeof screen !== 'undefined' && screen.orientation && screen.orientation.removeEventListener) {
          screen.orientation.removeEventListener('change', handleScreenOrientationChange);
        }
      } catch (e) {
        // Ignore cleanup errors
      }
      if (mediaQuery?.removeEventListener) {
        mediaQuery.removeEventListener('change', handleMediaChange);
      } else if (mediaQuery?.removeListener) {
        mediaQuery.removeListener(handleMediaChange);
      }
    };
  }, []);
  
  // Calculate responsive book dimensions
  const getBookDimensions = () => {
    const { width: vw, height: vh } = windowSize;
    // Use proper orientation detection instead of just comparing dimensions
    const isLandscape = isLandscapeOrientation || vw > vh;
    const isMobile = vw < 768 || vh < 500;
    const isTablet = (vw >= 768 && vw < 1024) || (vh >= 768 && vh < 1024);
    
    if (isFullscreen) {
      // Fullscreen mode - maximize usage
      if (isLandscape) {
        const bookWidth = Math.min(vw * 0.38, 700);
        const bookHeight = Math.min(vh * 0.85, 900);
        return { width: bookWidth, height: bookHeight };
      } else {
        const bookWidth = Math.min(vw * 0.45, 600);
        const bookHeight = Math.min(vh * 0.70, 800);
        return { width: bookWidth, height: bookHeight };
      }
    }
    
    // Normal mode - account for header and controls
    if (isMobile) {
      if (isLandscape) {
        // Mobile landscape - TWO PAGE SPREAD like a real book
        // Reserve minimal space for compact controls
        const reservedHeight = 100; // Compact header + controls
        const availableHeight = vh - reservedHeight;
        const bookHeight = Math.min(availableHeight * 0.92, 380);
        // Each page is roughly 0.7 aspect ratio, two pages side by side
        const bookWidth = Math.min(bookHeight * 0.72, vw * 0.42);
        return { width: bookWidth, height: bookHeight };
      } else {
        // Mobile portrait - SINGLE PAGE MODE - maximum immersion
        // Minimal reserved space: Header ~44px, controls ~80px, padding ~16px = ~140px
        const reservedSpace = 140;
        const availableHeight = vh - reservedSpace;
        const bookHeight = Math.min(availableHeight, 720);
        // Make book as wide as possible while maintaining good aspect ratio
        const bookWidth = Math.min(vw - 12, bookHeight * 0.82, 480);
        return { width: bookWidth, height: bookHeight };
      }
    }
    
    if (isTablet) {
      if (isLandscape) {
        // Tablet landscape (iPad)
        const bookWidth = Math.min(vw * 0.32, 450);
        const bookHeight = Math.min(vh * 0.65, 600);
        return { width: bookWidth, height: bookHeight };
      } else {
        // Tablet portrait
        const bookWidth = Math.min(vw * 0.40, 400);
        const bookHeight = Math.min(vh * 0.50, 550);
        return { width: bookWidth, height: bookHeight };
      }
    }
    
    // Desktop - Large immersive experience (fill 80% of screen height)
    if (isLandscape) {
      // Desktop landscape: book should be very large and fill most of the viewport
      // Target 80% of viewport height for the book
      const targetHeight = vh * 0.80;
      const availableHeight = vh - 100; // Minimal header + bottom controls
      const bookHeight = Math.max(Math.min(targetHeight, availableHeight), 700); // At least 700px
      // Each page width should maintain a book-like aspect ratio (roughly 0.65-0.7)
      // Spread width will be 2x this, so make sure spread fits in viewport
      // For a spread to fit, single page width should be max ~45% of viewport
      const bookWidth = Math.min(bookHeight * 0.70, vw * 0.42);
      return { width: bookWidth, height: bookHeight };
    } else {
      // Desktop portrait (rare case)
      const targetHeight = vh * 0.80;
      const availableHeight = vh - 100;
      const bookHeight = Math.max(Math.min(targetHeight, availableHeight), 650);
      const bookWidth = Math.min(bookHeight * 0.72, vw * 0.50);
      return { width: bookWidth, height: bookHeight };
    }
  };
  
  const bookDimensions = getBookDimensions();
  
  // Determine if we should use single-page (portrait) mode
  // Mobile portrait = single page, Mobile landscape = two-page spread
  // Uses proper orientation APIs for real device detection
  // forceLandscapeTest overrides for testing purposes
  const isMobile = windowSize.width < 768 || windowSize.height < 500;
  const isMobileLandscape = forceLandscapeTest || (isMobile && isLandscapeOrientation);
  const isMobilePortrait = !forceLandscapeTest && isMobile && !isLandscapeOrientation;
  
  // Show navigation buttons on touch devices (iPad, iPhone, and other mobile)
  const showMobileNavButtons = isIPad || isIPhone || isMobile;
  
  // Apply CSS to text containers for scroll support
  useEffect(() => {
    const selectors = '[data-scrollable="true"], .text-scroll-container, .overflow-y-auto';
    document.querySelectorAll(selectors).forEach((el) => {
      el.style.touchAction = 'pan-y';
      el.style.overflowY = 'auto';
      el.style.webkitOverflowScrolling = 'touch';
      el.style.pointerEvents = 'auto';
    });
  }, [isFullscreen, currentPage]);
  
  // Re-apply CSS after delay for late-rendered elements
  useEffect(() => {
    const timer = setTimeout(() => {
      document.querySelectorAll('[data-scrollable="true"], .text-scroll-container, .overflow-y-auto').forEach(el => {
        el.style.touchAction = 'pan-y';
        el.style.pointerEvents = 'auto';
      });
    }, 500);
    return () => clearTimeout(timer);
  }, [currentPage]);
  
  const isCover = currentPage === -1;
  const isBackCover = currentPage === -2;
  const totalPages = allPages.length;
  // Handle back cover: when currentPage is -2, get the last page (which has isBackCover: true)
  const currentPageData = currentPage >= 0 
    ? allPages[currentPage] 
    : (currentPage === -2 && allPages.length > 0 ? allPages[allPages.length - 1] : null);
  
  // Swipe gestures for page navigation
  // DISABLED on iPad - iPad uses tap zones and buttons only (no swipe conflicts)
  // CSS touch-action handles scroll vs swipe differentiation on other devices
  const swipeHandlers = useSwipeGestures({
    onSwipeLeft: () => {
      console.log('[SwipeHandler] onSwipeLeft triggered');
      if (currentPage < totalPages - 1 && !isFlipping) {
        setSwipeHint('next');
        setTimeout(() => setSwipeHint(null), 300);
        goToPage(currentPage + 1, 'next');
      }
    },
    onSwipeRight: () => {
      console.log('[SwipeHandler] onSwipeRight triggered');
      if (currentPage > -1 && !isFlipping) {
        setSwipeHint('prev');
        setTimeout(() => setSwipeHint(null), 300);
        goToPage(currentPage - 1, 'prev');
      }
    },
    threshold: 50,
    enabled: !isFlipping && !isIPad, // Disable swipe on iPad completely
    ignoreScrollableElements: false
  });

  useEffect(() => {
    // Mark component as mounted
    mountedRef.current = true;
    
    // IMPORTANT: Abort the PREVIOUS controller before creating a new one
    // This prevents the cleanup from aborting the NEW book's requests
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    // Create new AbortController for THIS book session
    abortControllerRef.current = new AbortController();
    
    // RESET ALL STATE for fresh book load - critical for multi-book navigation
    setBook(null);
    setLoading(true);
    setCurrentPage(-1);
    setAllPages([]);
    setAudioElement(null);
    setIsPlaying(false);
    setAudioLoading(false);
    setNarrationPreparing(false);
    setNarrationReady(false);
    setRequiresAuth(false);
    
    // Clear previous book's cache immediately when bookId changes
    audioCache.current.clear();
    preloadingPages.current.clear();
    lastPlayedPageRef.current = -999;
    autoReadRef.current = false;
    shouldStartPlayingRef.current = false;
    
    if (!authLoading) {
      // Ensure axios has the auth header set if user is logged in
      if (token && !axios.defaults.headers.common['Authorization']) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      }
      fetchBook();
      fetchVoices();
      if (user) {
        // Check for saved reading progress and prompt to continue
        fetchReadingProgress().then((savedPage) => {
          if (savedPage > 0) {
            setSavedPageNumber(savedPage);
            setShowContinuePrompt(true);
          }
        });
        fetchReadingStats();
      }
    }
    
    // CLEANUP when component unmounts or bookId changes
    return () => {
      console.log('[BookReader] Component unmounting or bookId changing, running cleanup');
      mountedRef.current = false;
      
      // Stop all audio immediately
      if (audioRef.current) {
        try {
          audioRef.current.pause();
          audioRef.current.src = '';
        } catch (e) {}
      }
      
      // Clear all caches and timeouts
      audioCache.current.clear();
      preloadingPages.current.clear();
      clearAllTimeouts();
      
      // Abort pending requests for THIS book (not the next one)
      // The next effect iteration will create a fresh controller
    };
  }, [bookId, user, authLoading, token, clearAllTimeouts]);

  // Ref to track if we should continue auto-reading
  // NOTE: Only update this ref explicitly, NOT on every render
  const autoReadRef = useRef(autoRead);
  // Sync ref with state ONLY when state intentionally changes (via useEffect)
  useEffect(() => {
    // Only update if this is a genuine state change (not initial render)
    // This prevents overwriting manually set ref values
    autoReadRef.current = autoRead;
  }, [autoRead]);
  
  // Pause narration when user leaves the page/app (switches tabs, goes to another app)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Page is hidden - pause audio and auto-read
        console.log('[Audio] Page hidden - pausing narration');
        if (audioRef.current) {
          try {
            audioRef.current.pause();
          } catch (e) {}
        }
        if (persistentAudioRef.current) {
          try {
            persistentAudioRef.current.pause();
          } catch (e) {}
        }
        setIsPlaying(false);
        // Keep autoRead state but stop current playback
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);
  
  // Ref to track current page for async operations
  const currentPageRef = useRef(currentPage);
  currentPageRef.current = currentPage;
  
  // Ref to trigger playback after listen button is clicked
  const shouldStartPlayingRef = useRef(false);

  // Save reading progress when page changes
  useEffect(() => {
    if (user && currentPage >= 0 && totalPages > 0) {
      saveReadingProgress();
    }
  }, [currentPage, user, totalPages]);
  
  const fetchVoices = async () => {
    try {
      const res = await axios.get(`${API}/voices`);
      setVoices(res.data);
    } catch (error) {
      console.error('Failed to load voices');
    }
  };

  const fetchBook = async (isRetry = false) => {
    try {
      // Check if component is still mounted
      if (!mountedRef.current) return;
      
      // Check if book is available offline first
      if (!isOnline || isBookOffline(bookId)) {
        console.log('[BookReader] Attempting to load offline book:', bookId);
        try {
          const offlineBook = await getOfflineBook(bookId);
          const offlinePages = await getOfflinePages(bookId);
          
          if (offlineBook && offlinePages && offlinePages.length > 0) {
            console.log('[BookReader] Loaded from offline storage:', offlineBook.title, offlinePages.length, 'pages');
            setIsOfflineMode(true);
            
            // Build book object from offline data
            // Create blob URL for cover if available
            let coverImageUrl = offlineBook.coverUrl;
            if (offlineBook.coverBlob) {
              coverImageUrl = URL.createObjectURL(offlineBook.coverBlob);
              blobUrlsRef.current.set('cover', coverImageUrl);
            }
            
            const bookData = {
              id: offlineBook.id,
              title: offlineBook.title,
              cover_image: coverImageUrl,
              author_name: offlineBook.authorName,
              child_name: offlineBook.childName,
              requires_auth: false,
              pages: offlinePages.map((page, index) => ({
                id: page.id,
                page_number: page.pageNumber || index,
                text_content: page.textContent || page.text_content || '',
                image_url: page.imageUrl || page.image_url,
                // Create object URL from blob for offline images
                offline_image_blob: page.imageBlob
              }))
            };
            
            if (!mountedRef.current) return;
            
            setBook(bookData);
            
            // Process pages for display
            const pages = bookData.pages.map((page, index) => ({
              ...page,
              chapterTitle: bookData.title,
              chapterNumber: 1
            }));
            
            setAllPages(pages);
            setRequiresAuth(false);
            
            // Check for continue reading position
            try {
              const savedPosition = localStorage.getItem(`azories-reading-${bookId}`);
              if (savedPosition) {
                const { page } = JSON.parse(savedPosition);
                if (page > 0 && page < pages.length) {
                  setSavedPageNumber(page);
                  setShowContinuePrompt(true);
                }
              }
            } catch (e) {}
            
            setLoading(false);
            return; // Successfully loaded offline
          }
        } catch (offlineError) {
          console.warn('[BookReader] Failed to load offline book:', offlineError);
        }
        
        // If we're offline and couldn't load from storage, show error
        if (!isOnline) {
          console.error('[BookReader] Offline and book not available');
          toast.error('This book is not available offline');
          setLoading(false);
          return;
        }
      }
      
      // Online mode - fetch from API
      // Ensure we have the latest token
      const currentToken = localStorage.getItem('azories-token');
      const headers = currentToken ? { Authorization: `Bearer ${currentToken}` } : {};
      
      console.log('[BookReader] Fetching book:', bookId);
      console.log('[BookReader] Auth token present:', !!currentToken);
      
      const res = await axios.get(`${API}/books/${bookId}/full`, {
        headers,
        signal: abortControllerRef.current?.signal
      });
      
      // DEBUG: Log raw API response
      console.log('[BookReader] RAW API Response:', {
        title: res.data.title,
        requires_auth: res.data.requires_auth,
        chapters_count: res.data.chapters?.length || 0,
        pages_in_chapter_1: res.data.chapters?.[0]?.pages?.length || 0,
        direct_pages_count: res.data.pages?.length || 0,
        first_page_image: res.data.chapters?.[0]?.pages?.[0]?.image_url?.substring(0, 50) || 'NO IMAGE'
      });
      
      // Check again after async operation
      if (!mountedRef.current) return;
      
      setBook(res.data);
      setNarratorVoice(res.data.narrator_voice_id || '21m00Tcm4TlvDq8ikWAM');
      setNarratorVoiceLocked(res.data.narrator_voice_locked || false);
      
      // Track book read event - fire and forget, never block
      try {
        const token = localStorage.getItem('azories-token');
        // Don't await - fire and forget
        axios.post(`${API}/analytics/track`, {
          event_type: 'book_read',
          book_id: bookId,
          page: `/read/${bookId}`,
          metadata: { title: res.data.title }
        }, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          signal: abortControllerRef.current?.signal,
          timeout: 5000 // 5s timeout
        }).catch(() => {}); // Silently ignore all errors
      } catch (e) {
        // Silently fail analytics
      }
      
      if (!mountedRef.current) return;
      
      if (res.data.requires_auth) {
        setRequiresAuth(true);
        setAllPages([]);
      } else {
        // Extract pages - prioritize pages array with content, fallback to chapters
        let pages = [];
        
        const directPages = res.data.pages || [];
        const chapters = res.data.chapters || [];
        
        // Check which source has more substantial text content
        const pagesHasContent = directPages.some(p => p.text_content && p.text_content.trim().length > 0);
        const chaptersHasContent = chapters.some(ch => 
          ch.pages?.some(p => p.text_content && p.text_content.trim().length > 0)
        );
        
        // Prefer pages array if it has content, otherwise use chapters
        if (pagesHasContent) {
          pages = directPages.map((page, index) => ({
            ...page,
            chapterTitle: res.data.title || 'Story',
            chapterNumber: 1
          }));
          console.log('[BookReader] Loaded', pages.length, 'pages from pages array');
        } else if (chaptersHasContent) {
          chapters.forEach((chapter, chapterIndex) => {
            chapter.pages?.forEach(page => {
              pages.push({ ...page, chapterTitle: chapter.title, chapterNumber: chapterIndex + 1 });
            });
          });
          console.log('[BookReader] Loaded', pages.length, 'pages from chapters');
        } else if (directPages.length > 0) {
          // Fallback to pages even without text (image-only books)
          pages = directPages.map((page, index) => ({
            ...page,
            chapterTitle: res.data.title || 'Story',
            chapterNumber: 1
          }));
          console.log('[BookReader] Loaded', pages.length, 'pages from pages (no text)');
        } else {
          console.log('[BookReader] NO PAGES FOUND! directPages:', directPages.length, 'chapters:', chapters.length);
          console.log('[BookReader] chaptersHasContent:', chaptersHasContent, 'pagesHasContent:', pagesHasContent);
        }
        
        console.log('[BookReader] Final pages count:', pages.length);
        if (pages.length > 0) {
          console.log('[BookReader] First page:', { 
            hasImage: !!pages[0].image_url, 
            hasText: !!pages[0].text_content,
            imageUrl: pages[0].image_url?.substring(0, 50)
          });
        }
        
        // Append back cover as final page if available
        if (res.data.back_cover_image) {
          pages.push({
            isBackCover: true,
            image_url: res.data.back_cover_image,
            text_content: '',
            chapterTitle: 'Back Cover',
            chapterNumber: 999
          });
          console.log('[BookReader] Back cover added. Total pages now:', pages.length);
        }
        
        console.log('[BookReader] Setting allPages with', pages.length, 'pages. Last page isBackCover:', pages[pages.length-1]?.isBackCover);
        setAllPages(pages);
        
        // Track read
        axios.post(`${API}/books/${bookId}/track-read`).catch(() => {});
        
        // Show rotate prompt on mobile portrait (once per SESSION, not per book)
        // Use proper orientation detection with safe access
        const promptKey = 'azories-rotate-prompt-shown';
        const hasSeenPromptThisSession = sessionStorage.getItem(promptKey);
        const isMobileDevice = window.innerWidth < 768 || window.innerHeight < 500;
        let isPortraitOrientation = window.innerWidth <= window.innerHeight;
        try {
          if (typeof screen !== 'undefined' && screen.orientation && screen.orientation.type) {
            isPortraitOrientation = screen.orientation.type.includes('portrait');
          } else if (window.matchMedia) {
            isPortraitOrientation = window.matchMedia('(orientation: portrait)').matches;
          }
        } catch (e) {
          // Fallback to dimension check already set
        }
        
        if (!hasSeenPromptThisSession && isMobileDevice && isPortraitOrientation) {
          setShowRotatePrompt(true);
          sessionStorage.setItem(promptKey, 'true');
          // Auto-hide after 4 seconds
          setTimeout(() => setShowRotatePrompt(false), 4000);
        }
      }
    } catch (error) {
      // Don't show error for aborted requests (component unmounted)
      if (error.name === 'CanceledError' || error.name === 'AbortError') {
        console.log('[BookReader] Fetch aborted (component unmounted)');
        return;
      }
      
      // Handle 401 - authentication required
      if (error.response?.status === 401) {
        console.log('[BookReader] 401 received, attempting to refresh session...');
        
        if (!isRetry && token) {
          // Try to refresh user session
          try {
            await refreshUser();
            console.log('[BookReader] Session refreshed, retrying fetch...');
            return fetchBook(true);
          } catch (refreshError) {
            console.log('[BookReader] Session refresh failed');
          }
        }
        
        // Session invalid, redirect to login
        toast.error('Please log in to read your books');
        navigate('/login', { 
          state: { 
            from: `/book/${bookId}`, 
            message: 'Your session has expired. Please log in to continue reading.' 
          } 
        });
        return;
      }
      
      if (mountedRef.current) {
        toast.error('Failed to load book');
        navigate('/library');
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  };

  const fetchReadingProgress = async () => {
    try {
      const res = await axios.get(`${API}/reading-progress/${bookId}`);
      if (res.data.current_page > 0) {
        setReadingProgress(res.data.progress_percent);
        // Return the saved page so we can resume
        return res.data.current_page;
      }
    } catch {}
    return 0;
  };

  const fetchReadingStats = async () => {
    try {
      const res = await axios.get(`${API}/reading-stats`);
      setReadingStats(res.data);
    } catch {}
  };

  const saveReadingProgress = async () => {
    try {
      await axios.post(`${API}/reading-progress`, {
        book_id: bookId,
        current_page: currentPage,
        total_pages: totalPages,
        chapter_id: currentPageData?.chapter_id
      });
      setReadingProgress(Math.round((currentPage / Math.max(totalPages - 1, 1)) * 100));
    } catch {}
  };

  const goToPage = useCallback((newPage, direction, jumpDirect = false) => {
    const minPage = -1;
    const maxPage = allPages.length - 1;
    
    console.log('[goToPage] Called with:', { newPage, direction, jumpDirect, currentPage, maxPage });
    
    if (newPage < minPage || newPage > maxPage || isFlipping) {
      console.log('[goToPage] Blocked:', { belowMin: newPage < minPage, aboveMax: newPage > maxPage, isFlipping });
      return;
    }
    
    // CRITICAL: Stop any playing audio IMMEDIATELY before page turn
    if (audioElement) {
      audioElement.pause();
      audioElement.currentTime = 0; // Reset position
      setAudioElement(null);
      setIsPlaying(false);
    }
    
    // Reset the last played page so new page can play fresh
    lastPlayedPageRef.current = -999;
    
    // Check if navigating to back cover
    const isNavigatingToBackCover = newPage >= 0 && allPages[newPage]?.isBackCover;
    console.log('[goToPage] isNavigatingToBackCover:', isNavigatingToBackCover);
    
    // For mobile portrait/landscape, directly set the page (no pageflip library)
    if (isMobilePortrait || isMobileLandscape) {
      setCurrentPage(newPage);
      saveReadingProgress();
    } else if (realisticFlipRef.current) {
      // If jumpDirect is true OR navigating to back cover, navigate directly to the page
      if (jumpDirect || isNavigatingToBackCover) {
        // In flipbook, back cover is the last page
        // For back cover specifically, navigate to the last flipbook page
        if (isNavigatingToBackCover) {
          const totalFlipbookPages = realisticFlipRef.current.getTotalPages?.() || (allPages.length * 2);
          console.log('[goToPage] Navigating to back cover, flipbook page:', totalFlipbookPages - 1);
          realisticFlipRef.current.goToPage(totalFlipbookPages - 1);
        } else {
          // In flipbook, page 0 = cover, page 1 = first content page
          // newPage 0 should map to flipbook page 1
          const flipbookPage = newPage + 1;
          realisticFlipRef.current.goToPage(flipbookPage);
        }
      } else if (direction === 'next') {
        realisticFlipRef.current.nextPage();
      } else {
        realisticFlipRef.current.prevPage();
      }
      // The onPageChange callback will update currentPage
    } else {
      // Fallback - direct page set
      setCurrentPage(newPage);
      saveReadingProgress();
    }
  }, [allPages, isFlipping, audioElement, isMobilePortrait, isMobileLandscape, saveReadingProgress]);

  const nextPage = useCallback(() => goToPage(currentPage + 1, 'next'), [currentPage, goToPage]);
  const prevPage = useCallback(() => goToPage(currentPage - 1, 'prev'), [currentPage, goToPage]);

  const toggleFullscreen = () => {
    // Check if we're on iPad/mobile where native fullscreen might not work
    // Use defensive checks for navigator properties (some browsers may not support them)
    const userAgent = typeof navigator !== 'undefined' ? navigator.userAgent || '' : '';
    const platform = typeof navigator !== 'undefined' ? navigator.platform || '' : '';
    const maxTouchPoints = typeof navigator !== 'undefined' ? navigator.maxTouchPoints || 0 : 0;
    
    const isIpad = /iPad|iPhone|iPod/.test(userAgent) || 
                   (platform === 'MacIntel' && maxTouchPoints > 1);
    
    if (isIpad) {
      // Use CSS-based fullscreen for iPad
      setIsFullscreen(!isFullscreen);
      return;
    }
    
    // Native fullscreen for desktop browsers
    try {
      const bookContainer = document.getElementById('book-container');
      if (!document.fullscreenElement) {
        if (bookContainer?.requestFullscreen) {
          bookContainer.requestFullscreen().catch(() => {
            // Fallback to CSS fullscreen if native fails
            setIsFullscreen(true);
          });
        } else {
          setIsFullscreen(true);
        }
        setIsFullscreen(true);
      } else {
        document.exitFullscreen().catch(() => {});
        setIsFullscreen(false);
      }
    } catch (err) {
      // Fallback to CSS fullscreen
      setIsFullscreen(!isFullscreen);
    }
  };

  const startReading = useCallback(() => {
    // Ensure auto-read is OFF when just reading
    setAutoRead(false);
    if (audioElement) {
      audioElement.pause();
      setIsPlaying(false);
    }
    
    // Auto-hide toolbar after starting to read (all devices)
    setTimeout(() => setHideControls(true), 1500);
    
    if (currentPage === -1) {
      // Transition from cover to first page
      if (isMobilePortrait || isMobileLandscape) {
        // In mobile mode (split view or landscape), directly set the page
        setCurrentPage(0);
      } else if (realisticFlipRef.current) {
        // In flipbook mode, flip the page
        realisticFlipRef.current.nextPage();
      } else {
        // Fallback
        setCurrentPage(0);
      }
    }
  }, [currentPage, audioElement, isMobilePortrait, isMobileLandscape]);

  // Download printable PDF (5 credits)
  const handlePrintBook = useCallback(async () => {
    if (!user) {
      toast.error('Please sign in to download your book');
      return;
    }
    
    setIsPrinting(true);
    try {
      const response = await axios.get(`${API}/books/${bookId}/print-pdf`, {
        responseType: 'blob',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${book?.title || 'book'}_printable_a5.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('Your printable book is downloading! 🖨️');
      setShowPrintDialog(false);
    } catch (error) {
      console.error('Print PDF error:', error);
      if (error.response?.status === 402) {
        toast.error('Not enough credits. You need 5 credits to download a printable PDF.');
      } else {
        toast.error(error.response?.data?.detail || 'Failed to generate printable PDF');
      }
    } finally {
      setIsPrinting(false);
    }
  }, [bookId, user, token, book?.title]);

  // startListening is defined after playAudio below

  // Pre-load audio for upcoming pages in the background
  const preloadAudio = useCallback(async (pageIndex) => {
    if (!mountedRef.current) return; // Component unmounted
    if (pageIndex < 0 || pageIndex >= allPages.length) return;
    if (audioCache.current.has(pageIndex)) return; // Already cached
    if (preloadingPages.current.has(pageIndex)) return; // Already loading
    
    const pageData = allPages[pageIndex];
    if (!pageData?.text_content || !narratorVoice) return;
    
    // PRIORITY 1: Check offline storage first when offline or book is saved offline
    if (!isOnline || isBookOffline(book?.id)) {
      try {
        const offlineAudio = await getOfflineAudio(book?.id, pageIndex);
        if (offlineAudio && offlineAudio.success && offlineAudio.url) {
          audioCache.current.set(pageIndex, { type: 'url', url: offlineAudio.url });
          console.log(`[Preload Offline] Cached audio for page ${pageIndex}`);
          return;
        }
      } catch (e) {
        console.warn(`[Preload Offline] Failed to get audio for page ${pageIndex}:`, e);
      }
      
      // If offline and no cached audio, don't try to fetch from API
      if (!isOnline) return;
    }
    
    // PRIORITY 2: Check if page already has a cached Cloudinary URL from database
    if (pageData.audio_url && pageData.audio_url.startsWith('https://')) {
      audioCache.current.set(pageIndex, { type: 'url', url: pageData.audio_url });
      return;
    }
    
    preloadingPages.current.add(pageIndex);
    
    try {
      const res = await axios.post(`${API}/tts/generate`, {
        text: pageData.text_content,
        voice_id: narratorVoice
      }, {
        signal: abortControllerRef.current?.signal
      });
      
      // Check if still mounted after async operation
      if (!mountedRef.current) return;
      
      // Prefer Cloudinary URL over base64 for faster loading
      if (res.data.audio_url) {
        audioCache.current.set(pageIndex, { type: 'url', url: res.data.audio_url });
      } else if (res.data.audio_base64) {
        audioCache.current.set(pageIndex, { type: 'base64', data: res.data.audio_base64 });
      }
    } catch (error) {
      // Ignore errors (including aborted requests)
    } finally {
      preloadingPages.current.delete(pageIndex);
    }
  }, [allPages, narratorVoice, isOnline, isBookOffline, getOfflineAudio, book?.id]);

  // Pre-load audio for first few pages when book is ready - START IMMEDIATELY
  useEffect(() => {
    const preloadFirstPages = async () => {
      if (allPages.length > 0 && narratorVoice && book?.id) {
        setNarrationPreparing(true);
        setNarrationReady(false);
        
        // Check if still mounted
        if (!mountedRef.current) return;
        
        // Trigger batch preparation in background for ALL pages
        try {
          axios.post(`${API}/tts/batch-prepare`, {
            book_id: book.id,
            voice_id: narratorVoice
          }, {
            signal: abortControllerRef.current?.signal
          }).catch(() => {}); // Fire and forget - don't block
        } catch (e) {
          // Ignore errors - this is optimization
        }
        
        // Check if still mounted
        if (!mountedRef.current) return;
        
        // Pre-load first 5 pages in parallel for instant start
        const preloadPromises = [];
        for (let i = 0; i < Math.min(5, allPages.length); i++) {
          if (allPages[i]?.text_content && !audioCache.current.has(i)) {
            preloadPromises.push(preloadAudio(i));
          }
        }
        
        // Wait for at least the first page to be ready (with shorter timeout)
        // But don't block the user for too long - they can start listening while audio loads
        if (preloadPromises.length > 0) {
          try {
            await Promise.race([
              preloadPromises[0], // Wait for first page at minimum
              new Promise(resolve => setTimeout(resolve, 2000)) // 2s timeout - quick user experience
            ]);
          } catch (e) {
            console.log('Preload error (non-critical):', e);
          }
        }
        
        // Always mark as ready after timeout - audio will generate on-demand if needed
        setNarrationPreparing(false);
        setNarrationReady(true);
      }
    };
    
    preloadFirstPages();
  }, [allPages.length, narratorVoice, preloadAudio, book?.id]);

  const playAudio = useCallback(async () => {
    // CRITICAL: Don't play if component is unmounting or unmounted
    if (!mountedRef.current) {
      return;
    }
    
    // Skip chapter title pages - handled by useEffect
    if (allPages[currentPageRef.current]?.isChapterTitle) {
      return;
    }
    
    const pageIndex = currentPageRef.current;
    const pageData = allPages[pageIndex];
    
    // CRITICAL: Prevent duplicate playback for the same page
    // Only play if this page hasn't been played yet
    if (lastPlayedPageRef.current === pageIndex) {
      return;
    }
    
    if (!narratorVoice || pageIndex < 0 || !pageData?.text_content) {
      // If page has no text content, move to next page in auto-read mode
      if (autoReadRef.current && pageIndex >= 0 && pageIndex < allPages.length - 1) {
        setTimeout(() => {
          if (autoReadRef.current) {
            goToPage(currentPageRef.current + 1, 'next');
          }
        }, 300);
      }
      return;
    }
    
    // Mark this page as being played IMMEDIATELY to prevent race conditions
    lastPlayedPageRef.current = pageIndex;
    
    // Stop any existing audio first
    if (audioElement) {
      audioElement.pause();
      audioElement.currentTime = 0;
    }

    // Check if audio is already cached in memory
    let cachedAudio = audioCache.current.get(pageIndex);
    
    // PRIORITY 1: Check offline storage FIRST when offline or book is saved offline
    // This ensures we use cached audio even when we have audio_url but no network
    if (!cachedAudio && (!isOnline || isBookOffline(bookId))) {
      const offlineAudio = await getOfflineAudio(bookId, pageIndex);
      if (offlineAudio && offlineAudio.success) {
        // getOfflineAudio returns { success: true, url, blob } where url is already an Object URL
        if (offlineAudio.url) {
          cachedAudio = { type: 'url', url: offlineAudio.url };
          audioCache.current.set(pageIndex, cachedAudio);
          console.log(`[Offline] Using cached audio URL for page ${pageIndex}`);
        } else if (offlineAudio.blob) {
          cachedAudio = { type: 'blob', data: offlineAudio.blob };
          audioCache.current.set(pageIndex, cachedAudio);
          console.log(`[Offline] Using cached audio blob for page ${pageIndex}`);
        }
      }
    }
    
    // PRIORITY 2: Check if page has pre-cached audio URL from database (online fallback)
    if (!cachedAudio && pageData.audio_url && pageData.audio_url.startsWith('https://')) {
      // Only use network URL if we're online
      if (isOnline) {
        cachedAudio = { type: 'url', url: pageData.audio_url };
        audioCache.current.set(pageIndex, cachedAudio);
      }
    }
    
    if (!cachedAudio) {
      // Not cached - need to generate (only if online)
      if (!isOnline) {
        toast.error('You are offline. Audio not available for this page.');
        setAudioLoading(false);
        return;
      }
      
      setAudioLoading(true);
      try {
        const res = await axios.post(`${API}/tts/generate`, {
          text: pageData.text_content,
          voice_id: narratorVoice
        });

        // CRITICAL: Check if user moved to different page while we were fetching
        if (currentPageRef.current !== pageIndex) {
          setAudioLoading(false);
          return;
        }

        // Prefer Cloudinary URL for faster loading
        if (res.data.audio_url) {
          cachedAudio = { type: 'url', url: res.data.audio_url };
          
          // Phase 3: Save audio to offline storage if book is saved offline
          if (isBookOffline(bookId)) {
            try {
              // Fetch the audio file and save as blob
              const audioResponse = await fetch(res.data.audio_url);
              const audioBlob = await audioResponse.blob();
              await saveAudioOffline(bookId, pageIndex, audioBlob);
              console.log(`[Offline] Saved audio for page ${pageIndex}`);
            } catch (err) {
              console.warn('[Offline] Failed to cache audio:', err);
            }
          }
        } else if (res.data.audio_base64) {
          cachedAudio = { type: 'base64', data: res.data.audio_base64 };
        }
        
        if (cachedAudio) {
          audioCache.current.set(pageIndex, cachedAudio);
        }
      } catch (error) {
        console.error('TTS Error:', error.response?.data || error.message);
        const errorDetail = error.response?.data?.detail;
        if (errorDetail?.includes?.('quota_exceeded') || errorDetail?.status === 'quota_exceeded') {
          toast.error('Audio quota exceeded. Please add credits at Profile → Universal Key → Add Balance');
        } else {
          toast.error(errorDetail || 'Failed to generate audio');
        }
        setIsPlaying(false);
        setAudioLoading(false);
        // Reset so user can try again
        lastPlayedPageRef.current = -999;
        return;
      } finally {
        setAudioLoading(false);
      }
    }

    // FINAL CHECK: Make sure we're still on the same page AND component is mounted
    if (currentPageRef.current !== pageIndex || !mountedRef.current) {
      return;
    }

    if (cachedAudio) {
      // IPAD FIX: Reuse persistent audio element to preserve user interaction permission
      // iPad Safari only allows audio.play() if the Audio element was created/interacted with by user tap
      let audio = persistentAudioRef.current;
      
      // Create audio element only if it doesn't exist yet
      if (!audio) {
        audio = new Audio();
        persistentAudioRef.current = audio;
        console.log('[Audio iPad] Created new persistent Audio element');
      }
      
      // Stop any currently playing audio
      audio.pause();
      audio.currentTime = 0;
      
      // Set the new source - changing src doesn't lose the user interaction permission
      if (cachedAudio.type === 'url') {
        audio.src = cachedAudio.url;
      } else if (cachedAudio.type === 'blob') {
        // Phase 3: Handle blob from offline storage
        audio.src = URL.createObjectURL(cachedAudio.data);
      } else {
        audio.src = `data:audio/mpeg;base64,${cachedAudio.data}`;
      }
      
      audio.volume = volume[0] / 100;
      audio.playbackRate = playbackSpeed[0];
      
      // Pre-load next 3 pages while this one plays (more aggressive preloading)
      if (mountedRef.current) {
        preloadAudio(pageIndex + 1);
        preloadAudio(pageIndex + 2);
        preloadAudio(pageIndex + 3);
      }
      
      // Clear previous onended handler and set new one
      audio.onended = () => {
        // Check mounted before updating state
        if (!mountedRef.current) return;
        console.log('[Audio iPad] onended fired, autoRead:', autoReadRef.current);
        setIsPlaying(false);
        setAudioElement(null); // Clear the audio element state (but keep persistentAudioRef)
        
        // Continue to next page when audio finishes in auto-read mode
        if (autoReadRef.current && currentPageRef.current < allPages.length - 1) {
          // Reset lastPlayedPage to allow next page to play
          lastPlayedPageRef.current = -999;
          
          // For iPad, we need to ensure audio plays after page transition
          const nextPageIndex = currentPageRef.current + 1;
          console.log('[Audio iPad] Auto-continuing to page', nextPageIndex);
          
          setTimeout(() => {
            if (autoReadRef.current && mountedRef.current) {
              // Go to next page
              goToPage(nextPageIndex, 'next');
              
              // CRITICAL FIX FOR IPAD: Explicitly trigger playAudio after page change
              // Using the same persistent audio element preserves user interaction permission
              setTimeout(() => {
                if (autoReadRef.current && mountedRef.current && currentPageRef.current === nextPageIndex) {
                  // Double-check we haven't already started playing
                  if (lastPlayedPageRef.current !== nextPageIndex) {
                    console.log('[Audio iPad] Triggering playAudio for page', nextPageIndex);
                    playAudio();
                  }
                }
              }, 400); // Allow time for page state to update
            }
          }, 200);
        }
      };
      
      // Double-check we're still on the correct page AND mounted before playing
      if (currentPageRef.current === pageIndex && mountedRef.current) {
        console.log('[Audio iPad] Attempting to play, audioUnlocked:', audioUnlockedRef.current);
        
        // Load the new source
        audio.load();
        
        // On iOS/iPad, we need to handle audio context unlocking
        const playPromise = audio.play();
        if (playPromise !== undefined) {
          playPromise
            .then(() => {
              if (mountedRef.current) {
                console.log('[Audio iPad] Play succeeded');
                audioUnlockedRef.current = true; // Mark audio as unlocked
                setAudioElement(audio);
                setIsPlaying(true);
              } else {
                // Component unmounted during play - just pause, don't destroy
                audio.pause();
              }
            })
            .catch(e => {
              console.error('[Audio iPad] Play failed:', e.name, e.message);
              // On iOS/iPad, audio fails without user interaction
              // Show a friendly tip message
              if (e.name === 'NotAllowedError' && mountedRef.current) {
                toast.info('Tap the 🔊 button to hear the story read aloud', {
                  duration: 4000,
                  icon: '💡',
                });
              }
              if (mountedRef.current) {
                setIsPlaying(false);
                lastPlayedPageRef.current = -999; // Allow retry
              }
            });
        } else {
          if (mountedRef.current) {
            audioUnlockedRef.current = true;
            setAudioElement(audio);
            setIsPlaying(true);
          }
        }
      }
    }
  }, [allPages, narratorVoice, volume, playbackSpeed, audioElement, preloadAudio, goToPage]);

  const toggleAudio = () => {
    // Haptic feedback for better touch response
    if (navigator.vibrate) {
      navigator.vibrate(50);
    }
    
    // IPAD FIX: Create persistent audio element on first user tap
    // This must happen during user interaction to get autoplay permission
    if (!persistentAudioRef.current) {
      persistentAudioRef.current = new Audio();
      console.log('[Audio iPad] Created persistent audio on user tap');
    }
    
    // On iOS, we need to unlock audio context on first user interaction
    if (!iosAudioUnlocked) {
      // Play silent audio using the persistent element to unlock it
      const audio = persistentAudioRef.current;
      audio.src = 'data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA';
      audio.play().then(() => {
        setIosAudioUnlocked(true);
        audioUnlockedRef.current = true;
        console.log('[Audio iPad] Audio unlocked via user tap');
      }).catch((e) => {
        console.log('[Audio iPad] Silent audio unlock failed:', e);
      });
    }
    
    if (isPlaying && audioElement) {
      audioElement.pause();
      setIsPlaying(false);
    } else {
      setAutoRead(true);
      autoReadRef.current = true; // Sync update
      playAudio();
    }
  };

  // Immediate stop when auto-read is turned off
  const handleAutoReadToggle = () => {
    // Haptic feedback for better touch response
    if (navigator.vibrate) {
      navigator.vibrate(50);
    }
    
    const newValue = !autoRead;
    setAutoRead(newValue);
    autoReadRef.current = newValue; // Sync update
    
    // Immediately stop audio if turning off
    if (!newValue && audioElement) {
      audioElement.pause();
      setIsPlaying(false);
    }
  };

  // Start listening - flip to first page and enable auto-read with audio
  const startListening = useCallback(() => {
    // Haptic feedback for better touch response
    if (navigator.vibrate) {
      navigator.vibrate(50);
    }
    
    // IPAD FIX: Create persistent audio element on first user tap
    // This must happen during user interaction to get autoplay permission
    if (!persistentAudioRef.current) {
      persistentAudioRef.current = new Audio();
      console.log('[Audio iPad] Created persistent audio on Listen tap');
    }
    
    // Unlock audio immediately on user tap
    if (!audioUnlockedRef.current) {
      const audio = persistentAudioRef.current;
      audio.src = 'data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA';
      audio.play().then(() => {
        audioUnlockedRef.current = true;
        setIosAudioUnlocked(true);
        console.log('[Audio iPad] Audio unlocked via Listen tap');
      }).catch((e) => {
        console.log('[Audio iPad] Silent unlock failed:', e);
      });
    }
    
    // Enable auto-read - update BOTH state AND ref synchronously
    setAutoRead(true);
    autoReadRef.current = true; // Sync update for immediate checks
    
    if (currentPage === -1) {
      // On cover - go to first page
      if (isMobilePortrait || isMobileLandscape) {
        // For mobile portrait/landscape, we use direct state update (no pageflip library)
        setCurrentPage(0);
        // CRITICAL: Directly trigger audio playback after a short delay for mobile
        // This ensures audio plays even if the useEffect doesn't catch the change
        setTimeout(() => {
          if (autoReadRef.current && mountedRef.current) {
            lastPlayedPageRef.current = -999; // Reset to allow playback
            playAudio();
          }
        }, 300);
      } else if (realisticFlipRef.current) {
        realisticFlipRef.current.nextPage();
      } else {
        // Fallback: directly set page
        setCurrentPage(0);
        // Also trigger audio for fallback case
        setTimeout(() => {
          if (autoReadRef.current && mountedRef.current) {
            lastPlayedPageRef.current = -999;
            playAudio();
          }
        }, 300);
      }
    } else {
      // Already on a content page - start playing immediately
      lastPlayedPageRef.current = -999; // Reset to allow playback
      playAudio();
    }
    
    // Auto-hide toolbar after starting to listen (all devices)
    setTimeout(() => setHideControls(true), 1500);
  }, [currentPage, playAudio, isMobilePortrait, isMobileLandscape]);

  // Share book function - copy direct link to clipboard
  const shareBook = useCallback(async () => {
    const shareUrl = `${window.location.origin}/read/${bookId}`;
    
    // Try native share first (mobile)
    if (navigator.share && book) {
      try {
        await navigator.share({
          title: book.title,
          text: `Check out "${book.title}" on Azories!`,
          url: shareUrl
        });
        return;
      } catch (e) {
        // User cancelled or native share failed - fall through to clipboard
      }
    }
    
    // Fallback to clipboard
    try {
      await navigator.clipboard.writeText(shareUrl);
      toast.success('Link copied! Share it with anyone 🐉', {
        duration: 3000,
        icon: '🔗'
      });
    } catch (e) {
      // Final fallback - show the URL
      toast.info(`Share this link: ${shareUrl}`, {
        duration: 5000
      });
    }
  }, [bookId, book]);

  // Trigger celebration when reaching the final page (back cover)
  const triggerCelebration = useCallback(() => {
    if (hasShownCelebrationRef.current) return;
    hasShownCelebrationRef.current = true;
    setShowCelebration(true);
    
    // Fire confetti from both sides
    const duration = 3000;
    const end = Date.now() + duration;
    
    const colors = ['#a855f7', '#ec4899', '#f59e0b', '#10b981', '#3b82f6'];
    
    (function frame() {
      confetti({
        particleCount: 3,
        angle: 60,
        spread: 55,
        origin: { x: 0, y: 0.7 },
        colors: colors
      });
      confetti({
        particleCount: 3,
        angle: 120,
        spread: 55,
        origin: { x: 1, y: 0.7 },
        colors: colors
      });
      
      if (Date.now() < end) {
        requestAnimationFrame(frame);
      }
    })();
    
    // Show a congratulatory toast
    toast.success('🎉 You finished the book! Amazing job!', {
      duration: 5000,
      icon: '🌟'
    });
    
    // Hide celebration overlay after animation
    setTimeout(() => setShowCelebration(false), duration);
  }, []);

  // Check if user reached the final page
  useEffect(() => {
    // Back cover is stored as currentPage === allPages.length - 1 (last item in allPages)
    // OR it could be when the page has isBackCover: true
    if (allPages.length > 0 && currentPage >= 0) {
      const currentPageData = allPages[currentPage];
      // Check if this is the back cover page
      if (currentPageData?.isBackCover) {
        triggerCelebration();
      }
    }
  }, [currentPage, allPages, triggerCelebration]);

  // Track when flip ends to trigger audio playback
  const prevIsFlippingRef = useRef(isFlipping);
  
  // Auto-read effect: play audio when page flip ENDS with auto-read enabled
  useEffect(() => {
    const wasFlipping = prevIsFlippingRef.current;
    prevIsFlippingRef.current = isFlipping;
    
    // Only trigger when flip animation completes (was flipping, now not)
    // OR when auto-read is first enabled on a static page
    const flipJustEnded = wasFlipping && !isFlipping;
    const onStaticPage = !isFlipping && !wasFlipping;
    
    // Don't trigger if we're still flipping
    if (isFlipping) {
      return;
    }
    
    // Don't trigger if we already played this page
    if (lastPlayedPageRef.current === currentPage) {
      return;
    }
    
    // Only proceed if auto-read is enabled and we're on a content page
    if (!autoReadRef.current || currentPage < 0 || allPages.length === 0) {
      return;
    }
    
    const page = allPages[currentPage];
    
    if (page?.isChapterTitle) {
      // Chapter title page - show briefly then advance
      const timer = setTimeout(() => {
        if (autoReadRef.current && currentPageRef.current < allPages.length - 1 && !isFlipping) {
          goToPage(currentPageRef.current + 1, 'next');
        }
      }, 1500);
      return () => clearTimeout(timer);
    } else if (page?.text_content) {
      // Has text content - play audio
      // Use longer delay after flip to ensure everything is settled
      const delay = flipJustEnded ? 400 : 150;
      const timer = setTimeout(() => {
        if (autoReadRef.current && lastPlayedPageRef.current !== currentPage && !isFlipping) {
          playAudio();
        }
      }, delay);
      return () => clearTimeout(timer);
    } else if (currentPage < allPages.length - 1) {
      // No content, advance to next page quickly
      const timer = setTimeout(() => {
        if (autoReadRef.current && currentPageRef.current < allPages.length - 1 && !isFlipping) {
          goToPage(currentPageRef.current + 1, 'next');
        }
      }, 500);
      return () => clearTimeout(timer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage, autoRead, allPages.length, isFlipping]);

  useEffect(() => {
    if (audioElement) {
      audioElement.volume = volume[0] / 100;
    }
  }, [volume, audioElement]);

  useEffect(() => {
    if (audioElement) {
      audioElement.playbackRate = playbackSpeed[0];
    }
  }, [playbackSpeed, audioElement]);

  useEffect(() => {
    return () => {
      if (audioElement) {
        audioElement.pause();
      }
    };
  }, [audioElement]);

  // Auto-scroll text during narration (karaoke-style reading)
  useEffect(() => {
    if (!audioElement || !isPlaying) {
      return;
    }
    
    const handleTimeUpdate = () => {
      if (audioElement.duration && audioElement.duration > 0) {
        const progress = audioElement.currentTime / audioElement.duration;
        setAudioProgress(progress);
        
        // Auto-scroll the text container based on audio progress
        const textContainer = textScrollRef.current;
        if (textContainer) {
          const scrollableHeight = textContainer.scrollHeight - textContainer.clientHeight;
          if (scrollableHeight > 0) {
            // Use a slight ease-out curve for more natural scrolling
            // Don't scroll all the way - leave some buffer at the end
            const targetScroll = Math.min(progress * 1.1, 1) * scrollableHeight;
            
            // Smooth scroll with requestAnimationFrame for performance
            const currentScroll = textContainer.scrollTop;
            const diff = targetScroll - currentScroll;
            
            // Only scroll if difference is significant (avoid jitter)
            if (Math.abs(diff) > 2) {
              // Smooth interpolation - move 15% of the way each update
              textContainer.scrollTop = currentScroll + (diff * 0.15);
            }
          }
        }
      }
    };
    
    // Listen to timeupdate events
    audioElement.addEventListener('timeupdate', handleTimeUpdate);
    
    return () => {
      audioElement.removeEventListener('timeupdate', handleTimeUpdate);
    };
  }, [audioElement, isPlaying]);

  // Reset audio progress and scroll when page changes
  useEffect(() => {
    setAudioProgress(0);
    // Reset scroll position when page changes
    if (textScrollRef.current) {
      textScrollRef.current.scrollTop = 0;
    }
  }, [currentPage]);

  // Scroll indicator for mobile text container
  useEffect(() => {
    const checkScrollable = () => {
      const el = textScrollRef.current;
      if (el) {
        const hasOverflow = el.scrollHeight > el.clientHeight + 10;
        const isAtBottom = el.scrollHeight - el.scrollTop <= el.clientHeight + 10;
        setShowScrollIndicator(hasOverflow && !isAtBottom);
      }
    };
    
    // Check on mount and when page changes
    checkScrollable();
    
    const el = textScrollRef.current;
    if (el) {
      el.addEventListener('scroll', checkScrollable);
      return () => el.removeEventListener('scroll', checkScrollable);
    }
  }, [currentPage, currentPageData]);

  if (loading || authLoading) {
    return (
      <div className="min-h-screen min-h-[100dvh] flex items-center justify-center bg-gradient-to-b from-purple-900/95 to-slate-900">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="font-body text-muted-foreground">Opening book...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen min-h-[100dvh] ${theme === 'dark' ? 'bg-[#1a1a2e]' : 'bg-[#f8f5f0]'} ${currentPageData?.isBackCover ? '!bg-[#1a0a2e]' : ''}`}>
      {/* Header - Hidden in landscape mode for maximum book space */}
      {/* MOBILE: Minimal floating UI - back button, share button */}
      {(isMobilePortrait || isMobileLandscape) && (
        <>
          {/* Floating back button - top left */}
          <div className="fixed top-3 left-3 z-50 flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={handleBackToLibrary}
              className="w-7 h-7 rounded-full bg-black/20 backdrop-blur-md text-white/90 hover:bg-black/40 hover:text-white shadow-lg"
              data-testid="mobile-back-btn"
            >
              <FiArrowLeft className="w-4 h-4" />
            </Button>
            
            {/* Offline indicator */}
            {isBookOffline(bookId) && (
              <span className="px-2 py-1 rounded-full bg-purple-600/80 backdrop-blur-md text-white text-xs font-medium flex items-center gap-1 shadow-lg">
                <FiWifiOff className="w-3 h-3" />
                Offline
              </span>
            )}
          </div>
          
          {/* Floating buttons - top right */}
          <div className="fixed top-3 right-3 z-50 flex items-center gap-2">
            {/* Order Printed Copy button - mobile */}
            <button
              onClick={() => {
                if (user) {
                  setShowPrintOrderModal(true);
                } else {
                  toast.info('Please log in to order a printed copy', {
                    action: {
                      label: 'Log In',
                      onClick: () => navigate('/login')
                    }
                  });
                }
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-purple-600 via-pink-500 to-purple-600 text-white text-xs font-medium rounded-full shadow-lg"
              data-testid="mobile-print-btn"
            >
              <FiPackage className="w-3.5 h-3.5" />
              <span>Print</span>
            </button>
            
            {/* Share button */}
            <Button
              variant="ghost"
              size="icon"
              onClick={shareBook}
              className="w-7 h-7 rounded-full bg-black/20 backdrop-blur-md text-white/90 hover:bg-black/40 hover:text-white shadow-lg"
              data-testid="mobile-share-btn"
            >
              <FiShare2 className="w-4 h-4" />
            </Button>
            
            {/* Edit button - Only visible to book owner */}
            {user && book && (book.author_id === user.id || book.user_id === user.id) && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => navigate(`/editor/${book.id}`)}
                className="w-7 h-7 rounded-full bg-black/20 backdrop-blur-md text-white/90 hover:bg-black/40 hover:text-white shadow-lg"
                data-testid="mobile-edit-btn"
              >
                <FiEdit2 className="w-4 h-4" />
              </Button>
            )}
          </div>
        </>
      )}
      
      {/* DESKTOP: Full header bar with all controls */}
      {!isMobilePortrait && !isMobileLandscape && (
        <div className={`fixed top-0 left-0 right-0 z-40 ${currentPageData?.isBackCover ? 'bg-[#1a0a2e] border-none' : 'bg-background/80 border-b border-border'} backdrop-blur-xl`}>
          <div className={`max-w-7xl mx-auto px-2 sm:px-4 py-1.5 sm:py-3 flex items-center justify-between`}>
            <div className="flex items-center gap-2 sm:gap-4 min-w-0 flex-1">
              <Button
                variant="ghost"
                size="icon"
                onClick={handleBackToLibrary}
                className={`rounded-full flex-shrink-0 w-8 h-8 sm:w-10 sm:h-10`}
              >
                <FiArrowLeft className="w-4 h-4 sm:w-5 sm:h-5" />
              </Button>
              <div className="min-w-0">
                <h1 className={`font-heading font-bold line-clamp-1 truncate text-sm sm:text-lg`}>{book?.title}</h1>
                <p className="font-ui text-[10px] sm:text-xs text-muted-foreground truncate">
                  {isCover ? 'Cover' : currentPage === -2 ? 'Back' : currentPageData?.isChapterTitle ? currentPageData?.chapterTitle : `Page ${currentPage + 1}`}
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
              {/* Reading Progress */}
              {user && readingProgress > 0 && (
                <div className="hidden md:flex items-center gap-2 px-3 py-1 bg-primary/10 rounded-full">
                  <FiTrendingUp className="w-4 h-4 text-primary" />
                  <span className="text-xs font-ui text-primary">{readingProgress}%</span>
                </div>
              )}
              
              {/* Reading Streak Badge */}
              {readingStats?.current_streak > 0 && (
                <div className="hidden lg:flex items-center gap-1 px-2 py-1 bg-orange-500/10 rounded-full">
                  <FiAward className="w-4 h-4 text-orange-500" />
                  <span className="text-xs font-ui text-orange-500">{readingStats.current_streak} day!</span>
                </div>
              )}
              
              {/* Ambient Sound Control */}
              <div className="hidden sm:block">
                <AmbientSound genre={book?.genre} isReading={currentPage >= 0} />
              </div>
              
              {/* Order Printed Copy Button - Always visible */}
              <button 
                onClick={() => {
                  if (user) {
                    setShowPrintOrderModal(true);
                  } else {
                    toast.info('Please log in to order a printed copy', {
                      action: {
                        label: 'Log In',
                        onClick: () => navigate('/login')
                      }
                    });
                  }
                }} 
                className="flex items-center gap-2 px-3 py-2 sm:px-4 sm:py-2 bg-gradient-to-r from-purple-600 via-pink-500 to-purple-600 hover:from-purple-500 hover:via-pink-400 hover:to-purple-500 text-white text-xs sm:text-sm font-medium rounded-full shadow-lg hover:shadow-purple-500/30 transition-all duration-300 hover:scale-105 animate-shimmer bg-[length:200%_100%]"
                style={{
                  animation: 'shimmer 3s ease-in-out infinite'
                }}
                title="Order a real printed book"
                data-testid="order-printed-book-btn"
              >
                <FiPackage className="w-4 h-4" />
                <span className="hidden sm:inline">Order Printed Copy</span>
                <span className="sm:hidden">Print</span>
                <span className="hidden sm:flex h-2 w-2 relative">
                  <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-white opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-white"></span>
                </span>
              </button>
              
              {/* Share Book Button */}
              <Button 
                variant="ghost" 
                size="icon" 
                onClick={shareBook} 
                className="rounded-full w-8 h-8 sm:w-10 sm:h-10"
                title="Share this book"
                data-testid="share-book-btn"
              >
                <FiShare2 className="w-4 h-4 sm:w-5 sm:h-5" />
              </Button>
              
              {/* Edit Book Button - Only visible to book owner */}
              {user && book && (book.author_id === user.id || book.user_id === user.id) && (
                <Button 
                  variant="ghost" 
                  size="icon" 
                  onClick={() => navigate(`/editor/${book.id}`)} 
                  className="rounded-full w-8 h-8 sm:w-10 sm:h-10"
                  title="Edit this book"
                  data-testid="edit-book-btn"
                >
                  <FiEdit2 className="w-4 h-4 sm:w-5 sm:h-5" />
                </Button>
              )}
              
              <Button variant="ghost" size="icon" onClick={toggleTheme} className="rounded-full w-8 h-8 sm:w-10 sm:h-10">
                {theme === 'dark' ? <FiSun className="w-4 h-4 sm:w-5 sm:h-5" /> : <FiMoon className="w-4 h-4 sm:w-5 sm:h-5" />}
              </Button>
              <Button variant="ghost" size="icon" onClick={toggleFullscreen} className="rounded-full w-8 h-8 sm:w-10 sm:h-10">
                {isFullscreen ? <FiMinimize2 className="w-4 h-4 sm:w-5 sm:h-5" /> : <FiMaximize2 className="w-4 h-4 sm:w-5 sm:h-5" />}
              </Button>
            </div>
          </div>
          
          {/* Progress bar - hidden on back cover */}
          {totalPages > 0 && !currentPageData?.isBackCover && (
            <div className="h-0.5 sm:h-1 bg-muted">
              <div 
                className="h-full bg-primary transition-all duration-300"
                style={{ width: `${((currentPage + 1) / (totalPages + 1)) * 100}%` }}
              />
            </div>
          )}
        </div>
      )}
      
      {/* Rotate phone prompt - only on mobile portrait */}
      {showRotatePrompt && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          className="fixed top-16 left-4 right-4 z-50 md:hidden"
        >
          <div className="bg-purple-600 text-white rounded-xl px-4 py-3 shadow-lg flex items-center gap-3">
            <div className="flex-shrink-0">
              <svg className="w-6 h-6 animate-pulse" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="4" y="2" width="16" height="20" rx="2" />
                <path d="M12 18h.01" />
                <path d="M2 12l2-2m0 0l2 2m-2-2v4" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <p className="text-sm font-medium flex-1">
              Rotate your phone for the best reading experience
            </p>
            <button 
              onClick={() => setShowRotatePrompt(false)}
              className="flex-shrink-0 p-1 hover:bg-white/20 rounded-full"
            >
              <FiX className="w-4 h-4" />
            </button>
          </div>
        </motion.div>
      )}
      
      {/* Book Display - with swipe support */}
      <div 
        id="book-container"
        className={`${
          isMobilePortrait ? 'pt-0 pb-16' : 
          isMobileLandscape ? 'pt-0 pb-0' : 
          'pt-16 sm:pt-20 pb-16 sm:pb-20'
        } px-1 sm:px-2 flex items-center justify-center min-h-screen transition-all duration-300 ${
          isFullscreen ? 'bg-black/95 fixed inset-0 z-50 pt-4 sm:pt-6 pb-4 sm:pb-6' : ''
        }`}
        data-testid="book-container"
      >
        {/* Swipe hint indicators */}
        <AnimatePresence>
          {swipeHint && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className={`fixed top-1/2 -translate-y-1/2 z-50 ${
                swipeHint === 'next' ? 'right-4' : 'left-4'
              }`}
            >
              <div className="bg-primary/80 text-white px-4 py-2 rounded-full text-sm">
                {swipeHint === 'next' ? '→ Next' : '← Previous'}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        
        {/* Exit Fullscreen Button - Always visible in fullscreen */}
        {isFullscreen && (
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleFullscreen}
            className="absolute top-4 right-4 z-[60] rounded-full bg-white/10 hover:bg-white/20 text-white w-12 h-12"
            data-testid="exit-fullscreen-btn"
          >
            <FiMinimize2 className="w-6 h-6" />
          </Button>
        )}
        
        <div className={`w-full transition-all duration-500 flex items-center justify-center ${
          isFullscreen ? 'max-w-[98vw] h-[90vh]' : 'max-w-[95vw] xl:max-w-[90vw]'
        }`} style={{ 
          perspective: '2000px',
          minHeight: isFullscreen ? '90vh' : '80vh'
        }}>
          <div className={`relative h-full ${isFullscreen ? 'flex items-center justify-center' : ''}`}>
            
            {/* Overlay buttons positioned over the cover - these work because they're outside react-pageflip */}
            {/* Only show overlay buttons for desktop/tablet covers - mobile has inline buttons */}
            {isCover && !isMobilePortrait && !isMobileLandscape && (
              <div 
                className="absolute z-[70] flex flex-col items-center gap-2"
                style={{
                  top: '82%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  pointerEvents: 'auto'
                }}
              >
                <div className="flex gap-3">
                  <button
                    onClick={startReading}
                    className="px-5 py-2.5 rounded-full bg-white/20 hover:bg-white/30 text-white font-medium flex items-center gap-2 transition-colors backdrop-blur shadow-lg text-sm"
                    data-testid="cover-read-overlay-btn"
                  >
                    <FiBook className="w-4 h-4" />
                    Read
                  </button>
                  <button
                    onClick={startListening}
                    className="px-5 py-2.5 rounded-full bg-purple-600 hover:bg-purple-500 active:bg-purple-700 active:scale-95 text-white font-medium flex items-center gap-2 transition-colors shadow-lg text-sm touch-manipulation cursor-pointer"
                    data-testid="cover-listen-overlay-btn"
                  >
                    <FiPlay className="w-4 h-4" />
                    Listen
                  </button>
                </div>
                <p className="text-white/70 text-xs">Choose your experience</p>
              </div>
            )}
            
            {/* Mobile Cover - Pure CSS for both portrait and landscape */}
            {isCover && (isMobilePortrait || isMobileLandscape) ? (
              <div 
                className={`flex ${isMobileLandscape ? 'flex-row gap-4 px-4' : 'flex-col'} items-center justify-center w-full mx-auto`}
                style={{ height: isMobileLandscape ? 'calc(100vh - 100px)' : 'calc(100vh - 160px)' }}
              >
                {/* Cover Image */}
                <div 
                  className={`relative ${isMobileLandscape ? 'h-full w-auto aspect-[3/4]' : 'w-full max-w-xs aspect-[3/4]'} rounded-xl overflow-hidden shadow-2xl`}
                  style={{
                    background: `linear-gradient(135deg, ${book?.cover_gradient_start || '#667eea'} 0%, ${book?.cover_gradient_end || '#764ba2'} 100%)`,
                    maxHeight: isMobileLandscape ? '100%' : '60vh'
                  }}
                >
                  {book?.cover_image && (
                    <img 
                      src={book.cover_image}
                      alt={book.title}
                      className="absolute inset-0 w-full h-full object-cover"
                    />
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/20" />
                  <div className="absolute inset-0 flex flex-col items-center justify-center text-white p-4">
                    <h1 className={`font-heading ${isMobileLandscape ? 'text-xl' : 'text-2xl'} font-bold text-center mb-2 drop-shadow-lg`}>
                      {book?.title}
                    </h1>
                    <p className="text-sm opacity-80 drop-shadow">{book?.author_name}</p>
                  </div>
                </div>
                
                {/* Buttons - below cover in portrait, beside in landscape */}
                <div className={`flex ${isMobileLandscape ? 'flex-col' : 'flex-row'} gap-3 ${isMobileLandscape ? '' : 'mt-6'}`}>
                  <button
                    onClick={startReading}
                    className={`${isMobileLandscape ? 'px-6 py-3' : 'px-5 py-2.5'} rounded-full bg-white/90 hover:bg-white text-gray-800 font-medium flex items-center gap-2 transition-colors shadow-lg text-sm`}
                    data-testid="cover-read-overlay-btn"
                  >
                    <FiBook className="w-4 h-4" />
                    Read
                  </button>
                  <button
                    onClick={startListening}
                    className={`${isMobileLandscape ? 'px-6 py-3' : 'px-5 py-2.5'} rounded-full bg-purple-600 hover:bg-purple-500 active:bg-purple-700 active:scale-95 text-white font-medium flex items-center gap-2 transition-colors shadow-lg text-sm touch-manipulation cursor-pointer`}
                    data-testid="cover-listen-overlay-btn"
                  >
                    <FiPlay className="w-4 h-4" />
                    Listen
                  </button>
                </div>
              </div>
            ) : isMobilePortrait && !isCover && currentPage >= 0 ? (
              <div className="flex flex-col w-full max-w-md mx-auto relative" style={{ height: `calc(100vh - 140px)` }}>
                {/* Navigation buttons for mobile portrait - smaller and positioned above page count */}
                {!currentPageData?.isBackCover && (
                  <>
                    {/* Previous page button - moved up to avoid page count */}
                    {currentPage > 0 && (
                      <button
                        onClick={() => goToPage(currentPage - 1, 'prev')}
                        className="absolute left-1 z-50 w-6 h-6 rounded-full bg-purple-600/90 active:bg-purple-700 active:scale-95 flex items-center justify-center text-white shadow-lg"
                        style={{ top: '40%' }}
                        data-testid="portrait-prev-btn"
                      >
                        <FiChevronLeft className="w-4 h-4" />
                      </button>
                    )}
                    
                    {/* Next page button - moved up to avoid page count */}
                    {currentPage < allPages.length - 1 && (
                      <button
                        onClick={() => goToPage(currentPage + 1, 'next')}
                        className="absolute right-1 z-50 w-6 h-6 rounded-full bg-purple-600/90 active:bg-purple-700 active:scale-95 flex items-center justify-center text-white shadow-lg"
                        style={{ top: '40%' }}
                        data-testid="portrait-next-btn"
                      >
                        <FiChevronRight className="w-4 h-4" />
                      </button>
                    )}
                  </>
                )}
                
                {/* Back Cover - Full page with dark background extending to edges */}
                {currentPageData?.isBackCover ? (
                  <div 
                    className="fixed inset-0 z-30"
                    style={{ backgroundColor: '#1a0a2e' }}
                  >
                    <img 
                      src={getImageSource(currentPageData) || currentPageData.image_url}
                      alt="Back Cover"
                      style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        height: '100%',
                        objectFit: 'contain',
                        objectPosition: 'center'
                      }}
                    />
                  </div>
                ) : (
                <>
                {/* Top: Illustration - 55% of available height with portrait crop */}
                {/* SWIPE HANDLERS ON IMAGE ONLY - text area is completely blocked */}
                <div 
                  className="relative flex-shrink-0 rounded-t-2xl overflow-hidden shadow-lg"
                  style={{ height: '55%', touchAction: 'pan-x' }}
                  {...swipeHandlers}
                >
                  {currentPageData?.image_url ? (
                    <img 
                      src={getImageSource(currentPageData) || currentPageData.image_url}
                      alt=""
                      style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover',
                        objectPosition: 'center top'
                      }}
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-muted/20">
                      <span className="text-muted-foreground text-sm">No illustration</span>
                    </div>
                  )}
                  {/* Page number badge */}
                  <div className="absolute bottom-2 right-2 px-2 py-1 rounded-full bg-black/50 text-white text-xs">
                    {currentPage + 1} / {allPages.length - (allPages[allPages.length - 1]?.isBackCover ? 1 : 0)}
                  </div>
                </div>
                
                {/* Bottom: Text content - 45% of available height */}
                <div 
                  className="flex-1 bg-[#fdfbf7] dark:bg-[#2a2a30] rounded-b-2xl shadow-lg overflow-hidden relative"
                >
                  <div 
                    ref={textScrollRef}
                    className="h-full overflow-y-auto px-5 py-4 pb-8 text-scroll-container"
                    data-scrollable="true"
                  >
                    {(currentPageData?.text_content || currentPageData?.text || currentPageData?.content) ? (
                      <p className="font-reader text-base leading-relaxed text-foreground/90 whitespace-pre-wrap">
                        {currentPageData.text_content || currentPageData.text || currentPageData.content}
                      </p>
                    ) : currentPageData?.isChapterTitle ? (
                      <div className="text-center py-4">
                        <p className="text-xs uppercase tracking-wider text-muted-foreground mb-2">
                          {currentPageData.chapterNumber ? `Chapter ${currentPageData.chapterNumber}` : 'Chapter'}
                        </p>
                        <h2 className="font-heading text-xl font-bold">{currentPageData.chapterTitle}</h2>
                      </div>
                    ) : (
                      <p className="text-muted-foreground text-sm italic text-center py-8">
                        Swipe or tap arrows to continue...
                      </p>
                    )}
                  </div>
                  {/* Scroll indicator - shows when more content below */}
                  {showScrollIndicator && !isPlaying && (
                    <div className="absolute bottom-0 left-0 right-0 pointer-events-none">
                      <div className="h-16 bg-gradient-to-t from-[#fdfbf7] dark:from-[#2a2a30] to-transparent" />
                      <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex flex-col items-center">
                        <div className="animate-bounce bg-[#fdfbf7] dark:bg-[#2a2a30] rounded-full p-1 shadow-sm">
                          <FiChevronDown className="w-4 h-4 text-purple-500/70" />
                        </div>
                      </div>
                    </div>
                  )}
                  {/* Narration progress bar - shows during audio playback */}
                  {isPlaying && audioProgress > 0 && (
                    <div className="absolute bottom-0 left-0 right-0 h-1 bg-purple-200/30 dark:bg-purple-900/30">
                      <div 
                        className="h-full bg-purple-500/60 transition-all duration-300 ease-out"
                        style={{ width: `${audioProgress * 100}%` }}
                      />
                    </div>
                  )}
                </div>
              </>
              )}
              </div>
            ) : isMobileLandscape && !isCover && currentPage >= 0 ? (
              /* Mobile Landscape Two-Page Spread - Optimized for PWA full screen */
              <div className="relative w-full h-screen">
                {/* Back Cover - Full page image in landscape */}
                {currentPageData?.isBackCover ? (
                  <div 
                    className="flex items-center justify-center w-full px-4 pt-6 pb-2"
                    style={{ height: 'calc(100vh - 24px)' }}
                  >
                    <div className="relative h-full aspect-[3/4] max-w-[50vw] rounded-lg overflow-hidden shadow-2xl">
                      <img 
                        src={getImageSource(currentPageData) || currentPageData.image_url}
                        alt="Back Cover"
                        style={{
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          width: '100%',
                          height: '100%',
                          objectFit: 'contain',
                          objectPosition: 'center',
                          backgroundColor: '#1a0a2e'
                        }}
                      />
                      {/* Read Again Button Overlay */}
                      <div className="absolute bottom-8 left-0 right-0 flex justify-center">
                        <button
                          onClick={() => {
                            console.log('[BackCover Landscape] Read Again clicked');
                            setCurrentPage(-1);
                          }}
                          className="px-8 py-3 rounded-full bg-purple-600 hover:bg-purple-500 active:bg-purple-700 active:scale-95 active:bg-purple-700 text-white font-semibold flex items-center gap-2 shadow-lg"
                          data-testid="read-again-btn-landscape"
                        >
                          Read Again <FiPlay className="w-5 h-5" />
                        </button>
                      </div>
                    </div>
                  </div>
                ) : (
                  /* Two-Page Spread - Maximum screen usage */
                  <div 
                    className="flex w-full gap-0.5 px-2 pt-6 pb-0"
                    style={{ height: 'calc(100vh - 24px)' }}
                  >
                    {/* Left Page: Illustration with portrait crop */}
                    {/* SWIPE HANDLERS ON IMAGE ONLY - text area is completely blocked */}
                    <div 
                      className="relative flex-1 rounded-l-lg overflow-hidden"
                      style={{ 
                        boxShadow: '4px 0 15px -5px rgba(0,0,0,0.2)',
                        touchAction: 'pan-x'
                      }}
                      {...swipeHandlers}
                    >
                      {currentPageData?.image_url ? (
                        <img 
                          src={getImageSource(currentPageData) || currentPageData.image_url}
                          alt=""
                          style={{
                            position: 'absolute',
                            top: 0,
                            left: 0,
                            width: '100%',
                            height: '100%',
                            objectFit: 'cover',
                            objectPosition: 'center top'
                          }}
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-purple-100 to-blue-50">
                          <span className="text-purple-300 text-sm">No illustration</span>
                        </div>
                      )}
                    </div>
                    
                    {/* Right Page: Text with vertical centering */}
                    <div 
                      className="flex-1 bg-[#fdfbf7] dark:bg-[#2a2a30] rounded-r-lg overflow-hidden flex flex-col relative"
                      style={{ 
                        boxShadow: '-4px 0 15px -5px rgba(0,0,0,0.1)'
                      }}
                    >
                      {/* Book/Chapter header - subtle */}
                      <div className="px-4 pt-2 pb-1 flex items-center justify-between">
                        <span className="text-[9px] uppercase tracking-widest text-muted-foreground/60 font-medium">
                          {currentPageData?.chapterTitle || book?.title}
                        </span>
                        <span className="text-[9px] text-muted-foreground/50">
                          {currentPage + 1}
                        </span>
                      </div>
                      
                      {/* Text content - scrollable with indicator */}
                      <div 
                        ref={textScrollRefLandscape}
                        className="flex-1 overflow-y-auto px-5 py-2 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent text-scroll-container"
                        data-scrollable="true"
                      >
                        {(currentPageData?.text_content || currentPageData?.text || currentPageData?.content) ? (
                          <p className="font-reader text-sm leading-relaxed text-foreground/90 whitespace-pre-wrap text-center">
                            {currentPageData.text_content || currentPageData.text || currentPageData.content}
                          </p>
                        ) : currentPageData?.isChapterTitle ? (
                          <div className="text-center">
                            <p className="text-[10px] uppercase tracking-widest text-muted-foreground mb-1">
                              Chapter {currentPageData.chapterNumber || ''}
                            </p>
                            <h3 className="font-heading text-base font-bold text-foreground">
                              {currentPageData.chapterTitle}
                            </h3>
                          </div>
                        ) : (
                          <p className="text-muted-foreground/60 text-xs italic text-center">
                            Tap edges to navigate
                          </p>
                        )}
                      </div>
                      
                      {/* Scroll down indicator - shown when more text below */}
                      {showScrollIndicator && !isPlaying && (
                        <div className="absolute bottom-12 left-0 right-0 pointer-events-none">
                          <div className="h-8 bg-gradient-to-t from-[#fdfbf7] dark:from-[#2a2a30] to-transparent" />
                          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 flex flex-col items-center">
                            <div className="animate-bounce bg-[#fdfbf7] dark:bg-[#2a2a30] rounded-full p-1 shadow-sm">
                              <FiChevronDown className="w-4 h-4 text-purple-500/70" />
                            </div>
                          </div>
                        </div>
                      )}
                      {/* Narration progress bar - landscape */}
                      {isPlaying && audioProgress > 0 && (
                        <div className="absolute bottom-12 left-0 right-0 h-1 bg-purple-200/30 dark:bg-purple-900/30">
                          <div 
                            className="h-full bg-purple-500/60 transition-all duration-300 ease-out"
                            style={{ width: `${audioProgress * 100}%` }}
                          />
                        </div>
                      )}
                      
                      {/* Decorative footer element */}
                      <div className="px-4 pb-2 flex justify-center">
                        <div className="flex items-center gap-2 text-muted-foreground/30">
                          <div className="w-8 h-px bg-current" />
                          <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" />
                          </svg>
                          <div className="w-8 h-px bg-current" />
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                
                {/* Navigation buttons for landscape - prev on left, next on right */}
                {!currentPageData?.isBackCover && (
                  <>
                    {/* Previous page button - LEFT side */}
                    {currentPage > 0 && (
                      <button
                        onClick={() => goToPage(currentPage - 1, 'prev')}
                        className="absolute left-2 top-1/2 -translate-y-1/2 z-50 w-6 h-6 rounded-full bg-purple-600/80 hover:bg-purple-600 active:bg-purple-700 flex items-center justify-center text-white shadow-lg"
                        data-testid="landscape-prev-btn"
                      >
                        <FiChevronLeft className="w-3 h-3" />
                      </button>
                    )}
                    
                    {/* Next page button - RIGHT side */}
                    {currentPage < allPages.length - 1 && (
                      <button
                        onClick={() => goToPage(currentPage + 1, 'next')}
                        className="absolute right-2 top-1/2 -translate-y-1/2 z-50 w-6 h-6 rounded-full bg-purple-600/80 hover:bg-purple-600 active:bg-purple-700 flex items-center justify-center text-white shadow-lg"
                        data-testid="landscape-next-btn"
                      >
                        <FiChevronRight className="w-3 h-3" />
                      </button>
                    )}
                  </>
                )}
              </div>
            ) : (
              /* Book view - Use RealisticPageFlip for all devices, add tap zones on iPad */
              <div 
                className={`relative flex justify-center items-center ${isFullscreen ? 'h-full w-full' : ''}`}
                style={{ 
                  minHeight: isFullscreen ? '100%' : `${bookDimensions.height + 50}px`,
                  width: '100%'
                }}
              >
                {/* RealisticPageFlip - same for all devices */}
                <RealisticPageFlip
                  key={`pageflip-${orientationKey}-${isMobileLandscape ? 'landscape' : 'portrait'}`}
                  ref={realisticFlipRef}
                  book={book}
                  pages={allPages}
                  onPageChange={(flipPage, contentPageIndex) => {
                    // contentPageIndex is the actual index in allPages array
                    // -1 = front cover, -2 = back cover, 0+ = content page
                    setCurrentPage(contentPageIndex);
                    if (contentPageIndex >= 0) {
                      saveReadingProgress();
                    }
                  }}
                  onFlipStart={() => setIsFlipping(true)}
                  onFlipEnd={() => setIsFlipping(false)}
                  onStartReading={startReading}
                  onStartListening={startListening}
                  initialPage={currentPage >= 0 ? currentPage + 1 : 0}
                  width={bookDimensions.width}
                  height={bookDimensions.height}
                  showControls={false}
                  isFullscreen={isFullscreen}
                  isMobilePortrait={isMobilePortrait}
                  disableSwipe={isIPad} // Disable swipe on iPad
                />
                
                {/* Mobile/Touch device: Tap zones for page navigation (60px wide edges) */}
                {showMobileNavButtons && (
                  <>
                    {/* Left tap zone - previous page (show on all pages except cover) */}
                    {currentPage > -1 && (
                      <div
                        onClick={(e) => {
                          e.stopPropagation();
                          if (!isFlipping && realisticFlipRef.current) {
                            realisticFlipRef.current.prevPage();
                          }
                        }}
                        className="absolute left-0 top-0 bottom-0 z-[200] cursor-pointer"
                        style={{ width: '60px' }}
                        data-testid="ipad-tap-zone-left"
                      >
                        <div className="absolute inset-0 bg-black/0 active:bg-purple-500/20 transition-colors flex items-center justify-start pl-1">
                          <div className="w-10 h-10 rounded-full bg-purple-600/80 shadow-lg flex items-center justify-center">
                            <FiChevronLeft className="w-6 h-6 text-white" />
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {/* Right tap zone - next page (show on cover AND all pages except last) */}
                    {currentPage < allPages.length - 1 && (
                      <div
                        onClick={(e) => {
                          e.stopPropagation();
                          if (!isFlipping && realisticFlipRef.current) {
                            realisticFlipRef.current.nextPage();
                          }
                        }}
                        className="absolute right-0 top-0 bottom-0 z-[200] cursor-pointer"
                        style={{ width: '60px' }}
                        data-testid="ipad-tap-zone-right"
                      >
                        <div className="absolute inset-0 bg-black/0 active:bg-purple-500/20 transition-colors flex items-center justify-end pr-1">
                          <div className="w-10 h-10 rounded-full bg-purple-600/80 shadow-lg flex items-center justify-center">
                            <FiChevronRight className="w-6 h-6 text-white" />
                          </div>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Hide/Show Controls Toggle + Floating Listen button - visible when controls are hidden, hide when modal open */}
      {hideControls && !showPrintOrderModal && (
        <div className="fixed bottom-8 right-4 z-[250] flex flex-col items-center gap-2">
          {/* Floating Listen/Pause button - z-index higher than tap zones (z-200) for iPad */}
          <button
            onClick={() => {
              // Haptic feedback on press
              if (navigator.vibrate) {
                navigator.vibrate(50);
              }
              if (audioLoading || narrationPreparing) return; // Prevent clicks while loading
              if (isPlaying) {
                // Stop narration
                if (audioElement) {
                  audioElement.pause();
                }
                setIsPlaying(false);
                setAutoRead(false);
                autoReadRef.current = false;
              } else {
                // Start narration
                startListening();
              }
            }}
            disabled={audioLoading || narrationPreparing}
            className={`w-10 h-10 rounded-full ${(audioLoading || narrationPreparing) ? 'bg-purple-400' : 'bg-purple-600 hover:bg-purple-500 active:bg-purple-700'} text-white shadow-lg flex items-center justify-center transition-colors touch-manipulation cursor-pointer`}
            data-testid="floating-listen-btn"
          >
            {(audioLoading || narrationPreparing) ? (
              <FiLoader className="w-5 h-5 animate-spin" />
            ) : isPlaying ? (
              <FiPause className="w-5 h-5" />
            ) : (
              <FiPlay className="w-5 h-5 ml-0.5" />
            )}
          </button>
          
          {/* Show controls button */}
          <button
            onClick={() => setHideControls(false)}
            className="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900/50 border-2 border-purple-400 text-purple-600 dark:text-purple-300 shadow-lg flex items-center justify-center hover:bg-purple-200 dark:hover:bg-purple-800/50 transition-colors touch-manipulation cursor-pointer"
            data-testid="show-controls-btn"
          >
            <FiChevronUp className="w-5 h-5" />
          </button>
        </div>
      )}
      
      {/* Hide controls button - visible when controls are shown (not on back cover), hide when modal open */}
      {!hideControls && !currentPageData?.isBackCover && !isMobileLandscape && !showPrintOrderModal && (
        <div className="fixed bottom-6 right-4 z-[250] flex flex-col items-center gap-2">
          {/* Play button - z-index higher than tap zones (z-200) for iPad */}
          <button
            onClick={() => {
              // Haptic feedback on press
              if (navigator.vibrate) {
                navigator.vibrate(50);
              }
              if (audioLoading || narrationPreparing) return; // Prevent clicks while loading
              if (isPlaying) {
                if (audioElement) {
                  audioElement.pause();
                }
                setIsPlaying(false);
                setAutoRead(false);
                autoReadRef.current = false;
              } else {
                startListening();
              }
            }}
            disabled={audioLoading || narrationPreparing}
            className={`w-10 h-10 rounded-full ${(audioLoading || narrationPreparing) ? 'bg-purple-400' : 'bg-purple-600 hover:bg-purple-500 active:bg-purple-700'} text-white shadow-lg flex items-center justify-center transition-colors touch-manipulation cursor-pointer`}
            data-testid="floating-listen-btn-visible"
          >
            {(audioLoading || narrationPreparing) ? (
              <FiLoader className="w-5 h-5 animate-spin" />
            ) : isPlaying ? (
              <FiPause className="w-5 h-5" />
            ) : (
              <FiPlay className="w-5 h-5 ml-0.5" />
            )}
          </button>
          
          {/* Hide controls button */}
          <button
            onClick={() => setHideControls(true)}
            className="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900/50 border-2 border-purple-400 text-purple-600 dark:text-purple-300 shadow-lg flex items-center justify-center hover:bg-purple-200 dark:hover:bg-purple-800/50 transition-colors touch-manipulation cursor-pointer"
            data-testid="hide-controls-btn"
          >
            <FiChevronDown className="w-5 h-5" />
          </button>
        </div>
      )}
      
      {/* Bottom Controls - Hidden in landscape, and when Print Modal is open */}
      {!isMobileLandscape && !showPrintOrderModal && (
        <div className={`fixed bottom-0 left-0 right-0 ${currentPageData?.isBackCover ? 'bg-[#1a0a2e] border-none' : 'bg-background/90 border-t border-border'} backdrop-blur-xl z-[100] transition-transform duration-300 ${hideControls && !currentPageData?.isBackCover ? 'translate-y-full' : ''}`}>
          <div className={`max-w-4xl mx-auto px-2 sm:px-4 py-1.5 sm:py-4`}>
            {/* Navigation - 50% smaller on mobile */}
            <div className={`flex items-center justify-center gap-2 sm:gap-4 mb-1 sm:mb-4`}>
              {/* Back Cover: Show Read Again + Library + Back button */}
              {currentPageData?.isBackCover ? (
                <>
                  <button
                    onClick={() => navigate('/library')}
                    className="w-7 h-7 sm:min-w-[56px] sm:min-h-[56px] sm:px-5 rounded-full border-2 border-purple-400 bg-purple-600/20 hover:bg-purple-600/40 active:bg-purple-600/60 text-purple-300 flex items-center justify-center gap-2 touch-manipulation"
                    style={{ touchAction: 'manipulation', WebkitTapHighlightColor: 'transparent' }}
                    data-testid="back-to-library-btn"
                  >
                    <FiHome className="w-3.5 h-3.5 sm:w-5 sm:h-5" />
                    <span className="hidden sm:inline">Library</span>
                  </button>
                  <button
                    onClick={() => {
                      console.log('[BackCover] Read Again clicked, going to front cover');
                      // For desktop flipbook, flip to page 0 (front cover)
                      // The onPageChange callback will set currentPage to -1
                      if (realisticFlipRef.current) {
                        realisticFlipRef.current.goToPage(0);
                      } else {
                        // Fallback for mobile
                        setCurrentPage(-1);
                      }
                    }}
                    className="h-7 px-3 sm:min-h-[56px] sm:px-6 rounded-full bg-purple-600 hover:bg-purple-500 active:bg-purple-700 active:scale-95 text-white text-xs sm:text-base font-medium flex items-center justify-center gap-1.5 sm:gap-2 touch-manipulation"
                    style={{ touchAction: 'manipulation', WebkitTapHighlightColor: 'transparent' }}
                    data-testid="read-again-btn"
                  >
                    Read Again <FiPlay className="w-3 h-3 sm:w-5 sm:h-5" />
                  </button>
                  <button
                    onClick={() => {
                      console.log('[BackCover] Back clicked, currentPage:', currentPage, 'allPages.length:', allPages.length);
                      // When on back cover (currentPage === -2), go to last content page
                      // Otherwise go to previous page
                      if (currentPage === -2) {
                        // Last content page is allPages.length - 2 (since back cover is allPages.length - 1)
                        const lastContentPage = allPages.length - 2;
                        setCurrentPage(lastContentPage);
                      } else {
                        setCurrentPage(currentPage - 1);
                      }
                      if (realisticFlipRef.current) {
                        realisticFlipRef.current.prevPage();
                      }
                    }}
                    className="w-7 h-7 sm:min-w-[56px] sm:min-h-[56px] sm:px-5 rounded-full border-2 border-border bg-background hover:bg-muted active:bg-muted/80 flex items-center justify-center touch-manipulation"
                    style={{ touchAction: 'manipulation', WebkitTapHighlightColor: 'transparent' }}
                    data-testid="back-from-backcover-btn"
                  >
                    <FiChevronLeft className="w-3.5 h-3.5 sm:w-6 sm:h-6" />
                  </button>
                </>
              ) : (
                <>
              <button
                onClick={prevPage}
                disabled={currentPage <= -1}
                className="w-7 h-7 sm:min-w-[56px] sm:min-h-[56px] sm:px-5 rounded-full border-2 border-border bg-background hover:bg-muted active:bg-muted/80 flex items-center justify-center touch-manipulation"
                style={{ touchAction: 'manipulation', WebkitTapHighlightColor: 'transparent' }}
                data-testid="portrait-prev-btn"
              >
                <FiChevronLeft className="w-3.5 h-3.5 sm:w-6 sm:h-6" />
              </button>
              
              {/* Show Start Listening on cover, Read Aloud on other pages */}
              {isCover ? (
                <button
                  onClick={startListening}
                  disabled={narrationPreparing || audioLoading}
                  className={`h-7 px-3 sm:min-h-[56px] sm:px-6 rounded-full ${(narrationPreparing || audioLoading) ? 'bg-purple-400' : 'bg-purple-600 hover:bg-purple-500 active:bg-purple-700 active:scale-95'} text-white text-xs sm:text-base font-medium flex items-center justify-center gap-1.5 sm:gap-2 touch-manipulation`}
                  style={{ touchAction: 'manipulation', WebkitTapHighlightColor: 'transparent' }}
                  data-testid="cover-start-listening-btn"
                >
                  {narrationPreparing ? (
                    <><div className="w-3 h-3 sm:w-5 sm:h-5 border-2 border-white border-t-transparent rounded-full animate-spin" /> Preparing...</>
                  ) : audioLoading ? (
                    <><div className="w-3 h-3 sm:w-5 sm:h-5 border-2 border-white border-t-transparent rounded-full animate-spin" /> Loading...</>
                  ) : (
                    <><FiPlay className="w-3 h-3 sm:w-5 sm:h-5" /> Listen</>
                  )}
                </button>
              ) : (
                <button
                  onClick={isPlaying || autoRead ? handleAutoReadToggle : toggleAudio}
                  disabled={audioLoading || narrationPreparing}
                  className={`h-7 px-3 sm:min-h-[56px] sm:px-6 rounded-full border-2 ${(isPlaying || autoRead) ? 'bg-primary text-primary-foreground border-primary' : 'border-border bg-background'} text-xs sm:text-base font-medium flex items-center justify-center gap-1.5 sm:gap-2 touch-manipulation`}
                  style={{ touchAction: 'manipulation', WebkitTapHighlightColor: 'transparent' }}
                  data-testid="read-aloud-btn"
                >
                  {narrationPreparing ? (
                    <><div className="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" /> Preparing...</>
                  ) : audioLoading ? (
                    <><div className="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" /> Loading</>
                  ) : (isPlaying || autoRead) ? (
                    <><FiPause className="w-3 h-3 sm:w-5 sm:h-5" /> Pause</>
                  ) : (
                    <><FiPlay className="w-3 h-3 sm:w-5 sm:h-5" /> Aloud</>
                  )}
                </button>
              )}
              
              {/* Show "Back Cover" button on the last story page */}
              {currentPage >= 0 && currentPage === allPages.length - 2 && allPages[allPages.length - 1]?.isBackCover && (
                <button
                  onClick={() => {
                    console.log('[Back Cover Button] Clicked, navigating to back cover');
                    setCurrentPage(allPages.length - 1);
                  }}
                  className="h-7 px-3 sm:min-h-[56px] sm:px-4 rounded-full bg-purple-600 text-white text-xs sm:text-sm font-medium flex items-center justify-center gap-1.5 hover:bg-purple-500 active:bg-purple-700 transition-colors"
                  data-testid="view-backcover-btn"
                >
                  <FiBook className="w-3 h-3 sm:w-4 sm:h-4" />
                  <span className="hidden sm:inline">Back Cover</span>
                </button>
              )}
              
              <button
                onClick={nextPage}
                disabled={currentPage >= allPages.length - 1}
                className="w-7 h-7 sm:min-w-[56px] sm:min-h-[56px] sm:px-5 rounded-full border-2 border-border bg-background hover:bg-muted active:bg-muted/80 flex items-center justify-center touch-manipulation"
                style={{ touchAction: 'manipulation', WebkitTapHighlightColor: 'transparent' }}
                data-testid="portrait-next-btn"
              >
                <FiChevronRight className="w-3.5 h-3.5 sm:w-6 sm:h-6" />
              </button>
                </>
              )}
            </div>
          
          {/* Audio Controls - Enhanced - Hidden on very small screens */}
          <div className="hidden sm:flex items-center justify-center gap-2 sm:gap-4 flex-wrap text-sm">
            {/* Voice Selector Dropdown */}
            <div className="hidden md:flex items-center gap-2">
              <FiMic className="w-4 h-4 text-muted-foreground" />
              <select
                value={narratorVoice}
                onChange={(e) => {
                  setNarratorVoice(e.target.value);
                  // Clear audio cache when voice changes
                  audioCache.current.clear();
                }}
                disabled={narratorVoiceLocked}
                className="px-3 py-1 rounded-full bg-muted/50 text-xs text-foreground border-none focus:ring-1 focus:ring-primary cursor-pointer"
                data-testid="voice-selector"
              >
                {voices.map(v => (
                  <option key={v.voice_id} value={v.voice_id}>
                    {v.name} ({v.accent})
                  </option>
                ))}
              </select>
            </div>
            
            {/* Volume Control */}
            <div className="flex items-center gap-2 w-24 sm:w-28">
              <button 
                onClick={() => setVolume(volume[0] > 0 ? [0] : [50])}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                {volume[0] === 0 ? <FiVolumeX className="w-4 h-4" /> : <FiVolume2 className="w-4 h-4" />}
              </button>
              <Slider value={volume} onValueChange={setVolume} max={100} step={1} className="flex-1" />
            </div>
            
            {/* Playback Speed - Quick buttons */}
            <div className="flex items-center gap-1">
              <span className="hidden md:inline text-muted-foreground text-xs mr-1">Speed:</span>
              {[0.75, 1, 1.5, 2].map(speed => (
                <button
                  key={speed}
                  onClick={() => setPlaybackSpeed([speed])}
                  className={`px-1.5 sm:px-2 py-1 rounded-full text-xs transition-colors ${
                    playbackSpeed[0] === speed 
                      ? 'bg-primary text-primary-foreground' 
                      : 'bg-muted/50 hover:bg-muted text-muted-foreground'
                  }`}
                >
                  {speed}x
                </button>
              ))}
            </div>
            
            <Button
              variant={autoRead ? "default" : "ghost"}
              size="sm"
              onClick={handleAutoReadToggle}
              className="rounded-full text-xs"
            >
              Auto: {autoRead ? 'ON' : 'OFF'}
            </Button>
          </div>
        </div>
      </div>
      )}
      
      {/* Auth Required Overlay */}
      {requiresAuth && (
        <div className="fixed inset-0 bg-background/95 backdrop-blur-xl z-50 flex items-center justify-center">
          <div className="text-center p-8">
            <FiLock className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
            <h2 className="font-heading text-2xl font-bold mb-2">Sign In Required</h2>
            <p className="text-muted-foreground mb-2">Create a free account to read this book</p>
            <Button onClick={() => navigate('/auth', { state: { from: `/read/${bookId}` } })} className="rounded-full">
              Sign In to Continue
            </Button>
          </div>
        </div>
      )}
      
      {/* Continue Reading Prompt */}
      {showContinuePrompt && savedPageNumber > 0 && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[200] flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="bg-background rounded-2xl shadow-2xl max-w-sm w-full overflow-hidden"
            data-testid="continue-reading-modal"
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-emerald-500 to-teal-500 px-6 py-4 text-white">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
                  <FiBookmark className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="font-heading text-lg font-bold">Welcome Back!</h2>
                  <p className="text-white/80 text-sm">Continue where you left off?</p>
                </div>
              </div>
            </div>
            
            {/* Content */}
            <div className="p-5">
              <p className="text-muted-foreground text-sm mb-4">
                You were on <span className="font-semibold text-foreground">page {savedPageNumber + 1}</span> of this book.
              </p>
              
              {/* Buttons */}
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => {
                    setShowContinuePrompt(false);
                    // Start from beginning (cover)
                  }}
                  data-testid="start-from-beginning-btn"
                >
                  Start Over
                </Button>
                <Button
                  className="flex-1 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white"
                  onClick={() => {
                    setShowContinuePrompt(false);
                    // Jump to saved page
                    goToPage(savedPageNumber, 'next', true);
                  }}
                  data-testid="continue-reading-btn"
                >
                  Continue
                </Button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
      
      {/* Print Book Dialog */}
      {showPrintDialog && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[200] flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="bg-background rounded-2xl shadow-2xl max-w-md w-full overflow-hidden"
          >
            {/* Header with gradient */}
            <div className="bg-gradient-to-r from-purple-600 to-indigo-600 px-6 py-5 text-white">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center">
                  <FiPrinter className="w-6 h-6" />
                </div>
                <div>
                  <h2 className="font-heading text-xl font-bold">Print My Book</h2>
                  <p className="text-white/80 text-sm">Create a real picture book!</p>
                </div>
              </div>
            </div>
            
            {/* Content */}
            <div className="p-6">
              <div className="mb-6">
                <h3 className="font-semibold text-lg mb-2">{book?.title}</h3>
                <p className="text-muted-foreground text-sm">
                  Download a beautifully formatted A5 booklet PDF. Print on A4 paper, fold in half, and you have a real picture book!
                </p>
              </div>
              
              {/* Features */}
              <div className="space-y-3 mb-6">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-4 h-4 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <p className="font-medium text-sm">Full illustration on every spread</p>
                    <p className="text-muted-foreground text-xs">Left page: picture, Right page: story</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-4 h-4 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <p className="font-medium text-sm">All pages + covers included</p>
                    <p className="text-muted-foreground text-xs">Front cover, story pages, and back cover</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-4 h-4 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <p className="font-medium text-sm">Perfect for gifting</p>
                    <p className="text-muted-foreground text-xs">Print at home or at a print shop</p>
                  </div>
                </div>
              </div>
              
              {/* Cost */}
              <div className="bg-muted/50 rounded-xl p-4 mb-6">
                <div className="flex items-center justify-between">
                  <span className="font-medium">Cost:</span>
                  <div className="flex items-center gap-2">
                    <span className="text-2xl font-bold text-purple-600 dark:text-purple-400">5</span>
                    <span className="text-muted-foreground">credits</span>
                  </div>
                </div>
              </div>
              
              {/* Buttons - Hide Download PDF on mobile (blank page issue) */}
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={() => setShowPrintDialog(false)}
                  className="flex-1 rounded-full"
                  disabled={isPrinting}
                >
                  Cancel
                </Button>
                {/* Download PDF hidden on mobile - causes blank page issue */}
                <Button
                  onClick={handlePrintBook}
                  className="hidden md:flex flex-1 rounded-full bg-purple-600 hover:bg-purple-500 active:bg-purple-700 active:scale-95"
                  disabled={isPrinting}
                  data-testid="confirm-print-btn"
                >
                  {isPrinting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <FiDownload className="w-4 h-4 mr-2" />
                      Download PDF
                    </>
                  )}
                </Button>
              </div>
              
              {/* Mobile notice - shown only on mobile */}
              <p className="md:hidden text-center text-sm text-muted-foreground mt-3">
                PDF download is available on desktop. Use "Order Physical Copy" below for mobile!
              </p>
              
              {/* Divider */}
              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-border" />
                </div>
                <div className="relative flex justify-center">
                  <span className="bg-background px-3 text-xs text-muted-foreground uppercase tracking-wide">or</span>
                </div>
              </div>
              
              {/* Order Physical Copy Option */}
              <button
                onClick={() => {
                  setShowPrintDialog(false);
                  setShowPrintOrderModal(true);
                }}
                className="w-full p-4 rounded-xl border-2 border-dashed border-purple-300 dark:border-purple-700 hover:border-purple-500 hover:bg-purple-50 dark:hover:bg-purple-900/20 transition-all group"
                data-testid="order-physical-book-btn"
              >
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-100 to-pink-100 dark:from-purple-900/50 dark:to-pink-900/50 flex items-center justify-center group-hover:scale-110 transition-transform">
                    <FiBook className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                  </div>
                  <div className="text-left flex-1">
                    <p className="font-semibold text-foreground">Order a Real Printed Book</p>
                    <p className="text-xs text-muted-foreground">Premium 8x10" photobook delivered to your door</p>
                  </div>
                  <div className="px-2 py-1 bg-green-100 dark:bg-green-900/40 rounded-full">
                    <span className="text-xs font-medium text-green-600 dark:text-green-400">New!</span>
                  </div>
                </div>
              </button>
            </div>
          </motion.div>
        </div>
      )}
      
      {/* Print Order Modal */}
      <PrintOrderModal
        isOpen={showPrintOrderModal}
        onClose={() => setShowPrintOrderModal(false)}
        book={book}
        pages={allPages}
      />
      
      {/* AI Reading Buddy */}
      {book && user && (
        <AIReadingBuddy
          book={book}
          currentPage={currentPage}
          isOpen={showAIBuddy}
          onToggle={() => setShowAIBuddy(!showAIBuddy)}
        />
      )}
      
      {/* Book Completion Celebration Overlay */}
      <AnimatePresence>
        {showCelebration && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] pointer-events-none flex items-center justify-center"
          >
            <motion.div
              initial={{ scale: 0.5, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.5, opacity: 0 }}
              transition={{ type: "spring", damping: 15 }}
              className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-8 py-6 rounded-2xl shadow-2xl text-center"
            >
              <motion.div
                animate={{ rotate: [0, 10, -10, 0] }}
                transition={{ duration: 0.5, repeat: Infinity }}
                className="text-6xl mb-4"
              >
                🎉
              </motion.div>
              <h2 className="text-2xl font-bold mb-2">The End!</h2>
              <p className="text-white/80">Amazing job finishing this story!</p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* PWA Home Screen Prompt - shows once on mobile */}
      <PWAPrompt />
    </div>
  );
}
