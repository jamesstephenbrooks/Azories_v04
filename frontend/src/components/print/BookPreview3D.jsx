import React, { useState } from 'react';

// Pure CSS 3D Book Mockup - 8x11 Portrait Format (like real children's books)
// Cover image directly fills the front face for perfect alignment

export default function BookPreview3D({ 
  coverImage, 
  title, 
  pageCount = 24,
  productType = 'softcover',
  className = "" 
}) {
  const [isHardcover, setIsHardcover] = useState(productType === 'hardcover');
  
  // Book dimensions - 8x11 portrait ratio: 200 * (11/8) = 275px
  const bookWidth = 200;
  const bookHeight = 275;
  
  // Calculate spine thickness based on page count
  // 24 pages = ~17px (thin softcover), 32 pages = ~22px, 50 pages = ~35px
  const baseSpineWidth = Math.max(10, Math.min(35, pageCount * 0.7));
  const spineWidth = isHardcover ? baseSpineWidth + 8 : baseSpineWidth;
  
  // Page edges slightly thinner than spine
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
      
      {/* 3D Book Container */}
      <div 
        className="relative flex items-center justify-center"
        style={{ 
          width: '320px', 
          height: '320px',
          perspective: '1000px',
        }}
      >
        {/* Book wrapper with 3D transform */}
        <div
          className="relative transition-transform duration-500"
          style={{
            width: `${bookWidth}px`,
            height: `${bookHeight}px`,
            transformStyle: 'preserve-3d',
            transform: 'rotateY(-25deg) rotateX(5deg)',
          }}
        >
          {/* Front Cover - shows actual book cover image */}
          <div
            className="absolute inset-0 overflow-hidden"
            style={{
              width: `${bookWidth}px`,
              height: `${bookHeight}px`,
              borderRadius: isHardcover ? '0' : '0 4px 4px 0',
              boxShadow: isHardcover 
                ? '8px 8px 25px rgba(0,0,0,0.35), 2px 2px 8px rgba(0,0,0,0.2)'
                : '5px 5px 20px rgba(0,0,0,0.3)',
              transform: 'translateZ(1px)',
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
            
            {/* Glossy overlay for hardcover */}
            {isHardcover && (
              <div 
                className="absolute inset-0 pointer-events-none"
                style={{
                  background: 'linear-gradient(135deg, rgba(255,255,255,0.25) 0%, transparent 40%, rgba(0,0,0,0.05) 100%)',
                }}
              />
            )}
          </div>
          
          {/* Spine */}
          <div
            className="absolute top-0 flex items-center justify-center"
            style={{
              left: `-${spineWidth}px`,
              width: `${spineWidth}px`,
              height: `${bookHeight}px`,
              background: isHardcover 
                ? 'linear-gradient(to right, #2d0055, #4a0080, #3a0070)'
                : 'linear-gradient(to right, #3a0070, #5a00a0, #4a0090)',
              transform: 'rotateY(90deg)',
              transformOrigin: 'right center',
              borderRadius: isHardcover ? '0' : '2px 0 0 2px',
              boxShadow: 'inset -2px 0 4px rgba(0,0,0,0.3)',
            }}
          >
            {/* Spine text (rotated) */}
            <span 
              className="text-white text-[8px] font-medium tracking-wider whitespace-nowrap overflow-hidden"
              style={{
                writingMode: 'vertical-rl',
                textOrientation: 'mixed',
                transform: 'rotate(180deg)',
                maxHeight: `${bookHeight - 20}px`,
                textShadow: '0 1px 2px rgba(0,0,0,0.5)',
              }}
            >
              {title || 'Book Title'}
            </span>
          </div>
          
          {/* Page Edges (right side) */}
          <div
            className="absolute"
            style={{
              right: `-${pageEdgeWidth}px`,
              top: '2px',
              width: `${pageEdgeWidth}px`,
              height: `${bookHeight - 4}px`,
              background: 'linear-gradient(to right, #f8f8f8, #e8e8e8, #f0f0f0)',
              transform: 'rotateY(-90deg)',
              transformOrigin: 'left center',
              boxShadow: 'inset 2px 0 4px rgba(0,0,0,0.1)',
            }}
          >
            {/* Page lines texture */}
            <div 
              className="w-full h-full"
              style={{
                background: 'repeating-linear-gradient(to bottom, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 3px)',
              }}
            />
          </div>
          
          {/* Bottom edge (pages) */}
          <div
            className="absolute left-0"
            style={{
              bottom: `-${pageEdgeWidth * 0.5}px`,
              width: `${bookWidth}px`,
              height: `${pageEdgeWidth * 0.5}px`,
              background: 'linear-gradient(to bottom, #f0f0f0, #e0e0e0)',
              transform: 'rotateX(90deg)',
              transformOrigin: 'top center',
              boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.1)',
            }}
          />
          
          {/* Top edge (pages) */}
          <div
            className="absolute left-0"
            style={{
              top: `-${pageEdgeWidth * 0.5}px`,
              width: `${bookWidth}px`,
              height: `${pageEdgeWidth * 0.5}px`,
              background: 'linear-gradient(to top, #f8f8f8, #f0f0f0)',
              transform: 'rotateX(-90deg)',
              transformOrigin: 'bottom center',
            }}
          />
          
          {/* Back cover (barely visible) */}
          <div
            className="absolute inset-0"
            style={{
              width: `${bookWidth}px`,
              height: `${bookHeight}px`,
              background: isHardcover 
                ? 'linear-gradient(135deg, #2d0055 0%, #4a0080 100%)'
                : 'linear-gradient(135deg, #3a0070 0%, #5a00a0 100%)',
              transform: `translateZ(-${spineWidth}px)`,
              borderRadius: isHardcover ? '0' : '4px 0 0 4px',
            }}
          />
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
