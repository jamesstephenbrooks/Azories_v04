import { useState, useEffect, useRef, Suspense } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { 
  OrbitControls, 
  useGLTF, 
  PerspectiveCamera,
  useProgress,
  Stars,
  Text
} from '@react-three/drei';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import * as THREE from 'three';
import { Button } from '@/components/ui/button';
import { FiX, FiBook, FiMaximize2, FiMinimize2, FiVolume2, FiVolumeX } from 'react-icons/fi';

// Gothic Library Model URL
const LIBRARY_MODEL_URL = 'https://customer-assets.emergentagent.com/job_513aa01a-ca6e-4353-9972-f674c11a8691/artifacts/hhekpfcn_gothic_library_2_cycles.glb';

// Loading screen component
function Loader() {
  const { progress } = useProgress();
  return (
    <group position={[0, 3, 0]}>
      <Text
        fontSize={0.5}
        color="white"
        anchorX="center"
        anchorY="middle"
      >
        {`Loading Library... ${progress.toFixed(0)}%`}
      </Text>
    </group>
  );
}

// The Gothic Library 3D Model
function GothicLibrary({ onBookClick, books = [] }) {
  const { scene } = useGLTF(LIBRARY_MODEL_URL);
  const libraryRef = useRef();
  
  useEffect(() => {
    if (scene) {
      // Adjust scene scale and position if needed
      scene.scale.set(1, 1, 1);
      scene.position.set(0, 0, 0);
      
      // Enable shadows for all meshes
      scene.traverse((child) => {
        if (child.isMesh) {
          child.castShadow = true;
          child.receiveShadow = true;
        }
      });
    }
  }, [scene]);

  return (
    <group ref={libraryRef}>
      <primitive object={scene} />
    </group>
  );
}

// Floating Book Card in 3D Space
function FloatingBookCard({ book, position, onClick }) {
  const meshRef = useRef();
  const [hovered, setHovered] = useState(false);
  
  useFrame((state) => {
    if (meshRef.current) {
      // Gentle floating animation
      meshRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime + position[0]) * 0.05;
      meshRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.1;
    }
  });

  return (
    <group 
      ref={meshRef} 
      position={position}
      onPointerOver={() => setHovered(true)}
      onPointerOut={() => setHovered(false)}
      onClick={onClick}
    >
      {/* Book cover plane */}
      <mesh castShadow>
        <boxGeometry args={[0.4, 0.6, 0.05]} />
        <meshStandardMaterial 
          color={hovered ? "#8b5cf6" : "#4c1d95"} 
          emissive={hovered ? "#8b5cf6" : "#000000"}
          emissiveIntensity={hovered ? 0.3 : 0}
        />
      </mesh>
      
      {/* Book title HTML overlay */}
      {hovered && (
        <Html position={[0, 0.4, 0]} center distanceFactor={10}>
          <div className="bg-black/80 backdrop-blur px-3 py-2 rounded-lg text-center whitespace-nowrap">
            <p className="text-white text-sm font-bold">{book.title}</p>
            <p className="text-white/70 text-xs">{book.author_name}</p>
          </div>
        </Html>
      )}
    </group>
  );
}

// Camera Controller with smooth movement
function CameraController() {
  const { camera } = useThree();
  
  useEffect(() => {
    // Set initial camera position for a grand view
    camera.position.set(0, 5, 15);
    camera.lookAt(0, 3, 0);
  }, [camera]);

  return (
    <OrbitControls 
      enablePan={true}
      enableZoom={true}
      enableRotate={true}
      minDistance={2}
      maxDistance={50}
      maxPolarAngle={Math.PI / 1.5}
      minPolarAngle={Math.PI / 6}
      autoRotate={false}
      autoRotateSpeed={0.3}
      target={[0, 3, 0]}
    />
  );
}

// Ambient Sound for the library
function useLibraryAmbience() {
  const audioRef = useRef(null);
  const [isMuted, setIsMuted] = useState(false);

  useEffect(() => {
    // Create ambient library sound
    const audio = new Audio('https://assets.mixkit.co/sfx/preview/mixkit-light-rain-loop-2393.mp3');
    audio.loop = true;
    audio.volume = 0.2;
    audioRef.current = audio;
    
    // Try to play (may be blocked by browser autoplay policy)
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

// Main Immersive Library Component
export default function ImmersiveLibrary3D({ books = [], onClose, onSelectBook }) {
  const navigate = useNavigate();
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [selectedBook, setSelectedBook] = useState(null);
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

  // Generate book positions in a circle around the library
  const bookPositions = books.slice(0, 12).map((_, idx) => {
    const angle = (idx / 12) * Math.PI * 2;
    const radius = 8;
    return [
      Math.sin(angle) * radius,
      2 + Math.random() * 2,
      Math.cos(angle) * radius
    ];
  });

  return (
    <div 
      ref={containerRef}
      className="fixed inset-0 z-50 bg-black"
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
            <h2 className="text-white font-bold">The Grand Library</h2>
            <p className="text-white/70 text-xs">Click and drag to explore • Scroll to zoom</p>
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

      {/* Instructions */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-10">
        <div className="bg-black/50 backdrop-blur px-6 py-3 rounded-full text-center">
          <p className="text-white/80 text-sm">
            🖱️ Drag to rotate • 🔍 Scroll to zoom • 📚 Click floating books to read
          </p>
        </div>
      </div>

      {/* 3D Canvas */}
      <Canvas shadows dpr={[1, 2]} gl={{ antialias: true }}>
        <Suspense fallback={<Loader />}>
          {/* Lighting */}
          <ambientLight intensity={0.3} />
          <directionalLight
            position={[10, 20, 10]}
            intensity={1}
            castShadow
            shadow-mapSize={[2048, 2048]}
          />
          <pointLight position={[0, 10, 0]} intensity={0.5} color="#ffd700" />
          <pointLight position={[-5, 5, -5]} intensity={0.3} color="#ff6b35" />
          <pointLight position={[5, 5, 5]} intensity={0.3} color="#4ecdc4" />

          {/* Environment */}
          <Stars radius={100} depth={50} count={1000} factor={4} fade />
          <fog attach="fog" args={['#1a1a2e', 20, 80]} />
          
          {/* The Gothic Library */}
          <GothicLibrary books={books} onBookClick={handleBookClick} />
          
          {/* Floating Book Cards */}
          {books.slice(0, 12).map((book, idx) => (
            <FloatingBookCard
              key={book.id}
              book={book}
              position={bookPositions[idx]}
              onClick={() => handleBookClick(book)}
            />
          ))}
          
          {/* Camera */}
          <PerspectiveCamera makeDefault fov={60} near={0.1} far={1000} />
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
                    {selectedBook.age_rating && (
                      <span className="px-2 py-1 bg-white/10 rounded-full text-xs text-white/80">
                        {selectedBook.age_rating}
                      </span>
                    )}
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

// Preload the model
useGLTF.preload(LIBRARY_MODEL_URL);
