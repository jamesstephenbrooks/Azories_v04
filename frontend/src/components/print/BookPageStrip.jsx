import React, { useRef } from 'react';
import { FiChevronLeft, FiChevronRight } from 'react-icons/fi';

// Page spread thumbnails - showing image + text side by side like the actual printed book
// Includes Cover at start and Back Cover at end
export default function BookPageStrip({ 
  pages = [], 
  coverImage,
  backCoverImage,
  className = "" 
}) {
  const scrollRef = useRef(null);
  
  // Build page spreads - cover first, then each page with image + text, then back cover
  const spreads = [];
  
  // Add cover as first item
  if (coverImage) {
    spreads.push({
      type: 'cover',
      image: coverImage,
      label: 'Cover'
    });
  }
  
  // Filter out back cover and any non-content pages from the page array
  const contentPages = pages.filter(page => !page.isBackCover && !page.isTitlePage);
  
  // Add each page as a spread (image on left, text preview on right)
  contentPages.forEach((page, index) => {
    // Handle different field names that might exist
    const imageUrl = page.image_url || page.imageUrl || page.image || page.illustration_url;
    const textContent = page.text_content || page.text || page.content || page.story_text || page.page_text;
    
    spreads.push({
      type: 'page',
      image: imageUrl,
      text: textContent,
      label: `Page ${index + 1}`
    });
  });
  
  // Add back cover as last item
  if (backCoverImage) {
    spreads.push({
      type: 'backCover',
      image: backCoverImage,
      label: 'Back Cover'
    });
  }

  const scroll = (direction) => {
    if (scrollRef.current) {
      scrollRef.current.scrollBy({
        left: direction === 'left' ? -180 : 180,
        behavior: 'smooth'
      });
    }
  };

  if (spreads.length === 0) return null;

  return (
    <div className={`w-full ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">Preview All Pages</h4>
        <span className="text-xs text-purple-600 dark:text-purple-400 bg-purple-100 dark:bg-purple-900/30 px-2 py-0.5 rounded-full">
          {spreads.length} pages
        </span>
      </div>
      
      {/* Scrollable spread strip */}
      <div className="relative">
        {/* Left arrow */}
        {spreads.length > 3 && (
          <button
            onClick={() => scroll('left')}
            className="absolute left-0 top-1/2 -translate-y-1/2 z-10 w-6 h-6 bg-white shadow-md rounded-full flex items-center justify-center hover:bg-gray-50"
          >
            <FiChevronLeft className="w-4 h-4 text-gray-600" />
          </button>
        )}
        
        {/* Spreads */}
        <div
          ref={scrollRef}
          className="flex gap-3 overflow-x-auto py-2 px-1"
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        >
          {spreads.map((spread, index) => (
            <div key={index} className="flex-shrink-0">
              {spread.type === 'cover' || spread.type === 'backCover' ? (
                // Cover or Back Cover - single image
                <div className="text-center">
                  <div className="w-20 h-24 rounded shadow-md border border-gray-200 dark:border-gray-600 overflow-hidden bg-white">
                    <img
                      src={spread.image}
                      alt={spread.label}
                      className="w-full h-full object-cover"
                      loading="lazy"
                    />
                  </div>
                  <span className="text-[10px] text-gray-500 mt-1 block font-medium">
                    {spread.label}
                  </span>
                </div>
              ) : (
                // Page spread - image + text side by side
                <div className="text-center">
                  <div className="flex w-40 h-24 rounded shadow-md border border-gray-200 dark:border-gray-600 overflow-hidden bg-white">
                    {/* Left side - illustration */}
                    <div className="w-1/2 h-full overflow-hidden bg-gray-100">
                      {spread.image ? (
                        <img
                          src={spread.image}
                          alt={spread.label}
                          className="w-full h-full object-cover"
                          loading="lazy"
                        />
                      ) : (
                        <div className="w-full h-full bg-gradient-to-br from-purple-100 to-purple-200 flex items-center justify-center">
                          <span className="text-purple-400 text-[8px]">No image</span>
                        </div>
                      )}
                    </div>
                    {/* Right side - text preview */}
                    <div className="w-1/2 h-full p-1.5 bg-white overflow-hidden">
                      <p className="text-[6px] leading-tight text-gray-600 line-clamp-6 text-left">
                        {spread.text || 'Story text appears here...'}
                      </p>
                    </div>
                  </div>
                  <span className="text-[10px] text-gray-500 mt-1 block">
                    {spread.label}
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>
        
        {/* Right arrow */}
        {spreads.length > 3 && (
          <button
            onClick={() => scroll('right')}
            className="absolute right-0 top-1/2 -translate-y-1/2 z-10 w-6 h-6 bg-white shadow-md rounded-full flex items-center justify-center hover:bg-gray-50"
          >
            <FiChevronRight className="w-4 h-4 text-gray-600" />
          </button>
        )}
      </div>
      
      <style>{`
        div::-webkit-scrollbar { display: none; }
        .line-clamp-6 {
          display: -webkit-box;
          -webkit-line-clamp: 6;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
      `}</style>
    </div>
  );
}
