import React, { useState } from 'react';
import { motion } from 'framer-motion';

/**
 * 3D Book Preview Component
 * Shows a realistic preview of what the printed book will look like
 */
export default function BookPreview3D({ 
  coverImage, 
  backCoverImage,
  title, 
  authorName,
  pageCount = 24,
  className = "" 
}) {
  const [rotation, setRotation] = useState({ x: 5, y: -25 });
  const [isDragging, setIsDragging] = useState(false);
  const [startPos, setStartPos] = useState({ x: 0, y: 0 });

  // Calculate book thickness based on page count (each page ~0.1mm, so 24 pages = ~2.4mm = ~10px at scale)
  const thickness = Math.max(15, Math.min(60, pageCount * 0.8));
  
  // Book dimensions (8x10 aspect ratio scaled down)
  const bookWidth = 200;
  const bookHeight = 250;

  const handleMouseDown = (e) => {
    setIsDragging(true);
    setStartPos({ x: e.clientX, y: e.clientY });
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    const deltaX = e.clientX - startPos.x;
    const deltaY = e.clientY - startPos.y;
    setRotation({
      x: Math.max(-30, Math.min(30, rotation.x - deltaY * 0.5)),
      y: rotation.y + deltaX * 0.5
    });
    setStartPos({ x: e.clientX, y: e.clientY });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleTouchStart = (e) => {
    const touch = e.touches[0];
    setIsDragging(true);
    setStartPos({ x: touch.clientX, y: touch.clientY });
  };

  const handleTouchMove = (e) => {
    if (!isDragging) return;
    const touch = e.touches[0];
    const deltaX = touch.clientX - startPos.x;
    const deltaY = touch.clientY - startPos.y;
    setRotation({
      x: Math.max(-30, Math.min(30, rotation.x - deltaY * 0.5)),
      y: rotation.y + deltaX * 0.5
    });
    setStartPos({ x: touch.clientX, y: touch.clientY });
  };

  return (
    <div className={`flex flex-col items-center ${className}`}>
      {/* 3D Book Container */}
      <div 
        className="relative cursor-grab active:cursor-grabbing select-none"
        style={{ 
          perspective: '1000px',
          perspectiveOrigin: 'center center'
        }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleMouseUp}
      >
        <motion.div
          className="relative"
          style={{
            width: bookWidth,
            height: bookHeight,
            transformStyle: 'preserve-3d',
            transform: `rotateX(${rotation.x}deg) rotateY(${rotation.y}deg)`,
          }}
          animate={{
            rotateX: rotation.x,
            rotateY: rotation.y
          }}
          transition={{ type: 'spring', stiffness: 100, damping: 20 }}
        >
          {/* Front Cover */}
          <div
            className="absolute inset-0 rounded-r-md overflow-hidden shadow-2xl"
            style={{
              transform: `translateZ(${thickness / 2}px)`,
              backfaceVisibility: 'hidden',
            }}
          >
            {coverImage ? (
              <img 
                src={coverImage} 
                alt={title}
                className="w-full h-full object-cover"
                draggable="false"
              />
            ) : (
              <div className="w-full h-full bg-gradient-to-br from-purple-600 to-purple-900 flex items-center justify-center p-4">
                <span className="text-white text-center font-bold text-lg">{title}</span>
              </div>
            )}
            {/* Glossy overlay */}
            <div 
              className="absolute inset-0 pointer-events-none"
              style={{
                background: 'linear-gradient(135deg, rgba(255,255,255,0.3) 0%, transparent 50%, rgba(0,0,0,0.1) 100%)'
              }}
            />
          </div>

          {/* Back Cover */}
          <div
            className="absolute inset-0 rounded-l-md overflow-hidden"
            style={{
              transform: `translateZ(${-thickness / 2}px) rotateY(180deg)`,
              backfaceVisibility: 'hidden',
            }}
          >
            {backCoverImage ? (
              <img 
                src={backCoverImage} 
                alt="Back cover"
                className="w-full h-full object-cover"
                draggable="false"
              />
            ) : (
              <div className="w-full h-full bg-gradient-to-br from-purple-800 to-purple-950" />
            )}
          </div>

          {/* Spine */}
          <div
            className="absolute overflow-hidden"
            style={{
              width: thickness,
              height: bookHeight,
              left: -thickness / 2,
              transform: `rotateY(-90deg) translateZ(${bookWidth / 2}px)`,
              background: 'linear-gradient(to right, #4c1d95, #6b21a8, #4c1d95)',
            }}
          >
            {/* Spine title */}
            <div 
              className="absolute inset-0 flex items-center justify-center"
              style={{
                writingMode: 'vertical-rl',
                textOrientation: 'mixed',
                transform: 'rotate(180deg)'
              }}
            >
              <span className="text-white text-xs font-medium truncate px-1" style={{ maxHeight: bookHeight - 20 }}>
                {title}
              </span>
            </div>
          </div>

          {/* Right Edge (pages) */}
          <div
            className="absolute"
            style={{
              width: thickness,
              height: bookHeight,
              right: -thickness / 2,
              transform: `rotateY(90deg) translateZ(${bookWidth / 2}px)`,
              background: 'linear-gradient(to right, #f5f5f5, #e8e8e8, #f5f5f5)',
            }}
          >
            {/* Page lines */}
            <div className="w-full h-full flex flex-col justify-evenly px-0.5">
              {[...Array(Math.floor(pageCount / 4))].map((_, i) => (
                <div key={i} className="w-full h-px bg-gray-300" />
              ))}
            </div>
          </div>

          {/* Top Edge */}
          <div
            className="absolute"
            style={{
              width: bookWidth,
              height: thickness,
              top: -thickness / 2,
              transform: `rotateX(90deg) translateZ(${bookHeight / 2}px)`,
              background: 'linear-gradient(to bottom, #fafafa, #e5e5e5)',
            }}
          />

          {/* Bottom Edge */}
          <div
            className="absolute"
            style={{
              width: bookWidth,
              height: thickness,
              bottom: -thickness / 2,
              transform: `rotateX(-90deg) translateZ(${bookHeight / 2}px)`,
              background: 'linear-gradient(to top, #fafafa, #e5e5e5)',
            }}
          />

          {/* Shadow under book */}
          <div
            className="absolute"
            style={{
              width: bookWidth * 1.2,
              height: 30,
              bottom: -40,
              left: -bookWidth * 0.1,
              background: 'radial-gradient(ellipse at center, rgba(0,0,0,0.3) 0%, transparent 70%)',
              transform: `rotateX(90deg)`,
              filter: 'blur(5px)'
            }}
          />
        </motion.div>
      </div>

      {/* Instructions */}
      <p className="text-xs text-muted-foreground mt-4">
        Drag to rotate the book preview
      </p>

      {/* Book specs */}
      <div className="mt-4 text-center">
        <p className="text-sm font-medium text-foreground">{title}</p>
        {authorName && <p className="text-xs text-muted-foreground">by {authorName}</p>}
        <div className="flex items-center justify-center gap-4 mt-2 text-xs text-muted-foreground">
          <span>8" × 10" Hardcover</span>
          <span>•</span>
          <span>{pageCount} pages</span>
        </div>
      </div>
    </div>
  );
}
