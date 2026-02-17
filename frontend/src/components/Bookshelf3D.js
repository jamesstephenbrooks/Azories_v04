import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiBook, FiUser, FiHeadphones, FiRotateCcw } from 'react-icons/fi';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';

// Immersive Harry Potter style 3D Library
export default function Bookshelf3D({ books, onSelectBook, selectedBook }) {
  const navigate = useNavigate();
  const [hoveredBook, setHoveredBook] = useState(null);
  const [rotationY, setRotationY] = useState(0);
  const [rotationX, setRotationX] = useState(10);
  const isDragging = useRef(false);
  const startPos = useRef({ x: 0, y: 0 });
  const containerRef = useRef(null);
  
  // Auto rotate when not interacting
  const [autoRotate, setAutoRotate] = useState(true);
  
  useEffect(() => {
    if (!autoRotate || isDragging.current) return;
    
    const interval = setInterval(() => {
      setRotationY(prev => (prev + 0.15) % 360);
    }, 50);
    
    return () => clearInterval(interval);
  }, [autoRotate]);
  
  const handleMouseDown = (e) => {
    isDragging.current = true;
    setAutoRotate(false);
    startPos.current = { x: e.clientX, y: e.clientY };
  };
  
  const handleMouseMove = (e) => {
    if (!isDragging.current) return;
    const deltaX = e.clientX - startPos.current.x;
    const deltaY = e.clientY - startPos.current.y;
    setRotationY(prev => prev + deltaX * 0.3);
    setRotationX(prev => Math.max(-20, Math.min(30, prev + deltaY * 0.2)));
    startPos.current = { x: e.clientX, y: e.clientY };
  };
  
  const handleMouseUp = () => {
    isDragging.current = false;
  };

  const resetView = () => {
    setRotationY(0);
    setRotationX(10);
    setAutoRotate(true);
  };

  // Generate color based on genre
  const getBookColor = (genre) => {
    const colors = {
      'Adventure': '#8B0000',
      'Fantasy': '#4B0082',
      'Science Fiction': '#1E3A5F',
      'Mystery': '#2C3E50',
      'Fairy Tales': '#8B4513',
      'Animals': '#228B22',
      'Friendship': '#C71585',
      'Family': '#D2691E',
      'Educational': '#2F4F4F',
      'Humor': '#DAA520',
      'Nature': '#006400',
      'Superhero': '#DC143C',
      'default': '#3E2723'
    };
    return colors[genre] || colors.default;
  };

  // Create multiple bookcase sections around the room
  const createBookcase = (books, startAngle, sectionIndex) => {
    const booksPerShelf = 8;
    const shelves = 4;
    const shelfBooks = [];
    
    for (let i = 0; i < shelves; i++) {
      shelfBooks.push(books.slice(i * booksPerShelf, (i + 1) * booksPerShelf));
    }
    
    return (
      <div
        key={sectionIndex}
        className="absolute"
        style={{
          transform: `rotateY(${startAngle}deg) translateZ(380px)`,
          transformStyle: 'preserve-3d'
        }}
      >
        {/* Bookcase frame */}
        <div 
          className="relative"
          style={{
            width: '500px',
            height: '500px',
            transformStyle: 'preserve-3d',
            marginLeft: '-250px'
          }}
        >
          {/* Back panel - dark wood */}
          <div 
            className="absolute inset-0"
            style={{ 
              transform: 'translateZ(-30px)',
              background: 'linear-gradient(180deg, #1a0f0a 0%, #0d0705 100%)',
              boxShadow: 'inset 0 0 100px rgba(0,0,0,0.8)'
            }}
          />
          
          {/* Left pillar */}
          <div 
            className="absolute top-0 bottom-0"
            style={{ 
              left: '-20px',
              width: '20px',
              background: 'linear-gradient(90deg, #2C1810 0%, #4A2C20 50%, #2C1810 100%)',
              transform: 'translateZ(0px)'
            }}
          >
            {/* Ornate carving */}
            <div className="absolute top-10 left-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-yellow-900/50" />
            <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-yellow-800/30" />
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-yellow-800/30" />
            <div className="absolute top-3/4 left-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-yellow-800/30" />
          </div>
          
          {/* Right pillar */}
          <div 
            className="absolute top-0 bottom-0"
            style={{ 
              right: '-20px',
              width: '20px',
              background: 'linear-gradient(90deg, #2C1810 0%, #4A2C20 50%, #2C1810 100%)',
              transform: 'translateZ(0px)'
            }}
          >
            <div className="absolute top-10 left-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-yellow-900/50" />
            <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-yellow-800/30" />
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-yellow-800/30" />
            <div className="absolute top-3/4 left-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-yellow-800/30" />
          </div>
          
          {/* Ornate top */}
          <div 
            className="absolute left-0 right-0 h-8"
            style={{
              top: '-10px',
              background: 'linear-gradient(180deg, #5D4037 0%, #3E2723 100%)',
              borderRadius: '4px 4px 0 0',
              boxShadow: '0 -4px 20px rgba(139,69,19,0.3)'
            }}
          >
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-16 h-2 bg-yellow-900/40 rounded-full" />
          </div>
          
          {/* Shelves with books */}
          {shelfBooks.map((shelf, shelfIndex) => (
            <div 
              key={shelfIndex}
              className="absolute left-0 right-0"
              style={{ 
                bottom: `${20 + shelfIndex * 115}px`,
                transformStyle: 'preserve-3d'
              }}
            >
              {/* Shelf board with depth */}
              <div 
                className="absolute left-0 right-0 h-4"
                style={{ 
                  bottom: 0,
                  transform: 'translateZ(20px)',
                  background: 'linear-gradient(180deg, #6D4C41 0%, #4E342E 100%)',
                  boxShadow: '0 4px 15px rgba(0,0,0,0.5)'
                }}
              />
              
              {/* Shelf depth (side) */}
              <div 
                className="absolute left-0 right-0 h-5"
                style={{ 
                  bottom: '-3px',
                  transform: 'translateZ(28px) rotateX(-90deg)',
                  transformOrigin: 'top',
                  background: 'linear-gradient(180deg, #5D4037 0%, #3E2723 100%)'
                }}
              />
              
              {/* Shelf front lip */}
              <div 
                className="absolute left-0 right-0 h-6"
                style={{ 
                  bottom: '-4px',
                  transform: 'translateZ(33px)',
                  background: 'linear-gradient(180deg, #5D4037 0%, #3E2723 100%)',
                  borderRadius: '2px'
                }}
              />
              
              {/* Books on this shelf */}
              <div 
                className="absolute flex items-end justify-center gap-1 px-6"
                style={{ 
                  bottom: '8px',
                  left: 0,
                  right: 0,
                  transform: 'translateZ(20px)',
                  transformStyle: 'preserve-3d'
                }}
              >
                {shelf.map((book, bookIndex) => {
                  const isHovered = hoveredBook === book.id;
                  const isSelected = selectedBook?.id === book.id;
                  const bookHeight = 85 + (bookIndex % 4) * 10;
                  const bookWidth = 18 + (bookIndex % 3) * 4;
                  
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
                        z: isSelected ? 100 : isHovered ? 50 : 0,
                        rotateY: isSelected ? 25 : isHovered ? 10 : 0,
                        scale: isHovered ? 1.1 : 1
                      }}
                      transition={{ type: 'spring', stiffness: 400, damping: 25 }}
                      onMouseEnter={() => { setHoveredBook(book.id); setAutoRotate(false); }}
                      onMouseLeave={() => setHoveredBook(null)}
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectBook(book);
                      }}
                    >
                      {/* Book body with leather texture */}
                      <div 
                        className="absolute inset-0 rounded-sm flex items-center justify-center overflow-hidden"
                        style={{ 
                          backgroundColor: getBookColor(book.genre),
                          boxShadow: isHovered 
                            ? '0 0 30px rgba(255,200,100,0.5), 3px 5px 15px rgba(0,0,0,0.6)' 
                            : '3px 5px 15px rgba(0,0,0,0.6)',
                          border: '1px solid rgba(0,0,0,0.3)',
                          backgroundImage: 'linear-gradient(90deg, rgba(0,0,0,0.2) 0%, transparent 20%, transparent 80%, rgba(0,0,0,0.2) 100%)'
                        }}
                      >
                        {/* Gold spine decorations */}
                        <div 
                          className="absolute top-3 left-1/2 -translate-x-1/2 w-3 h-0.5 rounded"
                          style={{ background: 'linear-gradient(90deg, #B8860B, #FFD700, #B8860B)' }}
                        />
                        <div 
                          className="absolute top-5 left-1/2 -translate-x-1/2 w-4 h-0.5 rounded"
                          style={{ background: 'linear-gradient(90deg, #B8860B, #FFD700, #B8860B)' }}
                        />
                        <div 
                          className="absolute bottom-3 left-1/2 -translate-x-1/2 w-3 h-0.5 rounded"
                          style={{ background: 'linear-gradient(90deg, #B8860B, #FFD700, #B8860B)' }}
                        />
                        <div 
                          className="absolute bottom-5 left-1/2 -translate-x-1/2 w-4 h-0.5 rounded"
                          style={{ background: 'linear-gradient(90deg, #B8860B, #FFD700, #B8860B)' }}
                        />
                        
                        {/* Title */}
                        <span 
                          className="text-white/90 font-bold text-center px-0.5"
                          style={{ 
                            writingMode: 'vertical-rl',
                            textOrientation: 'mixed',
                            fontSize: '8px',
                            maxHeight: `${bookHeight - 30}px`,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            textShadow: '1px 1px 3px rgba(0,0,0,0.8)',
                            letterSpacing: '0.5px'
                          }}
                        >
                          {book.title.length > 16 ? book.title.substring(0, 14) + '...' : book.title}
                        </span>
                      </div>
                      
                      {/* Book spine depth */}
                      <div 
                        className="absolute top-0 h-full"
                        style={{
                          right: '-5px',
                          width: '5px',
                          background: '#1a1a1a',
                          transform: 'rotateY(90deg)',
                          transformOrigin: 'left'
                        }}
                      />
                      
                      {/* Book pages (top) */}
                      <div 
                        className="absolute left-0 right-0"
                        style={{
                          top: '-3px',
                          height: '5px',
                          background: 'linear-gradient(90deg, #f5f0e1, #e8e0cc, #f5f0e1)',
                          transform: 'rotateX(90deg)',
                          transformOrigin: 'bottom'
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
    );
  };

  // Distribute books across 4 bookcases (front, back, left, right)
  const booksPerCase = Math.ceil(books.length / 4);
  const bookcases = [
    { books: books.slice(0, booksPerCase), angle: 0 },
    { books: books.slice(booksPerCase, booksPerCase * 2), angle: 90 },
    { books: books.slice(booksPerCase * 2, booksPerCase * 3), angle: 180 },
    { books: books.slice(booksPerCase * 3), angle: 270 }
  ];

  return (
    <div className="w-full">
      {/* 3D Library Room */}
      <div 
        ref={containerRef}
        className="w-full h-[650px] rounded-3xl overflow-hidden cursor-grab active:cursor-grabbing relative"
        style={{ 
          perspective: '1500px',
          background: 'radial-gradient(ellipse at center bottom, #1a0f0a 0%, #0d0805 50%, #050302 100%)'
        }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {/* Ambient candlelight effects */}
        <div className="absolute top-1/4 left-1/4 w-32 h-32 rounded-full opacity-20 animate-pulse"
          style={{ background: 'radial-gradient(circle, #ff9500 0%, transparent 70%)', filter: 'blur(30px)' }}
        />
        <div className="absolute top-1/3 right-1/4 w-24 h-24 rounded-full opacity-15 animate-pulse"
          style={{ background: 'radial-gradient(circle, #ff7b00 0%, transparent 70%)', filter: 'blur(25px)', animationDelay: '0.5s' }}
        />
        <div className="absolute bottom-1/3 left-1/3 w-28 h-28 rounded-full opacity-15 animate-pulse"
          style={{ background: 'radial-gradient(circle, #ff8c00 0%, transparent 70%)', filter: 'blur(28px)', animationDelay: '1s' }}
        />
        
        {/* Dust particles overlay */}
        <div className="absolute inset-0 opacity-30"
          style={{
            backgroundImage: `radial-gradient(circle at 20% 30%, rgba(255,200,100,0.1) 1px, transparent 1px),
                             radial-gradient(circle at 60% 70%, rgba(255,200,100,0.08) 1px, transparent 1px),
                             radial-gradient(circle at 80% 20%, rgba(255,200,100,0.1) 1px, transparent 1px)`,
            backgroundSize: '100px 100px, 150px 150px, 80px 80px'
          }}
        />
        
        {/* 3D Room Container */}
        <div 
          className="absolute inset-0 flex items-center justify-center"
          style={{
            transformStyle: 'preserve-3d',
            transform: `rotateX(${rotationX}deg) rotateY(${rotationY}deg)`,
            transition: isDragging.current ? 'none' : 'transform 0.1s ease-out'
          }}
        >
          {/* Floor */}
          <div 
            className="absolute"
            style={{
              width: '1000px',
              height: '1000px',
              transform: 'rotateX(90deg) translateZ(-250px)',
              background: 'radial-gradient(circle at center, #2d1f14 0%, #1a0f0a 60%, #0d0705 100%)',
              boxShadow: 'inset 0 0 200px rgba(0,0,0,0.8)'
            }}
          />
          
          {/* Ceiling with chandelier hint */}
          <div 
            className="absolute"
            style={{
              width: '1000px',
              height: '1000px',
              transform: 'rotateX(-90deg) translateZ(-350px)',
              background: 'radial-gradient(circle at center, #1a1410 0%, #0d0805 100%)'
            }}
          />
          
          {/* Bookcases around the room */}
          {bookcases.map((bookcase, index) => 
            createBookcase(bookcase.books, bookcase.angle, index)
          )}
          
          {/* Center reading table (decorative) */}
          <div 
            className="absolute"
            style={{
              width: '100px',
              height: '100px',
              transform: 'translateZ(0) translateY(200px)',
              transformStyle: 'preserve-3d'
            }}
          >
            <div 
              className="absolute"
              style={{
                width: '100px',
                height: '100px',
                borderRadius: '50%',
                background: 'radial-gradient(circle, #4a3728 0%, #2d1f14 100%)',
                transform: 'rotateX(90deg)',
                boxShadow: '0 0 30px rgba(0,0,0,0.5)'
              }}
            />
          </div>
        </div>
        
        {/* Reset button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={resetView}
          className="absolute top-4 right-4 rounded-full bg-black/30 hover:bg-black/50 text-white"
        >
          <FiRotateCcw className="w-4 h-4 mr-2" />
          Reset View
        </Button>
        
        {/* Auto-rotate indicator */}
        {autoRotate && (
          <div className="absolute top-4 left-4 px-3 py-1 rounded-full bg-black/30 text-white/70 text-xs">
            Auto-rotating • Click to stop
          </div>
        )}
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
        Drag to explore the library • Click on a book to select • The library auto-rotates
      </p>
    </div>
  );
}
