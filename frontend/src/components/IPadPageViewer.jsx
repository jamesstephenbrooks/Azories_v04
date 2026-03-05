import { useState, useRef, useCallback, forwardRef, useImperativeHandle, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiChevronLeft, FiChevronRight, FiChevronDown } from 'react-icons/fi';
import { getOptimizedImageUrl } from '@/utils/imageOptimizer';

/**
 * IPadPageViewer - A simple, conflict-free page viewer for iPad
 * 
 * Key features:
 * - NO swipe gesture detection at all
 * - 60px tap zones on left/right edges for page navigation
 * - Completely free vertical scrolling in text areas
 * - Always-visible arrow buttons
 * - Simple fade transition between pages
 * 
 * This eliminates all touch conflicts with react-pageflip.
 */

// Optimized Cloudinary URL helper
const getOptimizedCloudinaryUrl = (url, { width, quality = 'auto', format = 'auto' } = {}) => {
  return getOptimizedImageUrl(url, { width: width || 800, quality, format });
};

// Shimmer placeholder for loading states
const ImageShimmer = () => (
  <div className="absolute inset-0 bg-gradient-to-r from-muted/30 via-muted/50 to-muted/30 overflow-hidden">
    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse" 
      style={{ animation: 'shimmer 1.5s infinite' }} />
  </div>
);

// Lazy-loading image component
const LazyImage = ({ src, alt = "", className = "", style = {}, onLoad, priority = false }) => {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);
  
  const optimizedSrc = useMemo(() => {
    return getOptimizedCloudinaryUrl(src, { width: 800 });
  }, [src]);
  
  useEffect(() => {
    setLoaded(false);
    setError(false);
  }, [optimizedSrc]);
  
  if (!optimizedSrc || error) {
    return (
      <div className="absolute inset-0 bg-muted/10 flex items-center justify-center">
        <div className="text-center text-muted-foreground/40">
          <span className="text-xs">Illustration</span>
        </div>
      </div>
    );
  }
  
  return (
    <>
      {!loaded && <ImageShimmer />}
      <img 
        src={optimizedSrc}
        alt={alt}
        className={`${className} transition-opacity duration-300 ${loaded ? 'opacity-100' : 'opacity-0'}`}
        style={style}
        onLoad={() => { setLoaded(true); onLoad?.(); }}
        onError={() => setError(true)}
        loading={priority ? "eager" : "lazy"}
        decoding="async"
      />
    </>
  );
};

// Scrollable text area with scroll indicator
const ScrollableTextArea = ({ children, className = "" }) => {
  const scrollRef = useRef(null);
  const [showScrollIndicator, setShowScrollIndicator] = useState(false);
  
  useEffect(() => {
    const checkScrollable = () => {
      const el = scrollRef.current;
      if (el) {
        const hasOverflow = el.scrollHeight > el.clientHeight + 10;
        const isAtBottom = el.scrollHeight - el.scrollTop <= el.clientHeight + 10;
        setShowScrollIndicator(hasOverflow && !isAtBottom);
      }
    };
    
    checkScrollable();
    const el = scrollRef.current;
    if (el) {
      el.addEventListener('scroll', checkScrollable);
      window.addEventListener('resize', checkScrollable);
      return () => {
        el.removeEventListener('scroll', checkScrollable);
        window.removeEventListener('resize', checkScrollable);
      };
    }
  }, [children]);
  
  return (
    <div className="relative flex-1 overflow-hidden">
      {/* Text container - completely free scrolling, no touch interference */}
      <div 
        ref={scrollRef}
        className={`h-full overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-muted-foreground/30 scrollbar-track-transparent ${className}`}
        style={{ 
          touchAction: 'pan-y',  // Only vertical scrolling
          WebkitOverflowScrolling: 'touch',
          overscrollBehavior: 'contain'
        }}
      >
        {children}
      </div>
      {/* Scroll indicator */}
      {showScrollIndicator && (
        <div className="absolute bottom-0 left-0 right-0 pointer-events-none">
          <div className="h-12 bg-gradient-to-t from-[#fdfbf7] dark:from-[#2a2a30] to-transparent" />
          <div className="absolute bottom-2 left-1/2 -translate-x-1/2">
            <div className="animate-bounce bg-[#fdfbf7] dark:bg-[#2a2a30] rounded-full p-1 shadow-sm">
              <FiChevronDown className="w-4 h-4 text-purple-500/70" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Cover page component
const CoverView = ({ book, onStartReading, onStartListening }) => {
  const [imageLoaded, setImageLoaded] = useState(false);
  
  return (
    <div className="flex flex-col items-center justify-center w-full h-full p-4">
      {/* Cover image */}
      <div 
        className="relative w-full max-w-sm aspect-[3/4] rounded-xl overflow-hidden shadow-2xl"
        style={{ maxHeight: '55vh' }}
      >
        {book?.cover_image && !imageLoaded && <ImageShimmer />}
        {book?.cover_image ? (
          <img 
            src={book.cover_image}
            alt={book.title}
            className={`w-full h-full object-cover transition-opacity duration-300 ${imageLoaded ? 'opacity-100' : 'opacity-0'}`}
            onLoad={() => setImageLoaded(true)}
          />
        ) : (
          <div 
            className="w-full h-full flex flex-col items-center justify-center text-white p-6"
            style={{
              background: `linear-gradient(135deg, ${book?.cover_gradient_start || '#667eea'} 0%, ${book?.cover_gradient_end || '#764ba2'} 100%)`
            }}
          >
            <h1 className="font-heading text-2xl font-bold text-center mb-2 drop-shadow-lg">
              {book?.title}
            </h1>
            <p className="text-sm opacity-80">{book?.author_name}</p>
          </div>
        )}
      </div>
      
      {/* Action buttons */}
      <div className="flex flex-row gap-3 mt-6">
        <button
          onClick={onStartReading}
          className="px-5 py-2.5 rounded-full bg-white/90 hover:bg-white text-gray-800 font-medium flex items-center gap-2 transition-colors shadow-lg text-sm"
          data-testid="ipad-start-reading-btn"
        >
          <FiChevronRight className="w-4 h-4" />
          Read
        </button>
        <button
          onClick={onStartListening}
          className="px-5 py-2.5 rounded-full bg-purple-600 hover:bg-purple-500 text-white font-medium flex items-center gap-2 transition-colors shadow-lg text-sm"
          data-testid="ipad-start-listening-btn"
        >
          Listen
        </button>
      </div>
    </div>
  );
};

// Back cover page component
const BackCoverView = ({ book }) => {
  const hasBackCoverImage = book?.back_cover_image && book.back_cover_image.trim() !== '';
  const [imageLoaded, setImageLoaded] = useState(false);
  
  return (
    <div className="w-full h-full flex items-center justify-center p-4">
      <div 
        className="relative w-full max-w-sm aspect-[3/4] rounded-xl overflow-hidden shadow-2xl"
        style={{ 
          maxHeight: '60vh',
          background: `linear-gradient(225deg, ${book?.cover_gradient_start || '#667eea'} 0%, ${book?.cover_gradient_end || '#764ba2'} 100%)`
        }}
      >
        {hasBackCoverImage ? (
          <img 
            src={book.back_cover_image}
            alt="Back Cover"
            onLoad={() => setImageLoaded(true)}
            className={`w-full h-full object-contain transition-opacity duration-300 ${imageLoaded ? 'opacity-100' : 'opacity-0'}`}
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center text-white p-8">
            <p className="text-center opacity-80 max-w-xs leading-relaxed text-sm">
              {book?.back_cover_text || book?.description || 'Thank you for reading!'}
            </p>
            {book?.age_rating && (
              <span className="mt-6 px-4 py-1 rounded-full bg-white/20 text-sm">
                {book.age_rating}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// Content page view (image + text split or single)
const ContentPageView = ({ page, pageNumber, isLandscape }) => {
  const hasImage = page?.image_url && page.image_url.trim() !== '';
  const hasText = page?.text_content && page.text_content.trim() !== '';
  const hasVideo = page?.video_url && page.video_url.trim() !== '';
  const useVideo = page?.use_video && hasVideo;
  
  if (isLandscape) {
    // Landscape: side-by-side layout (image left, text right)
    return (
      <div className="w-full h-full flex flex-row gap-2 p-2">
        {/* Image side */}
        <div className="w-1/2 h-full relative rounded-lg overflow-hidden bg-[#fdfbf7] dark:bg-[#2a2a30] shadow-md">
          {useVideo ? (
            <video 
              src={page.video_url}
              autoPlay loop muted playsInline
              className="absolute inset-0 w-full h-full object-cover"
            />
          ) : hasImage ? (
            <LazyImage 
              src={page.image_url}
              alt=""
              style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', objectFit: 'cover' }}
              priority={true}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-muted-foreground/40">
              <span className="text-xs">No illustration</span>
            </div>
          )}
        </div>
        
        {/* Text side - COMPLETELY FREE SCROLL */}
        <div className="w-1/2 h-full flex flex-col bg-[#fdfbf7] dark:bg-[#2a2a30] rounded-lg shadow-md overflow-hidden">
          <div className="flex-1 p-4 overflow-hidden">
            {/* Chapter header if first of chapter */}
            {page?.chapterTitle && page?.isFirstOfChapter && (
              <div className="mb-2 pb-2 border-b border-muted-foreground/20">
                <span className="text-xs font-ui text-muted-foreground tracking-widest uppercase">
                  Chapter {page.chapterNumber}
                </span>
                <h3 className="font-heading text-base font-bold text-foreground mt-1">
                  {page.chapterTitle}
                </h3>
              </div>
            )}
            
            {hasText ? (
              <ScrollableTextArea>
                <p className="font-reader text-sm leading-[1.6] whitespace-pre-wrap text-foreground/90">
                  {page.text_content}
                </p>
              </ScrollableTextArea>
            ) : (
              <div className="h-full flex items-center justify-center text-muted-foreground/40">
                <span className="text-sm italic">This page has no text</span>
              </div>
            )}
          </div>
          {/* Page number */}
          <div className="px-4 pb-2 text-right">
            <span className="text-xs text-muted-foreground/60">{pageNumber}</span>
          </div>
        </div>
      </div>
    );
  }
  
  // Portrait: stacked layout (image top, text bottom)
  return (
    <div className="w-full h-full flex flex-col p-2 gap-2">
      {/* Image section */}
      <div 
        className="relative rounded-lg overflow-hidden bg-[#fdfbf7] dark:bg-[#2a2a30] shadow-md flex-shrink-0"
        style={{ height: hasImage ? '45%' : '0%', minHeight: hasImage ? '120px' : '0' }}
      >
        {useVideo ? (
          <video 
            src={page.video_url}
            autoPlay loop muted playsInline
            className="absolute inset-0 w-full h-full object-cover"
          />
        ) : hasImage ? (
          <LazyImage 
            src={page.image_url}
            alt=""
            style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', objectFit: 'cover' }}
            priority={true}
          />
        ) : null}
      </div>
      
      {/* Text section - COMPLETELY FREE SCROLL */}
      <div className="flex-1 flex flex-col bg-[#fdfbf7] dark:bg-[#2a2a30] rounded-lg shadow-md overflow-hidden">
        <div className="flex-1 p-4 overflow-hidden">
          {/* Chapter header */}
          {page?.chapterTitle && page?.isFirstOfChapter && (
            <div className="mb-2 pb-2 border-b border-muted-foreground/20">
              <span className="text-xs font-ui text-muted-foreground tracking-widest uppercase">
                Chapter {page.chapterNumber}
              </span>
              <h3 className="font-heading text-lg font-bold text-foreground mt-1">
                {page.chapterTitle}
              </h3>
            </div>
          )}
          
          {hasText ? (
            <ScrollableTextArea>
              <p className="font-reader text-base leading-[1.7] whitespace-pre-wrap text-foreground/90">
                {page.text_content}
              </p>
            </ScrollableTextArea>
          ) : (
            <div className="h-full flex items-center justify-center text-muted-foreground/40">
              <span className="text-base italic">This page has no text</span>
            </div>
          )}
        </div>
        {/* Page number */}
        <div className="px-4 pb-2 text-right">
          <span className="text-sm text-muted-foreground/60">{pageNumber}</span>
        </div>
      </div>
    </div>
  );
};

// Main IPadPageViewer component
const IPadPageViewer = forwardRef(({ 
  book, 
  pages = [], 
  onPageChange, 
  onStartReading,
  onStartListening,
  initialPage = -1, // -1 = cover
  isLandscape = false,
  isFullscreen = false,
  className = ''
}, ref) => {
  // -1 = front cover, 0 to pages.length-1 = content, pages.length = back cover (if exists)
  const [currentPage, setCurrentPage] = useState(initialPage);
  const [isTransitioning, setIsTransitioning] = useState(false);
  
  // Check if there's a back cover
  const hasBackCover = pages.some(p => p.isBackCover);
  const contentPages = pages.filter(p => !p.isBackCover);
  const totalContentPages = contentPages.length;
  const maxPage = hasBackCover ? totalContentPages : totalContentPages - 1;
  
  // Determine what we're showing
  const isCover = currentPage === -1;
  const isBackCover = currentPage === totalContentPages;
  const currentContentPage = !isCover && !isBackCover && currentPage >= 0 ? contentPages[currentPage] : null;
  
  // Navigation functions
  const goToPage = useCallback((newPage) => {
    if (newPage < -1 || newPage > maxPage || isTransitioning) return;
    
    setIsTransitioning(true);
    setTimeout(() => {
      setCurrentPage(newPage);
      onPageChange?.(newPage);
      setTimeout(() => setIsTransitioning(false), 150);
    }, 100);
  }, [maxPage, isTransitioning, onPageChange]);
  
  const nextPage = useCallback(() => {
    goToPage(currentPage + 1);
  }, [currentPage, goToPage]);
  
  const prevPage = useCallback(() => {
    goToPage(currentPage - 1);
  }, [currentPage, goToPage]);
  
  // Expose methods via ref
  useImperativeHandle(ref, () => ({
    nextPage,
    prevPage,
    goToPage,
    getCurrentPage: () => currentPage,
    getTotalPages: () => totalContentPages + 2 // +2 for covers
  }));
  
  // Handle tap zones
  const handleTapZone = useCallback((side) => {
    if (side === 'left') {
      prevPage();
    } else if (side === 'right') {
      nextPage();
    }
  }, [nextPage, prevPage]);
  
  // Handle start reading from cover
  const handleStartReading = useCallback(() => {
    goToPage(0);
    onStartReading?.();
  }, [goToPage, onStartReading]);
  
  const handleStartListening = useCallback(() => {
    goToPage(0);
    onStartListening?.();
  }, [goToPage, onStartListening]);

  return (
    <div className={`ipad-page-viewer relative w-full h-full ${className}`}>
      {/* Main content area */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentPage}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          className="w-full h-full"
        >
          {isCover ? (
            <CoverView 
              book={book} 
              onStartReading={handleStartReading}
              onStartListening={handleStartListening}
            />
          ) : isBackCover ? (
            <BackCoverView book={book} />
          ) : (
            <ContentPageView 
              page={currentContentPage}
              pageNumber={currentPage + 1}
              isLandscape={isLandscape}
            />
          )}
        </motion.div>
      </AnimatePresence>
      
      {/* LEFT TAP ZONE - 60px wide, only on content pages */}
      {!isCover && currentPage > -1 && (
        <div
          onClick={() => handleTapZone('left')}
          className="absolute left-0 top-0 bottom-0 z-40 cursor-pointer"
          style={{ width: '60px' }}
          data-testid="ipad-tap-zone-left"
        >
          {/* Visual hint on hover/touch */}
          <div className="absolute inset-0 bg-black/0 hover:bg-black/5 active:bg-black/10 transition-colors flex items-center justify-start pl-2">
            <FiChevronLeft className="w-6 h-6 text-white/0 hover:text-white/50" />
          </div>
        </div>
      )}
      
      {/* RIGHT TAP ZONE - 60px wide, only on content pages and cover */}
      {currentPage < maxPage && (
        <div
          onClick={() => handleTapZone('right')}
          className="absolute right-0 top-0 bottom-0 z-40 cursor-pointer"
          style={{ width: '60px' }}
          data-testid="ipad-tap-zone-right"
        >
          {/* Visual hint on hover/touch */}
          <div className="absolute inset-0 bg-black/0 hover:bg-black/5 active:bg-black/10 transition-colors flex items-center justify-end pr-2">
            <FiChevronRight className="w-6 h-6 text-white/0 hover:text-white/50" />
          </div>
        </div>
      )}
      
      {/* ALWAYS VISIBLE NAVIGATION ARROWS */}
      {!isCover && (
        <>
          {/* Left arrow button */}
          {currentPage > -1 && (
            <motion.button
              whileTap={{ scale: 0.9 }}
              onClick={prevPage}
              disabled={isTransitioning}
              className="absolute left-2 top-1/2 -translate-y-1/2 z-50 w-10 h-10 rounded-full bg-black/30 backdrop-blur-sm flex items-center justify-center text-white shadow-lg disabled:opacity-50"
              aria-label="Previous page"
              data-testid="ipad-prev-btn"
            >
              <FiChevronLeft className="w-5 h-5" />
            </motion.button>
          )}
          
          {/* Right arrow button */}
          {currentPage < maxPage && (
            <motion.button
              whileTap={{ scale: 0.9 }}
              onClick={nextPage}
              disabled={isTransitioning}
              className="absolute right-2 top-1/2 -translate-y-1/2 z-50 w-10 h-10 rounded-full bg-black/30 backdrop-blur-sm flex items-center justify-center text-white shadow-lg disabled:opacity-50"
              aria-label="Next page"
              data-testid="ipad-next-btn"
            >
              <FiChevronRight className="w-5 h-5" />
            </motion.button>
          )}
        </>
      )}
      
      {/* Page indicator */}
      <div className="absolute bottom-2 left-1/2 -translate-x-1/2 z-50 px-3 py-1 rounded-full bg-black/30 backdrop-blur-sm">
        <span className="text-white text-xs font-medium">
          {isCover ? 'Cover' : isBackCover ? 'Back Cover' : `${currentPage + 1} / ${totalContentPages}`}
        </span>
      </div>
      
      {/* CSS */}
      <style>{`
        @keyframes shimmer {
          0% { opacity: 0.5; }
          50% { opacity: 1; }
          100% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
});

IPadPageViewer.displayName = 'IPadPageViewer';

export default IPadPageViewer;
