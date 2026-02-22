import { useRef, useState, useCallback, forwardRef, useImperativeHandle } from 'react';
import HTMLFlipBook from 'react-pageflip';
import { motion } from 'framer-motion';
import { FiBook, FiChevronLeft, FiChevronRight } from 'react-icons/fi';

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
        
        {/* Content */}
        <div className="relative h-full w-full p-6 md:p-10">
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

// Cover page component
const CoverPage = forwardRef(({ book, onClick }, ref) => {
  return (
    <div 
      ref={ref}
      className="demoPage page-wrapper relative w-full h-full cursor-pointer"
      data-density="hard"
      onClick={onClick}
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
        {/* Cover image */}
        {book?.cover_image && (
          <img 
            src={book.cover_image} 
            alt={book.title}
            className="absolute inset-0 w-full h-full object-cover opacity-90"
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

// Image-only page (for left side of spread)
const ImagePage = forwardRef(({ page, pageNumber }, ref) => {
  const hasImage = page?.image_url && page.image_url.trim() !== '';
  
  return (
    <Page ref={ref} pageNumber={pageNumber} isLeft={true}>
      <div className="h-full flex items-center justify-center p-2">
        {hasImage ? (
          <div className="w-full h-full rounded-lg overflow-hidden shadow-lg">
            <img 
              src={page.image_url} 
              alt=""
              className="w-full h-full object-cover"
              style={{
                objectFit: page.image_fit || 'cover',
                objectPosition: `${page.image_position_x || 50}% ${page.image_position_y || 50}%`
              }}
            />
          </div>
        ) : (
          <div className="w-full h-full rounded-lg bg-muted/10 border border-dashed border-muted-foreground/20 flex items-center justify-center">
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
      </div>
    </Page>
  );
});

ImagePage.displayName = 'ImagePage';

// Text-only page (for right side of spread)
const TextPage = forwardRef(({ page, pageNumber }, ref) => {
  const hasText = page?.text_content && page.text_content.trim() !== '';
  
  return (
    <Page ref={ref} pageNumber={pageNumber} isLeft={false}>
      <div className="h-full flex flex-col">
        {hasText ? (
          <p className="font-reader text-sm md:text-base leading-relaxed whitespace-pre-wrap text-foreground/90">
            {page.text_content}
          </p>
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
const ContentPage = forwardRef(({ page, pageNumber, isLeft }, ref) => {
  const hasImage = page?.image_url && page.image_url.trim() !== '';
  const hasText = page?.text_content && page.text_content.trim() !== '';
  
  return (
    <Page ref={ref} pageNumber={pageNumber} isLeft={isLeft}>
      <div className="h-full flex flex-col">
        {/* Image section - always show container for layout consistency */}
        <div 
          className={`mb-4 rounded-lg overflow-hidden flex-shrink-0 ${!hasImage ? 'bg-muted/20 border border-dashed border-muted-foreground/20' : ''}`} 
          style={{ height: hasImage || !hasText ? '45%' : '0%', minHeight: hasImage ? '120px' : hasText ? '0' : '120px' }}
        >
          {hasImage ? (
            <img 
              src={page.image_url} 
              alt=""
              className="w-full h-full object-cover"
              style={{
                objectFit: page.image_fit || 'cover',
                objectPosition: `${page.image_position_x || 50}% ${page.image_position_y || 50}%`
              }}
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
  initialPage = 0,
  width = 400,
  height = 600,
  showControls = true,
  className = ''
}, ref) => {
  const flipBookRef = useRef(null);
  const [currentPage, setCurrentPage] = useState(initialPage);
  const [isFlipping, setIsFlipping] = useState(false);
  
  // Build the page mapping once so we can track which flipbook page = which content page
  // This map tracks: flipbookPageIndex -> contentPageIndex (from pages array)
  const pageMapping = useRef([]);

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
  // Total pages should work naturally with the library
  const allBookPages = [];
  const newPageMapping = [];
  
  // Front cover - single page (hard cover)
  allBookPages.push(<CoverPage key="cover" book={book} onClick={goToNextPage} />);
  newPageMapping.push(-1); // Cover = no content page
  
  // Process content pages as spreads (image left, text right)
  pages.forEach((page, index) => {
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
        />
      );
      newPageMapping.push(index); // Text page also maps to content[index]
    }
  });
  
  // Back cover - single page (hard cover)
  // The library handles this automatically with showCover=true
  allBookPages.push(<BackCoverPage key="back-cover" book={book} />);
  newPageMapping.push(-2); // Back cover = special marker
  
  // Store the mapping
  pageMapping.current = newPageMapping;
  
  // Calculate total content spreads for page indicator
  const totalContentPages = pages.length;

  return (
    <div className={`realistic-page-flip relative ${className}`}>
      {/* Book container with 3D perspective */}
      <div 
        className="book-container relative"
        style={{ 
          perspective: '2000px',
          transformStyle: 'preserve-3d',
        }}
      >
        {/* Book shadow underneath */}
        <div 
          className="absolute -bottom-4 left-1/2 -translate-x-1/2 w-[90%] h-8 bg-black/20 rounded-full blur-xl"
          style={{ transform: 'translateX(-50%) rotateX(80deg)' }}
        />
        
        <HTMLFlipBook
          key={`flipbook-${pages.length}`}
          ref={flipBookRef}
          width={width}
          height={height}
          size="stretch"
          minWidth={250}
          maxWidth={600}
          minHeight={350}
          maxHeight={800}
          showCover={true}
          mobileScrollSupport={true}
          onFlip={handleFlip}
          onChangeState={handleFlipStart}
          className="book-flipbook"
          style={{}}
          startPage={initialPage}
          startZIndex={0}
          autoSize={true}
          maxShadowOpacity={0.5}
          drawShadow={true}
          flippingTime={600}
          usePortrait={false}
          useMouseEvents={true}
          swipeDistance={20}
          showPageCorners={true}
          clickEventForward={true}
          disableFlipByClick={false}
        >
          {allBookPages}
        </HTMLFlipBook>
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
            {currentPage === 0 ? 'Cover' : currentPage >= allBookPages.length - 1 ? 'Back Cover' : `Page ${Math.ceil(currentPage / 2)} of ${totalContentPages}`}
          </div>
          
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={goToNextPage}
            disabled={currentPage === allBookPages.length - 1 || isFlipping}
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
      `}</style>
    </div>
  );
});

RealisticPageFlip.displayName = 'RealisticPageFlip';

export default RealisticPageFlip;
export { Page, CoverPage, BackCoverPage, ChapterTitlePage, ContentPage, ImagePage, TextPage };
