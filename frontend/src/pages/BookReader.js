import { useState, useEffect, useCallback, useRef } from 'react';
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
  FiSun, FiMoon, FiLock, FiBook, FiAward, FiTrendingUp, FiMic, FiX
} from 'react-icons/fi';
import { useTheme } from '@/context/ThemeContext';
import AmbientSound from '@/components/AmbientSound';
import AIReadingBuddy from '@/components/AIReadingBuddy';
import { useSwipeGestures } from '@/hooks/useSwipeGestures';
import RealisticPageFlip from '@/components/RealisticPageFlip';
import PWAPrompt from '@/components/PWAPrompt';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function BookReader() {
  const { bookId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const { user, token, loading: authLoading } = useAuth();
  const audioRef = useRef(null);
  
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
  
  // Audio state
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioLoading, setAudioLoading] = useState(false);
  const [audioElement, setAudioElement] = useState(null);
  const [volume, setVolume] = useState([75]);
  const [playbackSpeed, setPlaybackSpeed] = useState([1]);
  const [autoRead, setAutoRead] = useState(false);  // OFF by default - user clicks Read/Listen to enable
  const [narrationPreparing, setNarrationPreparing] = useState(false); // Show "Preparing narration..." message
  const [narrationReady, setNarrationReady] = useState(false); // First few pages are cached
  
  // Audio cache for pre-loading upcoming pages
  const audioCache = useRef(new Map()); // pageIndex -> audio base64
  const preloadingPages = useRef(new Set()); // pages currently being preloaded
  
  // Track which page audio has been played for - prevents duplicate playback
  const lastPlayedPageRef = useRef(-999);
  
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
  
  const isCover = currentPage === -1;
  const totalPages = allPages.length;
  const currentPageData = currentPage >= 0 ? allPages[currentPage] : null;
  
  // Swipe gestures for page navigation
  const swipeHandlers = useSwipeGestures({
    onSwipeLeft: () => {
      if (currentPage < totalPages - 1 && !isFlipping) {
        setSwipeHint('next');
        setTimeout(() => setSwipeHint(null), 300);
        goToPage(currentPage + 1, 'next');
      }
    },
    onSwipeRight: () => {
      if (currentPage > -1 && !isFlipping) {
        setSwipeHint('prev');
        setTimeout(() => setSwipeHint(null), 300);
        goToPage(currentPage - 1, 'prev');
      }
    },
    threshold: 50,
    enabled: !isFlipping
  });

  useEffect(() => {
    if (!authLoading) {
      // Ensure axios has the auth header set if user is logged in
      if (token && !axios.defaults.headers.common['Authorization']) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      }
      fetchBook();
      fetchVoices();
      if (user) {
        fetchReadingProgress();
        fetchReadingStats();
      }
    }
  }, [bookId, user, authLoading, token]);

  // Ref to track if we should continue auto-reading
  // NOTE: Only update this ref explicitly, NOT on every render
  const autoReadRef = useRef(autoRead);
  // Sync ref with state ONLY when state intentionally changes (via useEffect)
  useEffect(() => {
    // Only update if this is a genuine state change (not initial render)
    // This prevents overwriting manually set ref values
    autoReadRef.current = autoRead;
  }, [autoRead]);
  
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

  const fetchBook = async () => {
    try {
      const res = await axios.get(`${API}/books/${bookId}/full`);
      setBook(res.data);
      setNarratorVoice(res.data.narrator_voice_id || '21m00Tcm4TlvDq8ikWAM');
      setNarratorVoiceLocked(res.data.narrator_voice_locked || false);
      
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
          console.log('[BookReader] Added back cover as final page');
        }
        
        setAllPages(pages);
        
        // Track read
        axios.post(`${API}/books/${bookId}/track-read`).catch(() => {});
        
        // Show rotate prompt on mobile portrait (once per book, not per session)
        // Use proper orientation detection with safe access
        const promptKey = `azories-rotate-prompt-${bookId}`;
        const hasSeenPromptForThisBook = sessionStorage.getItem(promptKey);
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
        
        if (!hasSeenPromptForThisBook && isMobileDevice && isPortraitOrientation) {
          setShowRotatePrompt(true);
          sessionStorage.setItem(promptKey, 'true');
          // Auto-hide after 4 seconds
          setTimeout(() => setShowRotatePrompt(false), 4000);
        }
      }
    } catch (error) {
      toast.error('Failed to load book');
      navigate('/library');
    } finally {
      setLoading(false);
    }
  };

  const fetchReadingProgress = async () => {
    try {
      const res = await axios.get(`${API}/reading-progress/${bookId}`);
      if (res.data.current_page > 0) {
        setReadingProgress(res.data.progress_percent);
      }
    } catch {}
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

  const goToPage = useCallback((newPage, direction) => {
    const minPage = -1;
    const maxPage = allPages.length - 1;
    
    if (newPage < minPage || newPage > maxPage || isFlipping) return;
    
    // CRITICAL: Stop any playing audio IMMEDIATELY before page turn
    if (audioElement) {
      audioElement.pause();
      audioElement.currentTime = 0; // Reset position
      setAudioElement(null);
      setIsPlaying(false);
    }
    
    // Reset the last played page so new page can play fresh
    lastPlayedPageRef.current = -999;
    
    // For mobile portrait/landscape, directly set the page (no pageflip library)
    if (isMobilePortrait || isMobileLandscape) {
      setCurrentPage(newPage);
      saveReadingProgress();
    } else if (realisticFlipRef.current) {
      // Use the ref to control the page flip component
      if (direction === 'next') {
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
  }, [allPages.length, isFlipping, audioElement, isMobilePortrait, isMobileLandscape, saveReadingProgress]);

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

  // startListening is defined after playAudio below

  // Pre-load audio for upcoming pages in the background
  const preloadAudio = useCallback(async (pageIndex) => {
    if (pageIndex < 0 || pageIndex >= allPages.length) return;
    if (audioCache.current.has(pageIndex)) return; // Already cached
    if (preloadingPages.current.has(pageIndex)) return; // Already loading
    
    const pageData = allPages[pageIndex];
    if (!pageData?.text_content || !narratorVoice) return;
    
    preloadingPages.current.add(pageIndex);
    
    try {
      const res = await axios.post(`${API}/tts/generate`, {
        text: pageData.text_content,
        voice_id: narratorVoice
      });
      
      if (res.data.audio_base64) {
        audioCache.current.set(pageIndex, res.data.audio_base64);
      }
    } catch (error) {
    } finally {
      preloadingPages.current.delete(pageIndex);
    }
  }, [allPages, narratorVoice]);

  // Pre-load audio for first few pages when book is ready - START IMMEDIATELY
  useEffect(() => {
    const preloadFirstPages = async () => {
      if (allPages.length > 0 && narratorVoice) {
        setNarrationPreparing(true);
        setNarrationReady(false);
        
        // Pre-load first 3 pages in background for instant start
        const preloadPromises = [];
        for (let i = 0; i < Math.min(3, allPages.length); i++) {
          if (allPages[i]?.text_content && !audioCache.current.has(i)) {
            preloadPromises.push(preloadAudio(i));
          }
        }
        
        // Wait for at least the first page to be ready
        if (preloadPromises.length > 0) {
          try {
            await Promise.race([
              preloadPromises[0], // Wait for first page at minimum
              new Promise(resolve => setTimeout(resolve, 10000)) // 10s timeout
            ]);
          } catch (e) {
            console.log('Preload error (non-critical):', e);
          }
        }
        
        setNarrationPreparing(false);
        setNarrationReady(true);
      }
    };
    
    preloadFirstPages();
  }, [allPages.length, narratorVoice, preloadAudio]);

  const playAudio = useCallback(async () => {
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

    // Check if audio is already cached
    let audioBase64 = audioCache.current.get(pageIndex);
    
    if (!audioBase64) {
      // Not cached - need to generate
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

        audioBase64 = res.data.audio_base64;
        if (audioBase64) {
          audioCache.current.set(pageIndex, audioBase64); // Cache it
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

    // FINAL CHECK: Make sure we're still on the same page before playing
    if (currentPageRef.current !== pageIndex) {
      return;
    }

    if (audioBase64) {
      const audio = new Audio(`data:audio/mpeg;base64,${audioBase64}`);
      audio.volume = volume[0] / 100;
      audio.playbackRate = playbackSpeed[0];
      
      // Pre-load next 2 pages while this one plays
      preloadAudio(pageIndex + 1);
      preloadAudio(pageIndex + 2);
      
      audio.onended = () => {
        setIsPlaying(false);
        // Continue to next page when audio finishes in auto-read mode
        if (autoReadRef.current && currentPageRef.current < allPages.length - 1) {
          // Reset lastPlayedPage to allow next page to play
          lastPlayedPageRef.current = -999;
          setTimeout(() => {
            if (autoReadRef.current) {
              goToPage(currentPageRef.current + 1, 'next');
            }
          }, 200);
        }
      };
      
      // Double-check we're still on the correct page before playing
      if (currentPageRef.current === pageIndex) {
        // On iOS/iPad, we need to handle audio context unlocking
        const playPromise = audio.play();
        if (playPromise !== undefined) {
          playPromise
            .then(() => {
              setAudioElement(audio);
              setIsPlaying(true);
            })
            .catch(e => {
              console.error('Audio play failed:', e);
              // On iOS/iPad, audio fails without user interaction
              // Show a helpful message
              if (e.name === 'NotAllowedError') {
                toast.error('Tap "Read Aloud" again to start audio (iOS requires tap interaction)');
              }
              setIsPlaying(false);
              lastPlayedPageRef.current = -999; // Allow retry
            });
        } else {
          setAudioElement(audio);
          setIsPlaying(true);
        }
      }
    }
  }, [allPages, narratorVoice, volume, playbackSpeed, audioElement, preloadAudio, goToPage]);

  const toggleAudio = () => {
    // On iOS, we need to unlock audio context on first user interaction
    if (!iosAudioUnlocked) {
      // Create and play a silent audio to unlock
      const silentAudio = new Audio('data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA');
      silentAudio.play().then(() => {
        setIosAudioUnlocked(true);
        silentAudio.pause();
      }).catch(() => {});
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
    // Enable auto-read - update BOTH state AND ref synchronously
    setAutoRead(true);
    autoReadRef.current = true; // Sync update for immediate checks
    
    if (currentPage === -1) {
      // On cover - go to first page
      // For mobile portrait/landscape, we use direct state update (no pageflip library)
      if (isMobilePortrait || isMobileLandscape) {
        setCurrentPage(0);
        // Audio will play via the auto-read effect when page changes
      } else if (realisticFlipRef.current) {
        realisticFlipRef.current.nextPage();
      } else {
        // Fallback: directly set page
        setCurrentPage(0);
      }
    } else {
      // Already on a content page - start playing immediately
      playAudio();
    }
  }, [currentPage, playAudio, isMobilePortrait, isMobileLandscape]);

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
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="font-body text-muted-foreground">Opening book...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen ${theme === 'dark' ? 'bg-[#1a1a2e]' : 'bg-[#f8f5f0]'}`}>
      {/* Header - Hidden in landscape mode for maximum book space */}
      {!isMobileLandscape && (
        <div className={`fixed top-0 left-0 right-0 z-40 bg-background/80 backdrop-blur-xl border-b border-border`}>
          <div className={`max-w-7xl mx-auto px-2 sm:px-4 py-1.5 sm:py-3 flex items-center justify-between`}>
            <div className="flex items-center gap-2 sm:gap-4 min-w-0 flex-1">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => navigate('/library')}
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
              {/* Reading Progress - hidden on small screens */}
              {user && readingProgress > 0 && (
                <div className="hidden md:flex items-center gap-2 px-3 py-1 bg-primary/10 rounded-full">
                  <FiTrendingUp className="w-4 h-4 text-primary" />
                  <span className="text-xs font-ui text-primary">{readingProgress}%</span>
                </div>
              )}
              
              {/* Reading Streak Badge - hidden on small screens */}
              {readingStats?.current_streak > 0 && (
                <div className="hidden lg:flex items-center gap-1 px-2 py-1 bg-orange-500/10 rounded-full">
                  <FiAward className="w-4 h-4 text-orange-500" />
                  <span className="text-xs font-ui text-orange-500">{readingStats.current_streak} day!</span>
                </div>
              )}
              
              {/* Ambient Sound Control - hidden on mobile portrait */}
              <div className="hidden sm:block">
                <AmbientSound genre={book?.genre} isReading={currentPage >= 0} />
              </div>
              
              <Button variant="ghost" size="icon" onClick={toggleTheme} className="rounded-full w-8 h-8 sm:w-10 sm:h-10">
                {theme === 'dark' ? <FiSun className="w-4 h-4 sm:w-5 sm:h-5" /> : <FiMoon className="w-4 h-4 sm:w-5 sm:h-5" />}
              </Button>
              <Button variant="ghost" size="icon" onClick={toggleFullscreen} className="rounded-full w-8 h-8 sm:w-10 sm:h-10">
                {isFullscreen ? <FiMinimize2 className="w-4 h-4 sm:w-5 sm:h-5" /> : <FiMaximize2 className="w-4 h-4 sm:w-5 sm:h-5" />}
              </Button>
            </div>
          </div>
          
          {/* Progress bar */}
          {totalPages > 0 && (
            <div className="h-0.5 sm:h-1 bg-muted">
              <div 
                className="h-full bg-primary transition-all duration-300"
                style={{ width: `${((currentPage + 1) / (totalPages + 1)) * 100}%` }}
              />
            </div>
          )}
        </div>
      )}
      
      {/* Minimal Landscape Header - Just back button and tiny progress */}
      {isMobileLandscape && (
        <div className="fixed top-0 left-0 right-0 z-40 flex items-center justify-between px-2 py-1 bg-black/30 backdrop-blur-sm">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate('/library')}
            className="w-8 h-8 rounded-full text-white/80 hover:text-white hover:bg-white/20"
          >
            <FiArrowLeft className="w-4 h-4" />
          </Button>
          <span className="text-white/60 text-xs font-medium">
            {currentPage + 1} / {totalPages}
          </span>
          <div className="w-8" /> {/* Spacer for balance */}
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
        className={`${isMobileLandscape ? 'pt-4 pb-0' : 'pt-4 sm:pt-6 pb-16 sm:pb-20'} px-1 sm:px-2 flex items-center justify-center min-h-[calc(100vh-60px)] transition-all duration-300 ${
          isFullscreen ? 'bg-black/95 fixed inset-0 z-50 pt-4 sm:pt-6 pb-4 sm:pb-6' : ''
        }`}
        {...swipeHandlers}
        style={{ touchAction: 'pan-y pinch-zoom' }}
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
                    className="px-5 py-2.5 rounded-full bg-purple-600 hover:bg-purple-500 text-white font-medium flex items-center gap-2 transition-colors shadow-lg text-sm"
                    data-testid="cover-listen-overlay-btn"
                  >
                    <FiPlay className="w-4 h-4" />
                    Listen
                  </button>
                </div>
                <p className="text-white/70 text-xs">Choose your experience</p>
              </div>
            )}
            
            {/* Back Cover overlay - Read Again button for desktop */}
            {/* currentPage === -2 indicates back cover in flipbook mode, OR currentPageData?.isBackCover for mobile */}
            {(currentPage === -2 || currentPageData?.isBackCover) && !isMobilePortrait && !isMobileLandscape && (
              <div 
                className="absolute z-[70] flex flex-col items-center"
                style={{
                  bottom: '12%',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  pointerEvents: 'auto'
                }}
              >
                <button
                  onClick={() => goToPage(0, 'prev')}
                  className="px-6 py-2.5 rounded-full bg-purple-600 hover:bg-purple-500 text-white font-medium flex items-center gap-2 transition-colors shadow-lg text-sm"
                  data-testid="read-again-btn"
                >
                  Read Again <FiPlay className="w-4 h-4" />
                </button>
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
                    className={`${isMobileLandscape ? 'px-6 py-3' : 'px-5 py-2.5'} rounded-full bg-purple-600 hover:bg-purple-500 text-white font-medium flex items-center gap-2 transition-colors shadow-lg text-sm`}
                    data-testid="cover-listen-overlay-btn"
                  >
                    <FiPlay className="w-4 h-4" />
                    Listen
                  </button>
                </div>
              </div>
            ) : isMobilePortrait && !isCover && currentPage >= 0 ? (
              <div className="flex flex-col w-full max-w-md mx-auto" style={{ height: `calc(100vh - 140px)` }}>
                {/* Back Cover - Full page image */}
                {currentPageData?.isBackCover ? (
                  <div className="relative flex-1 rounded-2xl overflow-hidden shadow-lg">
                    <img 
                      src={currentPageData.image_url}
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
                    {/* Read Again button */}
                    <button
                      onClick={() => goToPage(0, 'prev')}
                      className="absolute bottom-4 left-1/2 -translate-x-1/2 px-6 py-2 rounded-full bg-purple-600 hover:bg-purple-500 text-white font-medium flex items-center gap-2 shadow-lg"
                      data-testid="read-again-btn"
                    >
                      Read Again <FiPlay className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                <>
                {/* Top: Illustration - 55% of available height with portrait crop */}
                <div 
                  className="relative flex-shrink-0 rounded-t-2xl overflow-hidden shadow-lg"
                  style={{ height: '55%' }}
                >
                  {currentPageData?.image_url ? (
                    <img 
                      src={currentPageData.image_url}
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
                    className="h-full overflow-y-auto px-5 py-4 pb-8"
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
                  {showScrollIndicator && (
                    <div className="absolute bottom-0 left-0 right-0 pointer-events-none">
                      <div className="h-16 bg-gradient-to-t from-[#fdfbf7] dark:from-[#2a2a30] to-transparent" />
                      <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex flex-col items-center">
                        <div className="animate-bounce bg-[#fdfbf7] dark:bg-[#2a2a30] rounded-full p-1 shadow-sm">
                          <FiChevronDown className="w-4 h-4 text-purple-500/70" />
                        </div>
                      </div>
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
                        src={currentPageData.image_url}
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
                      {/* Read Again button */}
                      <button
                        onClick={() => goToPage(0, 'prev')}
                        className="absolute bottom-4 left-1/2 -translate-x-1/2 px-6 py-2 rounded-full bg-purple-600 hover:bg-purple-500 text-white font-medium flex items-center gap-2 shadow-lg"
                        data-testid="read-again-btn"
                      >
                        Read Again <FiPlay className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ) : (
                  /* Two-Page Spread - Maximum screen usage */
                  <div 
                    className="flex w-full gap-0.5 px-2 pt-6 pb-0"
                    style={{ height: 'calc(100vh - 24px)' }}
                  >
                    {/* Left Page: Illustration with portrait crop */}
                    <div 
                      className="relative flex-1 rounded-l-lg overflow-hidden"
                      style={{ 
                        boxShadow: '4px 0 15px -5px rgba(0,0,0,0.2)'
                      }}
                    >
                      {currentPageData?.image_url ? (
                        <img 
                          src={currentPageData.image_url}
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
                      className="flex-1 bg-[#fdfbf7] dark:bg-[#2a2a30] rounded-r-lg overflow-hidden flex flex-col"
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
                      
                      {/* Text content - vertically centered with larger font */}
                      <div className="flex-1 flex flex-col justify-center px-5 py-2">
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
              </div>
            ) : (
              /* Realistic Page Flip Mode - for landscape and cover */
              <div 
                className={`flex justify-center items-center ${isFullscreen ? 'h-full w-full' : ''}`}
                style={{ 
                  minHeight: isFullscreen ? '100%' : `${bookDimensions.height + 50}px`,
                  width: '100%'
                }}
              >
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
                />
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Hide/Show Controls Toggle - visible on touch devices */}
      {hideControls && (
        <button
          onClick={() => setHideControls(false)}
          className="fixed bottom-4 right-4 z-50 p-3 rounded-full bg-primary/80 text-white shadow-lg"
          data-testid="show-controls-btn"
        >
          <FiChevronUp className="w-5 h-5" />
        </button>
      )}
      
      {/* Bottom Controls - Hidden in landscape (edge arrows are used instead) */}
      {!isMobileLandscape && (
        <div className={`fixed bottom-0 left-0 right-0 bg-background/90 backdrop-blur-xl border-t border-border z-40 transition-transform duration-300 ${hideControls ? 'translate-y-full' : ''}`}>
          <div className={`max-w-4xl mx-auto px-2 sm:px-4 py-3 sm:py-4`}>
            {/* Navigation - LARGE touch targets for mobile, instant response */}
            <div className={`flex items-center justify-center gap-4 sm:gap-4 mb-2 sm:mb-4`}>
              <button
                onClick={prevPage}
                disabled={currentPage <= -1}
                className="min-w-[56px] min-h-[56px] px-5 rounded-full border-2 border-border bg-background hover:bg-muted active:bg-muted/80 flex items-center justify-center touch-manipulation"
                style={{ touchAction: 'manipulation', WebkitTapHighlightColor: 'transparent' }}
                data-testid="portrait-prev-btn"
              >
                <FiChevronLeft className="w-6 h-6" />
              </button>
              
              {/* Show Start Listening on cover, Read Aloud on other pages */}
              {isCover ? (
                <button
                  onClick={startListening}
                  disabled={narrationPreparing}
                  className={`min-h-[56px] px-6 rounded-full ${narrationPreparing ? 'bg-purple-400' : 'bg-purple-600 hover:bg-purple-500 active:bg-purple-700'} text-white font-medium flex items-center justify-center gap-2 touch-manipulation`}
                  style={{ touchAction: 'manipulation', WebkitTapHighlightColor: 'transparent' }}
                  data-testid="cover-start-listening-btn"
                >
                  {narrationPreparing ? (
                    <><div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" /> Preparing narration...</>
                  ) : (
                    <><FiPlay className="w-5 h-5" /> Listen</>
                  )}
                </button>
              ) : (
                <button
                  onClick={isPlaying || autoRead ? handleAutoReadToggle : toggleAudio}
                  disabled={audioLoading || narrationPreparing}
                  className={`min-h-[56px] px-6 rounded-full border-2 ${(isPlaying || autoRead) ? 'bg-primary text-primary-foreground border-primary' : 'border-border bg-background'} font-medium flex items-center justify-center gap-2 touch-manipulation`}
                  style={{ touchAction: 'manipulation', WebkitTapHighlightColor: 'transparent' }}
                  data-testid="read-aloud-btn"
                >
                  {narrationPreparing ? (
                    <><div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" /> Preparing...</>
                  ) : audioLoading ? (
                    <><div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" /> Loading</>
                  ) : (isPlaying || autoRead) ? (
                    <><FiPause className="w-5 h-5" /> Pause</>
                  ) : (
                    <><FiPlay className="w-5 h-5" /> Aloud</>
                  )}
                </button>
              )}
              
              <button
                onClick={nextPage}
                disabled={currentPage >= allPages.length - 1}
                className="min-w-[56px] min-h-[56px] px-5 rounded-full border-2 border-border bg-background hover:bg-muted active:bg-muted/80 flex items-center justify-center touch-manipulation"
                style={{ touchAction: 'manipulation', WebkitTapHighlightColor: 'transparent' }}
                data-testid="portrait-next-btn"
              >
                <FiChevronRight className="w-6 h-6" />
              </button>
            </div>
          
          {/* Audio Controls - Enhanced - Hidden on very small screens */}
          <div className="hidden sm:flex items-center justify-center gap-2 sm:gap-4 flex-wrap text-sm">
            {/* Current Voice Display (read-only) */}
            <div className="hidden md:flex items-center gap-2">
              <FiMic className="w-4 h-4 text-muted-foreground" />
              <div className="flex items-center gap-1 px-3 py-1 rounded-full bg-muted/50 text-xs text-muted-foreground">
                <span>{voices.find(v => v.voice_id === narratorVoice)?.name || 'Default Voice'}</span>
              </div>
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
            
            {/* Hide Controls Button - useful for iPad */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setHideControls(true)}
              className="rounded-full text-xs"
              title="Hide controls"
            >
              <FiChevronDown className="w-4 h-4" />
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
      
      {/* AI Reading Buddy */}
      {book && user && (
        <AIReadingBuddy
          book={book}
          currentPage={currentPage}
          isOpen={showAIBuddy}
          onToggle={() => setShowAIBuddy(!showAIBuddy)}
        />
      )}
      
      {/* PWA Home Screen Prompt - shows once on mobile */}
      <PWAPrompt />
    </div>
  );
}
