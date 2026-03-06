import React, { useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { FiChevronLeft, FiChevronRight, FiX, FiZoomIn } from 'react-icons/fi';

export default function BookPageStrip({ 
  pages = [], 
  coverImage,
  title,
  className = "" 
}) {
  const scrollRef = useRef(null);
  const [selectedPage, setSelectedPage] = useState(null);
  const [showLightbox, setShowLightbox] = useState(false);
  
  // Combine cover with pages
  const allPages = [
    { image: coverImage, label: 'Cover', isCover: true },
    ...pages.map((page, index) => ({
      image: page.image_url || page.imageUrl || page.image,
      text: page.text_content || page.text || '',
      label: `Page ${index + 1}`,
      pageNumber: index + 1
    }))
  ].filter(p => p.image);

  const scroll = (direction) => {
    if (scrollRef.current) {
      const scrollAmount = 200;
      scrollRef.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth'
      });
    }
  };

  const openLightbox = (page) => {
    setSelectedPage(page);
    setShowLightbox(true);
  };

  const closeLightbox = () => {
    setShowLightbox(false);
    setSelectedPage(null);
  };

  const navigateLightbox = (direction) => {
    const currentIndex = allPages.findIndex(p => p === selectedPage);
    let newIndex = direction === 'prev' ? currentIndex - 1 : currentIndex + 1;
    if (newIndex < 0) newIndex = allPages.length - 1;
    if (newIndex >= allPages.length) newIndex = 0;
    setSelectedPage(allPages[newIndex]);
  };

  return (
    <div className={`w-full ${className}`}>
      {/* Page count label */}
      <div className="flex items-center justify-between mb-3 px-1">
        <h4 className="text-sm font-medium text-foreground">Preview All Pages</h4>
        <span className="text-xs text-muted-foreground bg-purple-100 dark:bg-purple-900/30 px-2 py-1 rounded-full">
          {allPages.length} pages
        </span>
      </div>
      
      {/* Scrollable page strip */}
      <div className="relative group">
        {/* Left scroll button */}
        <button
          onClick={() => scroll('left')}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-10 w-8 h-8 bg-white/90 dark:bg-gray-800/90 rounded-full shadow-lg flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:bg-white dark:hover:bg-gray-700"
          aria-label="Scroll left"
        >
          <FiChevronLeft className="w-5 h-5 text-gray-700 dark:text-gray-300" />
        </button>
        
        {/* Thumbnail strip */}
        <div
          ref={scrollRef}
          className="flex gap-3 overflow-x-auto scrollbar-hide py-2 px-1"
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        >
          {allPages.map((page, index) => (
            <motion.button
              key={index}
              onClick={() => openLightbox(page)}
              className="flex-shrink-0 group/thumb relative"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.98 }}
            >
              {/* Thumbnail */}
              <div className={`w-20 h-28 rounded-lg overflow-hidden shadow-md border-2 transition-all ${
                page.isCover 
                  ? 'border-purple-500 ring-2 ring-purple-300' 
                  : 'border-gray-200 dark:border-gray-700 hover:border-purple-400'
              }`}>
                <img
                  src={page.image}
                  alt={page.label}
                  className="w-full h-full object-cover"
                  loading="lazy"
                />
                {/* Zoom indicator on hover */}
                <div className="absolute inset-0 bg-black/0 group-hover/thumb:bg-black/30 transition-colors flex items-center justify-center">
                  <FiZoomIn className="w-5 h-5 text-white opacity-0 group-hover/thumb:opacity-100 transition-opacity" />
                </div>
              </div>
              
              {/* Page label */}
              <p className="text-xs text-center text-muted-foreground mt-1">
                {page.label}
              </p>
            </motion.button>
          ))}
        </div>
        
        {/* Right scroll button */}
        <button
          onClick={() => scroll('right')}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-10 w-8 h-8 bg-white/90 dark:bg-gray-800/90 rounded-full shadow-lg flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:bg-white dark:hover:bg-gray-700"
          aria-label="Scroll right"
        >
          <FiChevronRight className="w-5 h-5 text-gray-700 dark:text-gray-300" />
        </button>
      </div>
      
      {/* Lightbox for enlarged view */}
      {showLightbox && selectedPage && (
        <div 
          className="fixed inset-0 z-[200] bg-black/90 flex items-center justify-center p-4"
          onClick={closeLightbox}
        >
          {/* Close button */}
          <button
            onClick={closeLightbox}
            className="absolute top-4 right-4 w-10 h-10 bg-white/20 hover:bg-white/30 rounded-full flex items-center justify-center text-white transition-colors"
          >
            <FiX className="w-6 h-6" />
          </button>
          
          {/* Navigation buttons */}
          <button
            onClick={(e) => { e.stopPropagation(); navigateLightbox('prev'); }}
            className="absolute left-4 top-1/2 -translate-y-1/2 w-12 h-12 bg-white/20 hover:bg-white/30 rounded-full flex items-center justify-center text-white transition-colors"
          >
            <FiChevronLeft className="w-8 h-8" />
          </button>
          
          <button
            onClick={(e) => { e.stopPropagation(); navigateLightbox('next'); }}
            className="absolute right-4 top-1/2 -translate-y-1/2 w-12 h-12 bg-white/20 hover:bg-white/30 rounded-full flex items-center justify-center text-white transition-colors"
          >
            <FiChevronRight className="w-8 h-8" />
          </button>
          
          {/* Enlarged image */}
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="max-w-3xl max-h-[85vh] relative"
            onClick={(e) => e.stopPropagation()}
          >
            <img
              src={selectedPage.image}
              alt={selectedPage.label}
              className="max-w-full max-h-[80vh] object-contain rounded-lg shadow-2xl"
            />
            
            {/* Page info */}
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4 rounded-b-lg">
              <p className="text-white font-medium text-center">{selectedPage.label}</p>
              {selectedPage.text && (
                <p className="text-white/80 text-sm text-center mt-1 line-clamp-2">
                  {selectedPage.text}
                </p>
              )}
            </div>
          </motion.div>
          
          {/* Page indicator */}
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-1">
            {allPages.map((_, index) => (
              <button
                key={index}
                onClick={(e) => { e.stopPropagation(); setSelectedPage(allPages[index]); }}
                className={`w-2 h-2 rounded-full transition-colors ${
                  allPages[index] === selectedPage 
                    ? 'bg-white' 
                    : 'bg-white/40 hover:bg-white/60'
                }`}
              />
            ))}
          </div>
        </div>
      )}
      
      <style jsx>{`
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
      `}</style>
    </div>
  );
}
