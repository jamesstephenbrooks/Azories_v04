import { useState, useEffect, useRef, Suspense } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { Button } from '@/components/ui/button';
import { FiX, FiBook, FiMaximize2, FiMinimize2, FiVolume2, FiVolumeX } from 'react-icons/fi';

// Gothic Library Model URL
const LIBRARY_MODEL_URL = 'https://customer-assets.emergentagent.com/job_513aa01a-ca6e-4353-9972-f674c11a8691/artifacts/tsbv1z7k_gothic_library_2_cycles.glb';

// Loading Progress Component (outside Canvas)
function LoadingScreen({ progress }) {
  return (
    <div className="absolute inset-0 z-30 flex flex-col items-center justify-center bg-gradient-to-b from-[#1a0a2e] to-[#0d0015]">
      <div className="text-center space-y-6">
        <div className="relative w-32 h-32 mx-auto">
          <div className="absolute inset-0 border-4 border-purple-500/30 rounded-full animate-ping" />
          <div className="absolute inset-2 border-4 border-purple-500/50 rounded-full animate-spin" style={{ animationDuration: '3s' }} />
          <div className="absolute inset-4 border-4 border-purple-400/70 rounded-full animate-spin" style={{ animationDuration: '2s', animationDirection: 'reverse' }} />
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-3xl font-bold text-white">{Math.round(progress)}%</span>
          </div>
        </div>
        
        <div className="space-y-2">
          <h2 className="text-2xl font-bold text-white">Entering the Grand Library</h2>
          <p className="text-purple-300 text-sm">Preparing a magical experience...</p>
        </div>
        
        <div className="w-64 h-2 bg-purple-900/50 rounded-full overflow-hidden mx-auto">
          <motion.div
            className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>
        
        <p className="text-purple-400/70 text-xs">Loading high-quality 3D assets...</p>
      </div>
    </div>
  );
}

// The Gothic Library Model Component
function GothicLibraryModel({ onProgress, onLoaded }) {
  const [model, setModel] = useState(null);
  const groupRef = useRef();

  useEffect(() => {
    const dracoLoader = new DRACOLoader();
    dracoLoader.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.6/');
    dracoLoader.setDecoderConfig({ type: 'js' });
    
    const gltfLoader = new GLTFLoader();
    gltfLoader.setDRACOLoader(dracoLoader);

    gltfLoader.load(
      LIBRARY_MODEL_URL,
      (gltf) => {
        console.log('Model loaded successfully');
        
        gltf.scene.traverse((child) => {
          if (child.isMesh) {
            child.castShadow = true;
            child.receiveShadow = true;
          }
        });
        
        gltf.scene.scale.set(0.5, 0.5, 0.5);
        gltf.scene.position.set(0, 0, 0);
        
        setModel(gltf.scene);
        if (onLoaded) onLoaded();
      },
      (progress) => {
        if (progress.total > 0) {
          const percent = (progress.loaded / progress.total) * 100;
          if (onProgress) onProgress(percent);
        }
      },
      (err) => {
        console.error('Error loading model:', err);
      }
    );

    return () => {
      dracoLoader.dispose();
    };
  }, [onProgress, onLoaded]);

  if (!model) return null;

  return (
    <group ref={groupRef}>
      <primitive object={model} />
    </group>
  );
}

// Camera controller using Three.js OrbitControls
function CameraController() {
  const { camera, gl } = useThree();
  const controlsRef = useRef();

  useEffect(() => {
    camera.position.set(0, 3, 8);
    
    const controls = new OrbitControls(camera, gl.domElement);
    controls.enablePan = true;
    controls.enableZoom = true;
    controls.enableRotate = true;
    controls.minDistance = 1;
    controls.maxDistance = 20;
    controls.maxPolarAngle = Math.PI / 1.8;
    controls.minPolarAngle = Math.PI / 6;
    controls.target.set(0, 2, 0);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.update();
    
    controlsRef.current = controls;

    return () => {
      controls.dispose();
    };
  }, [camera, gl]);

  useFrame(() => {
    if (controlsRef.current) {
      controlsRef.current.update();
    }
  });

  return null;
}

// Scene Content
function SceneContent({ onProgress, onLoaded }) {
  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.4} color="#ffd9a0" />
      <directionalLight
        position={[5, 10, 5]}
        intensity={0.8}
        castShadow
        color="#fff5e6"
      />
      <pointLight position={[0, 8, 0]} intensity={0.5} color="#ff9500" distance={20} />
      <pointLight position={[-5, 3, 0]} intensity={0.3} color="#ff6b35" distance={15} />
      <pointLight position={[5, 3, 0]} intensity={0.3} color="#4ecdc4" distance={15} />
      
      {/* Fog for atmosphere */}
      <fog attach="fog" args={['#1a0a2e', 5, 50]} />
      
      {/* The Gothic Library Model */}
      <GothicLibraryModel onProgress={onProgress} onLoaded={onLoaded} />
      
      {/* Camera controls */}
      <CameraController />
    </>
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

// Main Immersive Library Component
export default function ImmersiveLibrary3D({ books = [], onClose }) {
  const navigate = useNavigate();
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [selectedBook, setSelectedBook] = useState(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [loadProgress, setLoadProgress] = useState(0);
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

  const handleReadBook = () => {
    if (selectedBook) {
      navigate(`/read/${selectedBook.id}`);
    }
  };

  return (
    <div 
      ref={containerRef}
      className="fixed inset-0 z-50 bg-black"
      data-testid="immersive-library-3d"
    >
      {/* Loading Screen */}
      {!isLoaded && <LoadingScreen progress={loadProgress} />}

      {/* Controls Overlay */}
      <div className={`absolute top-4 left-4 right-4 z-20 flex justify-between items-start transition-opacity ${isLoaded ? 'opacity-100' : 'opacity-0'}`}>
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
            <h2 className="text-white font-bold">✨ The Grand Gothic Library ✨</h2>
            <p className="text-white/70 text-xs">Drag to rotate • Scroll to zoom • Right-click to pan</p>
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

      {/* Instructions at bottom */}
      {isLoaded && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20">
          <div className="bg-black/50 backdrop-blur px-6 py-3 rounded-full text-center">
            <p className="text-white/80 text-sm">
              🖱️ Left-click + drag to rotate • 🔍 Scroll to zoom • Right-click + drag to pan
            </p>
          </div>
        </div>
      )}

      {/* Book selection panel */}
      {isLoaded && books.length > 0 && (
        <div className="absolute bottom-20 left-4 right-4 z-20">
          <div className="bg-black/70 backdrop-blur-lg rounded-2xl p-4 max-w-4xl mx-auto">
            <h3 className="text-white font-bold mb-3">📚 Library Collection</h3>
            <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-hide">
              {books.slice(0, 10).map((book) => (
                <motion.div
                  key={book.id}
                  whileHover={{ scale: 1.05, y: -5 }}
                  className="flex-shrink-0 cursor-pointer"
                  onClick={() => setSelectedBook(book)}
                >
                  <div className="w-20 h-28 rounded-lg overflow-hidden border-2 border-white/20 hover:border-purple-500 transition-colors">
                    {book.cover_image ? (
                      <img src={book.cover_image} alt={book.title} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center">
                        <FiBook className="w-6 h-6 text-white/70" />
                      </div>
                    )}
                  </div>
                  <p className="text-white text-xs mt-1 text-center truncate w-20">{book.title}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 3D Canvas */}
      <Canvas
        shadows
        dpr={[1, 1.5]}
        gl={{ 
          antialias: true,
          powerPreference: 'high-performance',
          alpha: false,
        }}
        camera={{ fov: 60, near: 0.1, far: 1000 }}
      >
        <SceneContent 
          onProgress={setLoadProgress} 
          onLoaded={() => setIsLoaded(true)} 
        />
      </Canvas>

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
