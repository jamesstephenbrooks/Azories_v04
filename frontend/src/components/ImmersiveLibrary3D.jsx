import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader';
import { Button } from '@/components/ui/button';
import { FiX, FiBook, FiMaximize2, FiMinimize2, FiVolume2, FiVolumeX, FiMapPin, FiMove, FiChevronUp, FiRotateCw, FiStar, FiBookmark, FiMessageCircle } from 'react-icons/fi';
import { useAuth } from '@/context/AuthContext';
import AILibrarian from './AILibrarian';

// Gothic Library Model URL - Using proxy to bypass CORS (v16 with collisions)
const ORIGINAL_GLB_URL = 'https://customer-assets.emergentagent.com/job_c72cb56a-2d89-4690-9629-ade6d46638c8/artifacts/n1oyaa5l_gothic_library_16_cycles-compressed.glb';
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
  const azoraRef = useRef(null);
  
  // Physics constants - low eye level for immersive experience
  const PLAYER_HEIGHT = 1.2; // Slightly higher eye level for better viewing
  const MOVE_SPEED = 4;
  
  // Azora (AI assistant) state
  const [azoraPosition, setAzoraPosition] = useState({ x: 2, z: 0 }); // Center of room
  const [isAzoraComing, setIsAzoraComing] = useState(false);
  const [showAzoraChat, setShowAzoraChat] = useState(false);
  const [selectedBook, setSelectedBook] = useState(null); // For book info card
  
  const [isLoaded, setIsLoaded] = useState(false);
  const [loadProgress, setLoadProgress] = useState(0);
  const [loadError, setLoadError] = useState(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isMuted, setIsMuted] = useState(true);
  const [isExploring, setIsExploring] = useState(false);
  const [showGenreMenu, setShowGenreMenu] = useState(false);
  const [isMobileDevice] = useState(isMobile());
  const [hoveredBook, setHoveredBook] = useState(null);
  const [savedPositions, setSavedPositions] = useState([]);
  const [showBookPanel, setShowBookPanel] = useState(true);
  
  // Mobile touch state
  const touchStartRef = useRef({ x: 0, y: 0 });
  const touchMoveRef = useRef({ active: false, x: 0, y: 0 });
  const joystickRef = useRef({ active: false, angle: 0, distance: 0 });
  
  // Mouse look state - support both pointer lock AND drag-to-look
  const isPointerLocked = useRef(false);
  const isDragging = useRef(false);
  const lastMousePos = useRef({ x: 0, y: 0 });
  const [showClickHint, setShowClickHint] = useState(true);
  const [lookMode, setLookMode] = useState('click'); // 'click' or 'drag'
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

  // Mouse movement for looking around - supports both pointer lock and drag
  const onMouseMove = useCallback((event) => {
    if (!cameraRef.current) return;
    
    // Method 1: Pointer lock (if active)
    if (isPointerLocked.current) {
      const movementX = event.movementX || 0;
      const movementY = event.movementY || 0;
      
      euler.current.setFromQuaternion(cameraRef.current.quaternion);
      euler.current.y -= movementX * 0.002;
      euler.current.x -= movementY * 0.002;
      
      // Clamp vertical look
      euler.current.x = Math.max(-Math.PI / 2 + 0.1, Math.min(Math.PI / 2 - 0.1, euler.current.x));
      
      cameraRef.current.quaternion.setFromEuler(euler.current);
      return;
    }
    
    // Method 2: Drag to look (if dragging)
    if (isDragging.current && isExploring) {
      const movementX = event.clientX - lastMousePos.current.x;
      const movementY = event.clientY - lastMousePos.current.y;
      
      lastMousePos.current = { x: event.clientX, y: event.clientY };
      
      euler.current.setFromQuaternion(cameraRef.current.quaternion);
      euler.current.y -= movementX * 0.003;
      euler.current.x -= movementY * 0.003;
      
      // Clamp vertical look
      euler.current.x = Math.max(-Math.PI / 2 + 0.1, Math.min(Math.PI / 2 - 0.1, euler.current.x));
      
      cameraRef.current.quaternion.setFromEuler(euler.current);
    }
  }, [isExploring]);

  // Mouse down - start drag look
  const onMouseDown = useCallback((event) => {
    if (!isExploring || isMobileDevice) return;
    // Right click or left click to drag
    isDragging.current = true;
    lastMousePos.current = { x: event.clientX, y: event.clientY };
    setShowClickHint(false);
  }, [isExploring, isMobileDevice]);

  // Mouse up - stop drag look
  const onMouseUp = useCallback(() => {
    isDragging.current = false;
  }, []);

  // Pointer lock handlers
  const requestPointerLock = useCallback(() => {
    if (canvasRef.current && isExploring) {
      console.log('Requesting pointer lock...');
      try {
        // Try the Promise-based API first
        const lockPromise = canvasRef.current.requestPointerLock();
        if (lockPromise && lockPromise.then) {
          lockPromise.then(() => {
            console.log('Pointer lock granted');
          }).catch((err) => {
            console.log('Pointer lock failed:', err);
          });
        }
      } catch (err) {
        console.log('Pointer lock error:', err);
      }
    } else {
      console.log('Cannot request pointer lock - canvas:', !!canvasRef.current, 'exploring:', isExploring);
    }
  }, [isExploring]);

  const onPointerLockChange = useCallback(() => {
    const locked = document.pointerLockElement === canvasRef.current;
    isPointerLocked.current = locked;
    console.log('Pointer lock changed:', locked);
    if (locked) {
      setShowClickHint(false);
    } else {
      // Show hint again when unlocked
      setShowClickHint(true);
    }
  }, []);

  // Teleport to genre section - use stored floor level
  const teleportToGenre = useCallback((section) => {
    if (!cameraRef.current || !boundsRef.current) return;
    
    // Use the known floor level from when the library loaded
    const floorY = boundsRef.current.floorY || 0;
    const targetY = floorY + PLAYER_HEIGHT;
    
    console.log('Teleporting to:', section.name, 'Floor Y:', floorY, 'Target Y:', targetY);
    
    // Clamp X and Z to stay within bounds
    const newX = Math.max(boundsRef.current.minX + 1, Math.min(boundsRef.current.maxX - 1, section.position.x));
    const newZ = Math.max(boundsRef.current.minZ + 1, Math.min(boundsRef.current.maxZ - 1, section.position.z));
    
    cameraRef.current.position.set(newX, targetY, newZ);
    playerVelocity.current.x = 0;
    playerVelocity.current.y = 0;
    playerVelocity.current.z = 0;
    playerOnGround.current = true;
    setShowGenreMenu(false);
  }, [PLAYER_HEIGHT]);

  // Save current position
  const saveCurrentPosition = useCallback(() => {
    if (!cameraRef.current || !user) return;
    
    const pos = {
      id: Date.now(),
      name: `Position ${savedPositions.length + 1}`,
      x: cameraRef.current.position.x,
      y: cameraRef.current.position.y,
      z: cameraRef.current.position.z,
      rotation: euler.current.y
    };
    
    const newPositions = [...savedPositions, pos].slice(-5); // Keep last 5
    setSavedPositions(newPositions);
    localStorage.setItem(`azories-3d-positions-${user.id}`, JSON.stringify(newPositions));
  }, [savedPositions, user]);

  // Teleport to saved position
  const teleportToSaved = useCallback((pos) => {
    if (!cameraRef.current) return;
    
    cameraRef.current.position.set(pos.x, pos.y, pos.z);
    euler.current.y = pos.rotation || 0;
    cameraRef.current.quaternion.setFromEuler(euler.current);
  }, []);

  // Mobile touch handlers
  const onTouchStart = useCallback((e) => {
    if (!isExploring || !isMobileDevice) return;
    
    const touch = e.touches[0];
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    const x = touch.clientX - rect.left;
    const y = touch.clientY - rect.top;
    const screenWidth = rect.width;
    
    // Left side - joystick for movement
    if (x < screenWidth / 2) {
      joystickRef.current = { active: true, startX: x, startY: y, x: 0, y: 0 };
    } else {
      // Right side - look around
      touchStartRef.current = { x: touch.clientX, y: touch.clientY };
      touchMoveRef.current = { active: true, x: 0, y: 0 };
    }
  }, [isExploring, isMobileDevice]);

  const onTouchMove = useCallback((e) => {
    if (!isExploring || !isMobileDevice) return;
    e.preventDefault();
    
    const touch = e.touches[0];
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    const x = touch.clientX - rect.left;
    
    // Joystick movement (left side)
    if (joystickRef.current.active && x < rect.width / 2) {
      const dx = x - joystickRef.current.startX;
      const dy = touch.clientY - rect.top - joystickRef.current.startY;
      const distance = Math.min(Math.sqrt(dx * dx + dy * dy), 50);
      const angle = Math.atan2(dy, dx);
      
      joystickRef.current.distance = distance;
      joystickRef.current.angle = angle;
      
      // Convert to movement keys
      const threshold = 15;
      keysPressed.current.forward = dy < -threshold;
      keysPressed.current.backward = dy > threshold;
      keysPressed.current.left = dx < -threshold;
      keysPressed.current.right = dx > threshold;
    }
    
    // Look around (right side)
    if (touchMoveRef.current.active && x >= rect.width / 2 && cameraRef.current) {
      const movementX = touch.clientX - touchStartRef.current.x;
      const movementY = touch.clientY - touchStartRef.current.y;
      
      euler.current.setFromQuaternion(cameraRef.current.quaternion);
      euler.current.y -= movementX * 0.003;
      euler.current.x -= movementY * 0.003;
      euler.current.x = Math.max(-Math.PI / 2 + 0.1, Math.min(Math.PI / 2 - 0.1, euler.current.x));
      cameraRef.current.quaternion.setFromEuler(euler.current);
      
      touchStartRef.current = { x: touch.clientX, y: touch.clientY };
    }
  }, [isExploring, isMobileDevice]);

  const onTouchEnd = useCallback(() => {
    joystickRef.current = { active: false, angle: 0, distance: 0 };
    touchMoveRef.current = { active: false, x: 0, y: 0 };
    keysPressed.current = { forward: false, backward: false, left: false, right: false };
  }, []);

  // Click on book in 3D - show info card first
  const onCanvasClick = useCallback((e) => {
    if (!isExploring || !cameraRef.current || isMobileDevice) return;
    if (isPointerLocked.current) return; // Don't process clicks when pointer is locked
    
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    const mouse = new THREE.Vector2(
      ((e.clientX - rect.left) / rect.width) * 2 - 1,
      -((e.clientY - rect.top) / rect.height) * 2 + 1
    );
    
    raycasterRef.current.setFromCamera(mouse, cameraRef.current);
    
    // Check for Azora click first
    if (azoraRef.current) {
      const azoraHits = raycasterRef.current.intersectObject(azoraRef.current, true);
      if (azoraHits.length > 0) {
        // Clicked on Azora - show chat
        setShowAzoraChat(true);
        return;
      }
    }
    
    // Then check for book clicks
    const hits = raycasterRef.current.intersectObjects(bookMeshesRef.current, true);
    
    if (hits.length > 0) {
      const bookMesh = hits[0].object;
      const bookId = bookMesh.userData?.bookId;
      if (bookId) {
        // Find the book data and show info card
        const bookData = books.find(b => b.id === bookId);
        if (bookData) {
          setSelectedBook(bookData);
        }
      }
    }
  }, [isExploring, isMobileDevice, books]);

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
        // COLLISION ON ALL MESHES except: books, tables, chairs, ceiling
        const collisionMeshes = [];
        const visibleMeshes = [];
        
        model.traverse((child) => {
          if (child.isMesh) {
            const name = child.name.toLowerCase();
            
            // Log all mesh names to help debug collision setup
            console.log('Mesh found:', child.name);
            
            // Check if this is EXPLICITLY a collision-only mesh (invisible)
            const isCollisionOnlyMesh = name.includes('collision') || name.includes('collider') || 
                name.includes('_col_') || name.startsWith('col_') || name.endsWith('_col') ||
                name.includes('bounds') || name.includes('blocker') || name.includes('barrier');
            
            // Check if this mesh should be EXCLUDED from collision
            const excludeFromCollision = name.includes('book') || name.includes('table') || 
                name.includes('chair') || name.includes('ceiling') || name.includes('seat') ||
                name.includes('lamp') || name.includes('candle') || name.includes('painting') ||
                name.includes('picture') || name.includes('frame') || name.includes('decoration');
            
            if (isCollisionOnlyMesh) {
              // Make collision-only meshes invisible but keep for raycasting
              child.visible = false;
              collisionMeshes.push(child);
              console.log('✓ Collision-only mesh:', child.name);
            } else {
              // Regular visible meshes
              child.castShadow = true;
              child.receiveShadow = true;
              if (child.material) {
                child.material.side = THREE.DoubleSide;
                child.material.needsUpdate = true;
              }
              visibleMeshes.push(child);
              
              // Add to collision if NOT excluded
              if (!excludeFromCollision) {
                collisionMeshes.push(child);
                console.log('✓ Collision enabled:', child.name);
              } else {
                console.log('✗ Collision disabled:', child.name);
              }
            }
          }
        });
        
        console.log(`Found ${collisionMeshes.length} collision meshes, ${visibleMeshes.length} visible meshes`);
        
        // Store collision meshes for raycasting
        collisionMeshesRef.current = collisionMeshes;
        
        scene.add(model);
        
        // Try to find a good starting position using raycasting
        const raycaster = new THREE.Raycaster();
        const downRay = new THREE.Vector3(0, -1, 0);
        
        // Cast ray down from center to find floor
        // Find a floor mesh specifically named "floor" and get its Y position
        let floorLevel = 0;
        let foundFloor = false;
        
        model.traverse((child) => {
          if (child.isMesh) {
            const name = child.name.toLowerCase();
            if (name.includes('floor') && !name.includes('edge')) {
              const meshBox = new THREE.Box3().setFromObject(child);
              // Get the top of the floor mesh
              if (!foundFloor || meshBox.max.y < floorLevel + 5) {
                floorLevel = meshBox.max.y;
                foundFloor = true;
                console.log('Found floor mesh:', child.name, 'at Y:', floorLevel);
              }
            }
          }
        });
        
        // Fallback: use raycast but filter for low Y values
        if (!foundFloor) {
          raycaster.set(new THREE.Vector3(0, 50, 0), downRay);
          const floorHits = raycaster.intersectObjects(collisionMeshesRef.current, true);
          
          // Find the lowest hit point that's above Y=0
          for (const hit of floorHits) {
            if (hit.point.y >= 0 && hit.point.y < 10) {
              floorLevel = hit.point.y;
              foundFloor = true;
              console.log('Found floor via raycast at:', floorLevel);
              break;
            }
          }
        }
        
        let startY = foundFloor ? floorLevel + PLAYER_HEIGHT : PLAYER_HEIGHT;
        console.log('Starting at Y:', startY, 'Floor level:', floorLevel);
        
        // Store the floor level in bounds for teleportation
        boundsRef.current.floorY = floorLevel;
        
        // Position camera inside the library at center
        camera.position.set(0, startY, 0);
        
        // Load the ornate book GLB model for books on shelves
        const BOOK_GLB_URL = 'https://customer-assets.emergentagent.com/job_c72cb56a-2d89-4690-9629-ade6d46638c8/artifacts/a67239en_ornate_book.glb';
        const BOOK_PROXY_URL = `${process.env.REACT_APP_BACKEND_URL}/api/proxy/glb?url=${encodeURIComponent(BOOK_GLB_URL)}`;
        
        const bookLoader = new GLTFLoader();
        bookLoader.setDRACOLoader(dracoLoader);
        
        // Bookshelf positions around the library (matching the GLB layout)
        const shelfPositions = [
          // Left side shelves
          { x: -7, z: -3, rotation: Math.PI / 2, levels: [floorLevel + 0.8, floorLevel + 1.5, floorLevel + 2.2] },
          { x: -7, z: 0, rotation: Math.PI / 2, levels: [floorLevel + 0.8, floorLevel + 1.5, floorLevel + 2.2] },
          { x: -7, z: 3, rotation: Math.PI / 2, levels: [floorLevel + 0.8, floorLevel + 1.5, floorLevel + 2.2] },
          // Right side shelves
          { x: 7, z: -3, rotation: -Math.PI / 2, levels: [floorLevel + 0.8, floorLevel + 1.5, floorLevel + 2.2] },
          { x: 7, z: 0, rotation: -Math.PI / 2, levels: [floorLevel + 0.8, floorLevel + 1.5, floorLevel + 2.2] },
          { x: 7, z: 3, rotation: -Math.PI / 2, levels: [floorLevel + 0.8, floorLevel + 1.5, floorLevel + 2.2] },
          // Back shelves
          { x: -3, z: -7, rotation: 0, levels: [floorLevel + 0.8, floorLevel + 1.5, floorLevel + 2.2] },
          { x: 0, z: -7, rotation: 0, levels: [floorLevel + 0.8, floorLevel + 1.5, floorLevel + 2.2] },
          { x: 3, z: -7, rotation: 0, levels: [floorLevel + 0.8, floorLevel + 1.5, floorLevel + 2.2] },
        ];
        
        // Load the book model once, then clone for each book
        bookLoader.load(
          BOOK_PROXY_URL,
          (gltf) => {
            const bookTemplate = gltf.scene;
            const bookMeshes = [];
            
            console.log('Loaded ornate book model, placing', books.length, 'books on shelves');
            
            // Place books on shelves
            let bookIndex = 0;
            shelfPositions.forEach((shelf, shelfIdx) => {
              shelf.levels.forEach((levelY, levelIdx) => {
                // Put 2-3 books per shelf level
                const booksPerLevel = 2 + (shelfIdx % 2);
                for (let i = 0; i < booksPerLevel && bookIndex < books.length; i++) {
                  const book = books[bookIndex];
                  
                  // Clone the book model
                  const bookMesh = bookTemplate.clone();
                  
                  // Scale the book appropriately
                  bookMesh.scale.set(0.15, 0.15, 0.15);
                  
                  // Position on shelf - spread books along the shelf
                  const offsetX = (i - (booksPerLevel - 1) / 2) * 0.25;
                  const offsetZ = (i - (booksPerLevel - 1) / 2) * 0.25;
                  
                  if (Math.abs(shelf.rotation) === Math.PI / 2) {
                    // Side shelves (facing X direction)
                    bookMesh.position.set(shelf.x, levelY, shelf.z + offsetZ);
                  } else {
                    // Front/back shelves (facing Z direction)
                    bookMesh.position.set(shelf.x + offsetX, levelY, shelf.z);
                  }
                  
                  bookMesh.rotation.y = shelf.rotation + (Math.random() * 0.1 - 0.05); // Slight random tilt
                  
                  // Traverse and setup materials/shadows
                  bookMesh.traverse((child) => {
                    if (child.isMesh) {
                      child.castShadow = true;
                      child.receiveShadow = true;
                      // Add slight color variation to make books unique
                      if (child.material) {
                        child.material = child.material.clone();
                        // Tint based on genre
                        const genreColors = {
                          'Fantasy': 0x9333ea,
                          'Adventure': 0x22c55e,
                          'Mystery': 0x3b82f6,
                          'Science Fiction': 0x06b6d4,
                          'Romance': 0xec4899,
                          'Horror': 0xef4444
                        };
                        const tintColor = genreColors[book.genre] || 0x8b5cf6;
                        if (child.material.color) {
                          child.material.color.lerp(new THREE.Color(tintColor), 0.3);
                        }
                      }
                    }
                  });
                  
                  // Store book data for click detection
                  bookMesh.userData = { 
                    bookId: book.id, 
                    title: book.title,
                    isBook: true 
                  };
                  
                  scene.add(bookMesh);
                  bookMeshes.push(bookMesh);
                  bookIndex++;
                }
              });
            });
            
            bookMeshesRef.current = bookMeshes;
            console.log('Placed', bookMeshes.length, 'books on shelves');
          },
          undefined,
          (error) => {
            console.error('Failed to load book model:', error);
            // Fallback to simple box books
            const bookMeshes = [];
            books.slice(0, 20).forEach((book, index) => {
              const geometry = new THREE.BoxGeometry(0.1, 0.2, 0.15);
              const material = new THREE.MeshStandardMaterial({ color: 0x8b5cf6 });
              const bookMesh = new THREE.Mesh(geometry, material);
              
              const angle = (index / 20) * Math.PI * 2;
              const radius = 6;
              bookMesh.position.set(
                Math.cos(angle) * radius,
                floorLevel + 1 + (index % 3) * 0.3,
                Math.sin(angle) * radius
              );
              bookMesh.userData = { bookId: book.id, title: book.title, isBook: true };
              scene.add(bookMesh);
              bookMeshes.push(bookMesh);
            });
            bookMeshesRef.current = bookMeshes;
          }
        );
        
        // Add floating genre text labels above sections
        const bannerHeight = floorLevel + 3.5; // 3.5 meters above floor
        
        GENRE_SECTIONS.forEach((section) => {
          if (section.name === 'Center') return; // Skip center
          
          // Create simple text sprite
          const canvas = document.createElement('canvas');
          canvas.width = 256;
          canvas.height = 64;
          const ctx = canvas.getContext('2d');
          
          // Clear canvas
          ctx.clearRect(0, 0, 256, 64);
          
          // Glowing text effect
          ctx.font = 'bold 32px Georgia, serif';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          
          // Outer glow
          ctx.shadowColor = section.color;
          ctx.shadowBlur = 20;
          ctx.fillStyle = section.color;
          ctx.fillText(section.name, 128, 32);
          
          // Inner text (white)
          ctx.shadowBlur = 10;
          ctx.fillStyle = '#ffffff';
          ctx.fillText(section.name, 128, 32);
          
          const texture = new THREE.CanvasTexture(canvas);
          texture.colorSpace = THREE.SRGBColorSpace;
          
          // Use sprite for always-facing-camera text
          const spriteMaterial = new THREE.SpriteMaterial({
            map: texture,
            transparent: true,
            depthWrite: false
          });
          
          const sprite = new THREE.Sprite(spriteMaterial);
          sprite.scale.set(3, 0.75, 1);
          sprite.position.set(section.position.x, bannerHeight, section.position.z);
          
          scene.add(sprite);
          console.log('Added genre text:', section.name, 'at Y:', bannerHeight);
          
          // Add floating animation via userData
          sprite.userData = { 
            isGenreBanner: true, 
            baseY: bannerHeight,
            phase: Math.random() * Math.PI * 2 
          };
        });
        
        // Load Azora 3D model (GLB) - Standing stationary near center
        const AZORA_GLB_URL = 'https://customer-assets.emergentagent.com/job_c72cb56a-2d89-4690-9629-ade6d46638c8/artifacts/t9l9jikb_f0066361-3481-4680-b638-accd998414b5.glb';
        const AZORA_PROXY_URL = `${process.env.REACT_APP_BACKEND_URL}/api/proxy/glb?url=${encodeURIComponent(AZORA_GLB_URL)}`;
        
        const azoraLoader = new GLTFLoader();
        azoraLoader.setDRACOLoader(dracoLoader);
        
        azoraLoader.load(
          AZORA_PROXY_URL,
          (gltf) => {
            const azoraModel = gltf.scene;
            
            // Scale Azora down to 50% as requested by user
            azoraModel.scale.set(0.5, 0.5, 0.5);
            
            // Position Azora standing in an open area near center, facing the entrance
            const azoraY = floorLevel;
            azoraModel.position.set(2, azoraY, 2); // Offset from center to avoid blocking entrance
            azoraModel.rotation.y = -Math.PI / 4; // Face toward center/entrance
            
            // Enable shadows
            azoraModel.traverse((child) => {
              if (child.isMesh) {
                child.castShadow = true;
                child.receiveShadow = true;
              }
            });
            
            // Play idle animation if available
            let mixer = null;
            if (gltf.animations && gltf.animations.length > 0) {
              mixer = new THREE.AnimationMixer(azoraModel);
              // Try to find an idle animation, otherwise use first one
              const idleAnim = gltf.animations.find(a => a.name.toLowerCase().includes('idle')) || gltf.animations[0];
              const action = mixer.clipAction(idleAnim);
              action.play();
              azoraModel.userData.mixer = mixer;
              console.log('Azora has', gltf.animations.length, 'animations, playing:', idleAnim.name);
            }
            
            // Azora is stationary - no walking
            azoraModel.userData = {
              ...azoraModel.userData,
              isAzora: true,
              baseY: azoraY,
              mixer: mixer
            };
            
            scene.add(azoraModel);
            azoraRef.current = azoraModel;
            console.log('Loaded Azora - standing at center, Y:', azoraY);
          },
          undefined,
          (error) => {
            console.error('Failed to load Azora model:', error);
            // Fallback to simple placeholder if GLB fails
            const fallbackGeom = new THREE.CylinderGeometry(0.3, 0.3, 1.5, 8);
            const fallbackMat = new THREE.MeshBasicMaterial({ color: 0x9333ea });
            const fallback = new THREE.Mesh(fallbackGeom, fallbackMat);
            fallback.position.set(2, floorLevel + 0.75, 2);
            fallback.userData = { isAzora: true, baseY: floorLevel + 0.75 };
            scene.add(fallback);
            azoraRef.current = fallback;
          }
        );
        
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

    // Animation loop with SIMPLIFIED physics - focus on stable movement
    const animate = () => {
      if (!mounted) return;
      animationIdRef.current = requestAnimationFrame(animate);
      
      const delta = Math.min(clockRef.current.getDelta(), 0.05); // Cap delta more aggressively
      
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
        
        // Normalize and apply speed - direct velocity, no acceleration
        if (moveDirection.length() > 0) {
          moveDirection.normalize();
          playerVelocity.current.x = moveDirection.x * MOVE_SPEED;
          playerVelocity.current.z = moveDirection.z * MOVE_SPEED;
        } else {
          // Stop immediately when not pressing keys (no friction sliding)
          playerVelocity.current.x = 0;
          playerVelocity.current.z = 0;
        }
        
        // Calculate desired new position
        let newX = camera.position.x + playerVelocity.current.x * delta;
        let newZ = camera.position.z + playerVelocity.current.z * delta;
        
        // SIMPLIFIED wall collision - cast ray in movement direction only
        const COLLISION_RADIUS = 0.4;
        
        if (collisionMeshes.length > 0 && (playerVelocity.current.x !== 0 || playerVelocity.current.z !== 0)) {
          const horizontalVelocity = new THREE.Vector3(
            playerVelocity.current.x,
            0,
            playerVelocity.current.z
          ).normalize();
          
          // Ray from chest height in movement direction
          const rayOrigin = new THREE.Vector3(
            camera.position.x,
            camera.position.y - 0.3, // chest height
            camera.position.z
          );
          
          raycaster.set(rayOrigin, horizontalVelocity);
          raycaster.far = COLLISION_RADIUS + 0.2;
          
          const hits = raycaster.intersectObjects(collisionMeshes, true);
          
          if (hits.length > 0 && hits[0].distance < COLLISION_RADIUS) {
            // Wall hit - STOP movement, don't slide
            newX = camera.position.x;
            newZ = camera.position.z;
            playerVelocity.current.x = 0;
            playerVelocity.current.z = 0;
          }
        }
        
        // Apply boundary collision (fallback)
        newX = Math.max(bounds.minX + 0.5, Math.min(bounds.maxX - 0.5, newX));
        newZ = Math.max(bounds.minZ + 0.5, Math.min(bounds.maxZ - 0.5, newZ));
        
        camera.position.x = newX;
        camera.position.z = newZ;
        
        // SIMPLIFIED floor detection - use stored floor level, don't raycast for floor
        // This prevents the "jumping to upper floors" bug completely
        const baseFloorY = bounds.floorY || 0;
        const targetY = baseFloorY + PLAYER_HEIGHT;
        
        // Keep player locked to ground floor - no vertical movement at all
        // This eliminates all vertical jumping/physics bugs
        if (Math.abs(camera.position.y - targetY) > 0.01) {
          // Smoothly interpolate to target height (handles spawning at wrong height)
          camera.position.y = camera.position.y + (targetY - camera.position.y) * 0.1;
        }
        
        // Clamp Y to prevent any vertical drift
        camera.position.y = Math.max(baseFloorY + PLAYER_HEIGHT * 0.5, Math.min(baseFloorY + PLAYER_HEIGHT * 1.5, camera.position.y));
        
        // Player is always on ground (no jumping in this library)
        playerOnGround.current = true;
        playerVelocity.current.y = 0;
      }
      
      // Animate floating genre banners
      const time = Date.now() * 0.001;
      scene.traverse((child) => {
        if (child.userData?.isGenreBanner) {
          // Floating animation
          child.position.y = child.userData.baseY + Math.sin(time + child.userData.phase) * 0.1;
        }
      });
      
      // Update Azora's animation mixer (for idle animation)
      if (azoraRef.current && azoraRef.current.userData?.mixer) {
        azoraRef.current.userData.mixer.update(delta);
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
    
    // Pointer lock error handler
    const onPointerLockError = () => {
      console.error('Pointer lock error - may need user interaction first');
    };
    
    window.addEventListener('resize', handleResize);
    document.addEventListener('keydown', onKeyDown);
    document.addEventListener('keyup', onKeyUp);
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mousedown', onMouseDown);
    document.addEventListener('mouseup', onMouseUp);
    document.addEventListener('pointerlockchange', onPointerLockChange);
    document.addEventListener('pointerlockerror', onPointerLockError);
    
    // Touch events for mobile
    const canvas = canvasRef.current;
    if (canvas) {
      canvas.addEventListener('touchstart', onTouchStart, { passive: false });
      canvas.addEventListener('touchmove', onTouchMove, { passive: false });
      canvas.addEventListener('touchend', onTouchEnd);
    }

    // Cleanup
    return () => {
      mounted = false;
      clearTimeout(loadTimeout);
      window.removeEventListener('resize', handleResize);
      document.removeEventListener('keydown', onKeyDown);
      document.removeEventListener('keyup', onKeyUp);
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mousedown', onMouseDown);
      document.removeEventListener('mouseup', onMouseUp);
      document.removeEventListener('pointerlockchange', onPointerLockChange);
      document.removeEventListener('pointerlockerror', onPointerLockError);
      
      if (canvas) {
        canvas.removeEventListener('touchstart', onTouchStart);
        canvas.removeEventListener('touchmove', onTouchMove);
        canvas.removeEventListener('touchend', onTouchEnd);
      }
      
      if (animationIdRef.current) {
        cancelAnimationFrame(animationIdRef.current);
      }
      if (rendererRef.current) {
        rendererRef.current.dispose();
      }
      dracoLoader.dispose();
    };
  }, [onKeyDown, onKeyUp, onMouseMove, onMouseDown, onMouseUp, onPointerLockChange, onTouchStart, onTouchMove, onTouchEnd, isExploring, books]);

  // Start exploring
  const handleStartExploring = () => {
    setIsExploring(true);
    // Controls are already shown in the welcome dialog, no need for extra popup
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
        onClick={isMobileDevice ? onCanvasClick : requestPointerLock}
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
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="absolute inset-0 flex items-center justify-center"
          >
            <div className="bg-gradient-to-br from-[#2d1f3d]/95 to-[#1a1520]/95 backdrop-blur-md rounded-2xl p-8 max-w-md mx-4 text-center border border-purple-500/30 shadow-2xl">
              <div className="w-16 h-16 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <FiMove className="w-8 h-8 text-purple-400" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Welcome to the Grand Library</h2>
              <p className="text-white/60 mb-6">
                Explore this magical library. Click and drag to look around, use keys to walk.
              </p>
              
              <div className="bg-black/30 rounded-lg p-4 mb-6 text-left">
                <p className="text-sm font-medium text-purple-300 mb-3">Controls:</p>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="flex items-center gap-2">
                    <kbd className="px-2 py-1 bg-purple-900/50 rounded text-purple-300 text-xs">W A S D</kbd>
                    <span className="text-white/70">Walk around</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <kbd className="px-2 py-1 bg-purple-900/50 rounded text-purple-300 text-xs">Click+Drag</kbd>
                    <span className="text-white/70">Look around</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <kbd className="px-2 py-1 bg-purple-900/50 rounded text-purple-300 text-xs">↑ ↓ ← →</kbd>
                    <span className="text-white/70">Alternative movement</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <kbd className="px-2 py-1 bg-purple-900/50 rounded text-purple-300 text-xs">Scroll</kbd>
                    <span className="text-white/70">Zoom (future)</span>
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
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 pointer-events-none">
            {showClickHint ? (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-purple-600 backdrop-blur-sm rounded-full px-6 py-3 text-white text-sm font-medium shadow-lg shadow-purple-500/30"
              >
                🖱️ Click & drag to look around
              </motion.div>
            ) : (
              <div className="bg-black/50 backdrop-blur-sm rounded-full px-4 py-2 text-white/70 text-sm">
                WASD to walk • Click+drag to look
              </div>
            )}
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
          
          {/* Book Info Card (when a book is selected in 3D view) */}
          <AnimatePresence>
            {selectedBook && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9, y: 20 }}
                className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-auto"
              >
                <div className="bg-gradient-to-br from-[#2d1f3d] to-[#1a1520] rounded-2xl p-6 max-w-sm border border-purple-500/30 shadow-2xl shadow-purple-500/20">
                  {/* Book Cover */}
                  <div className="relative w-32 h-44 mx-auto mb-4 rounded-lg overflow-hidden shadow-lg">
                    {selectedBook.cover_image ? (
                      <img 
                        src={selectedBook.cover_image} 
                        alt={selectedBook.title}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full bg-purple-900 flex items-center justify-center">
                        <FiBook className="w-8 h-8 text-purple-400" />
                      </div>
                    )}
                  </div>
                  
                  {/* Book Info */}
                  <h3 className="text-xl font-bold text-white text-center mb-1">{selectedBook.title}</h3>
                  <p className="text-sm text-purple-300 text-center mb-3">by {selectedBook.author_name || 'Unknown Author'}</p>
                  
                  {selectedBook.genre && (
                    <div className="flex justify-center mb-3">
                      <span className="px-3 py-1 bg-purple-500/20 rounded-full text-xs text-purple-300">
                        {selectedBook.genre}
                      </span>
                    </div>
                  )}
                  
                  {selectedBook.description && (
                    <p className="text-sm text-white/60 text-center mb-4 line-clamp-3">
                      {selectedBook.description}
                    </p>
                  )}
                  
                  {/* Action Buttons */}
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      onClick={() => setSelectedBook(null)}
                      className="flex-1 text-white border-white/30 hover:bg-white/10"
                    >
                      Close
                    </Button>
                    <Button
                      onClick={() => window.location.href = `/read/${selectedBook.id}`}
                      className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                    >
                      <FiBook className="w-4 h-4 mr-2" />
                      Read
                    </Button>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          
          {/* Azora Speech Bubble (when clicked in 3D) */}
          <AnimatePresence>
            {showAzoraChat && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9, y: 20 }}
                className="absolute bottom-24 left-1/2 -translate-x-1/2 pointer-events-auto max-w-md w-full mx-4"
              >
                <div className="bg-gradient-to-br from-purple-900/95 to-[#1a1520]/95 backdrop-blur-lg rounded-2xl p-4 border border-purple-500/30 shadow-2xl shadow-purple-500/20">
                  {/* Header */}
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div className="w-10 h-10 rounded-full bg-purple-500/30 flex items-center justify-center">
                        <FiMessageCircle className="w-5 h-5 text-purple-300" />
                      </div>
                      <div>
                        <h3 className="text-white font-semibold">Azora</h3>
                        <p className="text-xs text-purple-300">Magical Librarian</p>
                      </div>
                    </div>
                    <button
                      onClick={() => setShowAzoraChat(false)}
                      className="text-white/50 hover:text-white"
                    >
                      <FiX className="w-5 h-5" />
                    </button>
                  </div>
                  
                  {/* Message */}
                  <div className="bg-black/30 rounded-lg p-3 mb-3">
                    <p className="text-white/90 text-sm">
                      Hello there, young reader! I'm Azora, the keeper of this magical library. 
                      Looking for a story? I can help you find the perfect book for your adventure! 
                      What kind of stories do you enjoy?
                    </p>
                  </div>
                  
                  {/* Quick Actions */}
                  <div className="flex flex-wrap gap-2">
                    <button className="px-3 py-1.5 bg-purple-500/20 hover:bg-purple-500/30 rounded-full text-xs text-purple-200 transition-colors">
                      Fantasy Adventures
                    </button>
                    <button className="px-3 py-1.5 bg-purple-500/20 hover:bg-purple-500/30 rounded-full text-xs text-purple-200 transition-colors">
                      Mystery Stories
                    </button>
                    <button className="px-3 py-1.5 bg-purple-500/20 hover:bg-purple-500/30 rounded-full text-xs text-purple-200 transition-colors">
                      Science Fiction
                    </button>
                    <button className="px-3 py-1.5 bg-purple-500/20 hover:bg-purple-500/30 rounded-full text-xs text-purple-200 transition-colors">
                      Recommend for me
                    </button>
                  </div>
                </div>
                
                {/* Speech bubble tail */}
                <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-4 h-4 bg-gradient-to-br from-purple-900/95 to-[#1a1520]/95 rotate-45 border-r border-b border-purple-500/30"></div>
              </motion.div>
            )}
          </AnimatePresence>
          
          {/* AI Librarian - Azora (bottom corner chat - full chat interface) */}
          <AILibrarian books={books} isVisible={!showAzoraChat} onCallAzora={() => setShowAzoraChat(true)} />
        </>
      )}
    </div>
  );
}
