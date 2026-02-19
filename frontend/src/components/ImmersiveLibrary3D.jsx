import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { FiX, FiBook, FiMaximize2, FiMinimize2, FiVolume2, FiVolumeX, FiChevronLeft, FiChevronRight } from 'react-icons/fi';

// CSS 3D Immersive Library - No WebGL dependencies
export default function ImmersiveLibrary3D({ books = [], onClose }) {
  const navigate = useNavigate();
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [selectedBook, setSelectedBook] = useState(null);
  const [rotationY, setRotationY] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [startX, setStartX] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const containerRef = useRef();
  const audioRef = useRef(null);

  // Setup ambient audio
  useEffect(() => {
    const audio = new Audio('https://assets.mixkit.co/sfx/preview/mixkit-campfire-crackles-1330.mp3');
    audio.loop = true;
    audio.volume = 0.15;
    audioRef.current = audio;
    
    const playAudio = () => {
      audio.play().catch(() => {});
      document.removeEventListener('click', playAudio);
    };
    document.addEventListener('click', playAudio);

    return () => {
      audio.pause();
      document.removeEventListener('click', playAudio);
    };
  }, []);

  const toggleMute = () => {
    if (audioRef.current) {
      audioRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  // Mouse drag to rotate
  const handleMouseDown = (e) => {
    setIsDragging(true);
    setStartX(e.clientX);
  };

  const handleMouseMove = (e) => {
    if (isDragging) {
      const deltaX = e.clientX - startX;
      setRotationY(prev => prev + deltaX * 0.3);
      setStartX(e.clientX);
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const rotate = (direction) => {
    setRotationY(prev => prev + (direction * 45));
  };

  // Book colors for variety
  const bookColors = [
    'from-purple-600 to-purple-800',
    'from-pink-600 to-pink-800',
    'from-cyan-600 to-cyan-800',
    'from-emerald-600 to-emerald-800',
    'from-amber-600 to-amber-800',
    'from-red-600 to-red-800',
    'from-indigo-600 to-indigo-800',
    'from-teal-600 to-teal-800',
  ];

  // Distribute books around the room (8 positions)
  const bookPositions = books.slice(0, 24).map((book, idx) => {
    const angle = (idx % 8) * 45;
    const row = Math.floor(idx / 8);
    return { book, angle, row };
  });

  return (
    <div 
      ref={containerRef}
      className="fixed inset-0 z-50 bg-gradient-to-b from-[#1a0a2e] via-[#15051f] to-[#0d0015] overflow-hidden"
      data-testid="immersive-library-3d"
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {/* Starry background */}
      <div className="absolute inset-0 overflow-hidden">
        {[...Array(100)].map((_, i) => (
          <div
            key={i}
            className="absolute w-1 h-1 bg-white rounded-full animate-pulse"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 3}s`,
              opacity: Math.random() * 0.7 + 0.3,
            }}
          />
        ))}
      </div>

      {/* Controls Overlay */}
      <div className="absolute top-4 left-4 right-4 z-20 flex justify-between items-start">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="bg-black/50 hover:bg-black/70 text-white rounded-full backdrop-blur"
          >
            <FiX className="w-5 h-5" />
          </Button>
          <div className="bg-black/50 backdrop-blur px-4 py-2 rounded-full">
            <h2 className="text-white font-bold text-lg">✨ The Grand Library ✨</h2>
            <p className="text-white/70 text-xs">Drag to rotate • Click books to read</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleMute}
            className="bg-black/50 hover:bg-black/70 text-white rounded-full backdrop-blur"
          >
            {isMuted ? <FiVolumeX className="w-5 h-5" /> : <FiVolume2 className="w-5 h-5" />}
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleFullscreen}
            className="bg-black/50 hover:bg-black/70 text-white rounded-full backdrop-blur"
          >
            {isFullscreen ? <FiMinimize2 className="w-5 h-5" /> : <FiMaximize2 className="w-5 h-5" />}
          </Button>
        </div>
      </div>

      {/* Rotation controls */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-20 flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => rotate(-1)}
          className="bg-black/50 hover:bg-black/70 text-white rounded-full backdrop-blur w-12 h-12"
        >
          <FiChevronLeft className="w-6 h-6" />
        </Button>
        <div className="bg-black/50 backdrop-blur px-4 py-2 rounded-full">
          <p className="text-white/80 text-sm">Click arrows or drag to explore</p>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => rotate(1)}
          className="bg-black/50 hover:bg-black/70 text-white rounded-full backdrop-blur w-12 h-12"
        >
          <FiChevronRight className="w-6 h-6" />
        </Button>
      </div>

      {/* 3D Scene Container */}
      <div 
        className="absolute inset-0 flex items-center justify-center"
        style={{ perspective: '1500px' }}
      >
        {/* Room Container */}
        <div
          className="relative w-[600px] h-[400px]"
          style={{
            transformStyle: 'preserve-3d',
            transform: `rotateX(-15deg) rotateY(${rotationY}deg)`,
            transition: isDragging ? 'none' : 'transform 0.5s ease-out',
          }}
        >
          {/* Floor */}
          <div
            className="absolute left-1/2 top-1/2 w-[800px] h-[800px] -translate-x-1/2 -translate-y-1/2"
            style={{
              transform: 'rotateX(90deg) translateZ(-200px)',
              background: 'radial-gradient(circle at center, #3d2817 0%, #1a0a0a 70%)',
              boxShadow: 'inset 0 0 100px rgba(139, 92, 246, 0.2)',
            }}
          >
            {/* Carpet */}
            <div className="absolute left-1/2 top-1/2 w-48 h-96 -translate-x-1/2 -translate-y-1/2 bg-gradient-to-b from-red-900 to-red-950 rounded-lg" />
          </div>

          {/* Chandelier */}
          <div
            className="absolute left-1/2 top-0 -translate-x-1/2"
            style={{
              transform: 'translateZ(0px) translateY(-150px)',
            }}
          >
            <div className="relative">
              {/* Chain */}
              <div className="w-1 h-20 bg-gradient-to-b from-amber-600 to-amber-800 mx-auto" />
              {/* Ring */}
              <div className="w-32 h-32 rounded-full border-4 border-amber-600 relative">
                {/* Candles */}
                {[0, 60, 120, 180, 240, 300].map((angle, i) => (
                  <div
                    key={i}
                    className="absolute w-3 h-6 bg-amber-100 rounded-t-sm"
                    style={{
                      left: '50%',
                      top: '50%',
                      transform: `rotate(${angle}deg) translateY(-50px) translateX(-50%)`,
                    }}
                  >
                    {/* Flame */}
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-2 h-4 bg-gradient-to-t from-orange-500 to-yellow-300 rounded-full animate-pulse" />
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Bookshelves around the room */}
          {[0, 45, 90, 135, 180, 225, 270, 315].map((angle, shelfIdx) => (
            <div
              key={angle}
              className="absolute left-1/2 top-1/2"
              style={{
                transform: `rotateY(${angle}deg) translateZ(350px) translateY(-100px) translateX(-50%)`,
                transformStyle: 'preserve-3d',
              }}
            >
              {/* Bookshelf */}
              <div className="relative w-40 h-48 bg-gradient-to-b from-amber-900 to-amber-950 rounded-lg shadow-2xl border-2 border-amber-800/30">
                {/* Shelf dividers */}
                {[0, 1, 2].map((shelf) => (
                  <div
                    key={shelf}
                    className="absolute left-2 right-2 h-1 bg-amber-700"
                    style={{ top: `${(shelf + 1) * 25}%` }}
                  />
                ))}
                
                {/* Books on this shelf */}
                <div className="absolute inset-2 flex flex-wrap gap-1 content-start">
                  {bookPositions
                    .filter(bp => Math.floor(bp.angle / 45) === shelfIdx)
                    .slice(0, 3)
                    .map(({ book }, bookIdx) => (
                      <motion.div
                        key={book.id}
                        whileHover={{ scale: 1.1, y: -5 }}
                        className={`w-8 h-12 rounded-sm cursor-pointer bg-gradient-to-b ${bookColors[bookIdx % bookColors.length]} shadow-lg`}
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedBook(book);
                        }}
                        title={book.title}
                      >
                        {/* Book spine decoration */}
                        <div className="h-full flex flex-col justify-center items-center">
                          <div className="w-4 h-0.5 bg-white/30 rounded" />
                          <div className="w-3 h-0.5 bg-white/20 rounded mt-1" />
                        </div>
                      </motion.div>
                    ))}
                </div>
              </div>
            </div>
          ))}

          {/* Floating magic orbs */}
          {[-150, 0, 150].map((x, i) => (
            <div
              key={i}
              className="absolute left-1/2 top-1/2"
              style={{
                transform: `translateX(${x}px) translateY(${-50 + i * 30}px) translateZ(${100 - i * 50}px)`,
              }}
            >
              <div className="w-6 h-6 rounded-full bg-purple-500 animate-pulse shadow-[0_0_30px_10px_rgba(139,92,246,0.5)]" />
            </div>
          ))}

          {/* Gothic pillars in corners */}
          {[-1, 1].map((xDir) =>
            [-1, 1].map((zDir) => (
              <div
                key={`${xDir}-${zDir}`}
                className="absolute left-1/2 top-1/2"
                style={{
                  transform: `translateX(${xDir * 280}px) translateY(0px) translateZ(${zDir * 280}px)`,
                }}
              >
                <div className="w-8 h-64 bg-gradient-to-t from-gray-700 to-gray-600 rounded-t-lg shadow-xl" />
              </div>
            ))
          )}
        </div>
      </div>

      {/* Book Preview Modal */}
      <AnimatePresence>
        {selectedBook && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-30 flex items-center justify-center bg-black/80 backdrop-blur-sm"
            onClick={() => setSelectedBook(null)}
          >
            <motion.div
              initial={{ scale: 0.8, y: 50 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.8, y: 50 }}
              className="bg-gradient-to-br from-purple-900/95 to-indigo-900/95 backdrop-blur-xl rounded-2xl p-6 max-w-md w-full mx-4 shadow-2xl border border-purple-500/20"
              onClick={e => e.stopPropagation()}
            >
              <div className="flex gap-4">
                {selectedBook.cover_image ? (
                  <img 
                    src={selectedBook.cover_image} 
                    alt={selectedBook.title}
                    className="w-28 h-40 object-cover rounded-lg shadow-lg"
                  />
                ) : (
                  <div className="w-28 h-40 bg-gradient-to-br from-primary/40 to-purple-600/40 rounded-lg flex items-center justify-center">
                    <FiBook className="w-12 h-12 text-white/50" />
                  </div>
                )}
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-white mb-1">{selectedBook.title}</h3>
                  <p className="text-purple-300 text-sm mb-2">by {selectedBook.author_name}</p>
                  <p className="text-white/60 text-xs mb-3 line-clamp-3">
                    {selectedBook.description || selectedBook.back_cover_text || 'A magical story awaits...'}
                  </p>
                  <span className="px-3 py-1 bg-purple-500/30 rounded-full text-xs text-purple-200">
                    {selectedBook.genre}
                  </span>
                </div>
              </div>
              
              <div className="flex gap-3 mt-6">
                <Button
                  variant="outline"
                  className="flex-1 rounded-full border-purple-500/30 text-white hover:bg-purple-500/20"
                  onClick={() => setSelectedBook(null)}
                >
                  Back to Library
                </Button>
                <Button
                  className="flex-1 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white"
                  onClick={() => navigate(`/read/${selectedBook.id}`)}
                >
                  <FiBook className="mr-2" />
                  Read Now
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
