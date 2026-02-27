import { useRef, useState, useCallback, forwardRef, useImperativeHandle, useEffect, useMemo } from 'react';
import HTMLFlipBook from 'react-pageflip';
import { motion } from 'framer-motion';
import { FiBook, FiChevronLeft, FiChevronRight } from 'react-icons/fi';

// Shimmer placeholder component for loading states
const ImageShimmer = () => (
  <div className="absolute inset-0 bg-gradient-to-r from-muted/30 via-muted/50 to-muted/30 animate-shimmer overflow-hidden">
    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full animate-shimmer-slide" />
  </div>
);

// Optimized lazy-loading image component with preloading and placeholder
const LazyImage = ({ src, alt = "", className = "", style = {}, onLoad, priority = false }) => {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);
  const imgRef = useRef(null);
  
  useEffect(() => {
    // Reset states when src changes
    setLoaded(false);
    setError(false);
    
    if (!src) return;
    
    // For priority images, start loading immediately
    if (priority) {
      const img = new Image();
      img.onload = () => {
        setLoaded(true);
        onLoad?.();
      };
      img.onerror = () => setError(true);
      img.src = src;
    }
  }, [src, priority, onLoad]);
  
  const handleImageLoad = () => {
    setLoaded(true);
    onLoad?.();
  };
  
  const handleImageError = () => {
    setError(true);
  };
  
  if (!src || error) {
    return (
      <div className="absolute inset-0 bg-muted/10 flex items-center justify-center">
        <div className="text-center text-muted-foreground/40">
          <div className="w-16 h-16 mx-auto mb-2 rounded-full bg-muted/20 flex items-center justify-center">
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <span className="text-xs">Illustration</span>
        </div>
      </div>
    );
  }
  
  return (
    <>
      {/* Shimmer placeholder - visible until image loads */}
      {!loaded && <ImageShimmer />}
      
      {/* Actual image with fade-in effect */}
      <img 
        ref={imgRef}
        src={src}
        alt={alt}
        className={`${className} transition-opacity duration-300 ${loaded ? 'opacity-100' : 'opacity-0'}`}
        style={style}
        onLoad={handleImageLoad}
        onError={handleImageError}
        loading={priority ? "eager" : "lazy"}
        decoding="async"
      />
    </>
  );
};

// Image preloader cache - stores preloaded image URLs
const imagePreloadCache = new Set();

// Preload an image in the background
const preloadImage = (url) => {
  if (!url || imagePreloadCache.has(url)) return;
  
  const img = new Image();
  img.onload = () => imagePreloadCache.add(url);
  img.src = url;
};

// Individual page component with realistic styling
const Page = forwardRef(({ pageNumber, children, isLeft, isCover, isBackCover }, ref) => {
  return (
    <div 
      ref={ref}
      className="demoPage page-wrapper relative w-full h-full"
      data-density={isCover || isBackCover ? "hard" : "soft"}
    >
      <div 
        className={`
          absolute inset-0 bg-[#fdfbf7] dark:bg-[#2a2a30]
          ${isCover ? 'rounded-r-lg' : isBackCover ? 'rounded-l-lg' : ''}
          overflow-hidden
        `}
        style={{
          boxShadow: isLeft 
            ? 'inset -7px 0 30px -7px rgba(0,0,0,0.12)' 
            : 'inset 7px 0 30px -7px rgba(0,0,0,0.12)',
        }}
      >
        {/* Page texture overlay */}
        <div 
          className="absolute inset-0 pointer-events-none opacity-[0.03]"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
          }}
        />
        
        {/* Spine shadow gradient */}
        {isLeft ? (
          <div className="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-black/10 to-transparent pointer-events-none z-10" />
        ) : (
          <div className="absolute left-0 top-0 bottom-0 w-8 bg-gradient-to-r from-black/10 to-transparent pointer-events-none z-10" />
        )}
        
        {/* Content - reduced bottom padding to fit more text */}
        <div className="relative h-full w-full p-4 md:p-6 pb-8">
          {children}
        </div>
        
        {/* Page number */}
        {!isCover && !isBackCover && pageNumber && (
          <div className={`absolute bottom-4 ${isLeft ? 'left-6' : 'right-6'} text-sm text-muted-foreground/60`}>
            {pageNumber}
          </div>
        )}
        
        {/* Page corner curl effect for right pages */}
        {!isLeft && !isCover && !isBackCover && (
          <div 
            className="absolute bottom-0 right-0 w-12 h-12 pointer-events-none overflow-hidden"
          >
            <div 
              className="absolute -bottom-6 -right-6 w-16 h-16 rotate-45"
              style={{
                background: 'linear-gradient(135deg, transparent 50%, rgba(0,0,0,0.05) 50%, rgba(255,255,255,0.9) 51%, #f5f5f5 100%)',
                boxShadow: '-2px -2px 5px rgba(0,0,0,0.1)',
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
});

Page.displayName = 'Page';

// Cover page component - simple cover without hover overlay (buttons are external)
// Enhanced with lazy loading for cover image
const CoverPage = forwardRef(({ book }, ref) => {
  return (
    <div 
      ref={ref}
      className="demoPage page-wrapper relative w-full h-full cursor-pointer group"
      data-density="hard"
    >
      <div 
        className="absolute inset-0 rounded-r-lg overflow-hidden"
        style={{
          background: `linear-gradient(135deg, 
            ${book?.cover_gradient_start || '#667eea'} 0%, 
            ${book?.cover_gradient_end || '#764ba2'} 100%)`,
          boxShadow: '5px 0 15px rgba(0,0,0,0.3)',
        }}
      >
        {/* Cover image with lazy loading */}
        {book?.cover_image && (
          <LazyImage 
            src={book.cover_image}
            alt={book.title}
            className="absolute inset-0 w-full h-full object-cover opacity-90"
            priority={true}
          />
        )}
        
        {/* Cover overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/20" />
        
        {/* Cover content */}
        <div className="relative h-full flex flex-col items-center justify-center text-white p-8">
          <h1 className="font-heading text-3xl md:text-4xl font-bold text-center mb-4 drop-shadow-lg">
            {book?.title}
          </h1>
          <p className="text-lg opacity-80 drop-shadow">{book?.author_name}</p>
        </div>
        
        {/* Spine effect */}
        <div className="absolute left-0 top-0 bottom-0 w-4 bg-gradient-to-r from-black/40 to-transparent" />
      </div>
    </div>
  );
});

CoverPage.displayName = 'CoverPage';

// Back cover page component
const BackCoverPage = forwardRef(({ book }, ref) => {
  return (
    <div 
      ref={ref}
      className="demoPage page-wrapper relative w-full h-full"
      data-density="hard"
    >
      <div 
        className="absolute inset-0 rounded-l-lg overflow-hidden"
        style={{
          background: `linear-gradient(225deg, 
            ${book?.cover_gradient_start || '#667eea'} 0%, 
            ${book?.cover_gradient_end || '#764ba2'} 100%)`,
          boxShadow: '-5px 0 15px rgba(0,0,0,0.3)',
        }}
      >
        {/* Back cover content */}
        <div className="relative h-full flex flex-col items-center justify-center text-white p-8">
          <p className="text-center opacity-80 max-w-xs leading-relaxed">
            {book?.back_cover_text || book?.description || 'Thank you for reading!'}
          </p>
          {book?.age_rating && (
            <span className="mt-6 px-4 py-1 rounded-full bg-white/20 text-sm">
              {book.age_rating}
            </span>
          )}
        </div>
        
        {/* Spine effect */}
        <div className="absolute right-0 top-0 bottom-0 w-4 bg-gradient-to-l from-black/40 to-transparent" />
      </div>
    </div>
  );
});

BackCoverPage.displayName = 'BackCoverPage';

// Chapter title page component
const ChapterTitlePage = forwardRef(({ chapter, chapterNumber, totalChapters, isLeft }, ref) => {
  return (
    <Page ref={ref} isLeft={isLeft}>
      <div className="h-full flex flex-col items-center justify-center">
        <span className="text-sm font-ui text-muted-foreground mb-4 tracking-widest uppercase">
          Chapter {chapterNumber} of {totalChapters}
        </span>
        <h2 className="font-heading text-2xl md:text-3xl font-bold text-center leading-tight">
          {chapter?.title || `Chapter ${chapterNumber}`}
        </h2>
        <div className="mt-8 flex gap-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="w-2 h-2 rounded-full bg-primary/30" />
          ))}
        </div>
      </div>
    </Page>
  );
});

ChapterTitlePage.displayName = 'ChapterTitlePage';

// Image-only page (for left side of spread) - now supports video too
// Images and videos fill the entire page and are centered
// Enhanced with lazy loading, shimmer placeholders, and preloading
const ImagePage = forwardRef(({ page, pageNumber, isCurrentPage = false, onImageLoad }, ref) => {
  const hasImage = page?.image_url && page.image_url.trim() !== '';
  const hasVideo = page?.video_url && page.video_url.trim() !== '';
  const useVideo = page?.use_video && hasVideo;
  
  return (
    <div 
      ref={ref}
      className="demoPage page-wrapper relative w-full h-full"
      data-density="soft"
      data-page-number={pageNumber}
    >
      {/* Full-page media container - no padding, fills entire page */}
      <div 
        className="absolute inset-0 bg-[#fdfbf7] dark:bg-[#2a2a30] overflow-hidden"
        style={{
          boxShadow: 'inset -7px 0 30px -7px rgba(0,0,0,0.12)',
        }}
      >
        {/* Spine shadow gradient */}
        <div className="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-black/10 to-transparent pointer-events-none z-10" />
        
        {/* Full-page media - centered and covering the entire page */}
        {useVideo ? (
          <video 
            src={page.video_url}
            autoPlay
            loop
            muted
            playsInline
            className="absolute inset-0 w-full h-full"
            style={{
              objectFit: 'cover',
              objectPosition: 'center'
            }}
          />
        ) : hasImage ? (
          <LazyImage 
            src={page.image_url}
            alt=""
            className="absolute inset-0 w-full h-full"
            style={{
              objectFit: 'cover',
              objectPosition: `${page.image_position_x || 50}% ${page.image_position_y || 50}%`
            }}
            priority={isCurrentPage}
            onLoad={onImageLoad}
          />
        ) : (
          <div className="absolute inset-0 bg-muted/10 flex items-center justify-center">
            <div className="text-center text-muted-foreground/40">
              <div className="w-16 h-16 mx-auto mb-2 rounded-full bg-muted/20 flex items-center justify-center">
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <span className="text-xs">Illustration</span>
            </div>
          </div>
        )}
        
        {/* Page number overlay */}
        {pageNumber && (
          <div className="absolute bottom-4 left-6 text-sm text-white/70 drop-shadow-lg z-20">
            {pageNumber}
          </div>
        )}
      </div>
    </div>
  );
});

ImagePage.displayName = 'ImagePage';

// Text-only page (for right side of spread) - with auto-sizing and scroll for long text
const TextPage = forwardRef(({ page, pageNumber, isFirstOfChapter }, ref) => {
  const hasText = page?.text_content && page.text_content.trim() !== '';
  const textLength = page?.text_content?.length || 0;
  
  // Get font classes based on page settings
  const getFontClass = () => {
    switch (page?.font_family) {
      case 'serif': return 'font-serif';
      case 'sans': return 'font-sans';
      case 'mono': return 'font-mono';
      default: return 'font-reader';
    }
  };
  
  // Auto-size font based on text length
  const getAutoSizeClass = () => {
    // For very long text, use smaller font
    if (textLength > 800) return 'text-xs leading-snug';
    if (textLength > 600) return 'text-xs md:text-sm leading-snug';
    if (textLength > 400) return 'text-sm leading-relaxed';
    // Default/short text
    switch (page?.font_size) {
      case 'small': return 'text-xs md:text-sm leading-relaxed';
      case 'large': return 'text-base md:text-lg leading-relaxed';
      case 'xlarge': return 'text-lg md:text-xl leading-relaxed';
      default: return 'text-sm md:text-base leading-relaxed';
    }
  };
  
  const getAlignClass = () => {
    switch (page?.text_align) {
      case 'center': return 'text-center';
      case 'right': return 'text-right';
      case 'justify': return 'text-justify';
      default: return 'text-left';
    }
  };
  
  return (
    <Page ref={ref} pageNumber={pageNumber} isLeft={false}>
      <div className="h-full flex flex-col overflow-hidden">
        {/* Chapter title header for first page of chapter */}
        {isFirstOfChapter && page?.chapterTitle && (
          <div className="mb-3 pb-2 border-b border-muted-foreground/20 flex-shrink-0">
            <span className="text-xs font-ui text-muted-foreground tracking-widest uppercase">
              Chapter {page.chapterNumber}
            </span>
            <h3 className="font-heading text-base font-bold text-foreground mt-1">
              {page.chapterTitle}
            </h3>
          </div>
        )}
        
        {hasText ? (
          <div className="flex-1 overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-muted-foreground/20 scrollbar-track-transparent">
            <p className={`${getFontClass()} ${getAutoSizeClass()} ${getAlignClass()} whitespace-pre-wrap text-foreground/90`}>
              {page.text_content}
            </p>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground/40">
            <span className="text-sm italic">This page has no text</span>
          </div>
        )}
      </div>
    </Page>
  );
});

TextPage.displayName = 'TextPage';

// Legacy content page for single-page view (image above text)
// Enhanced with lazy loading
const ContentPage = forwardRef(({ page, pageNumber, isLeft, isCurrentPage = false }, ref) => {
  const hasImage = page?.image_url && page.image_url.trim() !== '';
  const hasText = page?.text_content && page.text_content.trim() !== '';
  
  return (
    <Page ref={ref} pageNumber={pageNumber} isLeft={isLeft}>
      <div className="h-full flex flex-col">
        {/* Image section - always show container for layout consistency */}
        <div 
          className={`mb-4 rounded-lg overflow-hidden flex-shrink-0 relative ${!hasImage ? 'bg-muted/20 border border-dashed border-muted-foreground/20' : ''}`} 
          style={{ height: hasImage || !hasText ? '45%' : '0%', minHeight: hasImage ? '120px' : hasText ? '0' : '120px' }}
        >
          {hasImage ? (
            <LazyImage 
              src={page.image_url}
              alt=""
              className="w-full h-full object-cover"
              style={{
                objectFit: page.image_fit || 'cover',
                objectPosition: `${page.image_position_x || 50}% ${page.image_position_y || 50}%`
              }}
              priority={isCurrentPage}
            />
          ) : !hasText ? (
            <div className="w-full h-full flex items-center justify-center text-muted-foreground/40">
              <span className="text-sm">No illustration</span>
            </div>
          ) : null}
        </div>
        
        {/* Text content */}
        <div className="flex-1 overflow-hidden">
          {hasText ? (
            <p className="font-reader text-base md:text-lg leading-relaxed whitespace-pre-wrap text-foreground/90">
              {page.text_content}
            </p>
          ) : (
            <div className="h-full flex items-center justify-center text-muted-foreground/40">
              <span className="text-sm italic">This page has no content</span>
            </div>
          )}
        </div>
      </div>
    </Page>
  );
});

ContentPage.displayName = 'ContentPage';

// Main RealisticPageFlip component
const RealisticPageFlip = forwardRef(({ 
  book, 
  pages = [], 
  onPageChange, 
  onFlipStart,
  onFlipEnd,
  onStartReading,
  onStartListening,
  initialPage = 0,
  width = 400,
  height = 600,
  showControls = true,
  className = '',
  isFullscreen = false,
  isMobilePortrait = false
}, ref) => {
  const flipBookRef = useRef(null);
  const [currentPage, setCurrentPage] = useState(initialPage);
  const [isFlipping, setIsFlipping] = useState(false);
  
  // Build the page mapping once so we can track which flipbook page = which content page
  // This map tracks: flipbookPageIndex -> contentPageIndex (from pages array)
  const pageMapping = useRef([]);
  
  // Preload images for upcoming pages when current page changes
  useEffect(() => {
    if (pages.length === 0) return;
    
    // Calculate which content pages to preload (current + next 2-3 pages)
    const contentPageIndex = pageMapping.current[currentPage] ?? -1;
    
    // Preload current page and next 3 content pages
    for (let i = 0; i <= 3; i++) {
      const pageIdx = contentPageIndex + i;
      if (pageIdx >= 0 && pageIdx < pages.length) {
        const page = pages[pageIdx];
        if (page?.image_url) {
          preloadImage(page.image_url);
        }
      }
    }
  }, [currentPage, pages]);

  // Expose methods via ref
  useImperativeHandle(ref, () => ({
    nextPage: () => flipBookRef.current?.pageFlip()?.flipNext(),
    prevPage: () => flipBookRef.current?.pageFlip()?.flipPrev(),
    goToPage: (pageNum) => flipBookRef.current?.pageFlip()?.flip(pageNum),
    getCurrentPage: () => currentPage,
    getTotalPages: () => pages.length + 2, // +2 for cover and back cover
    // Get the content page index for audio sync
    getContentPageIndex: (flipPageNum) => pageMapping.current[flipPageNum] ?? -1,
  }));

  const handleFlip = useCallback((e) => {
    const newFlipPage = e.data;
    setCurrentPage(newFlipPage);
    
    // Map flipbook page to content page index for voiceover sync
    // The mapping tells us which content page this flipbook page corresponds to
    const contentPageIndex = pageMapping.current[newFlipPage] ?? -1;
    onPageChange?.(newFlipPage, contentPageIndex);
  }, [onPageChange]);

  const handleFlipStart = useCallback((e) => {
    // e.data is the state: "user_fold", "fold_corner", "flipping", "read"
    if (e.data === 'flipping') {
      setIsFlipping(true);
      onFlipStart?.();
    } else if (e.data === 'read') {
      setIsFlipping(false);
      onFlipEnd?.();
    }
  }, [onFlipStart, onFlipEnd]);

  const goToNextPage = () => {
    flipBookRef.current?.pageFlip()?.flipNext();
  };

  const goToPrevPage = () => {
    flipBookRef.current?.pageFlip()?.flipPrev();
  };

  // Build all pages array - create spreads with image on left, text on right
  // IMPORTANT: For react-pageflip with showCover=true:
  // - Front cover is page 0 (single page, shown alone on right)
  // - After flipping cover, first spread is pages 1-2
  // - Back cover should be the last page (single page, shown alone on left)
  // Note: showCover=true creates a blank adjacent page which is unavoidable
  const allBookPages = [];
  const newPageMapping = [];
  
  // Front cover - single page (hard cover)
  allBookPages.push(
    <CoverPage 
      key="cover" 
      book={book} 
    />
  );
  newPageMapping.push(-1); // Cover = no content page
  
  // Process content pages as spreads (image left, text right)
  let lastChapterNumber = null;
  pages.forEach((page, index) => {
    // Check if this is the first page of a new chapter
    const isFirstOfChapter = page.chapterNumber !== lastChapterNumber;
    lastChapterNumber = page.chapterNumber;
    
    if (page.isChapterTitle) {
      // Chapter titles get their own spread
      allBookPages.push(
        <ChapterTitlePage 
          key={`chapter-${index}`}
          chapter={page}
          chapterNumber={page.chapterNumber}
          totalChapters={page.totalChapters}
          isLeft={true}
        />
      );
      newPageMapping.push(index); // Map to content index
      
      // Add blank right page after chapter title
      allBookPages.push(
        <Page key={`chapter-blank-${index}`} isLeft={false}>
          <div className="h-full" />
        </Page>
      );
      newPageMapping.push(index); // Still same content page
    } else {
      // Regular content: Image on left page, Text on right page
      // Both the image and text page correspond to the SAME content page
      allBookPages.push(
        <ImagePage 
          key={`img-${index}`}
          page={page}
          pageNumber={index + 1}
        />
      );
      newPageMapping.push(index); // Image page maps to content[index]
      
      allBookPages.push(
        <TextPage 
          key={`txt-${index}`}
          page={page}
          pageNumber={index + 1}
          isFirstOfChapter={isFirstOfChapter}
        />
      );
      newPageMapping.push(index); // Text page also maps to content[index]
    }
  });
  
  // Back cover - single page (hard cover)
  // Note: showCover=true creates a blank adjacent page which is unavoidable
  allBookPages.push(<BackCoverPage key="back-cover" book={book} />);
  newPageMapping.push(-2); // Back cover = special marker
  
  // Store the mapping
  pageMapping.current = newPageMapping;
  
  // Calculate total content spreads for page indicator
  const totalContentPages = pages.length;
  const totalFlipbookPages = allBookPages.length;

  // Check if we're on cover (first page) or back cover (last page)
  // react-pageflip uses 0-indexed pages, back cover is the last page
  const isOnFrontCover = currentPage === 0;
  const isOnBackCover = currentPage >= totalFlipbookPages - 2; // Back cover is last or second-to-last due to spread display
  const shouldClipLeft = isOnFrontCover;
  const shouldClipRight = isOnBackCover && !isOnFrontCover;
  
  // Calculate shift amount - need extra shift to center with controls below
  // In mobile portrait mode, no shift needed since it's single page
  const coverShift = isMobilePortrait ? 0 : (width / 2) + 80;

  return (
    <div className={`realistic-page-flip relative ${className}`} style={{ 
      // Set minimum dimensions to ensure book displays at proper size
      minWidth: isMobilePortrait ? '280px' : `${width * 2}px`,
      minHeight: `${height}px`,
      transformOrigin: 'center center' 
    }}>
      {/* Book container with 3D perspective */}
      <div 
        className="book-container relative flex justify-center"
        style={{ 
          perspective: '2000px',
          transformStyle: 'preserve-3d',
        }}
      >
        {/* Wrapper that gets clipped and positioned */}
        <div 
          style={{
            // Shift LEFT to center when showing front cover (clip left, visible part moves to center)
            // Shift RIGHT to center when showing back cover (clip right, visible part moves to center)
            // In mobile portrait mode, no shifting needed
            marginLeft: isMobilePortrait ? '0' : (shouldClipLeft ? `-${coverShift}px` : shouldClipRight ? `${coverShift}px` : '0'),
            transition: 'margin 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
          }}
        >
          {/* Clip the appropriate side when showing covers - not needed in portrait mode */}
          <div 
            style={{
              overflow: (!isMobilePortrait && (shouldClipLeft || shouldClipRight)) ? 'hidden' : 'visible',
              // Clip left half for front cover, right half for back cover (only in landscape/spread mode)
              clipPath: isMobilePortrait ? 'none' : (shouldClipLeft ? 'inset(0 0 0 50%)' : shouldClipRight ? 'inset(0 50% 0 0)' : 'none'),
              transition: 'clip-path 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
            }}
          >
          {/* Book shadow underneath */}
          <div 
            className="absolute -bottom-4 left-1/2 -translate-x-1/2 w-[90%] h-8 bg-black/20 rounded-full blur-xl"
            style={{ transform: 'translateX(-50%) rotateX(80deg)' }}
          />
        
        <HTMLFlipBook
          key={`flipbook-${pages.length}-${isMobilePortrait ? 'portrait' : 'landscape'}`}
          ref={flipBookRef}
          width={width}
          height={height}
          size="fixed"
          minWidth={isMobilePortrait ? 200 : 400}
          maxWidth={2000}
          minHeight={isMobilePortrait ? 300 : 500}
          maxHeight={2400}
          showCover={true}
          mobileScrollSupport={true}
          onFlip={handleFlip}
          onChangeState={handleFlipStart}
          className={`book-flipbook ${currentPage === 0 ? 'cover-view' : ''} ${isMobilePortrait ? 'mobile-portrait' : ''}`}
          style={{}}
          startPage={initialPage}
          startZIndex={0}
          autoSize={false}
          maxShadowOpacity={isMobilePortrait ? 0.3 : 0.5}
          drawShadow={true}
          flippingTime={isMobilePortrait ? 400 : 650}
          usePortrait={isMobilePortrait}
          disableFlipByClick={false}
          useMouseEvents={true}
          swipeDistance={isMobilePortrait ? 20 : 30}
          showPageCorners={!isMobilePortrait}
          clickEventForward={true}
        >
          {allBookPages}
        </HTMLFlipBook>
          </div>
        </div>
      </div>

      {/* Navigation controls */}
      {showControls && (
        <div className="flex items-center justify-center gap-6 mt-6">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={goToPrevPage}
            disabled={currentPage === 0 || isFlipping}
            className="w-12 h-12 rounded-full bg-primary/10 hover:bg-primary/20 flex items-center justify-center text-primary disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            aria-label="Previous page"
          >
            <FiChevronLeft className="w-6 h-6" />
          </motion.button>
          
          <div className="text-sm text-muted-foreground">
            {currentPage === 0 ? 'Cover' : currentPage >= totalFlipbookPages - 2 ? 'Back Cover' : `Page ${Math.ceil(currentPage / 2)} of ${totalContentPages}`}
          </div>
          
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={goToNextPage}
            disabled={currentPage >= totalFlipbookPages - 1 || isFlipping}
            className="w-12 h-12 rounded-full bg-primary/10 hover:bg-primary/20 flex items-center justify-center text-primary disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            aria-label="Next page"
          >
            <FiChevronRight className="w-6 h-6" />
          </motion.button>
        </div>
      )}

      {/* CSS for realistic effects */}
      <style>{`
        .demoPage {
          background-color: #fdfbf7;
        }
        
        .book-flipbook {
          box-shadow: 
            0 0 20px rgba(0,0,0,0.2),
            0 20px 50px rgba(0,0,0,0.3);
          border-radius: 0 8px 8px 0;
        }
        
        .book-flipbook .stf__parent {
          transform-style: preserve-3d;
        }
        
        .book-flipbook .stf__wrapper {
          transform-style: preserve-3d;
        }
        
        .book-flipbook .stf__block {
          transform-style: preserve-3d;
        }
        
        /* Hide the blank left page when showing cover (first page) */
        .book-flipbook.cover-view .stf__block:first-child .--left:first-child {
          visibility: hidden !important;
          opacity: 0 !important;
        }
        
        /* When on cover, shift the book to center the cover */
        .book-flipbook.cover-view .stf__parent {
          transform: translateX(25%) !important;
        }
        
        /* Realistic page shadow during flip */
        .book-flipbook .stf__item {
          background: linear-gradient(to right, 
            rgba(0,0,0,0.1) 0%, 
            transparent 5%, 
            transparent 95%, 
            rgba(0,0,0,0.05) 100%
          );
        }
        
        /* Page fold effect */
        .book-flipbook .--left {
          border-right: 1px solid rgba(0,0,0,0.1);
          background: linear-gradient(to left, rgba(0,0,0,0.05) 0%, transparent 10%);
        }
        
        .book-flipbook .--right {
          border-left: 1px solid rgba(0,0,0,0.05);
          background: linear-gradient(to right, rgba(0,0,0,0.05) 0%, transparent 10%);
        }
        
        /* Hard cover styling */
        .book-flipbook [data-density="hard"] {
          background: inherit !important;
        }
        
        /* Smooth animations */
        .book-flipbook * {
          -webkit-font-smoothing: antialiased;
        }
        
        /* Page corner hover effect */
        .page-wrapper:hover .page-corner-hint {
          opacity: 1;
          transform: translate(0, 0) rotate(-10deg);
        }
        
        .page-corner-hint {
          opacity: 0;
          transform: translate(10px, 10px) rotate(0deg);
          transition: all 0.3s ease;
        }
        
        /* Shimmer animation for image loading placeholders */
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
        
        @keyframes shimmer-slide {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(200%); }
        }
        
        .animate-shimmer {
          background-size: 200% 100%;
          animation: shimmer 1.5s infinite linear;
        }
        
        .animate-shimmer-slide {
          animation: shimmer-slide 1.5s infinite ease-in-out;
        }
      `}</style>
    </div>
  );
});

RealisticPageFlip.displayName = 'RealisticPageFlip';

export default RealisticPageFlip;
export { Page, CoverPage, BackCoverPage, ChapterTitlePage, ContentPage, ImagePage, TextPage };
