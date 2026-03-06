import React from 'react';

// Clean, simple book preview - perfectly centered
export default function BookPreview3D({ 
  coverImage, 
  title, 
  pageCount = 24,
  className = "" 
}) {
  return (
    <div className={`w-full flex flex-col items-center py-4 ${className}`}>
      {/* Book with page edge effect */}
      <div className="relative inline-block">
        {/* Stacked page edges behind cover */}
        <div 
          className="absolute inset-0 bg-gray-200 rounded-r translate-x-2 translate-y-1"
          style={{ boxShadow: '2px 2px 8px rgba(0,0,0,0.1)' }}
        />
        <div 
          className="absolute inset-0 bg-gray-100 rounded-r translate-x-1 translate-y-0.5"
        />
        
        {/* Main book cover */}
        <div 
          className="relative w-40 h-56 sm:w-44 sm:h-60 rounded-r overflow-hidden"
          style={{
            boxShadow: '0 10px 30px rgba(0,0,0,0.2), -3px 0 10px rgba(124,58,237,0.2)',
          }}
        >
          {coverImage ? (
            <img 
              src={coverImage} 
              alt={title || 'Book cover'}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-purple-600 to-purple-900 flex items-center justify-center p-4">
              <span className="text-white text-center font-bold">
                {title || 'Your Book'}
              </span>
            </div>
          )}
          
          {/* Left spine shadow */}
          <div 
            className="absolute top-0 left-0 bottom-0 w-4"
            style={{
              background: 'linear-gradient(to right, rgba(0,0,0,0.15) 0%, transparent 100%)',
            }}
          />
          
          {/* Subtle shine */}
          <div 
            className="absolute inset-0"
            style={{
              background: 'linear-gradient(115deg, transparent 40%, rgba(255,255,255,0.08) 50%, transparent 60%)',
            }}
          />
        </div>
      </div>
      
      {/* Book specs */}
      <div className="flex justify-center gap-2 mt-4">
        <span className="bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 px-3 py-1 rounded-full text-xs font-medium">
          8" × 10" Premium
        </span>
        <span className="bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 px-3 py-1 rounded-full text-xs font-medium">
          {pageCount} pages
        </span>
      </div>
    </div>
  );
}
