import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { Button } from '@/components/ui/button';
import { FiX, FiBook, FiMaximize2, FiMinimize2, FiVolume2, FiVolumeX, FiMove, FiArrowUp, FiArrowDown, FiArrowLeft, FiArrowRight } from 'react-icons/fi';

// Gothic Library Model URL - Using proxy to bypass CORS
const ORIGINAL_GLB_URL = 'https://customer-assets.emergentagent.com/job_f7ce8ac7-f125-4781-b4a2-bc90bdbc8e87/artifacts/pspisxvd_gothic_library_12_cycles-compressed.glb';
const LIBRARY_MODEL_URL = `${process.env.REACT_APP_BACKEND_URL}/api/proxy/glb?url=${encodeURIComponent(ORIGINAL_GLB_URL)}`;

// Detect mobile device
const isMobile = () => {
  if (typeof window === 'undefined') return false;
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || window.innerWidth < 768;
};

// First-person Library Viewer with WASD + Mobile touch controls
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
  const [isMuted, setIsMuted] = useState(true); // Start muted
  const [isExploring, setIsExploring] = useState(false);
  const [isMobileDevice] = useState(isMobile());
  const audioRef = useRef(null);

  // Touch controls state for mobile
  const touchStartRef = useRef({ x: 0, y: 0 });
  const lastTouchRef = useRef({ x: 0, y: 0 });

  // Handle keyboard input (desktop)
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
      default:
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
      default:
        break;
    }
  }, []);

  // Touch handlers for mobile camera rotation
  const handleTouchStart = useCallback((e) => {
    if (e.touches.length === 1) {
      touchStartRef.current = { x: e.touches[0].clientX, y: e.touches[0].clientY };
      lastTouchRef.current = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    }
  }, []);

  const handleTouchMove = useCallback((e) => {
    if (!isExploring || e.touches.length !== 1 || !cameraRef.current) return;
    
    const touch = e.touches[0];
    const deltaX = touch.clientX - lastTouchRef.current.x;
    const deltaY = touch.clientY - lastTouchRef.current.y;
    
    // Rotate camera based on touch movement
    if (controlsRef.current) {
      // For OrbitControls, we rotate the target around
      const rotationSpeed = 0.005;
      controlsRef.current.target.x += deltaX * rotationSpeed;
    }
    
    lastTouchRef.current = { x: touch.clientX, y: touch.clientY };
  }, [isExploring]);

  // Initialize Three.js scene
  useEffect(() => {
    if (!canvasRef.current) return;

    let mounted = true;

    // Create scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1a2e); // Dark blue-ish
    // Remove fog for better visibility while debugging
    // scene.fog = new THREE.Fog(0x1a1a2e, 10, 50);
    sceneRef.current = scene;

    // Add a ground helper plane so we can see the ground level
    const gridHelper = new THREE.GridHelper(30, 30, 0x444444, 0x222222);
    gridHelper.position.y = 0;
    scene.add(gridHelper);

    // Create camera - first person perspective
    const camera = new THREE.PerspectiveCamera(
      75,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    camera.position.set(0, 1.7, 5);
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

    // Use OrbitControls for both desktop and mobile (works better across devices)
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 0.5;
    controls.maxDistance = 30;
    controls.maxPolarAngle = Math.PI * 0.85;
    controls.minPolarAngle = Math.PI * 0.15;
    controls.target.set(0, 1.5, 0);
    controls.enablePan = true;
    controls.panSpeed = 0.5;
    // Enable touch for mobile
    controls.touches = {
      ONE: THREE.TOUCH.ROTATE,
      TWO: THREE.TOUCH.DOLLY_PAN
    };
    controlsRef.current = controls;

    // Add lighting - VERY BRIGHT for interior visibility
    const ambientLight = new THREE.AmbientLight(0xffffff, 2.0); // Very bright white ambient
    scene.add(ambientLight);

    const mainLight = new THREE.DirectionalLight(0xffffff, 1.5);
    mainLight.position.set(0, 20, 0);
    mainLight.castShadow = true;
    mainLight.shadow.mapSize.width = 1024;
    mainLight.shadow.mapSize.height = 1024;
    scene.add(mainLight);

    // Add hemisphere light for natural indoor lighting
    const hemiLight = new THREE.HemisphereLight(0xffeeb1, 0x080820, 1.5);
    scene.add(hemiLight);

    // Multiple warm point lights throughout the space (like candles/lamps)
    const warmLight1 = new THREE.PointLight(0xffaa55, 2.0, 50);
    warmLight1.position.set(-5, 3, -5);
    scene.add(warmLight1);

    const warmLight2 = new THREE.PointLight(0xffaa55, 2.0, 50);
    warmLight2.position.set(5, 3, 5);
    scene.add(warmLight2);

    const warmLight3 = new THREE.PointLight(0xffffff, 2.0, 60);
    warmLight3.position.set(0, 10, 0);
    scene.add(warmLight3);
    
    // Additional fill lights at various positions
    const fillLight1 = new THREE.PointLight(0xffd9a0, 1.5, 35);
    fillLight1.position.set(-3, 2, 3);
    scene.add(fillLight1);
    
    const fillLight2 = new THREE.PointLight(0xffd9a0, 1.5, 35);
    fillLight2.position.set(3, 2, -3);
    scene.add(fillLight2);
    
    // Lights at corners for full coverage
    const cornerLight1 = new THREE.PointLight(0xfff0d0, 1.2, 40);
    cornerLight1.position.set(-8, 4, -8);
    scene.add(cornerLight1);
    
    const cornerLight2 = new THREE.PointLight(0xfff0d0, 1.2, 40);
    cornerLight2.position.set(8, 4, 8);
    scene.add(cornerLight2);
    
    const cornerLight3 = new THREE.PointLight(0xfff0d0, 1.2, 40);
    cornerLight3.position.set(-8, 4, 8);
    scene.add(cornerLight3);
    
    const cornerLight4 = new THREE.PointLight(0xfff0d0, 1.2, 40);
    cornerLight4.position.set(8, 4, -8);
    scene.add(cornerLight4);

    // Load the GLB model
    const dracoLoader = new DRACOLoader();
    dracoLoader.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.6/');
    
    const gltfLoader = new GLTFLoader();
    gltfLoader.setDRACOLoader(dracoLoader);

    console.log('Loading model from:', LIBRARY_MODEL_URL);

    // Timeout for slow connections
    const loadTimeout = setTimeout(() => {
      if (mounted && !isLoaded) {
        console.warn('Model load timeout warning');
      }
    }, 60000);

    gltfLoader.load(
      LIBRARY_MODEL_URL,
      (gltf) => {
        if (!mounted) return;
        clearTimeout(loadTimeout);
        console.log('Gothic Library loaded successfully!');
        
        const model = gltf.scene;
        
        // Get bounding box
        const box = new THREE.Box3().setFromObject(model);
        const size = box.getSize(new THREE.Vector3());
        const center = box.getCenter(new THREE.Vector3());
        
        console.log('Model original size:', JSON.stringify({x: size.x, y: size.y, z: size.z}));
        console.log('Model original center:', JSON.stringify({x: center.x, y: center.y, z: center.z}));
        console.log('Model original bounds min:', JSON.stringify({x: box.min.x, y: box.min.y, z: box.min.z}));
        console.log('Model original bounds max:', JSON.stringify({x: box.max.x, y: box.max.y, z: box.max.z}));
        
        // Scale to reasonable walkable size - library should be about 20 units
        const maxDim = Math.max(size.x, size.y, size.z);
        const targetSize = 20;
        const scale = targetSize / maxDim;
        model.scale.setScalar(scale);
        
        // Recalculate after scaling
        const scaledBox = new THREE.Box3().setFromObject(model);
        const scaledSize = scaledBox.getSize(new THREE.Vector3());
        const scaledCenter = scaledBox.getCenter(new THREE.Vector3());
        
        console.log('Model scaled size:', JSON.stringify({x: scaledSize.x, y: scaledSize.y, z: scaledSize.z}));
        console.log('Model scaled center:', JSON.stringify({x: scaledCenter.x, y: scaledCenter.y, z: scaledCenter.z}));
        
        // Center the model at origin
        model.position.x = -scaledCenter.x;
        model.position.z = -scaledCenter.z;
        // Put floor at y=0
        model.position.y = -scaledBox.min.y;
        
        // Calculate new bounds after positioning
        const finalBox = new THREE.Box3().setFromObject(model);
        const finalCenter = finalBox.getCenter(new THREE.Vector3());
        const finalSize = finalBox.getSize(new THREE.Vector3());
        
        console.log('Model final bounds min:', JSON.stringify({x: finalBox.min.x, y: finalBox.min.y, z: finalBox.min.z}));
        console.log('Model final bounds max:', JSON.stringify({x: finalBox.max.x, y: finalBox.max.y, z: finalBox.max.z}));
        console.log('Model final center:', JSON.stringify({x: finalCenter.x, y: finalCenter.y, z: finalCenter.z}));
        
        // Process materials to ensure they render properly
        model.traverse((child) => {
          if (child.isMesh) {
            child.castShadow = true;
            child.receiveShadow = true;
            // Ensure materials are visible
            if (child.material) {
              child.material.side = THREE.DoubleSide; // Render both sides
              child.material.needsUpdate = true;
            }
          }
        });
        
        scene.add(model);
        
        // Position camera INSIDE the model at eye level for immersive experience
        // Model bounds: x/z from -10 to +10, y from 0 to 17.44
        // Start at center of the room at eye level
        camera.position.set(0, 5, 0); // Center of room, elevated view
        
        // Look outward towards the front of the room
        controls.target.set(0, 5, -5);
        controls.minDistance = 0.5;  // Can get close
        controls.maxDistance = 40;   // Can pull back far
        controls.maxPolarAngle = Math.PI * 0.9; // Almost can look straight up
        controls.minPolarAngle = Math.PI * 0.1; // Almost can look straight down
        controls.update();
        
        console.log('Camera positioned at:', JSON.stringify({x: camera.position.x, y: camera.position.y, z: camera.position.z}));
        console.log('Looking at:', JSON.stringify({x: controls.target.x, y: controls.target.y, z: controls.target.z}));
        
        setIsLoaded(true);
        setLoadError(null);
      },
      (progress) => {
        if (!mounted) return;
        if (progress.total > 0) {
          const percent = (progress.loaded / progress.total) * 100;
          setLoadProgress(percent);
        } else if (progress.loaded > 0) {
          setLoadProgress(Math.min((progress.loaded / 50000000) * 100, 99));
        }
      },
      (error) => {
        if (!mounted) return;
        clearTimeout(loadTimeout);
        console.error('Error loading model:', error);
        setLoadError(error.message || 'Failed to load 3D model');
        setLoadProgress(-1);
      }
    );

    // Animation loop
    const animate = () => {
      if (!mounted) return;
      animationIdRef.current = requestAnimationFrame(animate);
      
      const delta = clockRef.current.getDelta();
      
      // Handle WASD movement (desktop)
      if (isExploring && controlsRef.current) {
        const speed = 5.0 * delta;
        
        if (moveForward.current) {
          controlsRef.current.target.z -= speed;
          camera.position.z -= speed;
        }
        if (moveBackward.current) {
          controlsRef.current.target.z += speed;
          camera.position.z += speed;
        }
        if (moveLeft.current) {
          controlsRef.current.target.x -= speed;
          camera.position.x -= speed;
        }
        if (moveRight.current) {
          controlsRef.current.target.x += speed;
          camera.position.x += speed;
        }
      }
      
      if (controlsRef.current) {
        controlsRef.current.update();
      }
      
      renderer.render(scene, camera);
    };
    animate();

    // Handle resize
    const handleResize = () => {
      if (!mounted) return;
      const width = window.innerWidth;
      const height = window.innerHeight;
      
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };
    window.addEventListener('resize', handleResize);
    
    // Keyboard listeners
    document.addEventListener('keydown', onKeyDown);
    document.addEventListener('keyup', onKeyUp);

    // Cleanup
    return () => {
      mounted = false;
      clearTimeout(loadTimeout);
      window.removeEventListener('resize', handleResize);
      document.removeEventListener('keydown', onKeyDown);
      document.removeEventListener('keyup', onKeyUp);
      
      if (animationIdRef.current) {
        cancelAnimationFrame(animationIdRef.current);
      }
      if (controlsRef.current) {
        controlsRef.current.dispose();
      }
      if (rendererRef.current) {
        rendererRef.current.dispose();
      }
      dracoLoader.dispose();
      
      // Dispose scene
      if (sceneRef.current) {
        sceneRef.current.traverse((object) => {
          if (object.geometry) object.geometry.dispose();
          if (object.material) {
            if (Array.isArray(object.material)) {
              object.material.forEach(m => m.dispose());
            } else {
              object.material.dispose();
            }
          }
        });
      }
    };
  }, [onKeyDown, onKeyUp, isExploring, isLoaded]);

  // Ambient sound
  useEffect(() => {
    // Use a more reliable audio source
    const audio = new Audio('/sounds/fireplace.mp3');
    audio.loop = true;
    audio.volume = 0.15;
    audioRef.current = audio;

    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  const toggleMute = () => {
    if (audioRef.current) {
      if (isMuted) {
        audioRef.current.play().catch(() => {});
      } else {
        audioRef.current.pause();
      }
      setIsMuted(!isMuted);
    }
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen?.();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen?.();
      setIsFullscreen(false);
    }
  };

  const handleStartExploring = () => {
    setIsExploring(true);
  };

  // Mobile movement button handlers
  const handleMoveButton = (dir, pressed) => {
    switch(dir) {
      case 'forward': moveForward.current = pressed; break;
      case 'backward': moveBackward.current = pressed; break;
      case 'left': moveLeft.current = pressed; break;
      case 'right': moveRight.current = pressed; break;
      default: break;
    }
  };

  return (
    <div 
      ref={containerRef}
      className="fixed inset-0 z-50 bg-black"
      data-testid="immersive-library-3d"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
    >
      {/* Three.js Canvas */}
      <canvas ref={canvasRef} className="w-full h-full touch-none" />

      {/* Loading Screen */}
      {!isLoaded && (
        <div className="absolute inset-0 z-30 flex flex-col items-center justify-center bg-gradient-to-b from-[#1a0a2e] to-[#0d0015]">
          <div className="text-center space-y-6 px-4">
            <div className="relative w-24 h-24 sm:w-32 sm:h-32 mx-auto">
              <div className="absolute inset-0 border-4 border-purple-500/30 rounded-full animate-ping" />
              <div className="absolute inset-2 border-4 border-purple-500/50 rounded-full animate-spin" style={{ animationDuration: '3s' }} />
              <div className="absolute inset-4 border-4 border-purple-400/70 rounded-full animate-spin" style={{ animationDuration: '2s', animationDirection: 'reverse' }} />
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-2xl sm:text-3xl font-bold text-white">
                  {loadProgress < 0 ? '!' : `${Math.round(loadProgress)}%`}
                </span>
              </div>
            </div>
            
            <div className="space-y-2">
              <h2 className="text-xl sm:text-2xl font-bold text-white">
                {loadProgress < 0 ? 'Error Loading Library' : 'Entering the Grand Library'}
              </h2>
              <p className="text-purple-300 text-sm max-w-md mx-auto">
                {loadProgress < 0 
                  ? (loadError || 'Please try refreshing the page') 
                  : 'Loading 50MB 3D model... This may take a moment.'}
              </p>
            </div>
            
            {loadProgress >= 0 && (
              <div className="w-48 sm:w-64 h-2 bg-purple-900/50 rounded-full overflow-hidden mx-auto">
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
            
            {/* Exit button during loading */}
            <Button
              variant="ghost"
              onClick={onClose}
              className="text-purple-300 hover:text-white"
            >
              <FiX className="mr-2" /> Exit
            </Button>
          </div>
        </div>
      )}

      {/* Welcome Overlay */}
      {isLoaded && !isExploring && (
        <div className="absolute inset-0 z-20 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-gradient-to-br from-purple-900/95 to-indigo-900/95 rounded-2xl p-6 sm:p-8 max-w-md w-full shadow-2xl border border-purple-500/30 text-center"
          >
            <div className="w-14 h-14 sm:w-16 sm:h-16 mx-auto mb-4 rounded-full bg-purple-500/20 flex items-center justify-center">
              <FiMove className="w-7 h-7 sm:w-8 sm:h-8 text-purple-300" />
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-white mb-2">Welcome to the Grand Library</h2>
            <p className="text-purple-200 text-sm mb-6">
              Explore this magical library. Drag to look around, pinch to zoom!
            </p>
            
            <div className="bg-black/30 rounded-xl p-4 mb-6 text-left">
              <h3 className="text-white font-semibold mb-3 text-sm sm:text-base">Controls:</h3>
              {isMobileDevice ? (
                <ul className="text-purple-200 text-xs sm:text-sm space-y-2">
                  <li className="flex items-center gap-3">
                    <span className="px-2 py-1 bg-purple-500/30 rounded text-xs">Touch</span>
                    <span>Drag to look around</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <span className="px-2 py-1 bg-purple-500/30 rounded text-xs">Pinch</span>
                    <span>Zoom in/out</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <span className="px-2 py-1 bg-purple-500/30 rounded text-xs">Arrows</span>
                    <span>Use on-screen buttons to walk</span>
                  </li>
                </ul>
              ) : (
                <ul className="text-purple-200 text-xs sm:text-sm space-y-2">
                  <li className="flex items-center gap-3">
                    <span className="px-2 py-1 bg-purple-500/30 rounded text-xs font-mono">W A S D</span>
                    <span>Walk around</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <span className="px-2 py-1 bg-purple-500/30 rounded text-xs font-mono">Mouse</span>
                    <span>Drag to look around</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <span className="px-2 py-1 bg-purple-500/30 rounded text-xs font-mono">Scroll</span>
                    <span>Zoom in/out</span>
                  </li>
                </ul>
              )}
            </div>
            
            <div className="flex gap-3">
              <Button
                variant="outline"
                className="flex-1 border-purple-500/30 text-white hover:bg-purple-500/20 text-sm"
                onClick={onClose}
              >
                Exit
              </Button>
              <Button
                className="flex-1 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-sm"
                onClick={handleStartExploring}
              >
                Start Exploring
              </Button>
            </div>
          </motion.div>
        </div>
      )}

      {/* Top Controls when exploring */}
      {isLoaded && isExploring && (
        <div className="absolute top-4 left-4 right-4 z-10 flex justify-between items-start">
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="bg-black/50 hover:bg-black/70 text-white rounded-full backdrop-blur"
          >
            <FiX className="w-5 h-5" />
          </Button>
          
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
      )}

      {/* Mobile Movement Controls */}
      {isLoaded && isExploring && isMobileDevice && (
        <div className="absolute bottom-8 left-4 z-10">
          <div className="grid grid-cols-3 gap-1">
            <div />
            <Button
              variant="ghost"
              size="icon"
              className="bg-black/50 active:bg-purple-500/50 text-white rounded-full backdrop-blur w-12 h-12"
              onTouchStart={() => handleMoveButton('forward', true)}
              onTouchEnd={() => handleMoveButton('forward', false)}
              onMouseDown={() => handleMoveButton('forward', true)}
              onMouseUp={() => handleMoveButton('forward', false)}
              onMouseLeave={() => handleMoveButton('forward', false)}
            >
              <FiArrowUp className="w-5 h-5" />
            </Button>
            <div />
            
            <Button
              variant="ghost"
              size="icon"
              className="bg-black/50 active:bg-purple-500/50 text-white rounded-full backdrop-blur w-12 h-12"
              onTouchStart={() => handleMoveButton('left', true)}
              onTouchEnd={() => handleMoveButton('left', false)}
              onMouseDown={() => handleMoveButton('left', true)}
              onMouseUp={() => handleMoveButton('left', false)}
              onMouseLeave={() => handleMoveButton('left', false)}
            >
              <FiArrowLeft className="w-5 h-5" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="bg-black/50 active:bg-purple-500/50 text-white rounded-full backdrop-blur w-12 h-12"
              onTouchStart={() => handleMoveButton('backward', true)}
              onTouchEnd={() => handleMoveButton('backward', false)}
              onMouseDown={() => handleMoveButton('backward', true)}
              onMouseUp={() => handleMoveButton('backward', false)}
              onMouseLeave={() => handleMoveButton('backward', false)}
            >
              <FiArrowDown className="w-5 h-5" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="bg-black/50 active:bg-purple-500/50 text-white rounded-full backdrop-blur w-12 h-12"
              onTouchStart={() => handleMoveButton('right', true)}
              onTouchEnd={() => handleMoveButton('right', false)}
              onMouseDown={() => handleMoveButton('right', true)}
              onMouseUp={() => handleMoveButton('right', false)}
              onMouseLeave={() => handleMoveButton('right', false)}
            >
              <FiArrowRight className="w-5 h-5" />
            </Button>
          </div>
        </div>
      )}

      {/* Instructions hint */}
      {isLoaded && isExploring && !isMobileDevice && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-10">
          <div className="bg-black/50 backdrop-blur px-4 py-2 rounded-full">
            <p className="text-white/60 text-xs">
              WASD to walk • Drag to look • Scroll to zoom
            </p>
          </div>
        </div>
      )}

      {/* Book Collection */}
      {isLoaded && isExploring && books.length > 0 && (
        <div className="absolute bottom-4 right-4 z-10 max-w-xs">
          <div className="bg-black/70 backdrop-blur-lg rounded-xl p-3">
            <h3 className="text-white font-bold text-sm mb-2">📚 Books</h3>
            <div className="flex gap-2 overflow-x-auto pb-1">
              {books.slice(0, 5).map((book) => (
                <motion.div
                  key={book.id}
                  whileTap={{ scale: 0.95 }}
                  className="flex-shrink-0 cursor-pointer"
                  onClick={() => setSelectedBook(book)}
                >
                  <div className="w-12 h-16 rounded overflow-hidden border border-white/20">
                    {book.cover_image ? (
                      <img src={book.cover_image} alt={book.title} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full bg-purple-600 flex items-center justify-center">
                        <FiBook className="w-4 h-4 text-white/70" />
                      </div>
                    )}
                  </div>
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
            className="absolute inset-0 z-40 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
            onClick={() => setSelectedBook(null)}
          >
            <motion.div
              initial={{ scale: 0.8, y: 50 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.8, y: 50 }}
              className="bg-gradient-to-br from-purple-900/95 to-indigo-900/95 rounded-2xl p-5 max-w-sm w-full shadow-2xl border border-purple-500/20"
              onClick={e => e.stopPropagation()}
            >
              <div className="flex gap-4">
                {selectedBook.cover_image ? (
                  <img 
                    src={selectedBook.cover_image} 
                    alt={selectedBook.title}
                    className="w-20 h-28 object-cover rounded-lg shadow-lg"
                  />
                ) : (
                  <div className="w-20 h-28 bg-purple-500/40 rounded-lg flex items-center justify-center">
                    <FiBook className="w-8 h-8 text-white/50" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <h3 className="text-lg font-bold text-white mb-1 truncate">{selectedBook.title}</h3>
                  <p className="text-purple-300 text-sm mb-2">by {selectedBook.author_name}</p>
                  <p className="text-white/60 text-xs line-clamp-2">
                    {selectedBook.description || 'A magical story awaits...'}
                  </p>
                </div>
              </div>
              
              <div className="flex gap-3 mt-4">
                <Button
                  variant="outline"
                  className="flex-1 rounded-full border-purple-500/30 text-white hover:bg-purple-500/20 text-sm"
                  onClick={() => setSelectedBook(null)}
                >
                  Back
                </Button>
                <Button
                  className="flex-1 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 text-sm"
                  onClick={() => navigate(`/read/${selectedBook.id}`)}
                >
                  <FiBook className="mr-1" />
                  Read
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
