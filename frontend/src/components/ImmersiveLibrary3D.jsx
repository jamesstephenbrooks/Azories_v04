import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader';
import { Button } from '@/components/ui/button';
import { FiX, FiBook, FiMaximize2, FiMinimize2, FiVolume2, FiVolumeX, FiMapPin, FiMove, FiChevronUp, FiRotateCw, FiStar, FiBookmark } from 'react-icons/fi';
import { useAuth } from '@/context/AuthContext';
import AILibrarian from './AILibrarian';

// Gothic Library Model URL - Using proxy to bypass CORS (v14 with collisions)
const ORIGINAL_GLB_URL = 'https://customer-assets.emergentagent.com/job_f7ce8ac7-f125-4781-b4a2-bc90bdbc8e87/artifacts/n4e6ytup_gothic_library_14_cycles-compressed.glb';
const LIBRARY_MODEL_URL = `${process.env.REACT_APP_BACKEND_URL}/api/proxy/glb?url=${encodeURIComponent(ORIGINAL_GLB_URL)}`;

// Library boundaries (will be set after model loads)
const DEFAULT_BOUNDS = {
  minX: -9, maxX: 9,
  minZ: -9, maxZ: 9,
  floorY: 0,
  ceilingY: 15
};

// Genre sections for navigation with book shelves
const GENRE_SECTIONS = [
  { name: 'Fantasy', position: { x: -6, z: -6 }, color: '#9333ea', icon: '✨' },
  { name: 'Adventure', position: { x: 6, z: -6 }, color: '#f59e0b', icon: '🗺️' },
  { name: 'Mystery', position: { x: -6, z: 6 }, color: '#3b82f6', icon: '🔍' },
  { name: 'Science Fiction', position: { x: 6, z: 6 }, color: '#10b981', icon: '🚀' },
  { name: 'Center', position: { x: 0, z: 0 }, color: '#ec4899', icon: '📚' },
];

// Detect mobile device
const isMobile = () => {
  if (typeof window === 'undefined') return false;
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || window.innerWidth < 768;
};

// First-person Library Viewer with touch controls and interactive books
export default function ImmersiveLibrary3D({ books = [], onClose }) {
  const navigate = useNavigate();
  const { user } = useAuth();
  const containerRef = useRef(null);
  const canvasRef = useRef(null);
  const rendererRef = useRef(null);
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const animationIdRef = useRef(null);
  const clockRef = useRef(new THREE.Clock());
  const boundsRef = useRef(DEFAULT_BOUNDS);
  
  // Movement state - using refs for real-time updates
  const keysPressed = useRef({
    forward: false,
    backward: false,
    left: false,
    right: false
  });
  
  // Player state
  const playerVelocity = useRef(new THREE.Vector3());
  const playerOnGround = useRef(true);
  const cameraDirection = useRef(new THREE.Vector3());
  const sidewaysDirection = useRef(new THREE.Vector3());
  const collisionMeshesRef = useRef([]);
  const raycasterRef = useRef(new THREE.Raycaster());
  const bookMeshesRef = useRef([]);
  
  // Physics constants
  const GRAVITY = 20;
  const PLAYER_HEIGHT = 1.7;
  const MOVE_SPEED = 5;
  const FRICTION = 10;
  
  const [isLoaded, setIsLoaded] = useState(false);
  const [loadProgress, setLoadProgress] = useState(0);
  const [loadError, setLoadError] = useState(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isMuted, setIsMuted] = useState(true);
  const [isExploring, setIsExploring] = useState(false);
  const [showControls, setShowControls] = useState(false);
  const [showGenreMenu, setShowGenreMenu] = useState(false);
  const [isMobileDevice] = useState(isMobile());
  const [hoveredBook, setHoveredBook] = useState(null);
  const [savedPositions, setSavedPositions] = useState([]);
  const [showBookPanel, setShowBookPanel] = useState(true);
  
  // Mobile touch state
  const touchStartRef = useRef({ x: 0, y: 0 });
  const touchMoveRef = useRef({ active: false, x: 0, y: 0 });
  const joystickRef = useRef({ active: false, angle: 0, distance: 0 });
  
  // Mouse look state
  const isPointerLocked = useRef(false);
  const euler = useRef(new THREE.Euler(0, 0, 0, 'YXZ'));
  
  // Load saved positions from localStorage
  useEffect(() => {
    if (user) {
      const saved = localStorage.getItem(`azories-3d-positions-${user.id}`);
      if (saved) {
        try {
          setSavedPositions(JSON.parse(saved));
        } catch (e) {
          console.error('Failed to load saved positions:', e);
        }
      }
    }
  }, [user]);
  
  // Check if user should see controls tutorial (first time only)
  useEffect(() => {
    if (user && isLoaded) {
      const hasSeenControls = localStorage.getItem(`azories-3d-controls-seen-${user.id}`);
      if (!hasSeenControls) {
        setShowControls(true);
      }
    }
  }, [user, isLoaded]);

  const dismissControls = () => {
    if (user) {
      localStorage.setItem(`azories-3d-controls-seen-${user.id}`, 'true');
    }
    setShowControls(false);
  };

  // Handle keyboard input - camera relative
  const onKeyDown = useCallback((event) => {
    if (!isExploring) return;
    switch (event.code) {
      case 'KeyW':
      case 'ArrowUp':
        keysPressed.current.forward = true;
        break;
      case 'KeyS':
      case 'ArrowDown':
        keysPressed.current.backward = true;
        break;
      case 'KeyA':
      case 'ArrowLeft':
        keysPressed.current.left = true;
        break;
      case 'KeyD':
      case 'ArrowRight':
        keysPressed.current.right = true;
        break;
      default:
        break;
    }
  }, [isExploring]);

  const onKeyUp = useCallback((event) => {
    switch (event.code) {
      case 'KeyW':
      case 'ArrowUp':
        keysPressed.current.forward = false;
        break;
      case 'KeyS':
      case 'ArrowDown':
        keysPressed.current.backward = false;
        break;
      case 'KeyA':
      case 'ArrowLeft':
        keysPressed.current.left = false;
        break;
      case 'KeyD':
      case 'ArrowRight':
        keysPressed.current.right = false;
        break;
      default:
        break;
    }
  }, []);

  // Mouse movement for looking around
  const onMouseMove = useCallback((event) => {
    if (!isPointerLocked.current || !cameraRef.current) return;
    
    const movementX = event.movementX || 0;
    const movementY = event.movementY || 0;
    
    euler.current.setFromQuaternion(cameraRef.current.quaternion);
    euler.current.y -= movementX * 0.002;
    euler.current.x -= movementY * 0.002;
    
    // Clamp vertical look
    euler.current.x = Math.max(-Math.PI / 2 + 0.1, Math.min(Math.PI / 2 - 0.1, euler.current.x));
    
    cameraRef.current.quaternion.setFromEuler(euler.current);
  }, []);

  // Pointer lock handlers
  const requestPointerLock = useCallback(() => {
    if (canvasRef.current && isExploring) {
      canvasRef.current.requestPointerLock();
    }
  }, [isExploring]);

  const onPointerLockChange = useCallback(() => {
    isPointerLocked.current = document.pointerLockElement === canvasRef.current;
  }, []);

  // Teleport to genre section
  const teleportToGenre = useCallback((section) => {
    if (!cameraRef.current) return;
    
    cameraRef.current.position.set(
      section.position.x,
      PLAYER_HEIGHT,
      section.position.z
    );
    setShowGenreMenu(false);
  }, []);

  // Initialize Three.js scene
  useEffect(() => {
    if (!canvasRef.current) return;

    let mounted = true;

    // Create scene with warm library atmosphere
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1520);
    sceneRef.current = scene;

    // Create camera - first person perspective
    const camera = new THREE.PerspectiveCamera(
      75,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    camera.position.set(0, PLAYER_HEIGHT, 5);
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
    renderer.toneMappingExposure = 1.5;
    rendererRef.current = renderer;

    // Add warm library lighting
    const ambientLight = new THREE.AmbientLight(0xfff5e6, 0.6);
    scene.add(ambientLight);

    const mainLight = new THREE.DirectionalLight(0xffffff, 0.8);
    mainLight.position.set(0, 20, 10);
    mainLight.castShadow = true;
    scene.add(mainLight);

    // Warm point lights like candles/lamps
    const warmLightPositions = [
      [0, 8, 0], [-5, 4, -5], [5, 4, -5], [-5, 4, 5], [5, 4, 5]
    ];
    warmLightPositions.forEach(pos => {
      const light = new THREE.PointLight(0xffaa55, 1.5, 20);
      light.position.set(pos[0], pos[1], pos[2]);
      scene.add(light);
    });

    // Hemisphere light for natural feel
    const hemiLight = new THREE.HemisphereLight(0xffeedd, 0x222211, 0.5);
    scene.add(hemiLight);

    // Load the GLB model
    const dracoLoader = new DRACOLoader();
    dracoLoader.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.6/');
    
    const gltfLoader = new GLTFLoader();
    gltfLoader.setDRACOLoader(dracoLoader);

    console.log('Loading model from:', LIBRARY_MODEL_URL);

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
        
        console.log('Model size:', size);
        
        // Scale to reasonable size - library about 20 units wide
        const maxDim = Math.max(size.x, size.y, size.z);
        const targetSize = 20;
        const scale = targetSize / maxDim;
        model.scale.setScalar(scale);
        
        // Recalculate after scaling
        const scaledBox = new THREE.Box3().setFromObject(model);
        const scaledCenter = scaledBox.getCenter(new THREE.Vector3());
        
        // Center the model and put floor at y=0
        model.position.x = -scaledCenter.x;
        model.position.z = -scaledCenter.z;
        model.position.y = -scaledBox.min.y;
        
        // Update bounds for collision
        const finalBox = new THREE.Box3().setFromObject(model);
        boundsRef.current = {
          minX: finalBox.min.x + 0.5,
          maxX: finalBox.max.x - 0.5,
          minZ: finalBox.min.z + 0.5,
          maxZ: finalBox.max.z - 0.5,
          floorY: 0,
          ceilingY: finalBox.max.y
        };
        
        console.log('Library bounds:', boundsRef.current);
        
        // Collect collision meshes and regular meshes
        const collisionMeshes = [];
        const visibleMeshes = [];
        
        model.traverse((child) => {
          if (child.isMesh) {
            const name = child.name.toLowerCase();
            
            // Check if this is EXPLICITLY a collision mesh (not regular walls/floors)
            // Only hide meshes that are specifically named as collision geometry
            const isCollisionMesh = name.includes('collision') || name.includes('collider') || 
                name.includes('_col_') || name.startsWith('col_') || name.endsWith('_col');
            
            if (isCollisionMesh) {
              // Make collision-only meshes invisible but keep for raycasting
              child.visible = false;
              collisionMeshes.push(child);
              console.log('Found collision mesh:', child.name);
            } else {
              // Regular visible meshes - can also be used for collision if needed
              child.castShadow = true;
              child.receiveShadow = true;
              if (child.material) {
                child.material.side = THREE.DoubleSide;
                child.material.needsUpdate = true;
              }
              visibleMeshes.push(child);
              
              // Also add to collision detection if it's a structural element
              if (name.includes('wall') || name.includes('floor') || name.includes('ceiling')) {
                collisionMeshes.push(child);
              }
            }
          }
        });
        
        console.log(`Found ${collisionMeshes.length} collision meshes, ${visibleMeshes.length} visible meshes`);
        
        // Store collision meshes for raycasting
        collisionMeshesRef.current = collisionMeshes.length > 0 ? collisionMeshes : visibleMeshes;
        
        scene.add(model);
        
        // Try to find a good starting position using raycasting
        const raycaster = new THREE.Raycaster();
        const downRay = new THREE.Vector3(0, -1, 0);
        
        // Cast ray down from center to find floor
        raycaster.set(new THREE.Vector3(0, 10, 0), downRay);
        const floorHits = raycaster.intersectObjects(collisionMeshesRef.current, true);
        
        let startY = PLAYER_HEIGHT;
        if (floorHits.length > 0) {
          startY = floorHits[0].point.y + PLAYER_HEIGHT;
          console.log('Found floor at:', floorHits[0].point.y, 'Starting at:', startY);
        }
        
        // Position camera inside the library at detected floor level
        camera.position.set(0, startY, 3);
        
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

    // Animation loop with physics and raycasting collision
    const animate = () => {
      if (!mounted) return;
      animationIdRef.current = requestAnimationFrame(animate);
      
      const delta = Math.min(clockRef.current.getDelta(), 0.1);
      
      if (isExploring && cameraRef.current) {
        const camera = cameraRef.current;
        const bounds = boundsRef.current;
        const raycaster = raycasterRef.current;
        const collisionMeshes = collisionMeshesRef.current;
        
        // Get camera's forward direction (only horizontal)
        camera.getWorldDirection(cameraDirection.current);
        cameraDirection.current.y = 0;
        cameraDirection.current.normalize();
        
        // Get sideways direction (perpendicular to forward)
        sidewaysDirection.current.crossVectors(camera.up, cameraDirection.current).normalize();
        
        // Calculate movement based on keys pressed
        const moveDirection = new THREE.Vector3();
        
        if (keysPressed.current.forward) {
          moveDirection.add(cameraDirection.current);
        }
        if (keysPressed.current.backward) {
          moveDirection.sub(cameraDirection.current);
        }
        if (keysPressed.current.left) {
          moveDirection.add(sidewaysDirection.current);
        }
        if (keysPressed.current.right) {
          moveDirection.sub(sidewaysDirection.current);
        }
        
        // Normalize and apply speed
        if (moveDirection.length() > 0) {
          moveDirection.normalize();
          playerVelocity.current.x = moveDirection.x * MOVE_SPEED;
          playerVelocity.current.z = moveDirection.z * MOVE_SPEED;
        } else {
          // Apply friction when not moving
          playerVelocity.current.x *= Math.max(0, 1 - FRICTION * delta);
          playerVelocity.current.z *= Math.max(0, 1 - FRICTION * delta);
        }
        
        // Calculate desired new position
        let newX = camera.position.x + playerVelocity.current.x * delta;
        let newZ = camera.position.z + playerVelocity.current.z * delta;
        
        // Raycast-based wall collision detection
        if (collisionMeshes.length > 0 && (playerVelocity.current.x !== 0 || playerVelocity.current.z !== 0)) {
          const horizontalVelocity = new THREE.Vector3(
            playerVelocity.current.x,
            0,
            playerVelocity.current.z
          );
          
          if (horizontalVelocity.length() > 0.01) {
            const rayDir = horizontalVelocity.clone().normalize();
            const rayOrigin = camera.position.clone();
            rayOrigin.y -= 0.5; // Cast from chest height
            
            raycaster.set(rayOrigin, rayDir);
            raycaster.far = 0.8; // Check 0.8 units ahead
            
            const hits = raycaster.intersectObjects(collisionMeshes, true);
            if (hits.length > 0 && hits[0].distance < 0.6) {
              // Wall hit - stop movement in that direction
              newX = camera.position.x;
              newZ = camera.position.z;
              playerVelocity.current.x = 0;
              playerVelocity.current.z = 0;
            }
          }
        }
        
        // Apply boundary collision (fallback)
        newX = Math.max(bounds.minX, Math.min(bounds.maxX, newX));
        newZ = Math.max(bounds.minZ, Math.min(bounds.maxZ, newZ));
        
        camera.position.x = newX;
        camera.position.z = newZ;
        
        // Raycast-based floor detection
        let floorY = bounds.floorY;
        if (collisionMeshes.length > 0) {
          raycaster.set(
            new THREE.Vector3(camera.position.x, camera.position.y + 1, camera.position.z),
            new THREE.Vector3(0, -1, 0)
          );
          raycaster.far = 10;
          
          const floorHits = raycaster.intersectObjects(collisionMeshes, true);
          if (floorHits.length > 0) {
            floorY = floorHits[0].point.y;
          }
        }
        
        // Apply gravity and floor collision
        if (!playerOnGround.current) {
          playerVelocity.current.y -= GRAVITY * delta;
        }
        
        let newY = camera.position.y + playerVelocity.current.y * delta;
        
        if (newY <= floorY + PLAYER_HEIGHT) {
          camera.position.y = floorY + PLAYER_HEIGHT;
          playerVelocity.current.y = 0;
          playerOnGround.current = true;
        } else {
          camera.position.y = Math.min(bounds.ceilingY, newY);
          playerOnGround.current = false;
        }
      }
      
      renderer.render(scene, camera);
    };
    animate();

    // Event listeners
    const handleResize = () => {
      if (!mounted) return;
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };
    
    window.addEventListener('resize', handleResize);
    document.addEventListener('keydown', onKeyDown);
    document.addEventListener('keyup', onKeyUp);
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('pointerlockchange', onPointerLockChange);

    // Cleanup
    return () => {
      mounted = false;
      clearTimeout(loadTimeout);
      window.removeEventListener('resize', handleResize);
      document.removeEventListener('keydown', onKeyDown);
      document.removeEventListener('keyup', onKeyUp);
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('pointerlockchange', onPointerLockChange);
      
      if (animationIdRef.current) {
        cancelAnimationFrame(animationIdRef.current);
      }
      if (rendererRef.current) {
        rendererRef.current.dispose();
      }
      dracoLoader.dispose();
    };
  }, [onKeyDown, onKeyUp, onMouseMove, onPointerLockChange, isExploring]);

  // Start exploring
  const handleStartExploring = () => {
    setIsExploring(true);
    // Show controls for logged-in users who haven't seen them
    if (user) {
      const hasSeenControls = localStorage.getItem(`azories-3d-controls-seen-${user.id}`);
      if (!hasSeenControls) {
        setShowControls(true);
      }
    }
  };

  // Toggle fullscreen
  const toggleFullscreen = async () => {
    try {
      if (!document.fullscreenElement) {
        await containerRef.current?.requestFullscreen();
        setIsFullscreen(true);
      } else {
        await document.exitFullscreen();
        setIsFullscreen(false);
      }
    } catch (err) {
      console.error('Fullscreen error:', err);
    }
  };

  return (
    <div 
      ref={containerRef}
      className="fixed inset-0 z-50 bg-black"
      data-testid="immersive-library-container"
    >
      <canvas 
        ref={canvasRef} 
        className="w-full h-full cursor-crosshair"
        onClick={requestPointerLock}
      />
      
      {/* Loading Screen */}
      <AnimatePresence>
        {!isLoaded && !loadError && (
          <motion.div
            initial={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 flex flex-col items-center justify-center bg-gradient-to-b from-[#1a1520] to-[#2d1f3d]"
          >
            <div className="relative w-24 h-24 mb-6">
              <svg className="w-full h-full" viewBox="0 0 100 100">
                <circle
                  className="stroke-purple-900"
                  cx="50" cy="50" r="45"
                  fill="none" strokeWidth="8"
                />
                <circle
                  className="stroke-purple-500"
                  cx="50" cy="50" r="45"
                  fill="none" strokeWidth="8"
                  strokeDasharray={`${loadProgress * 2.83} 283`}
                  strokeLinecap="round"
                  transform="rotate(-90 50 50)"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-xl font-bold text-purple-300">{Math.round(loadProgress)}%</span>
              </div>
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Entering the Grand Library</h2>
            <p className="text-white/60 text-sm">Loading 3D model... This may take a moment.</p>
            <Button
              variant="ghost"
              className="mt-6 text-white/60 hover:text-white"
              onClick={onClose}
            >
              <FiX className="mr-2" /> Exit
            </Button>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Error State */}
      {loadError && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#1a1520]">
          <div className="text-red-400 text-6xl mb-4">⚠</div>
          <h2 className="text-xl font-bold text-white mb-2">Failed to load library</h2>
          <p className="text-white/60 mb-4">{loadError}</p>
          <Button onClick={onClose}>Return to Library</Button>
        </div>
      )}
      
      {/* Welcome Screen - Only show when loaded but not exploring */}
      <AnimatePresence>
        {isLoaded && !isExploring && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="absolute inset-0 flex items-center justify-center bg-black/50 backdrop-blur-sm"
          >
            <div className="bg-gradient-to-br from-[#2d1f3d] to-[#1a1520] rounded-2xl p-8 max-w-md mx-4 text-center border border-purple-500/30">
              <div className="w-16 h-16 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <FiMove className="w-8 h-8 text-purple-400" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Welcome to the Grand Library</h2>
              <p className="text-white/60 mb-6">
                Explore this magical library. Click to look around, use keys to walk.
              </p>
              
              <div className="bg-black/30 rounded-lg p-4 mb-6 text-left">
                <p className="text-sm font-medium text-purple-300 mb-3">Controls:</p>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="flex items-center gap-2">
                    <kbd className="px-2 py-1 bg-purple-900/50 rounded text-purple-300 text-xs">W A S D</kbd>
                    <span className="text-white/70">Walk around</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <kbd className="px-2 py-1 bg-purple-900/50 rounded text-purple-300 text-xs">Mouse</kbd>
                    <span className="text-white/70">Look around</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <kbd className="px-2 py-1 bg-purple-900/50 rounded text-purple-300 text-xs">↑ ↓ ← →</kbd>
                    <span className="text-white/70">Alternative movement</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <kbd className="px-2 py-1 bg-purple-900/50 rounded text-purple-300 text-xs">ESC</kbd>
                    <span className="text-white/70">Release mouse</span>
                  </div>
                </div>
              </div>
              
              <div className="flex gap-3 justify-center">
                <Button variant="outline" onClick={onClose} className="text-white border-white/30">
                  Exit
                </Button>
                <Button 
                  onClick={handleStartExploring}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  Start Exploring
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Controls Tutorial Overlay (for logged-in users, first time) */}
      <AnimatePresence>
        {showControls && isExploring && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 flex items-center justify-center bg-black/70 backdrop-blur-sm z-20"
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              className="bg-gradient-to-br from-[#2d1f3d] to-[#1a1520] rounded-2xl p-6 max-w-sm mx-4 border border-purple-500/30"
            >
              <h3 className="text-lg font-bold text-white mb-4 text-center">Quick Controls</h3>
              <div className="space-y-3 mb-6">
                <div className="flex items-center gap-3">
                  <kbd className="px-3 py-1.5 bg-purple-900/50 rounded text-purple-300 text-sm font-mono">WASD</kbd>
                  <span className="text-white/80">Move in direction you're facing</span>
                </div>
                <div className="flex items-center gap-3">
                  <kbd className="px-3 py-1.5 bg-purple-900/50 rounded text-purple-300 text-sm font-mono">Mouse</kbd>
                  <span className="text-white/80">Look around (click first)</span>
                </div>
                <div className="flex items-center gap-3">
                  <kbd className="px-3 py-1.5 bg-purple-900/50 rounded text-purple-300 text-sm font-mono">ESC</kbd>
                  <span className="text-white/80">Release mouse cursor</span>
                </div>
              </div>
              <Button 
                onClick={dismissControls}
                className="w-full bg-purple-600 hover:bg-purple-700"
              >
                Got it!
              </Button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* UI Controls when exploring */}
      {isLoaded && isExploring && (
        <>
          {/* Top bar */}
          <div className="absolute top-4 left-4 right-4 flex justify-between items-start pointer-events-none">
            <Button
              variant="ghost"
              size="icon"
              className="pointer-events-auto bg-black/50 hover:bg-black/70 text-white rounded-full"
              onClick={onClose}
            >
              <FiX className="w-5 h-5" />
            </Button>
            
            <div className="flex gap-2 pointer-events-auto">
              <Button
                variant="ghost"
                size="icon"
                className="bg-black/50 hover:bg-black/70 text-white rounded-full"
                onClick={() => setIsMuted(!isMuted)}
              >
                {isMuted ? <FiVolumeX className="w-5 h-5" /> : <FiVolume2 className="w-5 h-5" />}
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="bg-black/50 hover:bg-black/70 text-white rounded-full"
                onClick={toggleFullscreen}
              >
                {isFullscreen ? <FiMinimize2 className="w-5 h-5" /> : <FiMaximize2 className="w-5 h-5" />}
              </Button>
            </div>
          </div>
          
          {/* Genre navigation menu */}
          <div className="absolute top-4 left-1/2 -translate-x-1/2 pointer-events-auto">
            <Button
              variant="ghost"
              className="bg-black/50 hover:bg-black/70 text-white rounded-full px-4"
              onClick={() => setShowGenreMenu(!showGenreMenu)}
            >
              <FiMapPin className="w-4 h-4 mr-2" />
              Jump to Section
            </Button>
            
            <AnimatePresence>
              {showGenreMenu && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="absolute top-full left-1/2 -translate-x-1/2 mt-2 bg-black/90 rounded-xl p-2 min-w-[200px]"
                >
                  {GENRE_SECTIONS.map((section) => (
                    <button
                      key={section.name}
                      onClick={() => teleportToGenre(section)}
                      className="w-full px-4 py-2 text-left text-white hover:bg-white/10 rounded-lg flex items-center gap-3 transition-colors"
                    >
                      <div 
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: section.color }}
                      />
                      {section.name}
                    </button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
          
          {/* Bottom controls hint */}
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2">
            <div className="bg-black/50 backdrop-blur-sm rounded-full px-4 py-2 text-white/70 text-sm">
              WASD to walk • Click to look • ESC to release mouse
            </div>
          </div>
          
          {/* Books panel */}
          <div className="absolute bottom-4 right-4 pointer-events-auto">
            <div className="bg-black/80 backdrop-blur-sm rounded-xl p-3 max-w-xs">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg">📚</span>
                <span className="text-white font-medium text-sm">Books</span>
              </div>
              <div className="flex gap-2 overflow-x-auto pb-1">
                {books.slice(0, 5).map((book) => (
                  <button
                    key={book.id}
                    onClick={() => navigate(`/read/${book.id}`)}
                    className="flex-shrink-0 w-12 h-16 rounded-lg overflow-hidden hover:ring-2 hover:ring-purple-500 transition-all"
                  >
                    {book.cover_image ? (
                      <img 
                        src={book.cover_image} 
                        alt={book.title}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full bg-purple-900 flex items-center justify-center">
                        <FiBook className="text-purple-400" />
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </div>
          </div>
          
          {/* AI Librarian - Luna */}
          <AILibrarian books={books} isVisible={true} />
        </>
      )}
    </div>
  );
}
