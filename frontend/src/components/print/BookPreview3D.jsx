import React, { useState } from 'react';

// Pure CSS 3D Book Mockup - 8x11 Portrait Format
// Simplified perspective to avoid image distortion

export default function BookPreview3D({ 
  coverImage, 
  title, 
  pageCount = 24,
  productType = 'softcover',
  className = "" 
}) {
  const [isHardcover, setIsHardcover] = useState(productType === 'hardcover');
  
  // Book dimensions - 8x11 portrait ratio
  const bookWidth = 180;
  const bookHeight = 248; // 180 * (11/8) = 248
  
  // Calculate spine thickness based on page count
  const baseSpineWidth = Math.max(10, Math.min(35, pageCount * 0.7));
  const spineWidth = isHardcover ? baseSpineWidth + 8 : baseSpineWidth;
  
  // Page edges
  const pageEdgeWidth = Math.max(5, spineWidth * 0.4);
  
  return (
    <div className={`w-full flex flex-col items-center py-4 ${className}`}>
      {/* Product type toggle */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setIsHardcover(false)}
          className={`px-4 py-1.5 text-xs font-medium rounded-full transition-all ${
            !isHardcover 
              ? 'bg-purple-600 text-white shadow-md' 
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          Softcover
        </button>
        <button
          onClick={() => setIsHardcover(true)}
          className={`px-4 py-1.5 text-xs font-medium rounded-full transition-all ${
            isHardcover 
              ? 'bg-purple-600 text-white shadow-md' 
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          Hardcover
        </button>
      </div>
      
      {/* 3D Book Container - No perspective distortion */}
      <div 
        className="relative flex items-center justify-center"
        style={{ 
          width: '300px', 
          height: '300px',
        }}
      >
        {/* Book assembly - using simple shadow/offset for 3D effect */}
        <div className="relative" style={{ width: `${bookWidth}px`, height: `${bookHeight}px` }}>
          
          {/* Back cover shadow (creates depth) */}
          <div
            className="absolute"
            style={{
              left: `-${spineWidth + 4}px`,
              top: '8px',
              width: `${bookWidth}px`,
              height: `${bookHeight}px`,
              background: 'rgba(0,0,0,0.15)',
              borderRadius: isHardcover ? '0' : '4px',
              filter: 'blur(8px)',
            }}
          />
          
          {/* Spine */}
          <div
            className="absolute top-0 flex items-center justify-center"
            style={{
              left: `-${spineWidth}px`,
              width: `${spineWidth}px`,
              height: `${bookHeight}px`,
              background: isHardcover 
                ? 'linear-gradient(to right, #2d0055, #4a0080, #5a0090)'
                : 'linear-gradient(to right, #4a0080, #6a00b0, #5a00a0)',
              borderRadius: isHardcover ? '0' : '3px 0 0 3px',
              boxShadow: 'inset -3px 0 6px rgba(0,0,0,0.3)',
            }}
          >
            {/* Spine text */}
            <span 
              className="text-white text-[7px] font-medium tracking-wider whitespace-nowrap overflow-hidden opacity-80"
              style={{
                writingMode: 'vertical-rl',
                textOrientation: 'mixed',
                transform: 'rotate(180deg)',
                maxHeight: `${bookHeight - 30}px`,
              }}
            >
              {title || 'Book Title'}
            </span>
          </div>
          
          {/* Page edges (right side) - creates thickness illusion */}
          <div
            className="absolute top-[3px]"
            style={{
              right: `-${pageEdgeWidth}px`,
              width: `${pageEdgeWidth}px`,
              height: `${bookHeight - 6}px`,
              background: 'linear-gradient(to right, #f5f5f5, #e8e8e8, #f0f0f0)',
              borderRadius: '0 2px 2px 0',
              boxShadow: '2px 2px 4px rgba(0,0,0,0.1)',
            }}
          >
            {/* Page line texture */}
            <div 
              className="w-full h-full"
              style={{
                background: 'repeating-linear-gradient(to bottom, transparent, transparent 3px, rgba(0,0,0,0.04) 3px, rgba(0,0,0,0.04) 4px)',
              }}
            />
          </div>
          
          {/* Front Cover - FLAT, no perspective distortion */}
          <div
            className="absolute inset-0 overflow-hidden"
            style={{
              width: `${bookWidth}px`,
              height: `${bookHeight}px`,
              borderRadius: isHardcover ? '0' : '0 4px 4px 0',
              boxShadow: isHardcover 
                ? '4px 6px 20px rgba(0,0,0,0.3), 1px 2px 6px rgba(0,0,0,0.2)'
                : '3px 4px 15px rgba(0,0,0,0.25)',
              background: coverImage ? 'none' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            }}
          >
            {coverImage ? (
              <img
                src={coverImage}
                alt={title || 'Book cover'}
                className="w-full h-full object-cover"
                style={{
                  borderRadius: isHardcover ? '0' : '0 4px 4px 0',
                }}
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-white text-sm font-medium p-4 text-center">
                {title || 'Book Cover'}
              </div>
            )}
            
            {/* Subtle edge highlight for hardcover */}
            {isHardcover && (
              <div 
                className="absolute inset-0 pointer-events-none"
                style={{
                  boxShadow: 'inset 0 0 0 1px rgba(255,255,255,0.1)',
                  background: 'linear-gradient(180deg, rgba(255,255,255,0.08) 0%, transparent 30%, transparent 70%, rgba(0,0,0,0.05) 100%)',
                }}
              />
            )}
          </div>
        </div>
      </div>
      
      {/* Product info */}
      <div className="flex flex-col items-center gap-1.5 mt-2">
        <div className="flex gap-2">
          <span className="text-[10px] text-purple-600 bg-purple-50 px-2.5 py-1 rounded-full font-medium">
            8" x 11" Premium
          </span>
          <span className="text-[10px] text-purple-600 bg-purple-50 px-2.5 py-1 rounded-full font-medium">
            {pageCount} pages
          </span>
        </div>
        <span className="text-[11px] text-gray-500">
          {isHardcover ? 'Hardcover with matt lamination' : 'Softcover with matt lamination'}
        </span>
      </div>
    </div>
  );
}
