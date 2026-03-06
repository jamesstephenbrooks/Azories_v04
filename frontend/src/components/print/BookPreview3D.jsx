import React, { useState } from 'react';

// Cloudinary mockup images
const SOFTCOVER_MOCKUP = 'https://res.cloudinary.com/dlbmjqmoy/image/upload/v1772832658/azories/mockups/softcover_mockup.png';
const HARDCOVER_MOCKUP = 'https://res.cloudinary.com/dlbmjqmoy/image/upload/v1772832666/azories/mockups/hardcover_mockup.png';

// Realistic product mockup with cover overlay
export default function BookPreview3D({ 
  coverImage, 
  title, 
  pageCount = 24,
  productType = 'softcover',
  className = "" 
}) {
  const [isHardcover, setIsHardcover] = useState(productType === 'hardcover');
  
  // Cover overlay positioning (carefully measured from the mockup images)
  // Softcover: book is angled slightly, cover area needs perspective transform
  // Hardcover: similar angle but slightly different dimensions
  
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
      
      {/* Mockup container */}
      <div 
        className="relative"
        style={{ 
          width: '280px', 
          height: '280px',
        }}
      >
        {/* Base mockup image */}
        <img
          src={isHardcover ? HARDCOVER_MOCKUP : SOFTCOVER_MOCKUP}
          alt={isHardcover ? 'Hardcover book mockup' : 'Softcover book mockup'}
          className="w-full h-full object-contain"
        />
        
        {/* Cover image overlay - positioned to match the grey area in mockup */}
        {coverImage && (
          <div
            className="absolute overflow-hidden"
            style={isHardcover ? {
              // Hardcover positioning - accounts for thicker spine
              top: '4%',
              left: '24%',
              width: '48%',
              height: '85%',
              borderRadius: '2px',
            } : {
              // Softcover positioning
              top: '5%',
              left: '21%', 
              width: '51%',
              height: '84%',
              borderRadius: '2px',
            }}
          >
            <img
              src={coverImage}
              alt={title || 'Book cover'}
              className="w-full h-full object-cover"
            />
          </div>
        )}
      </div>
      
      {/* Product info */}
      <div className="flex flex-col items-center gap-1 mt-2">
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
