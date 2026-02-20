import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader';
import { PointerLockControls } from 'three/examples/jsm/controls/PointerLockControls';
import { Button } from '@/components/ui/button';
import { FiX, FiBook, FiMaximize2, FiMinimize2, FiVolume2, FiVolumeX, FiMove } from 'react-icons/fi';

// Gothic Library Model URL - Using proxy to bypass CORS
const ORIGINAL_GLB_URL = 'https://customer-assets.emergentagent.com/job_513aa01a-ca6e-4353-9972-f674c11a8691/artifacts/w6xrpyo6_gothic_library_4_cycles.glb';
const LIBRARY_MODEL_URL = `${process.env.REACT_APP_BACKEND_URL}/api/proxy/glb?url=${encodeURIComponent(ORIGINAL_GLB_URL)}`;

// First-person Library Viewer with WASD controls
export default function ImmersiveLibrary3D({ books = [], onClose }) {
  const navigate = useNavigate();
  const containerRef = useRef(null);
  const canvasRef = useRef(null);
  const rendererRef = useRef(null);
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const controlsRef = useRef(null);
  const animationIdRef = useRef(null);
  const clockRef = useRef(new THREE.Clock());
  
  // Movement state
  const moveForward = useRef(false);
  const moveBackward = useRef(false);
  const moveLeft = useRef(false);
  const moveRight = useRef(false);
  const velocity = useRef(new THREE.Vector3());
  const direction = useRef(new THREE.Vector3());
  
  const [isLoaded, setIsLoaded] = useState(false);
  const [loadProgress, setLoadProgress] = useState(0);
  const [loadError, setLoadError] = useState(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [selectedBook, setSelectedBook] = useState(null);
  const [isMuted, setIsMuted] = useState(false);
  const [isLocked, setIsLocked] = useState(false);
  const [showInstructions, setShowInstructions] = useState(true);
  const audioRef = useRef(null);

  // Handle keyboard input
  const onKeyDown = useCallback((event) => {
    switch (event.code) {
      case 'KeyW':
      case 'ArrowUp':
        moveForward.current = true;
        break;
      case 'KeyA':
      case 'ArrowLeft':
        moveLeft.current = true;
        break;
      case 'KeyS':
      case 'ArrowDown':
        moveBackward.current = true;
        break;
      case 'KeyD':
      case 'ArrowRight':
        moveRight.current = true;
        break;
      case 'Escape':
        if (controlsRef.current) {
          controlsRef.current.unlock();
        }
        break;
    }
  }, []);

  const onKeyUp = useCallback((event) => {
    switch (event.code) {
      case 'KeyW':
      case 'ArrowUp':
        moveForward.current = false;
        break;
      case 'KeyA':
      case 'ArrowLeft':
        moveLeft.current = false;
        break;
      case 'KeyS':
      case 'ArrowDown':
        moveBackward.current = false;
        break;
      case 'KeyD':
      case 'ArrowRight':
        moveRight.current = false;
        break;
    }
  }, []);

  // Initialize Three.js scene
  useEffect(() => {
    if (!canvasRef.current) return;

    // Create scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a0a2e);
    scene.fog = new THREE.Fog(0x1a0a2e, 1, 80);
    sceneRef.current = scene;

    // Create camera - first person perspective
    const camera = new THREE.PerspectiveCamera(
      75,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    // Start inside the library at eye level
    camera.position.set(0, 1.7, 0);
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
    renderer.toneMappingExposure = 1.2;
    rendererRef.current = renderer;

    // Create PointerLock controls for first-person movement
    const controls = new PointerLockControls(camera, renderer.domElement);
    controlsRef.current = controls;
    
    controls.addEventListener('lock', () => {
      setIsLocked(true);
      setShowInstructions(false);
    });
    
    controls.addEventListener('unlock', () => {
      setIsLocked(false);
      setShowInstructions(true);
    });

    // Add lighting - warm library atmosphere
    const ambientLight = new THREE.AmbientLight(0xffd9a0, 0.5);
    scene.add(ambientLight);

    // Main overhead light
    const mainLight = new THREE.DirectionalLight(0xfff5e6, 0.6);
    mainLight.position.set(5, 15, 5);
    mainLight.castShadow = true;
    mainLight.shadow.mapSize.width = 2048;
    mainLight.shadow.mapSize.height = 2048;
    mainLight.shadow.camera.near = 0.5;
    mainLight.shadow.camera.far = 50;
    scene.add(mainLight);

    // Warm point lights for candle/torch effect
    const warmLight1 = new THREE.PointLight(0xff9500, 0.8, 15);
    warmLight1.position.set(-3, 3, -3);
    scene.add(warmLight1);

    const warmLight2 = new THREE.PointLight(0xff7b00, 0.8, 15);
    warmLight2.position.set(3, 3, 3);
    scene.add(warmLight2);

    const warmLight3 = new THREE.PointLight(0xff8c00, 0.6, 20);
    warmLight3.position.set(0, 5, 0);
    scene.add(warmLight3);

    // Add some colored accent lights
    const accentLight1 = new THREE.PointLight(0x4a90d9, 0.3, 25);
    accentLight1.position.set(-5, 2, 5);
    scene.add(accentLight1);

    const accentLight2 = new THREE.PointLight(0xd94a4a, 0.3, 25);
    accentLight2.position.set(5, 2, -5);
    scene.add(accentLight2);

    // Load the GLB model
    const dracoLoader = new DRACOLoader();
    dracoLoader.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.6/');
    
    const gltfLoader = new GLTFLoader();
    gltfLoader.setDRACOLoader(dracoLoader);

    console.log('Loading model from:', LIBRARY_MODEL_URL);

    // Add timeout for the model load
    const loadTimeout = setTimeout(() => {
      console.warn('Model load timeout - taking too long');
      setLoadError('Loading is taking too long. The 50MB model may be too large for your connection. Try refreshing or use a different browser.');
    }, 120000); // 2 minute timeout

    gltfLoader.load(
      LIBRARY_MODEL_URL,
      (gltf) => {
        clearTimeout(loadTimeout);
        console.log('Gothic Library loaded successfully!');
        
        const model = gltf.scene;
        
        // Center and scale the model
        const box = new THREE.Box3().setFromObject(model);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        
        // Scale to reasonable size (library should be walkable)
        const maxDim = Math.max(size.x, size.y, size.z);
        const scale = 10 / maxDim; // Normalize to about 10 units
        model.scale.setScalar(scale);
        
        // Recalculate after scaling
        box.setFromObject(model);
        box.getCenter(center);
        
        // Center the model at origin
        model.position.sub(center);
        
        // Adjust Y so floor is at y=0
        const newBox = new THREE.Box3().setFromObject(model);
        model.position.y -= newBox.min.y;
        
        // Enable shadows on all meshes
        model.traverse((child) => {
          if (child.isMesh) {
            child.castShadow = true;
            child.receiveShadow = true;
            // Improve material quality
            if (child.material) {
              child.material.needsUpdate = true;
            }
          }
        });
        
        scene.add(model);
        
        // Position camera inside the library
        camera.position.set(0, 1.7, 2);
        
        setIsLoaded(true);
        setLoadError(null);
      },
      (progress) => {
        if (progress.total > 0) {
          const percent = (progress.loaded / progress.total) * 100;
          setLoadProgress(percent);
          console.log(`Loading: ${percent.toFixed(1)}%`);
        } else if (progress.loaded > 0) {
          // If total is unknown, show bytes loaded
          setLoadProgress(Math.min((progress.loaded / 50000000) * 100, 99));
        }
      },
      (error) => {
        clearTimeout(loadTimeout);
        console.error('Error loading model:', error);
        setLoadError(error.message || 'Failed to load 3D model. Please try refreshing the page.');
        setLoadProgress(-1);
      }
    );

    // Animation loop with movement
    const animate = () => {
      animationIdRef.current = requestAnimationFrame(animate);
      
      const delta = clockRef.current.getDelta();
      
      if (controlsRef.current && controlsRef.current.isLocked) {
        // Apply friction/damping
        velocity.current.x -= velocity.current.x * 10.0 * delta;
        velocity.current.z -= velocity.current.z * 10.0 * delta;
        
        // Calculate movement direction
        direction.current.z = Number(moveForward.current) - Number(moveBackward.current);
        direction.current.x = Number(moveRight.current) - Number(moveLeft.current);
        direction.current.normalize();
        
        // Apply movement
        const speed = 8.0;
        if (moveForward.current || moveBackward.current) {
          velocity.current.z -= direction.current.z * speed * delta;
        }
        if (moveLeft.current || moveRight.current) {
          velocity.current.x -= direction.current.x * speed * delta;
        }
        
        // Move the controls/camera
        controlsRef.current.moveRight(-velocity.current.x * delta * 10);
        controlsRef.current.moveForward(-velocity.current.z * delta * 10);
        
        // Keep camera at walking height
        cameraRef.current.position.y = 1.7;
      }
      
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
    
    // Add keyboard listeners
    document.addEventListener('keydown', onKeyDown);
    document.addEventListener('keyup', onKeyUp);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      document.removeEventListener('keydown', onKeyDown);
      document.removeEventListener('keyup', onKeyUp);
      
      if (animationIdRef.current) {
        cancelAnimationFrame(animationIdRef.current);
      }
      if (controlsRef.current) {
        controlsRef.current.dispose();
      }
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
  }, [onKeyDown, onKeyUp]);

  // Ambient sound
  useEffect(() => {
    const audio = new Audio('https://assets.mixkit.co/sfx/preview/mixkit-campfire-crackles-1330.mp3');
    audio.loop = true;
    audio.volume = 0.2;
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

  const handleStartExploring = () => {
    if (controlsRef.current) {
      controlsRef.current.lock();
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
                {loadProgress < 0 ? 'Error Loading Library' : 'Entering the Grand Library'}
              </h2>
              <p className="text-purple-300 text-sm max-w-md mx-auto">
                {loadProgress < 0 
                  ? (loadError || 'Please try refreshing the page') 
                  : 'Loading 50MB 3D model... This may take a moment on slower connections.'}
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
            
            {loadProgress < 0 && (
              <Button
                onClick={() => window.location.reload()}
                className="bg-purple-600 hover:bg-purple-700"
              >
                Retry Loading
              </Button>
            )}
          </div>
        </div>
      )}

      {/* Start Exploring Overlay - shows when loaded but not locked */}
      {isLoaded && !isLocked && showInstructions && (
        <div className="absolute inset-0 z-20 flex items-center justify-center bg-black/70 backdrop-blur-sm">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-gradient-to-br from-purple-900/95 to-indigo-900/95 rounded-2xl p-8 max-w-md w-full mx-4 shadow-2xl border border-purple-500/30 text-center"
          >
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-purple-500/20 flex items-center justify-center">
              <FiMove className="w-8 h-8 text-purple-300" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Welcome to the Grand Library</h2>
            <p className="text-purple-200 mb-6">
              Explore this magical library in first-person. Walk around and discover ancient tomes!
            </p>
            
            <div className="bg-black/30 rounded-xl p-4 mb-6 text-left">
              <h3 className="text-white font-semibold mb-3">Controls:</h3>
              <ul className="text-purple-200 text-sm space-y-2">
                <li className="flex items-center gap-3">
                  <span className="px-2 py-1 bg-purple-500/30 rounded text-xs font-mono">W A S D</span>
                  <span>Move around</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="px-2 py-1 bg-purple-500/30 rounded text-xs font-mono">Mouse</span>
                  <span>Look around</span>
                </li>
                <li className="flex items-center gap-3">
                  <span className="px-2 py-1 bg-purple-500/30 rounded text-xs font-mono">ESC</span>
                  <span>Pause / Show menu</span>
                </li>
              </ul>
            </div>
            
            <div className="flex gap-3">
              <Button
                variant="outline"
                className="flex-1 border-purple-500/30 text-white hover:bg-purple-500/20"
                onClick={onClose}
              >
                Exit Library
              </Button>
              <Button
                className="flex-1 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
                onClick={handleStartExploring}
              >
                Start Exploring
              </Button>
            </div>
          </motion.div>
        </div>
      )}

      {/* Top Controls - only show when exploring */}
      {isLoaded && isLocked && (
        <div className="absolute top-4 left-4 right-4 z-10 flex justify-between items-start pointer-events-none">
          <div className="bg-black/50 backdrop-blur px-4 py-2 rounded-full pointer-events-auto">
            <p className="text-white/70 text-sm">Press <span className="text-purple-300 font-mono">ESC</span> to pause</p>
          </div>
          
          <div className="flex items-center gap-2 pointer-events-auto">
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
      )}

      {/* Crosshair when exploring */}
      {isLoaded && isLocked && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
          <div className="w-1 h-1 bg-white/50 rounded-full" />
        </div>
      )}

      {/* Book Panel - shown when paused */}
      {isLoaded && !isLocked && books.length > 0 && (
        <div className="absolute bottom-4 left-4 right-4 z-10">
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
