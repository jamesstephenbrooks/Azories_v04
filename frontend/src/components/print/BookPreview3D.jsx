import React from 'react';

// Compact, clean book preview with subtle 3D effect
export default function BookPreview3D({ 
  coverImage, 
  title, 
  pageCount = 24,
  className = "" 
}) {
  return (
    <div className={`w-full flex flex-col items-center py-2 ${className}`}>
      {/* Book with stacked page effect */}
      <div className="relative inline-block">
        {/* Page stack behind */}
        <div className="absolute inset-0 bg-gray-100 rounded-r translate-x-1.5 translate-y-0.5 shadow-sm" />
        <div className="absolute inset-0 bg-gray-50 rounded-r translate-x-0.5" />
        
        {/* Main cover */}
        <div 
          className="relative w-36 h-48 rounded-r overflow-hidden"
          style={{ boxShadow: '0 8px 24px rgba(0,0,0,0.15)' }}
        >
          {coverImage ? (
            <img 
              src={coverImage} 
              alt={title || 'Book cover'}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-purple-500 to-purple-700 flex items-center justify-center p-3">
              <span className="text-white text-center font-semibold text-sm">
                {title || 'Your Book'}
              </span>
            </div>
          )}
          {/* Spine shadow */}
          <div className="absolute top-0 left-0 bottom-0 w-3 bg-gradient-to-r from-black/10 to-transparent" />
        </div>
      </div>
      
      {/* Specs */}
      <div className="flex gap-2 mt-3">
        <span className="text-[10px] text-purple-600 bg-purple-50 px-2 py-0.5 rounded-full">
          8" × 10" Premium
        </span>
        <span className="text-[10px] text-purple-600 bg-purple-50 px-2 py-0.5 rounded-full">
          {pageCount} pages
        </span>
      </div>
    </div>
  );
}
