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
  FiSun, FiMoon, FiLock, FiBook, FiAward, FiTrendingUp, FiMic
} from 'react-icons/fi';
import { useTheme } from '@/context/ThemeContext';
import AmbientSound from '@/components/AmbientSound';
import AIReadingBuddy from '@/components/AIReadingBuddy';
import { useSwipeGestures } from '@/hooks/useSwipeGestures';
import RealisticPageFlip from '@/components/RealisticPageFlip';

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
  
  // Audio state
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioLoading, setAudioLoading] = useState(false);
  const [audioElement, setAudioElement] = useState(null);
  const [volume, setVolume] = useState([75]);
  const [playbackSpeed, setPlaybackSpeed] = useState([1]);
  const [autoRead, setAutoRead] = useState(false);  // OFF by default - user clicks Read/Listen to enable
  
  // Audio cache for pre-loading upcoming pages
  const audioCache = useRef(new Map()); // pageIndex -> audio base64
  const preloadingPages = useRef(new Set()); // pages currently being preloaded
  
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
  
  // Realistic page flip mode - always enabled
  const realisticFlipRef = useRef(null);
  
  // Swipe state for visual feedback
  const [swipeHint, setSwipeHint] = useState(null);
  
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
  const autoReadRef = useRef(autoRead);
  autoReadRef.current = autoRead;
  
  // Ref to track current page for async operations
  const currentPageRef = useRef(currentPage);
  currentPageRef.current = currentPage;
  
  // Ref to trigger playback after listen button is clicked
  const shouldStartPlayingRef = useRef(false);

  useEffect(() => {
    // Stop currently playing audio when page changes
    if (audioElement) {
      audioElement.pause();
      setIsPlaying(false);
    }
    
    // Auto-read: play audio for current page content, or auto-advance for chapter titles
    // Use autoReadRef.current to catch synchronous updates from startListening
    if (autoReadRef.current && currentPage >= 0 && allPages.length > 0) {
      const page = allPages[currentPage];
      
      if (page?.isChapterTitle) {
        // Chapter title page - show briefly then advance
        const timer = setTimeout(() => {
          if (autoReadRef.current && currentPageRef.current < allPages.length - 1) {
            goToPage(currentPageRef.current + 1, 'next');
          }
        }, 1500); // Reduced from 2500ms for faster flow
        return () => clearTimeout(timer);
      } else if (page?.text_content) {
        // Has text content - play audio immediately
        const timer = setTimeout(() => {
          if (autoReadRef.current) {
            playAudio();
          }
        }, 100); // Reduced from 300ms - audio should be pre-cached
        return () => clearTimeout(timer);
      } else if (currentPage < allPages.length - 1) {
        // No content, advance to next page quickly
        const timer = setTimeout(() => {
          if (autoReadRef.current && currentPageRef.current < allPages.length - 1) {
            goToPage(currentPageRef.current + 1, 'next');
          }
        }, 500); // Reduced from 1000ms
        return () => clearTimeout(timer);
      }
    }
  }, [currentPage, autoRead, allPages.length, playAudio, goToPage]);

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
        // Flatten pages WITHOUT chapter title pages - text flows directly with images
        const pages = [];
        res.data.chapters?.forEach((chapter, chapterIndex) => {
          // Skip chapter title pages - just add content pages directly
          chapter.pages?.forEach(page => {
            pages.push({ ...page, chapterTitle: chapter.title, chapterNumber: chapterIndex + 1 });
          });
        });
        setAllPages(pages);
        
        // Track read
        axios.post(`${API}/books/${bookId}/track-read`).catch(() => {});
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
    
    if (audioElement) {
      audioElement.pause();
      setIsPlaying(false);
    }
    
    // Use the ref to control the page flip component
    if (realisticFlipRef.current) {
      if (direction === 'next') {
        realisticFlipRef.current.nextPage();
      } else {
        realisticFlipRef.current.prevPage();
      }
      // The onPageChange callback will update currentPage
    }
  }, [allPages.length, isFlipping, audioElement]);

  const nextPage = useCallback(() => goToPage(currentPage + 1, 'next'), [currentPage, goToPage]);
  const prevPage = useCallback(() => goToPage(currentPage - 1, 'prev'), [currentPage, goToPage]);

  const toggleFullscreen = () => {
    // Check if we're on iPad/mobile where native fullscreen might not work
    const isIpad = /iPad|iPhone|iPod/.test(navigator.userAgent) || 
                   (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    
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
      // Just flip to first page - no auto-read
      if (realisticFlipRef.current) {
        realisticFlipRef.current.nextPage();
      }
    }
  }, [currentPage, audioElement]);

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
        console.log(`Pre-loaded audio for page ${pageIndex}`);
      }
    } catch (error) {
      console.log(`Failed to preload audio for page ${pageIndex}:`, error.message);
    } finally {
      preloadingPages.current.delete(pageIndex);
    }
  }, [allPages, narratorVoice]);

  // Pre-load audio for first few pages when book is ready
  useEffect(() => {
    if (allPages.length > 0 && narratorVoice) {
      // Pre-load first 3 pages in background for instant start
      for (let i = 0; i < Math.min(3, allPages.length); i++) {
        preloadAudio(i);
      }
    }
  }, [allPages.length, narratorVoice, preloadAudio]);

  const playAudio = useCallback(async () => {
    // Skip chapter title pages - handled by useEffect
    if (allPages[currentPageRef.current]?.isChapterTitle) {
      console.log('Skipping chapter title page');
      return;
    }
    
    const pageIndex = currentPageRef.current;
    const pageData = allPages[pageIndex];
    
    console.log('playAudio called:', { pageIndex, hasVoice: !!narratorVoice, hasText: !!pageData?.text_content });
    
    if (!narratorVoice || pageIndex < 0 || !pageData?.text_content) {
      console.log('Early return - missing data:', { narratorVoice, pageIndex, textContent: pageData?.text_content?.substring(0, 50) });
      // If page has no text content, move to next page in auto-read mode
      if (autoReadRef.current && pageIndex >= 0 && pageIndex < allPages.length - 1) {
        setTimeout(() => {
          if (autoReadRef.current) {
            goToPage(currentPageRef.current + 1, 'next');
          }
        }, 300); // Reduced from 500ms
      }
      return;
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

        // Check if user is still on the same page before playing
        if (currentPageRef.current !== pageIndex) {
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
        return;
      } finally {
        setAudioLoading(false);
      }
    }

    if (audioBase64) {
      if (audioElement) {
        audioElement.pause();
      }

      const audio = new Audio(`data:audio/mpeg;base64,${audioBase64}`);
      audio.volume = volume[0] / 100;
      audio.playbackRate = playbackSpeed[0];
      
      // Pre-load next 2 pages while this one plays
      preloadAudio(pageIndex + 1);
      preloadAudio(pageIndex + 2);
      
      audio.onended = () => {
        setIsPlaying(false);
        // Continue to next page when audio finishes in auto-read mode - faster transition
        if (autoReadRef.current && currentPageRef.current < allPages.length - 1) {
          // Immediate transition since next audio is pre-loaded
          setTimeout(() => {
            if (autoReadRef.current) {
              goToPage(currentPageRef.current + 1, 'next');
            }
          }, 200); // Reduced from 500ms for faster flow
        }
      };
      
      // Double-check we're still on the correct page before playing
      if (currentPageRef.current === pageIndex) {
        audio.play().catch(e => {
          console.error('Audio play failed:', e);
          // On iOS, audio might fail without user interaction - try again
          setIsPlaying(false);
        });
        setAudioElement(audio);
        setIsPlaying(true);
      }
    }
  }, [allPages, narratorVoice, volume, playbackSpeed, audioElement, preloadAudio, goToPage]);

  const toggleAudio = () => {
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
    console.log('startListening called, currentPage:', currentPage);
    // Enable auto-read - update BOTH state AND ref synchronously
    setAutoRead(true);
    autoReadRef.current = true; // Sync update for immediate checks
    
    if (currentPage === -1) {
      // On cover - flip to first page, audio will start via effect when page changes
      console.log('On cover, flipping to first page with auto-read enabled');
      if (realisticFlipRef.current) {
        realisticFlipRef.current.nextPage();
      }
    } else {
      // Already on a content page - start playing immediately
      console.log('On content page, starting audio immediately');
      playAudio();
    }
  }, [currentPage, playAudio]);

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
      {/* Header */}
      <div className="fixed top-0 left-0 right-0 z-40 bg-background/80 backdrop-blur-xl border-b border-border">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate('/library')}
              className="rounded-full"
            >
              <FiArrowLeft className="w-5 h-5" />
            </Button>
            <div>
              <h1 className="font-heading font-bold text-lg line-clamp-1">{book?.title}</h1>
              <p className="font-ui text-xs text-muted-foreground">
                {isCover ? 'Front Cover' : currentPageData?.chapterTitle || ''}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {/* Reading Progress */}
            {user && readingProgress > 0 && (
              <div className="hidden sm:flex items-center gap-2 px-3 py-1 bg-primary/10 rounded-full">
                <FiTrendingUp className="w-4 h-4 text-primary" />
                <span className="text-xs font-ui text-primary">{readingProgress}%</span>
              </div>
            )}
            
            {/* Reading Streak Badge */}
            {readingStats?.current_streak > 0 && (
              <div className="hidden sm:flex items-center gap-1 px-2 py-1 bg-orange-500/10 rounded-full">
                <FiAward className="w-4 h-4 text-orange-500" />
                <span className="text-xs font-ui text-orange-500">{readingStats.current_streak} day streak!</span>
              </div>
            )}
            
            {/* Ambient Sound Control */}
            <AmbientSound genre={book?.genre} isReading={currentPage >= 0} />
            
            <Button variant="ghost" size="icon" onClick={toggleTheme} className="rounded-full">
              {theme === 'dark' ? <FiSun className="w-5 h-5" /> : <FiMoon className="w-5 h-5" />}
            </Button>
            <Button variant="ghost" size="icon" onClick={toggleFullscreen} className="rounded-full">
              {isFullscreen ? <FiMinimize2 className="w-5 h-5" /> : <FiMaximize2 className="w-5 h-5" />}
            </Button>
          </div>
        </div>
        
        {/* Progress bar */}
        {totalPages > 0 && (
          <div className="h-1 bg-muted">
            <div 
              className="h-full bg-primary transition-all duration-300"
              style={{ width: `${((currentPage + 1) / (totalPages + 1)) * 100}%` }}
            />
          </div>
        )}
      </div>
      
      {/* Book Display - with swipe support */}
      <div 
        id="book-container"
        className={`pt-20 pb-48 px-4 flex items-center justify-center min-h-screen transition-all duration-300 ${
          isFullscreen ? 'bg-black/95 fixed inset-0 z-50 pt-8 pb-8' : ''
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
        
        <div className={`w-full transition-all duration-500 ${
          isFullscreen ? 'max-w-[98vw] h-[90vh]' : 'max-w-7xl'
        }`} style={{ perspective: '2000px' }}>
          <div className={`relative h-full ${isFullscreen ? 'flex items-center justify-center' : ''}`}>
            
            {/* Realistic Page Flip Mode */}
            <div className={`flex justify-center items-center ${isFullscreen ? 'h-full w-full' : ''}`}>
              <RealisticPageFlip
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
                width={isFullscreen ? Math.min(window.innerWidth * 0.42, 800) : 500}
                height={isFullscreen ? Math.min(window.innerHeight * 0.80, 1000) : 680}
                showControls={false}
                isFullscreen={isFullscreen}
              />
            </div>
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
      
      {/* Bottom Controls */}
      <div className={`fixed bottom-0 left-0 right-0 bg-background/90 backdrop-blur-xl border-t border-border z-40 transition-transform duration-300 ${hideControls ? 'translate-y-full' : ''}`}>
        <div className="max-w-4xl mx-auto px-4 py-4">
          {/* Navigation */}
          <div className="flex items-center justify-center gap-4 mb-4">
            <Button
              variant="outline"
              size="lg"
              onClick={() => {
                if (realisticFlipRef.current) {
                  realisticFlipRef.current.prevPage();
                }
              }}
              disabled={currentPage <= -1 || isFlipping}
              className="rounded-full px-6"
            >
              <FiChevronLeft className="w-5 h-5 mr-1" />
              Previous
            </Button>
            
            <Button
              variant={(isPlaying || autoRead) ? "default" : "outline"}
              size="lg"
              onClick={isPlaying || autoRead ? handleAutoReadToggle : toggleAudio}
              disabled={audioLoading || isCover}
              className="rounded-full px-8"
              data-testid="read-aloud-btn"
            >
              {audioLoading ? (
                <><div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" /> Loading...</>
              ) : (isPlaying || autoRead) ? (
                <><FiPause className="w-5 h-5 mr-2" /> Pause</>
              ) : (
                <><FiPlay className="w-5 h-5 mr-2" /> Read Aloud</>
              )}
            </Button>
            
            <Button
              variant="outline"
              size="lg"
              onClick={() => {
                if (realisticFlipRef.current) {
                  realisticFlipRef.current.nextPage();
                }
              }}
              disabled={currentPage >= totalPages - 1 || isFlipping}
              className="rounded-full px-6"
            >
              Next
              <FiChevronRight className="w-5 h-5 ml-1" />
            </Button>
          </div>
          
          {/* Audio Controls - Enhanced */}
          <div className="flex items-center justify-center gap-4 flex-wrap text-sm">
            {/* Current Voice Display (read-only) */}
            <div className="flex items-center gap-2">
              <FiMic className="w-4 h-4 text-muted-foreground" />
              <div className="flex items-center gap-1 px-3 py-1 rounded-full bg-muted/50 text-xs text-muted-foreground">
                <span>{voices.find(v => v.voice_id === narratorVoice)?.name || 'Default Voice'}</span>
              </div>
            </div>
            
            {/* Volume Control */}
            <div className="flex items-center gap-2 w-28">
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
              <span className="text-muted-foreground text-xs mr-1">Speed:</span>
              {[0.75, 1, 1.25, 1.5, 2].map(speed => (
                <button
                  key={speed}
                  onClick={() => setPlaybackSpeed([speed])}
                  className={`px-2 py-1 rounded-full text-xs transition-colors ${
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
              Auto-Read: {autoRead ? 'ON' : 'OFF'}
            </Button>
            
            {/* Hide Controls Button - useful for iPad */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setHideControls(true)}
              className="rounded-full text-xs ml-2"
              title="Hide controls"
            >
              <FiChevronDown className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>
      
      {/* Auth Required Overlay */}
      {requiresAuth && (
        <div className="fixed inset-0 bg-background/95 backdrop-blur-xl z-50 flex items-center justify-center">
          <div className="text-center p-8">
            <FiLock className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
            <h2 className="font-heading text-2xl font-bold mb-2">Sign In Required</h2>
            <p className="text-muted-foreground mb-6">Create a free account to read this book</p>
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
    </div>
  );
}
