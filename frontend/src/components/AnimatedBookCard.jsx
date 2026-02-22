import { useState } from 'react';
import { motion } from 'framer-motion';
import { FiBook, FiEye, FiStar } from 'react-icons/fi';

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
          <img
            src={book.cover_image}
            alt={book.title}
            className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
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
    <motion.div
      className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/50 cursor-pointer"
      onClick={onClick}
      whileHover={{ x: 4 }}
      whileTap={{ scale: 0.98 }}
    >
      <div className="w-12 h-16 rounded overflow-hidden flex-shrink-0">
        {book.cover_image ? (
          <img src={book.cover_image} alt={book.title} className="w-full h-full object-cover" />
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
    </motion.div>
  );
}
