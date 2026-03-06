import React, { useRef } from 'react';
import { FiChevronLeft, FiChevronRight } from 'react-icons/fi';

// Clean page strip showing illustration thumbnails only
export default function BookPageStrip({ 
  pages = [], 
  coverImage,
  className = "" 
}) {
  const scrollRef = useRef(null);
  
  // Build array of images - cover + page illustrations
  const allImages = [
    coverImage && { image: coverImage, label: 'Cover' },
    ...pages.map((page, index) => ({
      image: page.image_url || page.imageUrl || page.image,
      label: `Page ${index + 1}`
    }))
  ].filter(item => item && item.image);

  const scroll = (direction) => {
    if (scrollRef.current) {
      scrollRef.current.scrollBy({
        left: direction === 'left' ? -150 : 150,
        behavior: 'smooth'
      });
    }
  };

  if (allImages.length === 0) return null;

  return (
    <div className={`w-full ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">Preview All Pages</h4>
        <span className="text-xs text-purple-600 dark:text-purple-400 bg-purple-100 dark:bg-purple-900/30 px-2 py-0.5 rounded-full">
          {allImages.length} pages
        </span>
      </div>
      
      {/* Scrollable thumbnail strip */}
      <div className="relative">
        {/* Left arrow */}
        {allImages.length > 4 && (
          <button
            onClick={() => scroll('left')}
            className="absolute left-0 top-1/2 -translate-y-1/2 z-10 w-6 h-6 bg-white shadow-md rounded-full flex items-center justify-center hover:bg-gray-50"
          >
            <FiChevronLeft className="w-4 h-4 text-gray-600" />
          </button>
        )}
        
        {/* Thumbnails */}
        <div
          ref={scrollRef}
          className="flex gap-2 overflow-x-auto py-1 px-1"
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        >
          {allImages.map((item, index) => (
            <div key={index} className="flex-shrink-0 text-center">
              {/* Thumbnail image - clean, no overlay */}
              <div className={`w-16 h-20 rounded overflow-hidden shadow-sm border ${
                index === 0 ? 'border-purple-400' : 'border-gray-200 dark:border-gray-600'
              }`}>
                <img
                  src={item.image}
                  alt={item.label}
                  className="w-full h-full object-cover"
                  loading="lazy"
                />
              </div>
              {/* Label */}
              <span className="text-[10px] text-gray-500 mt-0.5 block">
                {item.label}
              </span>
            </div>
          ))}
        </div>
        
        {/* Right arrow */}
        {allImages.length > 4 && (
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
      `}</style>
    </div>
  );
}
