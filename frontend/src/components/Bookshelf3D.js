import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiBook, FiUser, FiHeadphones } from 'react-icons/fi';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';

// CSS-based 3D Bookshelf
export default function Bookshelf3D({ books, onSelectBook, selectedBook }) {
  const navigate = useNavigate();
  const [hoveredBook, setHoveredBook] = useState(null);
  const [rotationY, setRotationY] = useState(0);
  const isDragging = useRef(false);
  const startX = useRef(0);
  
  const handleMouseDown = (e) => {
    isDragging.current = true;
    startX.current = e.clientX;
  };
  
  const handleMouseMove = (e) => {
    if (!isDragging.current) return;
    const deltaX = e.clientX - startX.current;
    setRotationY(prev => prev + deltaX * 0.2);
    startX.current = e.clientX;
  };
  
  const handleMouseUp = () => {
    isDragging.current = false;
  };

  // Generate color based on genre
  const getBookColor = (genre) => {
    const colors = {
      'Adventure': '#e74c3c',
      'Fantasy': '#9b59b6',
      'Science Fiction': '#3498db',
      'Mystery': '#2c3e50',
      'Fairy Tales': '#f39c12',
      'Animals': '#27ae60',
      'Friendship': '#e91e63',
      'Family': '#ff9800',
      'Educational': '#00bcd4',
      'Humor': '#ffeb3b',
      'Nature': '#4caf50',
      'default': '#8b4513'
    };
    return colors[genre] || colors.default;
  };

  // Arrange books on shelves
  const booksPerShelf = 8;
  const shelves = 3;
  const shelfBooks = [];
  
  for (let i = 0; i < shelves; i++) {
    shelfBooks.push(books.slice(i * booksPerShelf, (i + 1) * booksPerShelf));
  }

  return (
    <div className="w-full">
      {/* 3D Bookshelf Scene */}
      <div 
        className="w-full h-[500px] rounded-3xl overflow-hidden bg-gradient-to-b from-[#0a0a1a] to-[#1a1a3e] cursor-grab active:cursor-grabbing"
        style={{ perspective: '1500px' }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <div 
          className="w-full h-full flex items-center justify-center"
          style={{
            transformStyle: 'preserve-3d',
            transform: `rotateX(5deg) rotateY(${rotationY}deg)`,
            transition: isDragging.current ? 'none' : 'transform 0.3s ease-out'
          }}
        >
          {/* Bookcase Container */}
          <div 
            className="relative"
            style={{
              width: '700px',
              height: '400px',
              transformStyle: 'preserve-3d'
            }}
          >
            {/* Bookcase back */}
            <div 
              className="absolute inset-0 bg-gradient-to-b from-[#1a1a2e] to-[#0d0d1a] rounded-lg"
              style={{ transform: 'translateZ(-40px)' }}
            />
            
            {/* Left side */}
            <div 
              className="absolute left-0 top-0 bottom-0 w-4 bg-[#3e2723]"
              style={{ 
                transform: 'rotateY(90deg) translateZ(-2px)',
                transformOrigin: 'left'
              }}
            />
            
            {/* Right side */}
            <div 
              className="absolute right-0 top-0 bottom-0 w-4 bg-[#3e2723]"
              style={{ 
                transform: 'rotateY(-90deg) translateZ(-2px)',
                transformOrigin: 'right'
              }}
            />
            
            {/* Top */}
            <div className="absolute top-0 left-0 right-0 h-3 bg-[#4e342e] rounded-t-lg" />
            
            {/* Shelves with books */}
            {shelfBooks.map((shelf, shelfIndex) => (
              <div 
                key={shelfIndex}
                className="absolute left-4 right-4"
                style={{ 
                  top: `${30 + shelfIndex * 120}px`,
                  transformStyle: 'preserve-3d'
                }}
              >
                {/* Shelf board */}
                <div 
                  className="absolute left-0 right-0 h-3 bg-[#5d4037] rounded"
                  style={{ 
                    transform: 'translateZ(20px)',
                    boxShadow: '0 4px 8px rgba(0,0,0,0.3)'
                  }}
                />
                
                {/* Shelf front lip */}
                <div 
                  className="absolute left-0 right-0 h-4 bg-[#4e342e]"
                  style={{ 
                    top: '-1px',
                    transform: 'translateZ(35px)',
                    borderRadius: '2px'
                  }}
                />
                
                {/* Books on this shelf */}
                <div 
                  className="absolute flex items-end gap-1 px-2"
                  style={{ 
                    bottom: '5px',
                    transform: 'translateZ(20px)',
                    transformStyle: 'preserve-3d'
                  }}
                >
                  {shelf.map((book, bookIndex) => {
                    const isHovered = hoveredBook === book.id;
                    const isSelected = selectedBook?.id === book.id;
                    const bookHeight = 80 + (bookIndex % 3) * 10;
                    const bookWidth = 20 + (bookIndex % 4) * 3;
                    
                    return (
                      <motion.div
                        key={book.id}
                        className="relative cursor-pointer"
                        style={{
                          width: `${bookWidth}px`,
                          height: `${bookHeight}px`,
                          transformStyle: 'preserve-3d',
                          transformOrigin: 'bottom center'
                        }}
                        animate={{
                          translateZ: isSelected ? 60 : isHovered ? 30 : 0,
                          rotateY: isSelected ? 15 : 0,
                          scale: isHovered ? 1.05 : 1
                        }}
                        transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                        onMouseEnter={() => setHoveredBook(book.id)}
                        onMouseLeave={() => setHoveredBook(null)}
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectBook(book);
                        }}
                      >
                        {/* Book spine */}
                        <div 
                          className="absolute inset-0 rounded-sm shadow-lg flex items-center justify-center overflow-hidden"
                          style={{ 
                            backgroundColor: getBookColor(book.genre),
                            boxShadow: isHovered ? '0 0 20px rgba(255,255,255,0.3)' : '2px 2px 8px rgba(0,0,0,0.4)'
                          }}
                        >
                          {/* Gold decorations */}
                          <div className="absolute top-2 left-1/2 -translate-x-1/2 w-3 h-0.5 bg-yellow-400 rounded" />
                          <div className="absolute bottom-2 left-1/2 -translate-x-1/2 w-3 h-0.5 bg-yellow-400 rounded" />
                          
                          {/* Title (vertical) */}
                          <span 
                            className="text-white text-[8px] font-bold whitespace-nowrap overflow-hidden text-ellipsis"
                            style={{ 
                              writingMode: 'vertical-rl',
                              textOrientation: 'mixed',
                              maxHeight: `${bookHeight - 20}px`
                            }}
                          >
                            {book.title.length > 15 ? book.title.substring(0, 13) + '...' : book.title}
                          </span>
                        </div>
                        
                        {/* Book side (depth) */}
                        <div 
                          className="absolute top-0 right-0 h-full w-3"
                          style={{
                            backgroundColor: '#2a2a2a',
                            transform: 'rotateY(90deg) translateZ(0)',
                            transformOrigin: 'right'
                          }}
                        />
                      </motion.div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      
      {/* Selected book details */}
      <AnimatePresence>
        {selectedBook && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="mt-6 bg-card rounded-3xl p-6 border border-border"
          >
            <div className="flex gap-6">
              <div className="w-32 h-48 rounded-xl overflow-hidden flex-shrink-0 shadow-lg">
                {selectedBook.cover_image ? (
                  <img src={selectedBook.cover_image} alt={selectedBook.title} className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center">
                    <FiBook className="w-8 h-8 text-primary/40" />
                  </div>
                )}
              </div>
              <div className="flex-1">
                <h3 className="font-heading text-2xl font-bold mb-2">{selectedBook.title}</h3>
                <p className="font-body text-muted-foreground mb-4 line-clamp-2">
                  {selectedBook.description || 'A magical story awaits...'}
                </p>
                <div className="flex items-center gap-4 mb-4">
                  <span className="font-ui text-sm text-muted-foreground flex items-center gap-1">
                    <FiUser className="w-4 h-4" /> {selectedBook.author_name}
                  </span>
                  <span className="text-xs px-3 py-1 rounded-full bg-primary/10 text-primary font-ui">
                    {selectedBook.genre}
                  </span>
                </div>
                <div className="flex gap-3">
                  <Button 
                    onClick={() => navigate(`/read/${selectedBook.id}`)}
                    className="rounded-full"
                  >
                    <FiBook className="mr-2" /> Read Now
                  </Button>
                  <Button 
                    variant="secondary"
                    onClick={() => navigate(`/read/${selectedBook.id}?audio=true`)}
                    className="rounded-full"
                  >
                    <FiHeadphones className="mr-2" /> Listen
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => onSelectBook(null)}
                    className="rounded-full"
                  >
                    Close
                  </Button>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      <p className="text-center text-sm text-muted-foreground font-body mt-4">
        Drag to rotate the bookshelf • Click on a book to select it
      </p>
    </div>
  );
}
