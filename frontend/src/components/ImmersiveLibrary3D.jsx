import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { Button } from '@/components/ui/button';
import { FiX, FiBook, FiMaximize2, FiMinimize2, FiVolume2, FiVolumeX } from 'react-icons/fi';

// Gothic Library Model URL
const LIBRARY_MODEL_URL = 'https://customer-assets.emergentagent.com/job_513aa01a-ca6e-4353-9972-f674c11a8691/artifacts/w6xrpyo6_gothic_library_4_cycles.glb';

// Vanilla Three.js Library Viewer
export default function ImmersiveLibrary3D({ books = [], onClose }) {
  const navigate = useNavigate();
  const containerRef = useRef(null);
  const canvasRef = useRef(null);
  const rendererRef = useRef(null);
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const controlsRef = useRef(null);
  const animationIdRef = useRef(null);
  
  const [isLoaded, setIsLoaded] = useState(false);
  const [loadProgress, setLoadProgress] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [selectedBook, setSelectedBook] = useState(null);
  const [isMuted, setIsMuted] = useState(false);
  const audioRef = useRef(null);

  // Initialize Three.js scene
  useEffect(() => {
    if (!canvasRef.current) return;

    // Create scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a0a2e);
    scene.fog = new THREE.Fog(0x1a0a2e, 5, 100);
    sceneRef.current = scene;

    // Create camera
    const camera = new THREE.PerspectiveCamera(
      60,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    camera.position.set(0, 3, 10);
    cameraRef.current = camera;

    // Create renderer
    const renderer = new THREE.WebGLRenderer({
      canvas: canvasRef.current,
      antialias: true,
      powerPreference: 'high-performance',
    });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1;
    rendererRef.current = renderer;

    // Create controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 1;
    controls.maxDistance = 50;
    controls.maxPolarAngle = Math.PI / 1.8;
    controls.target.set(0, 2, 0);
    controlsRef.current = controls;

    // Add lighting
    const ambientLight = new THREE.AmbientLight(0xffd9a0, 0.4);
    scene.add(ambientLight);

    const mainLight = new THREE.DirectionalLight(0xfff5e6, 0.8);
    mainLight.position.set(5, 10, 5);
    mainLight.castShadow = true;
    mainLight.shadow.mapSize.width = 2048;
    mainLight.shadow.mapSize.height = 2048;
    scene.add(mainLight);

    const warmLight = new THREE.PointLight(0xff9500, 0.5, 30);
    warmLight.position.set(0, 8, 0);
    scene.add(warmLight);

    const accentLight1 = new THREE.PointLight(0xff6b35, 0.3, 20);
    accentLight1.position.set(-5, 3, 0);
    scene.add(accentLight1);

    const accentLight2 = new THREE.PointLight(0x4ecdc4, 0.3, 20);
    accentLight2.position.set(5, 3, 0);
    scene.add(accentLight2);

    // Load the GLB model
    const dracoLoader = new DRACOLoader();
    dracoLoader.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.6/');
    
    const gltfLoader = new GLTFLoader();
    gltfLoader.setDRACOLoader(dracoLoader);

    gltfLoader.load(
      LIBRARY_MODEL_URL,
      (gltf) => {
        console.log('✅ Gothic Library loaded successfully!');
        
        const model = gltf.scene;
        model.scale.set(0.5, 0.5, 0.5);
        model.position.set(0, 0, 0);
        
        // Enable shadows on all meshes
        model.traverse((child) => {
          if (child.isMesh) {
            child.castShadow = true;
            child.receiveShadow = true;
          }
        });
        
        scene.add(model);
        setIsLoaded(true);
      },
      (progress) => {
        if (progress.total > 0) {
          const percent = (progress.loaded / progress.total) * 100;
          setLoadProgress(percent);
          console.log(`Loading: ${percent.toFixed(1)}%`);
        }
      },
      (error) => {
        console.error('❌ Error loading model:', error);
        setLoadProgress(-1); // Error state
      }
    );

    // Animation loop
    const animate = () => {
      animationIdRef.current = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    // Handle resize
    const handleResize = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };
    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      if (animationIdRef.current) {
        cancelAnimationFrame(animationIdRef.current);
      }
      controls.dispose();
      renderer.dispose();
      dracoLoader.dispose();
      
      // Dispose scene objects
      scene.traverse((object) => {
        if (object.geometry) object.geometry.dispose();
        if (object.material) {
          if (Array.isArray(object.material)) {
            object.material.forEach(m => m.dispose());
          } else {
            object.material.dispose();
          }
        }
      });
    };
  }, []);

  // Ambient sound
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

  return (
    <div 
      ref={containerRef}
      className="fixed inset-0 z-50 bg-black"
      data-testid="immersive-library-3d"
    >
      {/* Three.js Canvas */}
      <canvas ref={canvasRef} className="w-full h-full" />

      {/* Loading Screen */}
      {!isLoaded && (
        <div className="absolute inset-0 z-30 flex flex-col items-center justify-center bg-gradient-to-b from-[#1a0a2e] to-[#0d0015]">
          <div className="text-center space-y-6">
            <div className="relative w-32 h-32 mx-auto">
              <div className="absolute inset-0 border-4 border-purple-500/30 rounded-full animate-ping" />
              <div className="absolute inset-2 border-4 border-purple-500/50 rounded-full animate-spin" style={{ animationDuration: '3s' }} />
              <div className="absolute inset-4 border-4 border-purple-400/70 rounded-full animate-spin" style={{ animationDuration: '2s', animationDirection: 'reverse' }} />
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-3xl font-bold text-white">
                  {loadProgress < 0 ? '!' : `${Math.round(loadProgress)}%`}
                </span>
              </div>
            </div>
            
            <div className="space-y-2">
              <h2 className="text-2xl font-bold text-white">
                {loadProgress < 0 ? 'Error Loading Model' : 'Entering the Grand Library'}
              </h2>
              <p className="text-purple-300 text-sm">
                {loadProgress < 0 ? 'Please try again later' : 'Loading high-quality 3D assets...'}
              </p>
            </div>
            
            {loadProgress >= 0 && (
              <div className="w-64 h-2 bg-purple-900/50 rounded-full overflow-hidden mx-auto">
                <motion.div
                  className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
                  initial={{ width: 0 }}
                  animate={{ width: `${loadProgress}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Controls */}
      <div className={`absolute top-4 left-4 right-4 z-20 flex justify-between items-start transition-opacity duration-500 ${isLoaded ? 'opacity-100' : 'opacity-0'}`}>
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

      {/* Instructions */}
      {isLoaded && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20">
          <div className="bg-black/50 backdrop-blur px-6 py-3 rounded-full">
            <p className="text-white/80 text-sm">
              🖱️ Left-click + drag to rotate • 🔍 Scroll to zoom • Right-click + drag to pan
            </p>
          </div>
        </div>
      )}

      {/* Book Panel */}
      {isLoaded && books.length > 0 && (
        <div className="absolute bottom-20 left-4 right-4 z-20">
          <div className="bg-black/70 backdrop-blur-lg rounded-2xl p-4 max-w-4xl mx-auto">
            <h3 className="text-white font-bold mb-3">📚 Library Collection</h3>
            <div className="flex gap-3 overflow-x-auto pb-2">
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

      {/* Book Modal */}
      <AnimatePresence>
        {selectedBook && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-40 flex items-center justify-center bg-black/80 backdrop-blur-sm"
            onClick={() => setSelectedBook(null)}
          >
            <motion.div
              initial={{ scale: 0.8, y: 50 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.8, y: 50 }}
              className="bg-gradient-to-br from-purple-900/95 to-indigo-900/95 rounded-2xl p-6 max-w-md w-full mx-4 shadow-2xl border border-purple-500/20"
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
                  <div className="w-28 h-40 bg-gradient-to-br from-purple-500/40 to-pink-500/40 rounded-lg flex items-center justify-center">
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
                  Back
                </Button>
                <Button
                  className="flex-1 rounded-full bg-gradient-to-r from-purple-500 to-pink-500"
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
