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
    setRotationY(prev => Math.max(-30, Math.min(30, prev + deltaX * 0.3)));
    startX.current = e.clientX;
  };
  
  const handleMouseUp = () => {
    isDragging.current = false;
  };

  // Generate color based on genre
  const getBookColor = (genre) => {
    const colors = {
      'Adventure': '#c0392b',
      'Fantasy': '#8e44ad',
      'Science Fiction': '#2980b9',
      'Mystery': '#34495e',
      'Fairy Tales': '#d35400',
      'Animals': '#27ae60',
      'Friendship': '#e91e63',
      'Family': '#e67e22',
      'Educational': '#16a085',
      'Humor': '#f1c40f',
      'Nature': '#2ecc71',
      'Superhero': '#e74c3c',
      'default': '#795548'
    };
    return colors[genre] || colors.default;
  };

  // Arrange books on shelves - max 10 per shelf
  const booksPerShelf = 10;
  const shelves = 3;
  const shelfBooks = [];
  
  for (let i = 0; i < shelves; i++) {
    shelfBooks.push(books.slice(i * booksPerShelf, (i + 1) * booksPerShelf));
  }

  return (
    <div className="w-full">
      {/* 3D Bookshelf Scene */}
      <div 
        className="w-full h-[550px] rounded-3xl overflow-hidden cursor-grab active:cursor-grabbing relative"
        style={{ 
          perspective: '1200px',
          background: 'linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)'
        }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {/* Ambient lighting effect */}
        <div 
          className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-96 rounded-full opacity-30"
          style={{ 
            background: 'radial-gradient(circle, rgba(255,200,100,0.4) 0%, transparent 70%)',
            filter: 'blur(40px)'
          }}
        />
        
        <div 
          className="w-full h-full flex items-center justify-center pt-8"
          style={{
            transformStyle: 'preserve-3d',
            transform: `rotateX(8deg) rotateY(${rotationY}deg)`,
            transition: isDragging.current ? 'none' : 'transform 0.3s ease-out'
          }}
        >
          {/* Bookcase Container */}
          <div 
            className="relative"
            style={{
              width: '800px',
              height: '450px',
              transformStyle: 'preserve-3d'
            }}
          >
            {/* Bookcase back panel */}
            <div 
              className="absolute inset-0 rounded-lg"
              style={{ 
                transform: 'translateZ(-50px)',
                background: 'linear-gradient(180deg, #2d2d44 0%, #1a1a2e 100%)',
                boxShadow: 'inset 0 0 60px rgba(0,0,0,0.5)'
              }}
            />
            
            {/* Left side panel */}
            <div 
              className="absolute top-0 bottom-0 w-6"
              style={{ 
                left: '-3px',
                transform: 'rotateY(90deg) translateZ(-3px)',
                transformOrigin: 'left',
                background: 'linear-gradient(90deg, #3d2b1f 0%, #5d4037 100%)'
              }}
            />
            
            {/* Right side panel */}
            <div 
              className="absolute top-0 bottom-0 w-6"
              style={{ 
                right: '-3px',
                transform: 'rotateY(-90deg) translateZ(-3px)',
                transformOrigin: 'right',
                background: 'linear-gradient(90deg, #5d4037 0%, #3d2b1f 100%)'
              }}
            />
            
            {/* Top panel */}
            <div 
              className="absolute left-0 right-0 h-4 rounded-t-lg"
              style={{
                top: '-2px',
                background: 'linear-gradient(180deg, #6d4c41 0%, #4e342e 100%)',
                boxShadow: '0 2px 8px rgba(0,0,0,0.3)'
              }}
            />
            
            {/* Shelves with books */}
            {shelfBooks.map((shelf, shelfIndex) => (
              <div 
                key={shelfIndex}
                className="absolute left-3 right-3"
                style={{ 
                  bottom: `${20 + shelfIndex * 140}px`,
                  transformStyle: 'preserve-3d'
                }}
              >
                {/* Shelf board */}
                <div 
                  className="absolute left-0 right-0 h-4 rounded"
                  style={{ 
                    bottom: 0,
                    transform: 'translateZ(25px)',
                    background: 'linear-gradient(180deg, #8d6e63 0%, #5d4037 100%)',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.4)'
                  }}
                />
                
                {/* Shelf front lip */}
                <div 
                  className="absolute left-0 right-0 h-5"
                  style={{ 
                    bottom: '-2px',
                    transform: 'translateZ(40px)',
                    background: 'linear-gradient(180deg, #6d4c41 0%, #4e342e 100%)',
                    borderRadius: '2px',
                    boxShadow: '0 2px 6px rgba(0,0,0,0.3)'
                  }}
                />
                
                {/* Books on this shelf */}
                <div 
                  className="absolute flex items-end justify-center gap-1 px-4"
                  style={{ 
                    bottom: '6px',
                    left: 0,
                    right: 0,
                    transform: 'translateZ(25px)',
                    transformStyle: 'preserve-3d'
                  }}
                >
                  {shelf.map((book, bookIndex) => {
                    const isHovered = hoveredBook === book.id;
                    const isSelected = selectedBook?.id === book.id;
                    // Vary book sizes based on index for realism
                    const bookHeight = 95 + (bookIndex % 4) * 12;
                    const bookWidth = 22 + (bookIndex % 3) * 4;
                    
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
                          z: isSelected ? 80 : isHovered ? 40 : 0,
                          rotateY: isSelected ? 20 : 0,
                          scale: isHovered ? 1.08 : 1
                        }}
                        transition={{ type: 'spring', stiffness: 400, damping: 25 }}
                        onMouseEnter={() => setHoveredBook(book.id)}
                        onMouseLeave={() => setHoveredBook(null)}
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectBook(book);
                        }}
                      >
                        {/* Book spine */}
                        <div 
                          className="absolute inset-0 rounded-sm flex items-center justify-center overflow-hidden"
                          style={{ 
                            backgroundColor: getBookColor(book.genre),
                            boxShadow: isHovered 
                              ? '0 0 25px rgba(255,255,255,0.4), 2px 4px 12px rgba(0,0,0,0.5)' 
                              : '2px 4px 12px rgba(0,0,0,0.5)',
                            border: '1px solid rgba(0,0,0,0.2)'
                          }}
                        >
                          {/* Gold decorations */}
                          <div 
                            className="absolute top-2 left-1/2 -translate-x-1/2 w-4 h-1 rounded"
                            style={{ background: 'linear-gradient(90deg, #d4af37, #f4e4ba, #d4af37)' }}
                          />
                          <div 
                            className="absolute bottom-2 left-1/2 -translate-x-1/2 w-4 h-1 rounded"
                            style={{ background: 'linear-gradient(90deg, #d4af37, #f4e4ba, #d4af37)' }}
                          />
                          
                          {/* Title (vertical) */}
                          <span 
                            className="text-white font-bold text-center px-0.5"
                            style={{ 
                              writingMode: 'vertical-rl',
                              textOrientation: 'mixed',
                              fontSize: '9px',
                              maxHeight: `${bookHeight - 24}px`,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              textShadow: '1px 1px 2px rgba(0,0,0,0.5)'
                            }}
                          >
                            {book.title.length > 18 ? book.title.substring(0, 16) + '...' : book.title}
                          </span>
                        </div>
                        
                        {/* Book side (depth effect) */}
                        <div 
                          className="absolute top-0 h-full"
                          style={{
                            right: '-4px',
                            width: '4px',
                            background: 'linear-gradient(90deg, #1a1a1a, #2a2a2a)',
                            transform: 'rotateY(90deg)',
                            transformOrigin: 'left'
                          }}
                        />
                        
                        {/* Book top */}
                        <div 
                          className="absolute left-0 right-0"
                          style={{
                            top: '-2px',
                            height: '4px',
                            background: '#f5f5dc',
                            transform: 'rotateX(90deg)',
                            transformOrigin: 'bottom'
                          }}
                        />
                      </motion.div>
                    );
                  })}
                  
                  {/* Empty shelf message */}
                  {shelf.length === 0 && (
                    <div className="text-white/30 text-sm py-8">Empty shelf</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
        
        {/* Floor reflection effect */}
        <div 
          className="absolute bottom-0 left-0 right-0 h-20"
          style={{
            background: 'linear-gradient(180deg, transparent 0%, rgba(0,0,0,0.3) 100%)'
          }}
        />
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
                  <div 
                    className="w-full h-full flex items-center justify-center"
                    style={{ backgroundColor: getBookColor(selectedBook.genre) }}
                  >
                    <FiBook className="w-8 h-8 text-white/60" />
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
                  <span 
                    className="text-xs px-3 py-1 rounded-full text-white font-ui"
                    style={{ backgroundColor: getBookColor(selectedBook.genre) }}
                  >
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
        Drag left/right to rotate the bookshelf • Click on a book to select it
      </p>
    </div>
  );
}
