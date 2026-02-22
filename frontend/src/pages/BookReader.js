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
  FiArrowLeft, FiChevronLeft, FiChevronRight, FiMaximize2, FiMinimize2,
  FiPlay, FiPause, FiVolume2, FiVolumeX, FiSun, FiMoon, FiLock, FiBook,
  FiAward, FiTrendingUp, FiMic, FiLayers
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
  
  const [allPages, setAllPages] = useState([]);
  const [narratorVoice, setNarratorVoice] = useState('');
  const [voices, setVoices] = useState([]);  // Available voices for selection
  
  // Reading progress
  const [readingProgress, setReadingProgress] = useState(0);
  const [readingStats, setReadingStats] = useState(null);
  
  // AI Reading Buddy
  const [showAIBuddy, setShowAIBuddy] = useState(false);
  
  // Realistic page flip mode
  const [useRealisticFlip, setUseRealisticFlip] = useState(true);
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
    // Auto-read: play audio for current page content, or auto-advance for chapter titles
    if (autoRead && currentPage >= 0 && allPages.length > 0) {
      const page = allPages[currentPage];
      
      if (page?.isChapterTitle) {
        // Chapter title page - show briefly then advance
        const timer = setTimeout(() => {
          // Use ref to check current state
          if (autoReadRef.current && currentPageRef.current < allPages.length - 1) {
            goToPage(currentPageRef.current + 1, 'next');
          }
        }, 2500);
        return () => clearTimeout(timer);
      } else if (page?.text_content) {
        // Has text content - play audio (small delay to ensure page is ready)
        const timer = setTimeout(() => {
          if (autoReadRef.current) {
            playAudio();
          }
        }, 200);
        return () => clearTimeout(timer);
      } else if (currentPage < allPages.length - 1) {
        // No content, advance to next page
        const timer = setTimeout(() => {
          if (autoReadRef.current && currentPageRef.current < allPages.length - 1) {
            goToPage(currentPageRef.current + 1, 'next');
          }
        }, 1000);
        return () => clearTimeout(timer);
      }
    }
  }, [currentPage, autoRead, allPages.length]);

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
    
    // In realistic flip mode, use the ref to control the page flip component
    if (useRealisticFlip && realisticFlipRef.current) {
      if (direction === 'next') {
        realisticFlipRef.current.nextPage();
      } else {
        realisticFlipRef.current.prevPage();
      }
      // The onPageChange callback will update currentPage
    } else {
      // Classic mode - use local animation
      setFlipDirection(direction);
      setIsFlipping(true);
      
      setTimeout(() => {
        setCurrentPage(newPage);
        setIsFlipping(false);
      }, 600);
    }
  }, [allPages.length, isFlipping, audioElement, useRealisticFlip]);

  const nextPage = useCallback(() => goToPage(currentPage + 1, 'next'), [currentPage, goToPage]);
  const prevPage = useCallback(() => goToPage(currentPage - 1, 'prev'), [currentPage, goToPage]);

  const toggleFullscreen = () => {
    const bookContainer = document.getElementById('book-container');
    if (!document.fullscreenElement) {
      if (bookContainer) {
        bookContainer.requestFullscreen();
      } else {
        document.documentElement.requestFullscreen();
      }
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  const startReading = useCallback(() => {
    if (currentPage === -1) {
      // Just flip to first page - no auto-read
      if (useRealisticFlip && realisticFlipRef.current) {
        realisticFlipRef.current.nextPage();
      } else {
        setFlipDirection('next');
        setIsFlipping(true);
        setTimeout(() => {
          setCurrentPage(0);
          setIsFlipping(false);
        }, 600);
      }
    }
  }, [currentPage, useRealisticFlip]);

  // startListening is defined after playAudio below

  const playAudio = async () => {
    // Skip chapter title pages - handled by useEffect
    if (allPages[currentPageRef.current]?.isChapterTitle) {
      return;
    }
    
    const pageIndex = currentPageRef.current;
    const pageData = allPages[pageIndex];
    
    if (!narratorVoice || pageIndex < 0 || !pageData?.text_content) {
      // If page has no text content, move to next page in auto-read mode
      if (autoReadRef.current && pageIndex < allPages.length - 1) {
        setTimeout(() => {
          if (autoReadRef.current) {
            goToPage(currentPageRef.current + 1, 'next');
          }
        }, 500);
      }
      return;
    }

    setAudioLoading(true);
    try {
      const res = await axios.post(`${API}/tts/generate`, {
        text: pageData.text_content,
        voice_id: narratorVoice
      });

      // Check if user is still on the same page before playing
      if (currentPageRef.current !== pageIndex) {
        // User navigated away, don't play this audio
        return;
      }

      if (res.data.audio_base64) {
        if (audioElement) {
          audioElement.pause();
        }

        const audio = new Audio(`data:audio/mpeg;base64,${res.data.audio_base64}`);
        audio.volume = volume[0] / 100;
        audio.playbackRate = playbackSpeed[0];
        
        audio.onended = () => {
          setIsPlaying(false);
          // Continue to next page when audio finishes in auto-read mode
          if (autoReadRef.current && currentPageRef.current < allPages.length - 1) {
            setTimeout(() => {
              if (autoReadRef.current) {
                goToPage(currentPageRef.current + 1, 'next');
              }
            }, 500);
          }
        };
        
        // Double-check we're still on the correct page before playing
        if (currentPageRef.current === pageIndex) {
          audio.play();
          setAudioElement(audio);
          setIsPlaying(true);
        }
      }
    } catch (error) {
      toast.error('Failed to generate audio');
      // Still continue to next page even if audio fails in auto-read mode
      if (autoReadRef.current && currentPageRef.current < allPages.length - 1) {
        setTimeout(() => {
          if (autoReadRef.current) {
            goToPage(currentPageRef.current + 1, 'next');
          }
        }, 1000);
      }
    } finally {
      setAudioLoading(false);
    }
  };

  const toggleAudio = () => {
    if (isPlaying && audioElement) {
      audioElement.pause();
      setIsPlaying(false);
    } else {
      setAutoRead(true); // Enable auto-read when user clicks play
      playAudio();
    }
  };

  // Immediate stop when auto-read is turned off
  const handleAutoReadToggle = () => {
    const newValue = !autoRead;
    setAutoRead(newValue);
    
    // Immediately stop audio if turning off
    if (!newValue && audioElement) {
      audioElement.pause();
      setIsPlaying(false);
    }
  };

  // Start listening - flip to first page and enable auto-read with audio
  const startListening = useCallback(() => {
    alert('startListening called!');
    console.log('startListening called, currentPage:', currentPage);
    // Enable auto-read first
    setAutoRead(true);
    console.log('setAutoRead(true) called');
    
    if (currentPage === -1) {
      // Flip to first page
      if (useRealisticFlip && realisticFlipRef.current) {
        realisticFlipRef.current.nextPage();
      } else {
        setFlipDirection('next');
        setIsFlipping(true);
        setTimeout(() => {
          setCurrentPage(0);
          setIsFlipping(false);
        }, 600);
      }
    }
    // The effect will handle playAudio when currentPage changes and autoRead is true
  }, [currentPage, useRealisticFlip]);

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
          isFullscreen ? 'max-w-[95vw] h-[85vh]' : 'max-w-5xl'
        }`} style={{ perspective: '2000px' }}>
          <div className={`relative h-full ${isFullscreen ? 'flex items-center justify-center' : ''}`}>
            
            {/* Realistic Page Flip Mode */}
            {useRealisticFlip ? (
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
                  width={isFullscreen ? Math.min(window.innerWidth * 0.45, 850) : 550}
                  height={isFullscreen ? Math.min(window.innerHeight * 0.88, 1000) : 770}
                  showControls={false}
                  className={isFullscreen ? 'scale-100' : ''}
                />
              </div>
            ) : (
            /* Original animation mode */
            isCover ? (
              // Front Cover - Single Page
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className={`mx-auto reader-page relative overflow-hidden cursor-pointer group rounded-r-lg shadow-2xl ${
                  isFullscreen ? 'h-full max-h-[85vh] aspect-[3/4]' : 'w-full max-w-lg aspect-[3/4]'
                }`}
                onClick={startReading}
                style={{
                  background: book?.cover_image ? 'transparent' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                }}
              >
                {book?.cover_image ? (
                  <img src={book.cover_image} alt="Cover" className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center p-8">
                    <div className="text-center text-white">
                      <FiBook className="w-20 h-20 mx-auto mb-6 opacity-50" />
                      <h2 className="font-heading text-4xl font-bold mb-2">{book?.cover_title || book?.title}</h2>
                      {book?.cover_subtitle && <p className="text-xl opacity-80">{book.cover_subtitle}</p>}
                      <p className="mt-6 opacity-60">By {book?.author_name}</p>
                    </div>
                  </div>
                )}
                
                {/* Play overlay with Read and Listen buttons */}
                <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <div className="text-center text-white space-y-4">
                    <div className="flex gap-4 justify-center">
                      <button 
                        onClick={(e) => { e.stopPropagation(); startReading(); }}
                        className="flex items-center gap-2 px-6 py-3 rounded-full bg-white/20 backdrop-blur hover:bg-white/30 transition-colors"
                      >
                        <FiBook className="w-6 h-6" />
                        <span className="font-heading text-lg">Read</span>
                      </button>
                      <button 
                        onClick={(e) => { e.stopPropagation(); startListening(); }}
                        className="flex items-center gap-2 px-6 py-3 rounded-full bg-primary hover:bg-primary/80 transition-colors"
                      >
                        <FiPlay className="w-6 h-6" />
                        <span className="font-heading text-lg">Listen</span>
                      </button>
                    </div>
                    <p className="text-sm opacity-70">Choose how you want to experience this story</p>
                  </div>
                </div>
                
                {/* Book info */}
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-6">
                  <p className="text-white/80 text-sm line-clamp-2 mb-2">{book?.back_cover_text || book?.description}</p>
                  {book?.age_rating && (
                    <span className="inline-block px-3 py-1 rounded-full bg-white/20 text-white text-xs">
                      {book.age_rating}
                    </span>
                  )}
                </div>
                
                {/* Book spine effect */}
                <div className="absolute left-0 top-0 bottom-0 w-4 bg-gradient-to-r from-black/30 to-transparent" />
              </motion.div>
            ) : (
              // Book pages with realistic page turn
              <div className={`flex justify-center ${isFullscreen ? 'h-full' : ''}`} style={{ transformStyle: 'preserve-3d' }}>
                {/* Left Page (Image/Previous) */}
                <div className={`relative ${isFullscreen ? 'h-full aspect-[3/4]' : 'w-full max-w-md aspect-[3/4]'}`}>
                  <motion.div
                    key={`left-${currentPage}`}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.4 }}
                    className="absolute inset-0 reader-page rounded-l-lg overflow-hidden"
                    style={{ 
                      boxShadow: '-8px 0 30px rgba(0,0,0,0.25), inset -2px 0 5px rgba(0,0,0,0.1)',
                      transformOrigin: 'right center'
                    }}
                  >
                    {/* Book spine effect */}
                    <div className="absolute right-0 top-0 bottom-0 w-3 bg-gradient-to-l from-black/20 to-transparent z-10" />
                    
                    {currentPageData?.isChapterTitle ? (
                      <div className="w-full h-full bg-gradient-to-br from-primary/10 via-secondary/5 to-primary/10 flex items-center justify-center">
                        <div className="text-center">
                          <div className="w-24 h-24 mx-auto mb-4 rounded-full bg-primary/20 flex items-center justify-center">
                            <FiBook className="w-12 h-12 text-primary/60" />
                          </div>
                          <div className="flex justify-center gap-3 mt-6">
                            {[...Array(3)].map((_, i) => (
                              <div key={i} className="w-2 h-2 rounded-full bg-primary/30" />
                            ))}
                          </div>
                        </div>
                      </div>
                    ) : currentPageData?.video_url ? (
                      <video src={currentPageData.video_url} className="w-full h-full object-cover" controls autoPlay loop muted />
                    ) : currentPageData?.image_url ? (
                      <img 
                        src={currentPageData.image_url} 
                        alt="" 
                        className="w-full h-full"
                        style={{
                          objectFit: currentPageData.image_fit || 'cover',
                          objectPosition: `${currentPageData.image_position_x || 50}% ${currentPageData.image_position_y || 50}%`
                        }}
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-primary/5 to-secondary/5">
                        <span className="font-reader text-6xl text-muted-foreground/20">{currentPage + 1}</span>
                      </div>
                    )}
                  </motion.div>
                </div>
                
                {/* Right Page (Text) with Realistic Page Turn Animation */}
                <div className={`relative ${isFullscreen ? 'h-full aspect-[3/4]' : 'w-full max-w-md aspect-[3/4]'}`} style={{ transformStyle: 'preserve-3d', perspective: '2000px' }}>
                  
                  {/* Background/Next Page - Always visible underneath */}
                  <div 
                    className="absolute inset-0 reader-page rounded-r-lg p-8 md:p-10 flex flex-col overflow-hidden"
                    style={{ 
                      boxShadow: 'inset 2px 0 8px rgba(0,0,0,0.1)',
                      zIndex: 1
                    }}
                  >
                    {currentPage < totalPages - 1 && (
                      <div className="flex-1 overflow-hidden opacity-30">
                        <p className="font-reader text-lg leading-relaxed text-muted-foreground/50">
                          {allPages[currentPage + 1]?.text_content?.substring(0, 200) || 'Next page...'}
                        </p>
                      </div>
                    )}
                  </div>
                  
                  {/* Current Page with flip animation */}
                  <AnimatePresence mode="wait">
                    <motion.div
                      key={`right-${currentPage}`}
                      initial={{ 
                        rotateY: flipDirection === 'next' ? -180 : 0,
                        x: flipDirection === 'next' ? 100 : 0,
                        opacity: 0,
                        scale: 0.95
                      }}
                      animate={{ 
                        rotateY: 0,
                        x: 0,
                        opacity: 1,
                        scale: 1
                      }}
                      exit={{ 
                        rotateY: flipDirection === 'prev' ? -180 : 0,
                        x: flipDirection === 'prev' ? 100 : 0,
                        opacity: 0,
                        scale: 0.95
                      }}
                      transition={{ 
                        duration: 0.6,
                        ease: [0.4, 0, 0.2, 1],
                        rotateY: { duration: 0.6, ease: [0.4, 0, 0.2, 1] }
                      }}
                      className="absolute inset-0 reader-page rounded-r-lg p-8 md:p-10 flex flex-col overflow-hidden"
                      style={{ 
                        boxShadow: '8px 0 30px rgba(0,0,0,0.25), inset 2px 0 5px rgba(0,0,0,0.05)',
                        transformStyle: 'preserve-3d',
                        transformOrigin: 'left center',
                        backfaceVisibility: 'hidden',
                        zIndex: 10
                      }}
                    >
                      {/* Book spine shadow on left edge */}
                      <div className="absolute left-0 top-0 bottom-0 w-4 bg-gradient-to-r from-black/15 to-transparent" />
                      
                      {currentPageData?.isChapterTitle ? (
                        <div className="flex-1 flex flex-col items-center justify-center">
                          <span className="text-sm font-ui text-muted-foreground mb-4 tracking-widest uppercase">
                            Chapter {currentPageData.chapterNumber} of {currentPageData.totalChapters}
                          </span>
                          <h2 className="font-heading text-3xl md:text-4xl font-bold text-center leading-tight">
                            {currentPageData.chapterTitle}
                          </h2>
                          <div className="mt-8 w-20 h-1 bg-primary/30 rounded-full" />
                        </div>
                      ) : (
                        <>
                          <div className="flex-1 overflow-auto">
                            <p className="font-reader text-lg md:text-xl leading-relaxed whitespace-pre-wrap">
                              {currentPageData?.text_content || 'This page is empty...'}
                            </p>
                          </div>
                          <div className="text-right mt-4 pt-4 border-t border-border/50">
                            <span className="font-ui text-sm text-muted-foreground">
                              Page {currentPage + 1} of {totalPages}
                            </span>
                          </div>
                        </>
                      )}
                      
                      {/* Realistic page curl effect - bottom right corner */}
                      <div 
                        className="absolute bottom-0 right-0 w-20 h-20 pointer-events-none overflow-hidden"
                        style={{ zIndex: 20 }}
                      >
                        <div 
                          className="absolute bottom-0 right-0 w-24 h-24"
                          style={{
                            background: `
                              linear-gradient(
                                -45deg,
                                transparent 0%,
                                transparent 45%,
                                rgba(0,0,0,0.03) 46%,
                                rgba(255,255,255,0.9) 47%,
                                rgba(245,245,245,1) 48%,
                                rgba(240,240,240,1) 100%
                              )
                            `,
                            borderTopLeftRadius: '100%',
                            boxShadow: '-4px -4px 10px rgba(0,0,0,0.15)',
                            transform: 'rotate(0deg)'
                          }}
                        />
                      </div>
                      
                      {/* Page shadow during turn */}
                      <motion.div
                        className="absolute inset-0 pointer-events-none"
                        style={{
                          background: 'linear-gradient(to left, transparent 0%, rgba(0,0,0,0.05) 100%)',
                          opacity: isFlipping ? 1 : 0,
                          transition: 'opacity 0.3s'
                        }}
                      />
                    </motion.div>
                  </AnimatePresence>
                  
                  {/* Page turning overlay during animation */}
                  {isFlipping && flipDirection === 'next' && (
                    <motion.div
                      initial={{ rotateY: 0 }}
                      animate={{ rotateY: -180 }}
                      transition={{ duration: 0.6, ease: [0.4, 0, 0.2, 1] }}
                      className="absolute inset-0 reader-page rounded-r-lg"
                      style={{
                        transformOrigin: 'left center',
                        transformStyle: 'preserve-3d',
                        boxShadow: '0 0 30px rgba(0,0,0,0.3)'
                      }}
                    >
                      {/* Front of turning page */}
                      <div 
                        className="absolute inset-0 bg-background rounded-r-lg p-8 flex items-center justify-center"
                        style={{ backfaceVisibility: 'hidden' }}
                      >
                        <FiBook className="w-16 h-16 text-muted-foreground/20" />
                      </div>
                      {/* Back of turning page */}
                      <div 
                        className="absolute inset-0 bg-muted/50 rounded-l-lg"
                        style={{ 
                          backfaceVisibility: 'hidden',
                          transform: 'rotateY(180deg)'
                        }}
                      />
                    </motion.div>
                  )}
                </div>
              </div>
            )
            )}
          </div>
        </div>
      </div>
      
      {/* Bottom Controls */}
      <div className="fixed bottom-0 left-0 right-0 bg-background/90 backdrop-blur-xl border-t border-border z-40">
        <div className="max-w-4xl mx-auto px-4 py-4">
          {/* Navigation */}
          <div className="flex items-center justify-center gap-4 mb-4">
            <Button
              variant="outline"
              size="lg"
              onClick={() => {
                if (useRealisticFlip && realisticFlipRef.current) {
                  realisticFlipRef.current.prevPage();
                } else {
                  prevPage();
                }
              }}
              disabled={(useRealisticFlip ? currentPage <= -1 : currentPage <= -1) || isFlipping}
              className="rounded-full px-6"
            >
              <FiChevronLeft className="w-5 h-5 mr-1" />
              Previous
            </Button>
            
            <Button
              variant={isPlaying ? "default" : "outline"}
              size="lg"
              onClick={toggleAudio}
              disabled={audioLoading || isCover}
              className="rounded-full px-8"
            >
              {audioLoading ? (
                <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin" />
              ) : isPlaying ? (
                <><FiPause className="w-5 h-5 mr-2" /> Pause</>
              ) : (
                <><FiPlay className="w-5 h-5 mr-2" /> Read Aloud</>
              )}
            </Button>
            
            <Button
              variant="outline"
              size="lg"
              onClick={() => {
                if (useRealisticFlip && realisticFlipRef.current) {
                  realisticFlipRef.current.nextPage();
                } else {
                  nextPage();
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
            {/* Narrator Voice Selector with Categories */}
            <div className="flex items-center gap-2">
              <FiMic className="w-4 h-4 text-muted-foreground" />
              <Select 
                value={narratorVoice} 
                onValueChange={(v) => {
                  setNarratorVoice(v);
                  // Update the book's narrator voice
                  if (book?.id) {
                    axios.put(`${API}/books/${book.id}`, { narrator_voice_id: v }).catch(() => {});
                  }
                }}
              >
                <SelectTrigger className="w-40 h-8 rounded-full text-xs">
                  <SelectValue placeholder="Select Voice" />
                </SelectTrigger>
                <SelectContent className="max-h-64">
                  {/* Group voices by category */}
                  {['Female', 'Male', 'Young Female', 'Young Male'].map(category => {
                    const categoryVoices = voices.filter(v => v.category === category);
                    if (categoryVoices.length === 0) return null;
                    return (
                      <div key={category}>
                        <div className="px-2 py-1 text-xs text-muted-foreground font-semibold bg-muted/50">{category}</div>
                        {categoryVoices.map((voice) => (
                          <SelectItem key={voice.voice_id} value={voice.voice_id} className="text-xs">
                            {voice.name} <span className="text-muted-foreground">({voice.accent})</span>
                          </SelectItem>
                        ))}
                      </div>
                    );
                  })}
                </SelectContent>
              </Select>
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
            
            {/* Page Flip Mode Toggle */}
            <Button
              variant={useRealisticFlip ? "default" : "ghost"}
              size="sm"
              onClick={() => setUseRealisticFlip(!useRealisticFlip)}
              className="rounded-full text-xs"
              title="Toggle realistic page flip animation"
            >
              <FiLayers className="w-3 h-3 mr-1" />
              {useRealisticFlip ? 'Realistic' : 'Classic'}
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
            <Button onClick={() => navigate('/auth')} className="rounded-full">
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
