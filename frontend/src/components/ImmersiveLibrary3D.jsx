import { useState, useEffect, useRef, Suspense, useMemo } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { 
  OrbitControls, 
  PerspectiveCamera,
  Stars,
  Text
} from '@react-three/drei';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import * as THREE from 'three';
import { Button } from '@/components/ui/button';
import { FiX, FiBook, FiMaximize2, FiMinimize2, FiVolume2, FiVolumeX } from 'react-icons/fi';

// Magical Bookshelf Component
function MagicalBookshelf({ position, rotation, books, onBookClick, hoveredId, setHoveredId }) {
  const shelfRef = useRef();
  
  return (
    <group position={position} rotation={rotation}>
      {/* Bookshelf frame */}
      <mesh position={[0, 1.5, 0]} castShadow receiveShadow>
        <boxGeometry args={[2.5, 3, 0.4]} />
        <meshStandardMaterial color="#3d2817" roughness={0.8} />
      </mesh>
      
      {/* Shelves */}
      {[0, 1, 2].map((i) => (
        <mesh key={i} position={[0, i * 0.9 + 0.3, 0.05]} castShadow>
          <boxGeometry args={[2.3, 0.08, 0.35]} />
          <meshStandardMaterial color="#5c3d2e" roughness={0.7} />
        </mesh>
      ))}
      
      {/* Books on shelf */}
      {books.slice(0, 6).map((book, idx) => {
        const row = Math.floor(idx / 3);
        const col = idx % 3;
        const bookColors = ['#8b5cf6', '#ec4899', '#06b6d4', '#10b981', '#f59e0b', '#ef4444'];
        
        return (
          <Float
            key={book.id}
            speed={2}
            rotationIntensity={0.1}
            floatIntensity={0.1}
          >
            <group
              position={[-0.6 + col * 0.6, row * 0.9 + 0.55, 0.1]}
              onPointerOver={() => setHoveredId(book.id)}
              onPointerOut={() => setHoveredId(null)}
              onClick={() => onBookClick(book)}
            >
              <mesh castShadow>
                <boxGeometry args={[0.12, 0.5, 0.25]} />
                <meshStandardMaterial 
                  color={hoveredId === book.id ? '#fbbf24' : bookColors[idx % bookColors.length]}
                  emissive={hoveredId === book.id ? '#fbbf24' : '#000000'}
                  emissiveIntensity={hoveredId === book.id ? 0.5 : 0}
                />
              </mesh>
              {hoveredId === book.id && (
                <Text
                  position={[0, 0.4, 0]}
                  fontSize={0.08}
                  color="#ffffff"
                  anchorX="center"
                  anchorY="bottom"
                  maxWidth={1}
                >
                  {book.title}
                </Text>
              )}
            </group>
          </Float>
        );
      })}
    </group>
  );
}

// Floating Magic Orb
function MagicOrb({ position }) {
  const orbRef = useRef();
  
  useFrame((state) => {
    if (orbRef.current) {
      orbRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 2) * 0.3;
      orbRef.current.rotation.y += 0.01;
    }
  });

  return (
    <group ref={orbRef} position={position}>
      <mesh>
        <sphereGeometry args={[0.15, 32, 32]} />
        <MeshDistortMaterial
          color="#8b5cf6"
          emissive="#8b5cf6"
          emissiveIntensity={2}
          distort={0.4}
          speed={3}
          transparent
          opacity={0.8}
        />
      </mesh>
      <Sparkles count={20} scale={1} size={2} speed={0.3} color="#fbbf24" />
    </group>
  );
}

// Gothic Pillar
function GothicPillar({ position }) {
  return (
    <group position={position}>
      {/* Base */}
      <mesh position={[0, 0.2, 0]} castShadow receiveShadow>
        <cylinderGeometry args={[0.4, 0.5, 0.4, 8]} />
        <meshStandardMaterial color="#4a4a4a" roughness={0.9} />
      </mesh>
      {/* Column */}
      <mesh position={[0, 2.5, 0]} castShadow receiveShadow>
        <cylinderGeometry args={[0.25, 0.3, 4.5, 8]} />
        <meshStandardMaterial color="#5a5a5a" roughness={0.8} />
      </mesh>
      {/* Capital */}
      <mesh position={[0, 4.9, 0]} castShadow>
        <cylinderGeometry args={[0.5, 0.25, 0.4, 8]} />
        <meshStandardMaterial color="#4a4a4a" roughness={0.9} />
      </mesh>
    </group>
  );
}

// Grand Chandelier
function Chandelier({ position }) {
  const chandelierRef = useRef();
  
  useFrame((state) => {
    if (chandelierRef.current) {
      chandelierRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.05;
    }
  });

  return (
    <group ref={chandelierRef} position={position}>
      {/* Chain */}
      <mesh position={[0, 1, 0]}>
        <cylinderGeometry args={[0.02, 0.02, 2, 8]} />
        <meshStandardMaterial color="#8B7355" metalness={0.8} />
      </mesh>
      {/* Ring */}
      <mesh position={[0, 0, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[0.8, 0.05, 8, 16]} />
        <meshStandardMaterial color="#CD853F" metalness={0.9} roughness={0.3} />
      </mesh>
      {/* Candles */}
      {[0, 1, 2, 3, 4, 5].map((i) => {
        const angle = (i / 6) * Math.PI * 2;
        return (
          <group key={i} position={[Math.sin(angle) * 0.7, -0.1, Math.cos(angle) * 0.7]}>
            <mesh>
              <cylinderGeometry args={[0.03, 0.04, 0.2, 8]} />
              <meshStandardMaterial color="#FFF8DC" />
            </mesh>
            {/* Flame */}
            <pointLight position={[0, 0.2, 0]} color="#FF6B00" intensity={0.5} distance={3} />
            <mesh position={[0, 0.15, 0]}>
              <sphereGeometry args={[0.04, 8, 8]} />
              <meshBasicMaterial color="#FFA500" />
            </mesh>
          </group>
        );
      })}
    </group>
  );
}

// Floor with carpet
function FloorWithCarpet() {
  return (
    <group>
      {/* Stone floor */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]} receiveShadow>
        <planeGeometry args={[30, 30]} />
        <meshStandardMaterial color="#3d3d3d" roughness={0.9} />
      </mesh>
      {/* Red carpet */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, 0]} receiveShadow>
        <planeGeometry args={[3, 15]} />
        <meshStandardMaterial color="#8B0000" roughness={0.8} />
      </mesh>
    </group>
  );
}

// Camera Controller
function CameraController() {
  const { camera } = useThree();
  
  useEffect(() => {
    camera.position.set(0, 4, 12);
    camera.lookAt(0, 2, 0);
  }, [camera]);

  return (
    <OrbitControls 
      enablePan={true}
      enableZoom={true}
      enableRotate={true}
      minDistance={5}
      maxDistance={25}
      maxPolarAngle={Math.PI / 2}
      minPolarAngle={Math.PI / 6}
      target={[0, 2, 0]}
    />
  );
}

// Ambient Sound Hook
function useLibraryAmbience() {
  const audioRef = useRef(null);
  const [isMuted, setIsMuted] = useState(false);

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

  return { isMuted, toggleMute };
}

// Main Component
export default function ImmersiveLibrary3D({ books = [], onClose, onSelectBook }) {
  const navigate = useNavigate();
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [selectedBook, setSelectedBook] = useState(null);
  const [hoveredBookId, setHoveredBookId] = useState(null);
  const containerRef = useRef();
  const { isMuted, toggleMute } = useLibraryAmbience();

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  const handleBookClick = (book) => {
    setSelectedBook(book);
  };

  const handleReadBook = () => {
    if (selectedBook) {
      navigate(`/read/${selectedBook.id}`);
    }
  };

  // Distribute books across bookshelves
  const booksByShelf = useMemo(() => {
    const shelves = [[], [], [], [], [], []];
    books.forEach((book, idx) => {
      shelves[idx % 6].push(book);
    });
    return shelves;
  }, [books]);

  return (
    <div 
      ref={containerRef}
      className="fixed inset-0 z-50 bg-gradient-to-b from-[#1a0a2e] to-[#0d0015]"
      data-testid="immersive-library-3d"
    >
      {/* Controls Overlay */}
      <div className="absolute top-4 left-4 right-4 z-10 flex justify-between items-start">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="bg-black/50 hover:bg-black/70 text-white rounded-full"
          >
            <FiX className="w-5 h-5" />
          </Button>
          <div className="bg-black/50 backdrop-blur px-4 py-2 rounded-full">
            <h2 className="text-white font-bold">✨ The Grand Library ✨</h2>
            <p className="text-white/70 text-xs">Drag to explore • Scroll to zoom • Click books to read</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleMute}
            className="bg-black/50 hover:bg-black/70 text-white rounded-full"
          >
            {isMuted ? <FiVolumeX className="w-5 h-5" /> : <FiVolume2 className="w-5 h-5" />}
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleFullscreen}
            className="bg-black/50 hover:bg-black/70 text-white rounded-full"
          >
            {isFullscreen ? <FiMinimize2 className="w-5 h-5" /> : <FiMaximize2 className="w-5 h-5" />}
          </Button>
        </div>
      </div>

      {/* 3D Canvas */}
      <Canvas shadows dpr={[1, 2]} gl={{ antialias: true }}>
        <Suspense fallback={null}>
          {/* Ambient Lighting */}
          <ambientLight intensity={0.2} color="#4a3f6b" />
          
          {/* Main spotlight */}
          <spotLight
            position={[0, 10, 0]}
            angle={0.5}
            penumbra={0.5}
            intensity={1}
            castShadow
            shadow-mapSize={[1024, 1024]}
            color="#ffd9a0"
          />
          
          {/* Side lights */}
          <pointLight position={[-8, 4, 0]} intensity={0.3} color="#ff6b35" />
          <pointLight position={[8, 4, 0]} intensity={0.3} color="#4ecdc4" />
          
          {/* Fog for atmosphere */}
          <fog attach="fog" args={['#1a0a2e', 10, 40]} />
          
          {/* Stars in background */}
          <Stars radius={50} depth={50} count={2000} factor={3} fade speed={0.5} />
          
          {/* Floor */}
          <FloorWithCarpet />
          
          {/* Gothic Pillars */}
          <GothicPillar position={[-6, 0, -5]} />
          <GothicPillar position={[6, 0, -5]} />
          <GothicPillar position={[-6, 0, 5]} />
          <GothicPillar position={[6, 0, 5]} />
          
          {/* Chandelier */}
          <Chandelier position={[0, 7, 0]} />
          
          {/* Bookshelves in a semi-circle */}
          <MagicalBookshelf 
            position={[-5, 0, -3]} 
            rotation={[0, Math.PI / 6, 0]} 
            books={booksByShelf[0]}
            onBookClick={handleBookClick}
            hoveredId={hoveredBookId}
            setHoveredId={setHoveredBookId}
          />
          <MagicalBookshelf 
            position={[0, 0, -5]} 
            rotation={[0, 0, 0]} 
            books={booksByShelf[1]}
            onBookClick={handleBookClick}
            hoveredId={hoveredBookId}
            setHoveredId={setHoveredBookId}
          />
          <MagicalBookshelf 
            position={[5, 0, -3]} 
            rotation={[0, -Math.PI / 6, 0]} 
            books={booksByShelf[2]}
            onBookClick={handleBookClick}
            hoveredId={hoveredBookId}
            setHoveredId={setHoveredBookId}
          />
          
          {/* Back wall bookshelves */}
          <MagicalBookshelf 
            position={[-8, 0, 0]} 
            rotation={[0, Math.PI / 2, 0]} 
            books={booksByShelf[3]}
            onBookClick={handleBookClick}
            hoveredId={hoveredBookId}
            setHoveredId={setHoveredBookId}
          />
          <MagicalBookshelf 
            position={[8, 0, 0]} 
            rotation={[0, -Math.PI / 2, 0]} 
            books={booksByShelf[4]}
            onBookClick={handleBookClick}
            hoveredId={hoveredBookId}
            setHoveredId={setHoveredBookId}
          />
          
          {/* Magic Orbs */}
          <MagicOrb position={[-3, 3, 2]} />
          <MagicOrb position={[3, 2.5, 3]} />
          <MagicOrb position={[0, 4, -2]} />
          
          {/* Sparkles throughout */}
          <Sparkles count={100} scale={20} size={3} speed={0.2} color="#ffd700" />
          
          {/* Camera */}
          <PerspectiveCamera makeDefault fov={60} near={0.1} far={100} />
          <CameraController />
        </Suspense>
      </Canvas>

      {/* Book Preview Modal */}
      <AnimatePresence>
        {selectedBook && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-20 flex items-center justify-center bg-black/70 backdrop-blur-sm"
            onClick={() => setSelectedBook(null)}
          >
            <motion.div
              initial={{ scale: 0.8, y: 50 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.8, y: 50 }}
              className="bg-gradient-to-br from-purple-900/90 to-indigo-900/90 backdrop-blur-xl rounded-2xl p-6 max-w-md w-full mx-4 shadow-2xl border border-white/10"
              onClick={e => e.stopPropagation()}
            >
              <div className="flex gap-4">
                {selectedBook.cover_image ? (
                  <img 
                    src={selectedBook.cover_image} 
                    alt={selectedBook.title}
                    className="w-24 h-36 object-cover rounded-lg shadow-lg"
                  />
                ) : (
                  <div className="w-24 h-36 bg-gradient-to-br from-primary/40 to-purple-600/40 rounded-lg flex items-center justify-center">
                    <FiBook className="w-10 h-10 text-white/50" />
                  </div>
                )}
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-white mb-1">{selectedBook.title}</h3>
                  <p className="text-white/70 text-sm mb-2">by {selectedBook.author_name}</p>
                  <p className="text-white/60 text-xs mb-3 line-clamp-3">
                    {selectedBook.description || selectedBook.back_cover_text || 'A magical story awaits...'}
                  </p>
                  <div className="flex gap-2">
                    <span className="px-2 py-1 bg-white/10 rounded-full text-xs text-white/80">
                      {selectedBook.genre}
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="flex gap-3 mt-6">
                <Button
                  variant="outline"
                  className="flex-1 rounded-full border-white/20 text-white hover:bg-white/10"
                  onClick={() => setSelectedBook(null)}
                >
                  Back to Library
                </Button>
                <Button
                  className="flex-1 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
                  onClick={handleReadBook}
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
