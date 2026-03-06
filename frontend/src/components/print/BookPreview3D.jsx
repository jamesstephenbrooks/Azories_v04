import React, { useState } from 'react';
import { FiBook, FiRotateCw } from 'react-icons/fi';

// Premium 3D-looking book preview using CSS transforms
export default function BookPreview3D({ 
  coverImage, 
  backCoverImage,
  title, 
  pageCount = 24,
  className = "" 
}) {
  const [showBack, setShowBack] = useState(false);
  
  // Calculate spine width based on page count (visual representation)
  const spineWidth = Math.max(8, Math.min(20, pageCount * 0.5));
  
  return (
    <div className={`w-full flex flex-col items-center justify-center py-8 ${className}`}>
      {/* 3D Book Container */}
      <div 
        className="relative preserve-3d cursor-pointer group"
        style={{ 
          perspective: '1000px',
          transformStyle: 'preserve-3d'
        }}
        onClick={() => setShowBack(!showBack)}
      >
        {/* Book */}
        <div 
          className="relative transition-transform duration-700 ease-in-out"
          style={{
            transformStyle: 'preserve-3d',
            transform: showBack 
              ? 'rotateY(180deg) rotateX(5deg)' 
              : 'rotateY(-20deg) rotateX(5deg)',
            width: '200px',
            height: '270px'
          }}
        >
          {/* Front Cover */}
          <div 
            className="absolute inset-0 rounded-r-sm shadow-2xl overflow-hidden backface-hidden"
            style={{
              backfaceVisibility: 'hidden',
              transform: 'translateZ(10px)',
            }}
          >
            {coverImage ? (
              <img 
                src={coverImage} 
                alt={title}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full bg-gradient-to-br from-purple-600 via-purple-700 to-purple-900 flex items-center justify-center p-4">
                <span className="text-white text-center font-bold text-lg leading-tight">
                  {title || 'Your Book'}
                </span>
              </div>
            )}
          </div>
          
          {/* Back Cover */}
          <div 
            className="absolute inset-0 rounded-l-sm shadow-2xl overflow-hidden"
            style={{
              backfaceVisibility: 'hidden',
              transform: 'translateZ(-10px) rotateY(180deg)',
            }}
          >
            <div className="w-full h-full bg-gradient-to-br from-purple-700 via-purple-800 to-purple-900 flex flex-col items-center justify-center p-6">
              {backCoverImage ? (
                <img 
                  src={backCoverImage} 
                  alt="Back cover"
                  className="w-24 h-24 object-contain mb-4 rounded-lg"
                />
              ) : (
                <div className="w-20 h-20 bg-white/10 rounded-full flex items-center justify-center mb-4">
                  <FiBook className="w-10 h-10 text-white/60" />
                </div>
              )}
              <p className="text-white/80 text-xs text-center">
                Azories Storybooks
              </p>
              <p className="text-white/60 text-xs mt-2">
                Premium Print Edition
              </p>
            </div>
          </div>
          
          {/* Spine */}
          <div 
            className="absolute top-0 h-full bg-gradient-to-b from-purple-600 via-purple-700 to-purple-800"
            style={{
              width: `${spineWidth}px`,
              left: `-${spineWidth / 2}px`,
              transform: `translateZ(0px) rotateY(-90deg) translateX(-${spineWidth / 2}px)`,
              transformOrigin: 'left center',
            }}
          >
            <div className="h-full flex items-center justify-center">
              <p 
                className="text-white text-xs font-medium whitespace-nowrap"
                style={{
                  transform: 'rotate(-90deg)',
                  width: '250px',
                  textAlign: 'center',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}
              >
                {title?.substring(0, 40) || 'My Story Book'}
              </p>
            </div>
          </div>
          
          {/* Page edges (right side) */}
          <div 
            className="absolute top-0 h-full"
            style={{
              width: `${spineWidth}px`,
              right: `-${spineWidth / 2}px`,
              transform: `translateZ(0px) rotateY(90deg) translateX(${spineWidth / 2}px)`,
              transformOrigin: 'right center',
              background: 'linear-gradient(to right, #f5f0e6, #e8e3d9)',
            }}
          />
          
          {/* Top edge */}
          <div 
            className="absolute left-0 w-full"
            style={{
              height: `${spineWidth}px`,
              top: `-${spineWidth / 2}px`,
              transform: `translateZ(0px) rotateX(90deg) translateY(-${spineWidth / 2}px)`,
              transformOrigin: 'top center',
              background: '#f5f0e6',
            }}
          />
          
          {/* Bottom edge */}
          <div 
            className="absolute left-0 w-full"
            style={{
              height: `${spineWidth}px`,
              bottom: `-${spineWidth / 2}px`,
              transform: `translateZ(0px) rotateX(-90deg) translateY(${spineWidth / 2}px)`,
              transformOrigin: 'bottom center',
              background: '#f5f0e6',
            }}
          />
          
          {/* Inner shadow on front cover */}
          <div 
            className="absolute inset-0 pointer-events-none"
            style={{
              background: 'linear-gradient(to right, rgba(0,0,0,0.3) 0%, transparent 15%)',
              backfaceVisibility: 'hidden',
              transform: 'translateZ(10px)',
              borderRadius: '0 4px 4px 0'
            }}
          />
        </div>
        
        {/* Shadow */}
        <div 
          className="absolute bottom-0 left-1/2 -translate-x-1/2 w-48 h-6 bg-black/20 blur-xl rounded-full transition-all duration-700"
          style={{
            transform: showBack 
              ? 'translateX(-50%) translateY(30px) scaleX(0.8)' 
              : 'translateX(-50%) translateY(30px) scaleX(1.2)'
          }}
        />
      </div>
      
      {/* Rotate instruction */}
      <div className="flex items-center gap-2 mt-6 text-sm text-muted-foreground">
        <FiRotateCw className="w-4 h-4" />
        <span>Click to {showBack ? 'see front' : 'see back'}</span>
      </div>
      
      {/* Book specs */}
      <div className="flex items-center gap-4 mt-4 text-xs text-muted-foreground">
        <span className="bg-purple-100 dark:bg-purple-900/30 px-3 py-1 rounded-full">
          8" × 10" Premium
        </span>
        <span className="bg-purple-100 dark:bg-purple-900/30 px-3 py-1 rounded-full">
          {pageCount} pages
        </span>
        <span className="bg-purple-100 dark:bg-purple-900/30 px-3 py-1 rounded-full">
          Hardcover
        </span>
      </div>
      
      <style>{`
        .preserve-3d {
          transform-style: preserve-3d;
        }
        .backface-hidden {
          backface-visibility: hidden;
        }
      `}</style>
    </div>
  );
}
