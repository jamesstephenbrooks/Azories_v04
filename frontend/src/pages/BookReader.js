import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { 
  FiArrowLeft, FiChevronLeft, FiChevronRight, FiMaximize2, FiMinimize2,
  FiPlay, FiPause, FiVolume2, FiVolumeX, FiSun, FiMoon
} from 'react-icons/fi';
import { useTheme } from '@/context/ThemeContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function BookReader() {
  const { bookId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  
  const [book, setBook] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isFlipping, setIsFlipping] = useState(false);
  const [flipDirection, setFlipDirection] = useState('next');
  
  // Audio state
  const [voices, setVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState('');
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioLoading, setAudioLoading] = useState(false);
  const [audioElement, setAudioElement] = useState(null);
  const [volume, setVolume] = useState([75]);
  
  // Flatten all pages from all chapters
  const [allPages, setAllPages] = useState([]);

  useEffect(() => {
    fetchBook();
    fetchVoices();
  }, [bookId]);

  useEffect(() => {
    if (searchParams.get('audio') === 'true' && allPages.length > 0) {
      // Auto-start audio mode
    }
  }, [searchParams, allPages]);

  const fetchBook = async () => {
    try {
      const res = await axios.get(`${API}/books/${bookId}/full`);
      setBook(res.data);
      
      // Flatten pages
      const pages = [];
      res.data.chapters?.forEach(chapter => {
        chapter.pages?.forEach(page => {
          pages.push({ ...page, chapterTitle: chapter.title });
        });
      });
      setAllPages(pages);
    } catch (error) {
      toast.error('Failed to load book');
      navigate('/library');
    } finally {
      setLoading(false);
    }
  };

  const fetchVoices = async () => {
    try {
      const res = await axios.get(`${API}/voices`);
      setVoices(res.data);
      if (res.data.length > 0) {
        setSelectedVoice(res.data[0].voice_id);
      }
    } catch (error) {
      console.error('Error fetching voices:', error);
    }
  };

  const goToPage = useCallback((newPage, direction) => {
    if (newPage < 0 || newPage >= allPages.length || isFlipping) return;
    
    setFlipDirection(direction);
    setIsFlipping(true);
    
    setTimeout(() => {
      setCurrentPage(newPage);
      setIsFlipping(false);
    }, 500);
  }, [allPages.length, isFlipping]);

  const nextPage = () => goToPage(currentPage + 1, 'next');
  const prevPage = () => goToPage(currentPage - 1, 'prev');

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  const playAudio = async () => {
    if (!selectedVoice || !allPages[currentPage]?.text_content) {
      toast.error('No text to read on this page');
      return;
    }

    setAudioLoading(true);
    try {
      const res = await axios.post(`${API}/tts/generate`, {
        text: allPages[currentPage].text_content,
        voice_id: selectedVoice
      });

      if (res.data.audio_base64) {
        // Stop current audio if playing
        if (audioElement) {
          audioElement.pause();
        }

        const audio = new Audio(`data:audio/mpeg;base64,${res.data.audio_base64}`);
        audio.volume = volume[0] / 100;
        audio.onended = () => setIsPlaying(false);
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

  useEffect(() => {
    if (audioElement) {
      audioElement.volume = volume[0] / 100;
    }
  }, [volume, audioElement]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowRight') nextPage();
      if (e.key === 'ArrowLeft') prevPage();
      if (e.key === 'Escape' && isFullscreen) toggleFullscreen();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentPage, isFullscreen, nextPage, prevPage]);

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

  const currentPageData = allPages[currentPage];
  const nextPageData = allPages[currentPage + 1];

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
                {currentPageData?.chapterTitle}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              className="rounded-full"
              data-testid="reader-theme-toggle"
            >
              {theme === 'dark' ? <FiSun className="w-5 h-5" /> : <FiMoon className="w-5 h-5" />}
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleFullscreen}
              className="rounded-full"
              data-testid="fullscreen-toggle"
            >
              {isFullscreen ? <FiMinimize2 className="w-5 h-5" /> : <FiMaximize2 className="w-5 h-5" />}
            </Button>
          </div>
        </div>
      </div>
      
      {/* Book Display */}
      <div className="pt-20 pb-40 px-4 flex items-center justify-center min-h-screen">
        <div className="w-full max-w-5xl book-perspective">
          <div className="flex shadow-2xl rounded-3xl overflow-hidden">
            {/* Left Page - Image/Video */}
            <AnimatePresence mode="wait">
              <motion.div
                key={`left-${currentPage}`}
                initial={{ opacity: 0, rotateY: flipDirection === 'prev' ? 90 : 0 }}
                animate={{ opacity: 1, rotateY: 0 }}
                exit={{ opacity: 0, rotateY: flipDirection === 'next' ? -90 : 0 }}
                transition={{ duration: 0.4 }}
                className="w-1/2 aspect-[3/4] reader-page page-shadow relative"
              >
                {currentPageData?.video_url ? (
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
            
            {/* Right Page - Text */}
            <AnimatePresence mode="wait">
              <motion.div
                key={`right-${currentPage}`}
                initial={{ opacity: 0, rotateY: flipDirection === 'next' ? -90 : 0 }}
                animate={{ opacity: 1, rotateY: 0 }}
                exit={{ opacity: 0, rotateY: flipDirection === 'prev' ? 90 : 0 }}
                transition={{ duration: 0.4 }}
                className="w-1/2 aspect-[3/4] reader-page page-shadow p-8 md:p-12 flex flex-col"
              >
                <div className="flex-1 overflow-auto">
                  <p className="font-reader text-lg md:text-xl leading-relaxed whitespace-pre-wrap">
                    {currentPageData?.text_content || 'This page is empty...'}
                  </p>
                </div>
                <div className="text-right mt-4">
                  <span className="font-ui text-sm text-muted-foreground">
                    Page {currentPage + 1} of {allPages.length}
                  </span>
                </div>
              </motion.div>
            </AnimatePresence>
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
              disabled={currentPage === 0 || isFlipping}
              className="rounded-full w-12 h-12"
              data-testid="prev-page-btn"
            >
              <FiChevronLeft className="w-6 h-6" />
            </Button>
            
            <div className="px-6 py-2 rounded-full bg-muted">
              <span className="font-ui">
                {currentPage + 1} / {allPages.length}
              </span>
            </div>
            
            <Button
              variant="outline"
              size="icon"
              onClick={nextPage}
              disabled={currentPage >= allPages.length - 1 || isFlipping}
              className="rounded-full w-12 h-12"
              data-testid="next-page-btn"
            >
              <FiChevronRight className="w-6 h-6" />
            </Button>
          </div>
          
          {/* Audio Controls */}
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <Select value={selectedVoice} onValueChange={setSelectedVoice}>
              <SelectTrigger 
                className="w-48 rounded-full"
                data-testid="voice-select"
              >
                <SelectValue placeholder="Select voice" />
              </SelectTrigger>
              <SelectContent>
                {voices.map((voice) => (
                  <SelectItem 
                    key={voice.voice_id} 
                    value={voice.voice_id}
                    data-testid={`voice-option-${voice.voice_id}`}
                  >
                    {voice.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <Button
              onClick={togglePlayPause}
              disabled={audioLoading}
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
            
            <div className="flex items-center gap-2 w-32">
              {volume[0] === 0 ? (
                <FiVolumeX className="w-5 h-5 text-muted-foreground" />
              ) : (
                <FiVolume2 className="w-5 h-5 text-muted-foreground" />
              )}
              <Slider
                value={volume}
                onValueChange={setVolume}
                max={100}
                step={1}
                className="flex-1"
                data-testid="volume-slider"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
