import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { motion } from 'framer-motion';
import { FiBook, FiEye, FiStar } from 'react-icons/fi';

// Get optimized Cloudinary URL with transformations for faster loading
const getOptimizedImageUrl = (url, { width = 300, quality = 'auto', format = 'auto' } = {}) => {
  if (!url) return url;
  if (url.includes('res.cloudinary.com')) {
    const transformations = `w_${width},q_${quality},f_${format}`;
    return url.replace('/upload/', `/upload/${transformations}/`);
  }
  return url;
};

// Lazy-loaded image component with intersection observer
const LazyImage = ({ src, alt, className, onLoad, thumbnailWidth = 300 }) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isInView, setIsInView] = useState(false);
  const [hasError, setHasError] = useState(false);
  const imgRef = useRef(null);

  // Get optimized thumbnail URL
  const optimizedSrc = useMemo(() => {
    return getOptimizedImageUrl(src, { width: thumbnailWidth, quality: 'auto', format: 'auto' });
  }, [src, thumbnailWidth]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.disconnect();
        }
      },
      { rootMargin: '100px', threshold: 0.1 }
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => observer.disconnect();
  }, []);

  // Generate a color based on the alt text for consistent placeholder
  const getPlaceholderGradient = useCallback(() => {
    const colors = [
      'from-purple-500 to-pink-500',
      'from-blue-500 to-cyan-500',
      'from-green-500 to-emerald-500',
      'from-orange-500 to-amber-500',
      'from-rose-500 to-red-500',
      'from-indigo-500 to-violet-500',
    ];
    const index = alt ? alt.charCodeAt(0) % colors.length : 0;
    return colors[index];
  }, [alt]);

  const handleLoad = () => {
    setIsLoaded(true);
    if (onLoad) onLoad();
  };

  return (
    <div ref={imgRef} className={`relative ${className}`}>
      {/* Placeholder/skeleton */}
      {!isLoaded && (
        <div className={`absolute inset-0 bg-gradient-to-br ${getPlaceholderGradient()} animate-pulse flex items-center justify-center`}>
          <FiBook className="w-8 h-8 text-white/40" />
        </div>
      )}
      
      {/* Actual image - only load when in view */}
      {isInView && !hasError && (
        <img
          src={optimizedSrc}
          alt={alt}
          className={`w-full h-full object-cover transition-opacity duration-300 ${isLoaded ? 'opacity-100' : 'opacity-0'}`}
          onLoad={handleLoad}
          onError={() => setHasError(true)}
          loading="lazy"
          decoding="async"
        />
      )}
      
      {/* Error fallback */}
      {hasError && (
        <div className={`absolute inset-0 bg-gradient-to-br ${getPlaceholderGradient()} flex items-center justify-center`}>
          <FiBook className="w-8 h-8 text-white/40" />
        </div>
      )}
    </div>
  );
};

export default function AnimatedBookCard({ book, onClick, size = 'md' }) {
  const [isHovered, setIsHovered] = useState(false);

  const sizeClasses = {
    sm: 'w-24',
    md: 'w-full',
    lg: 'w-48'
  };

  return (
    <div
      className={`relative cursor-pointer ${sizeClasses[size]} group transition-transform duration-200 hover:-translate-y-2`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onClick}
    >
      {/* Book Cover Container */}
      <div className="relative aspect-[3/4] rounded-xl overflow-hidden shadow-lg">
        {/* Cover Image */}
        {book.cover_image ? (
          <LazyImage
            src={book.cover_image}
            alt={book.title}
            className="w-full h-full transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
            <FiBook className="w-12 h-12 text-white/50" />
          </div>
        )}

        {/* Overlay on hover */}
        <div
          className={`absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent transition-opacity duration-200 ${isHovered ? 'opacity-100' : 'opacity-0'}`}
        />

        {/* Genre tag */}
        {book.genre && (
          <div className="absolute top-2 left-2">
            <span className="px-2 py-0.5 bg-black/50 backdrop-blur text-white text-xs rounded-full">
              {book.genre}
            </span>
          </div>
        )}

        {/* Featured badge */}
        {book.is_featured && (
          <div className="absolute top-2 right-2">
            <div
              className="px-2 py-0.5 bg-gradient-to-r from-yellow-400 to-orange-500 text-white text-xs rounded-full flex items-center gap-1"
            >
              <FiStar className="w-3 h-3" />
              Featured
            </div>
          </div>
        )}

        {/* Hover info */}
        <div
          className={`absolute bottom-0 left-0 right-0 p-3 transition-all duration-200 ${isHovered ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}
        >
          <p className="text-white text-xs line-clamp-2 mb-2">
            {book.description || book.back_cover_text || 'A magical story awaits...'}
          </p>
          <div className="flex items-center gap-3 text-white/70 text-xs">
            {book.views !== undefined && (
              <span className="flex items-center gap-1">
                <FiEye className="w-3 h-3" />
                {book.views}
              </span>
            )}
            {book.pages && (
              <span>{book.pages.length} pages</span>
            )}
          </div>
        </div>

        {/* 3D book spine effect */}
        <div className="absolute left-0 top-0 bottom-0 w-2 bg-gradient-to-r from-black/30 to-transparent" />
      </div>

      {/* Title and Author */}
      <div className="mt-2 px-1">
        <h3 className="font-medium text-sm line-clamp-1">{book.title}</h3>
        <p className="text-xs text-muted-foreground line-clamp-1">
          by {book.author_name || 'Anonymous'}
        </p>
      </div>
    </div>
  );
}

// Compact version for lists
export function AnimatedBookCardCompact({ book, onClick }) {
  return (
    <div
      className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/50 cursor-pointer transition-transform duration-200 hover:translate-x-1"
      onClick={onClick}
    >
      <div className="w-12 h-16 rounded overflow-hidden flex-shrink-0">
        {book.cover_image ? (
          <LazyImage src={book.cover_image} alt={book.title} className="w-full h-full" />
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
            <FiBook className="w-4 h-4 text-white/50" />
          </div>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <h4 className="font-medium text-sm line-clamp-1">{book.title}</h4>
        <p className="text-xs text-muted-foreground">{book.author_name}</p>
      </div>
    </div>
  );
}
