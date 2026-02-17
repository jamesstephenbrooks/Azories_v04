import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { toast } from 'sonner';
import { useAuth } from '@/context/AuthContext';
import { 
  FiArrowLeft, FiChevronLeft, FiChevronRight, FiMaximize2, FiMinimize2,
  FiPlay, FiPause, FiVolume2, FiVolumeX, FiSun, FiMoon, FiLock, FiBook
} from 'react-icons/fi';
import { useTheme } from '@/context/ThemeContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function BookReader() {
  const { bookId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const { user } = useAuth();
  const audioRef = useRef(null);
  
  const [book, setBook] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(-1); // -1 = front cover, -2 = back cover
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
  const [autoRead, setAutoRead] = useState(false);
  
  // Narrator voice (set by creator)
  const [narratorVoice, setNarratorVoice] = useState('');
  
  // Flatten all pages from all chapters
  const [allPages, setAllPages] = useState([]);

  useEffect(() => {
    fetchBook();
  }, [bookId]);

  useEffect(() => {
    if (searchParams.get('audio') === 'true' && allPages.length > 0) {
      setAutoRead(true);
    }
  }, [searchParams, allPages]);

  // Auto-read effect
  useEffect(() => {
    if (autoRead && !isPlaying && !audioLoading && currentPage >= 0 && allPages[currentPage]?.text_content) {
      playAudio();
    }
  }, [autoRead, currentPage]);

  const fetchBook = async () => {
    try {
      const res = await axios.get(`${API}/books/${bookId}/full`);
      setBook(res.data);
      setNarratorVoice(res.data.narrator_voice_id || '21m00Tcm4TlvDq8ikWAM');
      
      if (res.data.requires_auth) {
        setRequiresAuth(true);
        setAllPages([]);
      } else {
        // Flatten pages with chapter title pages inserted at the start of each chapter
        const pages = [];
        res.data.chapters?.forEach((chapter, chapterIndex) => {
          // Add a chapter title page at the start of each chapter
          pages.push({
            id: `chapter-title-${chapter.id}`,
            isChapterTitle: true,
            chapterTitle: chapter.title,
            chapterNumber: chapterIndex + 1,
            totalChapters: res.data.chapters.length
          });
          
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

  const goToPage = useCallback((newPage, direction) => {
    const minPage = -1; // Front cover
    const maxPage = allPages.length - 1;
    
    if (newPage < minPage || newPage > maxPage || isFlipping) return;
    
    // Stop current audio
    if (audioElement) {
      audioElement.pause();
      setIsPlaying(false);
    }
    
    setFlipDirection(direction);
    setIsFlipping(true);
    
    setTimeout(() => {
      setCurrentPage(newPage);
      setIsFlipping(false);
    }, 500);
  }, [allPages.length, isFlipping, audioElement]);

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

  // Start reading from the beginning
  const startReading = useCallback(() => {
    // Go to first content page (after cover)
    if (currentPage === -1) {
      setFlipDirection('next');
      setIsFlipping(true);
      setTimeout(() => {
        setCurrentPage(0);
        setIsFlipping(false);
        setAutoRead(true);
      }, 500);
    } else {
      setAutoRead(true);
    }
  }, [currentPage]);

  const playAudio = async () => {
    // Skip chapter title pages - auto advance
    if (allPages[currentPage]?.isChapterTitle) {
      if (autoRead && currentPage < allPages.length - 1) {
        setTimeout(() => nextPage(), 1500);
      }
      return;
    }
    
    // Skip pages without content
    if (!narratorVoice || currentPage < 0 || !allPages[currentPage]?.text_content) {
      // If auto-read, advance to next page
      if (autoRead && currentPage < allPages.length - 1) {
        setTimeout(() => nextPage(), 500);
      }
      return;
    }

    setAudioLoading(true);
    try {
      const res = await axios.post(`${API}/tts/generate`, {
        text: allPages[currentPage].text_content,
        voice_id: narratorVoice
      });

      if (res.data.audio_base64) {
        if (audioElement) {
          audioElement.pause();
        }

        const audio = new Audio(`data:audio/mpeg;base64,${res.data.audio_base64}`);
        audio.volume = volume[0] / 100;
        audio.playbackRate = playbackSpeed[0];
        
        audio.onended = () => {
          setIsPlaying(false);
          // Auto advance to next page if auto-read is on
          if (autoRead && currentPage < allPages.length - 1) {
            setTimeout(() => nextPage(), 500);
          }
        };
        
        audio.play();
        setAudioElement(audio);
        setIsPlaying(true);
      }
    } catch (error) {
      toast.error('Failed to generate audio');
    } finally {
      setAudioLoading(false);
    }
  };

  const togglePlayPause = () => {
    if (audioElement) {
      if (isPlaying) {
        audioElement.pause();
        setIsPlaying(false);
      } else {
        audioElement.play();
        setIsPlaying(true);
      }
    } else {
      playAudio();
    }
  };

  const toggleAutoRead = () => {
    setAutoRead(!autoRead);
    if (!autoRead && currentPage >= 0 && !isPlaying) {
      playAudio();
    }
  };

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

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowRight') nextPage();
      if (e.key === 'ArrowLeft') prevPage();
      if (e.key === 'Escape' && isFullscreen) toggleFullscreen();
      if (e.key === ' ') {
        e.preventDefault();
        togglePlayPause();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentPage, isFullscreen, nextPage, prevPage, togglePlayPause]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="font-body text-muted-foreground">Loading your book...</p>
        </div>
      </div>
    );
  }

  // Show front cover for non-authenticated users
  if (requiresAuth && !user) {
    return (
      <div className={`min-h-screen bg-background ${isFullscreen ? 'fixed inset-0 z-50' : ''}`}>
        {/* Top Bar */}
        <div className="glass fixed top-0 left-0 right-0 z-40 px-4 py-3">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => navigate('/library')}
                className="rounded-full"
              >
                <FiArrowLeft className="w-5 h-5" />
              </Button>
              <h1 className="font-heading text-lg font-semibold">{book?.title}</h1>
            </div>
          </div>
        </div>
        
        {/* Book Preview */}
        <div className="pt-20 pb-20 px-4 flex items-center justify-center min-h-screen">
          <div className="w-full max-w-3xl book-perspective">
            <div className="flex shadow-2xl rounded-3xl overflow-hidden">
              {/* Front Cover */}
              <div className="w-1/2 aspect-[3/4] reader-page relative overflow-hidden">
                {book?.cover_image ? (
                  <img src={book.cover_image} alt="Cover" className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center">
                    <div className="text-center p-6">
                      <FiBook className="w-16 h-16 mx-auto text-primary/40 mb-4" />
                      <h2 className="font-heading text-2xl font-bold">{book?.cover_title || book?.title}</h2>
                      {book?.cover_subtitle && (
                        <p className="font-body text-muted-foreground mt-2">{book.cover_subtitle}</p>
                      )}
                    </div>
                  </div>
                )}
              </div>
              
              {/* Back Cover - Summary */}
              <div className="w-1/2 aspect-[3/4] reader-page p-8 flex flex-col">
                <h3 className="font-heading text-xl font-bold mb-4">About This Book</h3>
                <p className="font-reader text-lg leading-relaxed flex-1">
                  {book?.back_cover_text || book?.description || 'A magical story awaits...'}
                </p>
                <div className="mt-6 pt-6 border-t border-border">
                  <p className="font-ui text-sm text-muted-foreground mb-2">By {book?.author_name}</p>
                  <p className="font-ui text-sm text-muted-foreground">Genre: {book?.genre}</p>
                  {book?.age_rating && (
                    <p className="font-ui text-sm text-muted-foreground">Age: {book.age_rating}</p>
                  )}
                </div>
              </div>
            </div>
            
            {/* Sign in prompt */}
            <div className="mt-8 text-center">
              <div className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-muted mb-4">
                <FiLock className="w-5 h-5 text-muted-foreground" />
                <span className="font-body text-muted-foreground">Sign in to read this book</span>
              </div>
              <div>
                <Button onClick={() => navigate('/auth')} className="rounded-full px-8">
                  Sign In to Read
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const currentPageData = allPages[currentPage];
  const totalPages = allPages.length;
  const isCover = currentPage === -1;

  return (
    <div className={`min-h-screen bg-background ${isFullscreen ? 'fixed inset-0 z-50' : ''}`}>
      {/* Top Bar */}
      <div className="glass fixed top-0 left-0 right-0 z-40 px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate('/library')}
              className="rounded-full"
              data-testid="back-to-library"
            >
              <FiArrowLeft className="w-5 h-5" />
            </Button>
            <div>
              <h1 className="font-heading text-lg font-semibold line-clamp-1">
                {book?.title}
              </h1>
              <p className="font-body text-sm text-muted-foreground">
                {isCover ? 'Front Cover' : currentPageData?.chapterTitle || ''}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              className="rounded-full"
            >
              {theme === 'dark' ? <FiSun className="w-5 h-5" /> : <FiMoon className="w-5 h-5" />}
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleFullscreen}
              className="rounded-full"
            >
              {isFullscreen ? <FiMinimize2 className="w-5 h-5" /> : <FiMaximize2 className="w-5 h-5" />}
            </Button>
          </div>
        </div>
      </div>
      
      {/* Book Display */}
      <div 
        id="book-container"
        className={`pt-20 pb-48 px-4 flex items-center justify-center min-h-screen transition-all duration-300 ${
          isFullscreen ? 'bg-black/95 fixed inset-0 z-50 pt-4 pb-4' : ''
        }`}
      >
        <div className={`w-full book-perspective transition-all duration-300 ${
          isFullscreen ? 'max-w-7xl' : 'max-w-5xl'
        }`}>
          <div className={`flex shadow-2xl rounded-3xl overflow-hidden ${
            isFullscreen ? 'scale-110' : ''
          }`}>
            {isCover ? (
              // Front Cover View - Single Page with Play Button
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="w-full aspect-[3/4] max-h-[80vh] reader-page relative overflow-hidden cursor-pointer group"
                onClick={startReading}
              >
                {book?.cover_image ? (
                  <img src={book.cover_image} alt="Cover" className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full bg-gradient-to-br from-primary/30 to-secondary/30 flex items-center justify-center">
                    <div className="text-center p-8">
                      <FiBook className="w-20 h-20 mx-auto text-primary/50 mb-6" />
                      <h2 className="font-heading text-4xl md:text-5xl font-bold">{book?.cover_title || book?.title}</h2>
                      {book?.cover_subtitle && (
                        <p className="font-body text-xl text-muted-foreground mt-3">{book.cover_subtitle}</p>
                      )}
                      <p className="font-body text-lg text-muted-foreground/70 mt-6">By {book?.author_name}</p>
                    </div>
                  </div>
                )}
                
                {/* Play overlay */}
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <div className="text-center text-white">
                    <div className="w-20 h-20 rounded-full bg-white/20 backdrop-blur flex items-center justify-center mb-4 mx-auto">
                      <FiPlay className="w-10 h-10 ml-1" />
                    </div>
                    <p className="font-heading text-xl">Click to Start Reading</p>
                  </div>
                </div>
                
                {/* Book info at bottom */}
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-6">
                  <p className="text-white/90 font-body text-sm line-clamp-2">
                    {book?.back_cover_text || book?.description || 'A magical story awaits...'}
                  </p>
                  {book?.age_rating && (
                    <span className="inline-block mt-2 px-3 py-1 rounded-full bg-white/20 text-white text-xs">
                      {book.age_rating}
                    </span>
                  )}
                </div>
              </motion.div>
            ) : (
              // Regular page view or Chapter Title page
              <>
                <AnimatePresence mode="wait">
                  <motion.div
                    key={`left-${currentPage}`}
                    initial={{ 
                      opacity: 0, 
                      rotateY: flipDirection === 'prev' ? 90 : 0,
                      x: flipDirection === 'prev' ? 50 : 0,
                      scale: 0.95
                    }}
                    animate={{ 
                      opacity: 1, 
                      rotateY: 0,
                      x: 0,
                      scale: 1
                    }}
                    exit={{ 
                      opacity: 0, 
                      rotateY: flipDirection === 'next' ? -90 : 0,
                      x: flipDirection === 'next' ? -50 : 0,
                      scale: 0.95
                    }}
                    transition={{ 
                      duration: 0.5,
                      ease: [0.4, 0, 0.2, 1]
                    }}
                    style={{
                      transformStyle: 'preserve-3d',
                      transformOrigin: flipDirection === 'next' ? 'right center' : 'left center',
                      boxShadow: '4px 4px 20px rgba(0,0,0,0.3)'
                    }}
                    className="w-1/2 aspect-[3/4] reader-page page-shadow relative"
                  >
                    {currentPageData?.isChapterTitle ? (
                      // Chapter Title Page - Left side (decorative)
                      <div className="w-full h-full bg-gradient-to-br from-primary/10 via-secondary/5 to-primary/10 flex items-center justify-center">
                        <div className="text-center">
                          <div className="w-32 h-32 mx-auto mb-4 rounded-full bg-primary/20 flex items-center justify-center">
                            <FiBook className="w-16 h-16 text-primary/60" />
                          </div>
                          <div className="flex justify-center gap-4 mt-8">
                            {[...Array(3)].map((_, i) => (
                              <div key={i} className="w-3 h-3 rounded-full bg-primary/30" />
                            ))}
                          </div>
                        </div>
                      </div>
                    ) : currentPageData?.video_url ? (
                      <video
                        src={currentPageData.video_url}
                        className="w-full h-full object-cover"
                        controls
                        autoPlay
                        loop
                        muted
                      />
                    ) : currentPageData?.image_url ? (
                      <img
                        src={currentPageData.image_url}
                        alt="Page illustration"
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-primary/5 to-secondary/5">
                        <span className="font-reader text-4xl text-muted-foreground/30">
                          {currentPage + 1}
                        </span>
                      </div>
                    )}
                  </motion.div>
                </AnimatePresence>
                
                <AnimatePresence mode="wait">
                  <motion.div
                    key={`right-${currentPage}`}
                    initial={{ 
                      opacity: 0, 
                      rotateY: flipDirection === 'next' ? -90 : 0,
                      x: flipDirection === 'next' ? -50 : 0,
                      scale: 0.95
                    }}
                    animate={{ 
                      opacity: 1, 
                      rotateY: 0,
                      x: 0,
                      scale: 1
                    }}
                    exit={{ 
                      opacity: 0, 
                      rotateY: flipDirection === 'prev' ? 90 : 0,
                      x: flipDirection === 'prev' ? 50 : 0,
                      scale: 0.95
                    }}
                    transition={{ 
                      duration: 0.5,
                      ease: [0.4, 0, 0.2, 1],
                      delay: 0.05
                    }}
                    style={{
                      transformStyle: 'preserve-3d',
                      transformOrigin: flipDirection === 'prev' ? 'left center' : 'right center',
                      boxShadow: '-4px 4px 20px rgba(0,0,0,0.3)'
                    }}
                    className="w-1/2 aspect-[3/4] reader-page page-shadow p-8 md:p-12 flex flex-col"
                  >
                    {currentPageData?.isChapterTitle ? (
                      // Chapter Title Page - Right side (title)
                      <div className="flex-1 flex flex-col items-center justify-center">
                        <span className="text-sm font-ui text-muted-foreground mb-4 tracking-widest uppercase">
                          Chapter {currentPageData.chapterNumber} of {currentPageData.totalChapters}
                        </span>
                        <h2 className="font-heading text-4xl md:text-5xl font-bold text-center leading-tight">
                          {currentPageData.chapterTitle}
                        </h2>
                        <div className="mt-8 w-24 h-1 bg-primary/30 rounded-full" />
                      </div>
                    ) : (
                      <>
                        <div className="flex-1 overflow-auto">
                          <p className="font-reader text-lg md:text-xl leading-relaxed whitespace-pre-wrap">
                            {currentPageData?.text_content || 'This page is empty...'}
                          </p>
                        </div>
                        <div className="text-right mt-4">
                          <span className="font-ui text-sm text-muted-foreground">
                            Page {currentPage + 1} of {totalPages}
                          </span>
                        </div>
                      </>
                    )}
                  </motion.div>
                </AnimatePresence>
              </>
            )}
          </div>
        </div>
      </div>
      
      {/* Navigation & Audio Controls */}
      <div className="glass fixed bottom-0 left-0 right-0 z-40 px-4 py-4">
        <div className="max-w-4xl mx-auto">
          {/* Page Navigation */}
          <div className="flex items-center justify-center gap-4 mb-4">
            <Button
              variant="outline"
              size="icon"
              onClick={prevPage}
              disabled={currentPage <= -1 || isFlipping}
              className="rounded-full w-12 h-12"
              data-testid="prev-page-btn"
            >
              <FiChevronLeft className="w-6 h-6" />
            </Button>
            
            <div className="px-6 py-2 rounded-full bg-muted">
              <span className="font-ui">
                {isCover ? 'Cover' : `${currentPage + 1} / ${totalPages}`}
              </span>
            </div>
            
            <Button
              variant="outline"
              size="icon"
              onClick={nextPage}
              disabled={currentPage >= totalPages - 1 || isFlipping}
              className="rounded-full w-12 h-12"
              data-testid="next-page-btn"
            >
              <FiChevronRight className="w-6 h-6" />
            </Button>
          </div>
          
          {/* Audio Controls */}
          <div className="flex items-center justify-center gap-4 flex-wrap">
            {/* Auto-read toggle */}
            <Button
              variant={autoRead ? "default" : "outline"}
              onClick={toggleAutoRead}
              className="rounded-full"
              data-testid="auto-read-btn"
            >
              {autoRead ? 'Auto-Read ON' : 'Auto-Read OFF'}
            </Button>
            
            <Button
              onClick={togglePlayPause}
              disabled={audioLoading || isCover}
              className="rounded-full w-12 h-12"
              data-testid="play-audio-btn"
            >
              {audioLoading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : isPlaying ? (
                <FiPause className="w-5 h-5" />
              ) : (
                <FiPlay className="w-5 h-5" />
              )}
            </Button>
            
            {/* Volume */}
            <div className="flex items-center gap-2 w-24">
              {volume[0] === 0 ? (
                <FiVolumeX className="w-4 h-4 text-muted-foreground" />
              ) : (
                <FiVolume2 className="w-4 h-4 text-muted-foreground" />
              )}
              <Slider
                value={volume}
                onValueChange={setVolume}
                max={100}
                step={1}
                className="flex-1"
              />
            </div>
            
            {/* Speed Control */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Speed:</span>
              <select
                value={playbackSpeed[0]}
                onChange={(e) => setPlaybackSpeed([parseFloat(e.target.value)])}
                className="bg-muted rounded-full px-3 py-1 text-sm font-ui"
              >
                <option value={0.5}>0.5x</option>
                <option value={0.75}>0.75x</option>
                <option value={1}>1x</option>
                <option value={1.25}>1.25x</option>
                <option value={1.5}>1.5x</option>
                <option value={2}>2x</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
