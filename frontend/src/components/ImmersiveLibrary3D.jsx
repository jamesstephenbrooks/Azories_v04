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
  const sceneRef = useRef(null);
  
  // Physics constants - realistic eye level for a child/young person
  const GRAVITY = 20;
  const PLAYER_HEIGHT = 1.4; // Lower eye level for more immersive feel (~4'7")
  const MOVE_SPEED = 4;
  const FRICTION = 10;
  
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

  // Teleport to genre section - with proper floor detection
  const teleportToGenre = useCallback((section) => {
    if (!cameraRef.current || !collisionMeshesRef.current) return;
    
    // Find floor level at the target position
    const raycaster = new THREE.Raycaster();
    raycaster.set(
      new THREE.Vector3(section.position.x, 20, section.position.z),
      new THREE.Vector3(0, -1, 0)
    );
    raycaster.far = 30;
    
    const floorHits = raycaster.intersectObjects(collisionMeshesRef.current, true);
    let targetY = PLAYER_HEIGHT + 5; // Default to a safe height
    
    // Find the actual floor at this position
    for (const hit of floorHits) {
      if (hit.point.y < 10 && hit.point.y >= 0) {
        targetY = hit.point.y + PLAYER_HEIGHT;
        console.log('Teleporting to floor at Y:', hit.point.y);
        break;
      }
    }
    
    cameraRef.current.position.set(
      section.position.x,
      targetY,
      section.position.z
    );
    playerVelocity.current.y = 0;
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

  // Click on book in 3D
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
    const hits = raycasterRef.current.intersectObjects(bookMeshesRef.current, true);
    
    if (hits.length > 0) {
      const bookMesh = hits[0].object;
      const bookId = bookMesh.userData?.bookId;
      if (bookId) {
        navigate(`/read/${bookId}`);
      }
    }
  }, [isExploring, isMobileDevice, navigate]);

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
        console.log('Starting at Y:', startY);
        
        // Position camera inside the library at center
        camera.position.set(0, startY, 0);
        
        // Create floating book sprites for interactive book selection
        const bookSprites = [];
        const textureLoader = new THREE.TextureLoader();
        
        books.slice(0, 12).forEach((book, index) => {
          // Calculate position around the library
          const angle = (index / 12) * Math.PI * 2;
          const radius = 5;
          const x = Math.cos(angle) * radius;
          const z = Math.sin(angle) * radius;
          const y = startY + Math.sin(index) * 0.3 + 0.5; // Float at varying heights
          
          // Create a plane geometry for the book cover
          const geometry = new THREE.PlaneGeometry(0.6, 0.8);
          
          // Create material with book cover or placeholder
          let material;
          if (book.cover_image) {
            const texture = textureLoader.load(book.cover_image, 
              () => {}, 
              () => {}, 
              () => {
                // Error loading texture - use fallback color
                material.color = new THREE.Color(0x9333ea);
              }
            );
            texture.colorSpace = THREE.SRGBColorSpace;
            material = new THREE.MeshBasicMaterial({ 
              map: texture, 
              side: THREE.DoubleSide,
              transparent: true
            });
          } else {
            material = new THREE.MeshBasicMaterial({ 
              color: 0x9333ea, 
              side: THREE.DoubleSide 
            });
          }
          
          const bookMesh = new THREE.Mesh(geometry, material);
          bookMesh.position.set(x, y, z);
          bookMesh.lookAt(0, y, 0); // Face center
          bookMesh.userData = { bookId: book.id, title: book.title };
          
          scene.add(bookMesh);
          bookSprites.push(bookMesh);
        });
        
        bookMeshesRef.current = bookSprites;
        
        // Create floating magical genre banners
        const createTextCanvas = (text, color) => {
          const canvas = document.createElement('canvas');
          canvas.width = 512;
          canvas.height = 128;
          const ctx = canvas.getContext('2d');
          
          // Gradient background
          const gradient = ctx.createLinearGradient(0, 0, 512, 0);
          gradient.addColorStop(0, 'rgba(0,0,0,0)');
          gradient.addColorStop(0.2, color + '40');
          gradient.addColorStop(0.5, color + '80');
          gradient.addColorStop(0.8, color + '40');
          gradient.addColorStop(1, 'rgba(0,0,0,0)');
          ctx.fillStyle = gradient;
          ctx.fillRect(0, 0, 512, 128);
          
          // Glowing text
          ctx.font = 'bold 48px "Georgia", serif';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          
          // Glow effect
          ctx.shadowColor = color;
          ctx.shadowBlur = 20;
          ctx.fillStyle = '#ffffff';
          ctx.fillText(text, 256, 64);
          ctx.fillText(text, 256, 64); // Double for stronger glow
          
          return canvas;
        };
        
        // Add floating genre banners above sections
        GENRE_SECTIONS.forEach((section) => {
          if (section.name === 'Center') return; // Skip center
          
          const bannerCanvas = createTextCanvas(section.name, section.color);
          const bannerTexture = new THREE.CanvasTexture(bannerCanvas);
          bannerTexture.colorSpace = THREE.SRGBColorSpace;
          
          const bannerGeometry = new THREE.PlaneGeometry(4, 1);
          const bannerMaterial = new THREE.MeshBasicMaterial({
            map: bannerTexture,
            transparent: true,
            side: THREE.DoubleSide,
            depthWrite: false
          });
          
          const banner = new THREE.Mesh(bannerGeometry, bannerMaterial);
          banner.position.set(section.position.x, startY + 3.5, section.position.z);
          banner.rotation.y = Math.atan2(section.position.x, section.position.z); // Face outward
          
          scene.add(banner);
          
          // Add floating animation via userData
          banner.userData = { 
            isGenreBanner: true, 
            baseY: startY + 3.5,
            phase: Math.random() * Math.PI * 2 
          };
        });
        
        // Create Azora 3D sprite (young witch librarian)
        const azoraGeometry = new THREE.PlaneGeometry(1.2, 1.8);
        const azoraCanvas = document.createElement('canvas');
        azoraCanvas.width = 256;
        azoraCanvas.height = 384;
        const azoraCtx = azoraCanvas.getContext('2d');
        
        // Draw stylized Azora (young witch)
        // Background glow
        const azoraGlow = azoraCtx.createRadialGradient(128, 192, 0, 128, 192, 150);
        azoraGlow.addColorStop(0, 'rgba(147, 51, 234, 0.3)');
        azoraGlow.addColorStop(1, 'rgba(0, 0, 0, 0)');
        azoraCtx.fillStyle = azoraGlow;
        azoraCtx.fillRect(0, 0, 256, 384);
        
        // Robe/Cloak (dark with purple tint)
        azoraCtx.fillStyle = '#1a1030';
        azoraCtx.beginPath();
        azoraCtx.moveTo(128, 100);
        azoraCtx.bezierCurveTo(60, 150, 50, 350, 70, 380);
        azoraCtx.lineTo(186, 380);
        azoraCtx.bezierCurveTo(206, 350, 196, 150, 128, 100);
        azoraCtx.fill();
        
        // Hood
        azoraCtx.fillStyle = '#2d1f50';
        azoraCtx.beginPath();
        azoraCtx.ellipse(128, 95, 50, 60, 0, Math.PI, 0);
        azoraCtx.fill();
        
        // Face (simple, warm tone)
        azoraCtx.fillStyle = '#f5d5c8';
        azoraCtx.beginPath();
        azoraCtx.ellipse(128, 90, 28, 35, 0, 0, Math.PI * 2);
        azoraCtx.fill();
        
        // Hair (flowing, light brown/blonde)
        azoraCtx.fillStyle = '#c4a574';
        azoraCtx.beginPath();
        azoraCtx.ellipse(128, 70, 32, 25, 0, Math.PI, 0);
        azoraCtx.fill();
        // Hair sides
        azoraCtx.beginPath();
        azoraCtx.moveTo(96, 80);
        azoraCtx.quadraticCurveTo(80, 120, 85, 170);
        azoraCtx.quadraticCurveTo(95, 140, 100, 100);
        azoraCtx.fill();
        azoraCtx.beginPath();
        azoraCtx.moveTo(160, 80);
        azoraCtx.quadraticCurveTo(176, 120, 171, 170);
        azoraCtx.quadraticCurveTo(161, 140, 156, 100);
        azoraCtx.fill();
        
        // Eyes (friendly)
        azoraCtx.fillStyle = '#6b5344';
        azoraCtx.beginPath();
        azoraCtx.ellipse(115, 88, 5, 6, 0, 0, Math.PI * 2);
        azoraCtx.ellipse(141, 88, 5, 6, 0, 0, Math.PI * 2);
        azoraCtx.fill();
        
        // Smile
        azoraCtx.strokeStyle = '#c49a87';
        azoraCtx.lineWidth = 2;
        azoraCtx.beginPath();
        azoraCtx.arc(128, 100, 12, 0.1 * Math.PI, 0.9 * Math.PI);
        azoraCtx.stroke();
        
        // Magic wand (held out)
        azoraCtx.strokeStyle = '#4a3728';
        azoraCtx.lineWidth = 4;
        azoraCtx.beginPath();
        azoraCtx.moveTo(170, 200);
        azoraCtx.lineTo(210, 160);
        azoraCtx.stroke();
        
        // Wand tip glow
        azoraCtx.fillStyle = '#a855f7';
        azoraCtx.shadowColor = '#a855f7';
        azoraCtx.shadowBlur = 15;
        azoraCtx.beginPath();
        azoraCtx.arc(212, 158, 8, 0, Math.PI * 2);
        azoraCtx.fill();
        azoraCtx.shadowBlur = 0;
        
        // Sparkles around wand
        azoraCtx.fillStyle = '#e9d5ff';
        [[-10, -15], [15, -8], [5, 12], [-8, 8]].forEach(([ox, oy]) => {
          azoraCtx.beginPath();
          azoraCtx.arc(212 + ox, 158 + oy, 2, 0, Math.PI * 2);
          azoraCtx.fill();
        });
        
        const azoraTexture = new THREE.CanvasTexture(azoraCanvas);
        azoraTexture.colorSpace = THREE.SRGBColorSpace;
        
        const azoraMaterial = new THREE.MeshBasicMaterial({
          map: azoraTexture,
          transparent: true,
          side: THREE.DoubleSide,
          depthWrite: false
        });
        
        const azoraMesh = new THREE.Mesh(azoraGeometry, azoraMaterial);
        azoraMesh.position.set(2, startY + 0.9, 0); // Standing in the library
        azoraMesh.userData = { isAzora: true, baseY: startY + 0.9 };
        scene.add(azoraMesh);
        azoraRef.current = azoraMesh;
        
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
        
        // Raycast-based wall collision detection - cast multiple rays and implement wall sliding
        if (collisionMeshes.length > 0 && (playerVelocity.current.x !== 0 || playerVelocity.current.z !== 0)) {
          const horizontalVelocity = new THREE.Vector3(
            playerVelocity.current.x,
            0,
            playerVelocity.current.z
          );
          
          if (horizontalVelocity.length() > 0.01) {
            const rayDir = horizontalVelocity.clone().normalize();
            let hitNormal = null;
            let minDistance = Infinity;
            
            // Cast rays at multiple heights (feet, waist, chest)
            const rayHeights = [0.3, 0.8, 1.4];
            for (const height of rayHeights) {
              const rayOrigin = new THREE.Vector3(
                camera.position.x,
                camera.position.y - PLAYER_HEIGHT + height,
                camera.position.z
              );
              
              raycaster.set(rayOrigin, rayDir);
              raycaster.far = 0.8; // Check 0.8 units ahead
              
              const hits = raycaster.intersectObjects(collisionMeshes, true);
              if (hits.length > 0 && hits[0].distance < minDistance) {
                minDistance = hits[0].distance;
                hitNormal = hits[0].face?.normal?.clone();
              }
            }
            
            if (minDistance < 0.5) {
              // Wall hit - implement wall sliding instead of stopping
              if (hitNormal) {
                // Transform normal to world space
                hitNormal.transformDirection(raycaster.intersectObjects(collisionMeshes, true)[0]?.object?.matrixWorld || new THREE.Matrix4());
                hitNormal.y = 0;
                hitNormal.normalize();
                
                // Project velocity onto the wall plane (slide along wall)
                const dot = playerVelocity.current.x * hitNormal.x + playerVelocity.current.z * hitNormal.z;
                newX = camera.position.x + (playerVelocity.current.x - hitNormal.x * dot) * delta * 0.5;
                newZ = camera.position.z + (playerVelocity.current.z - hitNormal.z * dot) * delta * 0.5;
              } else {
                // Fallback: just stop
                newX = camera.position.x;
                newZ = camera.position.z;
              }
              playerVelocity.current.x *= 0.3;
              playerVelocity.current.z *= 0.3;
            }
          }
        }
        
        // Secondary collision check after position update to prevent going through walls
        const finalCheckOrigin = new THREE.Vector3(newX, camera.position.y - 0.5, newZ);
        const directions = [
          new THREE.Vector3(1, 0, 0),
          new THREE.Vector3(-1, 0, 0),
          new THREE.Vector3(0, 0, 1),
          new THREE.Vector3(0, 0, -1)
        ];
        
        for (const dir of directions) {
          raycaster.set(finalCheckOrigin, dir);
          raycaster.far = 0.3;
          const hits = raycaster.intersectObjects(collisionMeshes, true);
          if (hits.length > 0 && hits[0].distance < 0.25) {
            // Too close to wall - push back
            newX -= dir.x * (0.25 - hits[0].distance);
            newZ -= dir.z * (0.25 - hits[0].distance);
          }
        }
        
        // Apply boundary collision (fallback)
        newX = Math.max(bounds.minX, Math.min(bounds.maxX, newX));
        newZ = Math.max(bounds.minZ, Math.min(bounds.maxZ, newZ));
        
        camera.position.x = newX;
        camera.position.z = newZ;
        
        // Raycast-based floor detection - only detect floor BELOW current position
        // This prevents jumping to upper floors
        let floorY = bounds.floorY;
        const currentFloorLevel = camera.position.y - PLAYER_HEIGHT;
        
        if (collisionMeshes.length > 0) {
          raycaster.set(
            new THREE.Vector3(camera.position.x, camera.position.y, camera.position.z),
            new THREE.Vector3(0, -1, 0)
          );
          raycaster.far = PLAYER_HEIGHT + 2; // Only check reasonable distance below
          
          const floorHits = raycaster.intersectObjects(collisionMeshes, true);
          
          // Find the highest floor that's BELOW current position
          for (const hit of floorHits) {
            // Only accept floors that are below us (with small tolerance for slopes)
            if (hit.point.y < camera.position.y - PLAYER_HEIGHT + 0.5) {
              floorY = hit.point.y;
              break; // Use the first (highest) floor below us
            }
          }
        }
        
        // Apply gravity and floor collision - smooth movement
        if (!playerOnGround.current) {
          playerVelocity.current.y -= GRAVITY * delta;
          // Cap falling speed
          playerVelocity.current.y = Math.max(playerVelocity.current.y, -15);
        }
        
        let newY = camera.position.y + playerVelocity.current.y * delta;
        const targetY = floorY + PLAYER_HEIGHT;
        
        if (newY <= targetY) {
          // Smooth landing
          camera.position.y = targetY;
          playerVelocity.current.y = 0;
          playerOnGround.current = true;
        } else if (newY > targetY + 0.1) {
          // In the air
          camera.position.y = Math.min(bounds.ceilingY, newY);
          playerOnGround.current = false;
        } else {
          // On ground, keep at floor level
          camera.position.y = targetY;
          playerOnGround.current = true;
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
          
          {/* AI Librarian - Luna */}
          <AILibrarian books={books} isVisible={true} />
        </>
      )}
    </div>
  );
}
