import React, { useState } from 'react';

// Realistic product mockup - shows the book as a physical product
export default function BookPreview3D({ 
  coverImage, 
  title, 
  pageCount = 24,
  productType = 'softcover', // 'softcover' or 'hardcover'
  className = "" 
}) {
  const [isHardcover, setIsHardcover] = useState(productType === 'hardcover');
  
  // Calculate spine thickness based on pages
  const spineThickness = Math.max(8, Math.min(16, pageCount * 0.3));
  
  return (
    <div className={`w-full flex flex-col items-center py-3 ${className}`}>
      {/* Product type toggle */}
      <div className="flex gap-2 mb-3">
        <button
          onClick={() => setIsHardcover(false)}
          className={`px-3 py-1 text-xs rounded-full transition-colors ${
            !isHardcover 
              ? 'bg-purple-600 text-white' 
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          Softcover
        </button>
        <button
          onClick={() => setIsHardcover(true)}
          className={`px-3 py-1 text-xs rounded-full transition-colors ${
            isHardcover 
              ? 'bg-purple-600 text-white' 
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          Hardcover
        </button>
      </div>
      
      {/* Realistic Book Mockup */}
      <div 
        className="relative"
        style={{ perspective: '1000px' }}
      >
        {/* Book with realistic 3D effect */}
        <div 
          className="relative"
          style={{
            transformStyle: 'preserve-3d',
            transform: 'rotateY(-20deg) rotateX(5deg)',
          }}
        >
          {/* Hardcover case (if hardcover) */}
          {isHardcover && (
            <div 
              className="absolute -inset-1 rounded-r-sm"
              style={{
                background: 'linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%)',
                transform: 'translateZ(-4px)',
                boxShadow: '0 15px 35px rgba(0,0,0,0.3)',
              }}
            />
          )}
          
          {/* Main book body */}
          <div 
            className={`relative overflow-hidden ${isHardcover ? 'rounded-r-sm' : 'rounded-r'}`}
            style={{
              width: '140px',
              height: '190px',
              boxShadow: isHardcover 
                ? '0 20px 40px rgba(0,0,0,0.35), 0 0 0 1px rgba(0,0,0,0.1)' 
                : '0 15px 30px rgba(0,0,0,0.25)',
            }}
          >
            {/* Cover image */}
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
            <div 
              className="absolute top-0 left-0 bottom-0 pointer-events-none"
              style={{
                width: '20px',
                background: 'linear-gradient(to right, rgba(0,0,0,0.2) 0%, transparent 100%)',
              }}
            />
            
            {/* Glossy shine effect */}
            <div 
              className="absolute inset-0 pointer-events-none"
              style={{
                background: 'linear-gradient(135deg, transparent 40%, rgba(255,255,255,0.12) 50%, transparent 60%)',
              }}
            />
            
            {/* Matt lamination effect (subtle texture) */}
            <div 
              className="absolute inset-0 pointer-events-none opacity-30"
              style={{
                backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox=\'0 0 200 200\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cfilter id=\'noiseFilter\'%3E%3CfeTurbulence type=\'fractalNoise\' baseFrequency=\'0.9\' numOctaves=\'4\' stitchTiles=\'stitch\'/%3E%3C/filter%3E%3Crect width=\'100%25\' height=\'100%25\' filter=\'url(%23noiseFilter)\'/%3E%3C/svg%3E")',
              }}
            />
          </div>
          
          {/* Spine */}
          <div 
            className={`absolute top-0 h-full ${isHardcover ? 'rounded-l' : ''}`}
            style={{
              width: `${spineThickness}px`,
              left: 0,
              transform: `translateX(-${spineThickness}px) rotateY(-90deg)`,
              transformOrigin: 'right center',
              background: isHardcover
                ? 'linear-gradient(to right, #1a1a1a 0%, #2d2d2d 50%, #1a1a1a 100%)'
                : 'linear-gradient(to right, #5b21b6 0%, #7c3aed 50%, #5b21b6 100%)',
            }}
          />
          
          {/* Page edges - right side */}
          <div 
            className="absolute top-1 bottom-1 right-0"
            style={{
              width: `${spineThickness}px`,
              transform: `translateX(${spineThickness}px) rotateY(90deg)`,
              transformOrigin: 'left center',
              background: 'linear-gradient(to right, #faf9f6 0%, #f0efe9 30%, #faf9f6 100%)',
            }}
          >
            {/* Page line texture */}
            {[...Array(Math.floor(pageCount / 4))].map((_, i) => (
              <div 
                key={i}
                className="absolute w-full border-t border-gray-200/40"
                style={{ top: `${(i + 1) * (100 / (pageCount / 4))}%` }}
              />
            ))}
          </div>
          
          {/* Top pages */}
          <div 
            className="absolute left-0 right-0"
            style={{
              height: `${spineThickness}px`,
              top: 0,
              transform: `translateY(-${spineThickness}px) rotateX(90deg)`,
              transformOrigin: 'bottom center',
              background: '#faf9f6',
            }}
          />
          
          {/* Bottom pages */}
          <div 
            className="absolute left-0 right-0"
            style={{
              height: `${spineThickness}px`,
              bottom: 0,
              transform: `translateY(${spineThickness}px) rotateX(-90deg)`,
              transformOrigin: 'top center',
              background: '#f0efe9',
            }}
          />
        </div>
        
        {/* Realistic shadow */}
        <div 
          className="absolute rounded-full"
          style={{
            width: '120px',
            height: '15px',
            left: '50%',
            bottom: '-15px',
            transform: 'translateX(-50%)',
            background: 'radial-gradient(ellipse, rgba(0,0,0,0.25) 0%, transparent 70%)',
            filter: 'blur(4px)',
          }}
        />
      </div>
      
      {/* Product info */}
      <div className="flex flex-col items-center gap-1 mt-4">
        <div className="flex gap-2">
          <span className="text-[10px] text-purple-600 bg-purple-50 px-2 py-0.5 rounded-full">
            8" × 10" Premium
          </span>
          <span className="text-[10px] text-purple-600 bg-purple-50 px-2 py-0.5 rounded-full">
            {pageCount} pages
          </span>
        </div>
        <span className="text-[10px] text-gray-500">
          {isHardcover ? 'Hardcover with matt lamination' : 'Softcover with matt lamination'}
        </span>
      </div>
    </div>
  );
}
