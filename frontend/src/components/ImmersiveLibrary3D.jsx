import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader';
import { Button } from '@/components/ui/button';
import { FiX, FiBook, FiBookOpen, FiMaximize2, FiMinimize2, FiVolume2, FiVolumeX, FiMapPin, FiMove, FiChevronUp, FiRotateCw, FiStar, FiBookmark, FiMessageCircle } from 'react-icons/fi';
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

// Genre sections - positions calibrated using debug mode clicks
// bannerPos is where the banner appears, shelfPos is where highlighted book appears
// position is where player spawns when teleporting to this section
const GENRE_SECTIONS = [
  // ORIGINAL LOCATIONS - Left side bookcases
  { 
    name: 'Fiction', 
    position: { x: -4.79, z: -1.35 }, 
    bannerPos: { x: -4.79, y: 6.5, z: -1.35 }, 
    shelfPos: { x: -4.5, y: 5.4, z: -1.35 }, 
    rotation: Math.PI / 2, 
    color: '#9333ea'
  },
  { 
    name: 'Adventure', 
    position: { x: -5.0, z: 0.42 }, 
    bannerPos: { x: -5.0, y: 6.5, z: 0.42 }, 
    shelfPos: { x: -4.7, y: 5.4, z: 0.42 }, 
    rotation: 0, 
    color: '#10b981'
  },
  { 
    name: 'Mystery', 
    position: { x: -4, z: -3 }, 
    bannerPos: { x: -4.79, y: 6.5, z: -3 }, 
    shelfPos: { x: -4.5, y: 5.4, z: -3 }, 
    rotation: Math.PI / 2, 
    color: '#3b82f6' 
  },
  { 
    name: 'Fantasy', 
    position: { x: -1.01, z: -8.12 }, 
    bannerPos: { x: -1.01, y: 5.7, z: -7.5 }, 
    shelfPos: { x: -1.01, y: 5.2, z: -7.2 }, 
    rotation: 0, 
    color: '#ec4899'
  },
  { 
    name: 'Comic', 
    position: { x: -3.41, z: -6.38 }, 
    bannerPos: { x: -2.5, y: 5.7, z: -6.5 }, 
    shelfPos: { x: -2.5, y: 5.2, z: -6.2 }, 
    rotation: 0, 
    color: '#f97316'
  },
  { 
    name: 'Science Fiction', 
    position: { x: -0.5, z: 4.5 }, 
    bannerPos: { x: -0.5, y: 5.87, z: 4.5 }, // Moved slightly away from bookcase
    shelfPos: { x: -0.5, y: 5.4, z: 4.5 }, 
    rotation: Math.PI, 
    color: '#06b6d4'
  },
  { 
    name: 'Humour', 
    position: { x: -3.41, z: 2.4 }, 
    bannerPos: { x: -3.41, y: 5.78, z: 2.4 }, // Moved away from wall
    shelfPos: { x: -3.41, y: 5.3, z: 2.4 }, 
    rotation: Math.PI, 
    color: '#f59e0b' 
  },
  // My Books section - shows user's created books
  { 
    name: 'My Books', 
    position: { x: -1.41, z: -1.43 }, 
    bannerPos: { x: -1.41, y: 3.54, z: -1.43 }, // User-specified location
    shelfPos: { x: -1.41, y: 3.1, z: -1.43 }, 
    rotation: 0, 
    color: '#8b5cf6',
    isPersonal: true // Flag to indicate this shows user's books
  },
  
  // NEW LOCATIONS - Right side bookcases (Ground Floor)
  { 
    name: 'Romance', 
    position: { x: 2.5, z: 4.0 }, 
    bannerPos: { x: 3.31, y: 5.2, z: 4.96 }, 
    shelfPos: { x: 3.0, y: 4.8, z: 4.96 }, 
    rotation: -Math.PI / 2, 
    color: '#f472b6' 
  },
  { 
    name: 'Biography', 
    position: { x: 2.0, z: 0.5 }, 
    bannerPos: { x: 2.57, y: 5.2, z: 1.16 }, 
    shelfPos: { x: 2.3, y: 4.8, z: 1.16 }, 
    rotation: -Math.PI / 2, 
    color: '#a78bfa' 
  },
  { 
    name: 'History', 
    position: { x: 2.0, z: -4.5 }, 
    bannerPos: { x: 2.61, y: 5.2, z: -4.01 }, // Raised to match Biography height
    shelfPos: { x: 2.3, y: 4.8, z: -4.01 }, 
    rotation: -Math.PI / 2, 
    color: '#78716c' 
  },
  
  // NEW LOCATIONS - Upper Floor (moved banners 20% out from bookcases + raised slightly)
  { 
    name: 'Horror', 
    position: { x: 0.0, z: 4.5 }, 
    bannerPos: { x: -0.87, y: 8.0, z: 4.9 }, // 20% move from z:5.26 toward 3.5, raised from 7.68 to 8.0
    shelfPos: { x: -0.87, y: 7.5, z: 4.9 }, 
    rotation: Math.PI, 
    color: '#dc2626' 
  },
  { 
    name: 'Non-Fiction', 
    position: { x: -2.5, z: 2.0 }, 
    bannerPos: { x: -3.1, y: 8.8, z: 2.7 }, // 20% move, raised from 8.57 to 8.8
    shelfPos: { x: -3.1, y: 8.3, z: 2.7 }, 
    rotation: Math.PI, 
    color: '#0891b2' 
  },
  { 
    name: 'Poetry', 
    position: { x: -0.5, z: -7.5 }, 
    bannerPos: { x: -1.05, y: 8.2, z: -7.8 }, // 20% move from z:-8.12 toward -6.5, raised from 7.89 to 8.2
    shelfPos: { x: -1.05, y: 7.7, z: -7.8 }, 
    rotation: 0, 
    color: '#d946ef' 
  },
  { 
    name: 'Drama', 
    position: { x: -2.5, z: -5.0 }, 
    bannerPos: { x: -2.85, y: 8.0, z: -5.5 }, // 20% move from z:-5.77 toward -4.5, raised from 7.71 to 8.0
    shelfPos: { x: -2.85, y: 7.5, z: -5.5 }, 
    rotation: 0, 
    color: '#0d9488' 
  },
];

// Teleport portals for moving between floors - near spiral staircases
// triggerPos.y = floor level for detection (0 for ground, 5.1 for upper)
// visualY = where to render the portal visually (on the stairs)
const TELEPORT_PORTALS = [
  // Back spiral staircase - "Go Upstairs" at bottom (ground floor)
  {
    id: 'stairs-up-back',
    name: 'Go Upstairs',
    triggerPos: { x: -1.60, y: 0, z: -6.01 }, // Detection at ground floor
    visualY: 4.18, // Visual position on stairs (original position)
    triggerRadius: 0.5,
    destPos: { x: -2.22, y: 5.1, z: -6.94 },
    destRotation: 0,
    color: '#00ffff',
    icon: '↑'
  },
  // Front spiral staircase - "Go Upstairs" at bottom (ground floor)
  {
    id: 'stairs-up-front',
    name: 'Go Upstairs',
    triggerPos: { x: -1.55, y: 0, z: 2.90 }, // Detection at ground floor
    visualY: 4.29, // Visual position on stairs (original position)
    triggerRadius: 0.5,
    destPos: { x: -2.23, y: 5.1, z: 4.03 },
    destRotation: Math.PI,
    color: '#00ffff',
    icon: '↑'
  },
  // Back spiral staircase - "Go Downstairs" at top (upper floor)
  {
    id: 'stairs-down-back',
    name: 'Go Downstairs',
    triggerPos: { x: -2.22, y: 5.1, z: -6.94 }, // Detection at upper floor
    visualY: 6.21, // Visual position at top of stairs (original position)
    triggerRadius: 0.5,
    destPos: { x: -1.60, y: 0, z: -6.01 },
    destRotation: Math.PI,
    color: '#00ffff',
    icon: '↓'
  },
  // Front spiral staircase - "Go Downstairs" at top (upper floor)
  {
    id: 'stairs-down-front',
    name: 'Go Downstairs',
    triggerPos: { x: -2.23, y: 5.1, z: 4.03 }, // Detection at upper floor
    visualY: 6.21, // Visual position at top of stairs (original position)
    triggerRadius: 0.5,
    destPos: { x: -1.55, y: 0, z: 2.90 },
    destRotation: 0,
    color: '#00ffff',
    icon: '↓'
  }
];

// Age range filter options for library search
const AGE_FILTER_OPTIONS = [
  { value: 'all', label: 'All Ages' },
  { value: '0-3', label: '0-3 years' },
  { value: '4-6', label: '4-6 years' },
  { value: '7-9', label: '7-9 years' },
  { value: '10-12', label: '10-12 years' },
  { value: '13+', label: '13+ years' },
];

// Map age_rating values to filter categories
const matchesAgeFilter = (bookAgeRating, filterValue) => {
  if (filterValue === 'all') return true;
  
  const rating = bookAgeRating || 'All Ages';
  
  // Map book age ratings to filter categories
  const ageMap = {
    'All Ages': ['all', '0-3', '4-6', '7-9', '10-12', '13+'],
    '5+': ['4-6', '7-9', '10-12', '13+'],
    '8+': ['7-9', '10-12', '13+'],
    '12+': ['10-12', '13+'],
    '16+': ['13+'],
  };
  
  const allowedFilters = ageMap[rating] || ['all'];
  return allowedFilters.includes(filterValue);
};

// Interactive 3D Book Model URL - served from public folder to avoid CORS issues
const ANIMATED_BOOK_GLB_URL = '/animated_book.glb';

// Detect mobile/tablet device - includes iPad detection
const isMobile = () => {
  if (typeof window === 'undefined') return false;
  
  // Check for touch capability first (covers most tablets)
  const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  
  // User agent check for mobile devices
  const mobileUA = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  
  // iPad-specific detection (iPadOS 13+ reports as desktop Safari)
  const isIPad = (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1) || 
                 /iPad/i.test(navigator.userAgent);
  
  // Screen size check for tablets
  const isTabletSize = window.innerWidth >= 768 && window.innerWidth <= 1366 && hasTouch;
  
  return mobileUA || isIPad || isTabletSize || (hasTouch && window.innerWidth < 1024);
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
  const genreBannersRef = useRef([]); // Store banner sprites for click detection
  const highlightedBookModelRef = useRef(null); // The actual 3D model
  const highlightedBookMixerRef = useRef(null); // Animation mixer for highlighted book
  const gltfLoaderRef = useRef(null); // Shared GLTF loader
  const teleportPortalsRef = useRef([]); // Teleport portal meshes
  
  // Teleport portal state
  const [nearPortal, setNearPortal] = useState(null); // Portal player is near
  const lastTeleportTime = useRef(0); // Prevent rapid re-teleporting
  
  // Physics constants - realistic eye level for library scale
  const PLAYER_HEIGHT = 1.1; // Lower eye level for better immersion in scaled library
  const MOVE_SPEED = 3;
  
  // Azora (AI assistant) state
  const [azoraPosition, setAzoraPosition] = useState({ x: 2, z: 0 }); // Center of room
  const [isAzoraComing, setIsAzoraComing] = useState(false);
  const [showAzoraChat, setShowAzoraChat] = useState(false);
  const [selectedBook, setSelectedBook] = useState(null); // For book info card
  const [selectedGenre, setSelectedGenre] = useState(null); // For genre book list panel
  const [highlightedBookGenre, setHighlightedBookGenre] = useState(null); // Track which genre has highlighted book
  const [ageFilter, setAgeFilter] = useState('all'); // Age filter for library: 'all', '0-3', '4-6', '7-9', '10-12', '13+'
  
  const [isLoaded, setIsLoaded] = useState(false);
  const [loadProgress, setLoadProgress] = useState(0);
  const [loadError, setLoadError] = useState(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isMuted, setIsMuted] = useState(true);
  const [isExploring, setIsExploring] = useState(false);
  const isExploringRef = useRef(false); // Ref to access in animation loop without triggering re-render
  const [showGenreMenu, setShowGenreMenu] = useState(false);
  const [isMobileDevice] = useState(isMobile());
  const [hoveredBook, setHoveredBook] = useState(null);
  const [savedPositions, setSavedPositions] = useState([]);
  const [showBookPanel, setShowBookPanel] = useState(true);
  const [debugMode, setDebugMode] = useState(false);
  const [debugCoords, setDebugCoords] = useState(null);
  
  // Mobile touch state
  const touchStartRef = useRef({ x: 0, y: 0 });
  const touchMoveRef = useRef({ active: false, x: 0, y: 0 });
  const joystickRef = useRef({ active: false, angle: 0, distance: 0 });
  const [joystickPos, setJoystickPos] = useState({ x: 0, y: 0 }); // For rendering joystick knob
  
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
    if (!isExploringRef.current) return;
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
  }, []);

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
    if (isDragging.current && isExploringRef.current) {
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
  }, []);

  // Mouse down - start drag look
  const onMouseDown = useCallback((event) => {
    if (!isExploringRef.current || isMobileDevice) return;
    // Right click or left click to drag
    isDragging.current = true;
    lastMousePos.current = { x: event.clientX, y: event.clientY };
    setShowClickHint(false);
  }, [isMobileDevice]);

  // Mouse up - stop drag look
  const onMouseUp = useCallback(() => {
    isDragging.current = false;
  }, []);

  // Pointer lock handlers
  const requestPointerLock = useCallback(() => {
    if (canvasRef.current && isExploringRef.current) {
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
      console.log('Cannot request pointer lock - canvas:', !!canvasRef.current, 'exploring:', isExploringRef.current);
    }
  }, []);

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

  // Teleport to genre section - use stored floor level and face the bookcase
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
    
    // Set camera rotation to face the bookcase
    euler.current.set(0, section.rotation, 0);
    cameraRef.current.quaternion.setFromEuler(euler.current);
    
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

  // Teleport using a portal
  const activatePortal = useCallback((portal) => {
    if (!cameraRef.current || !portal) return;
    
    // Prevent rapid re-teleporting (1 second cooldown)
    const now = Date.now();
    if (now - lastTeleportTime.current < 1000) return;
    lastTeleportTime.current = now;
    
    // Teleport to destination (PLAYER_HEIGHT = 1.1)
    const destY = portal.destPos.y + 1.1;
    cameraRef.current.position.set(portal.destPos.x, destY, portal.destPos.z);
    
    // Set rotation if specified
    if (portal.destRotation !== undefined) {
      euler.current.set(0, portal.destRotation, 0);
      cameraRef.current.quaternion.setFromEuler(euler.current);
    }
    
    // Reset velocity
    playerVelocity.current.set(0, 0, 0);
    
    // Clear the near portal state
    setNearPortal(null);
  }, []);

  // Remove the highlighted book from the scene
  const removeHighlightedBook = useCallback(() => {
    if (highlightedBookModelRef.current && sceneRef.current) {
      sceneRef.current.remove(highlightedBookModelRef.current);
      highlightedBookModelRef.current = null;
    }
    if (highlightedBookMixerRef.current) {
      highlightedBookMixerRef.current.stopAllAction();
      highlightedBookMixerRef.current = null;
    }
    setHighlightedBookGenre(null);
  }, []);

  // Highlight a book on the shelf for a specific genre - uses animated GLB
  // Now positions the book in front of camera and applies cover texture
  const highlightBookAtGenre = useCallback((genreName, book) => {
    if (!sceneRef.current || !cameraRef.current) {
      console.log('Scene or camera not ready, cannot highlight book');
      return;
    }
    
    // Find the genre section (for color)
    const section = GENRE_SECTIONS.find(s => s.name.toLowerCase() === genreName.toLowerCase());
    const bookColor = section?.color || '#ec4899';
    
    console.log('Highlighting book:', book.title, 'genre:', genreName);
    
    // Remove existing highlighted book and stop animation
    if (highlightedBookModelRef.current) {
      sceneRef.current.remove(highlightedBookModelRef.current);
      highlightedBookModelRef.current = null;
    }
    if (highlightedBookMixerRef.current) {
      highlightedBookMixerRef.current.stopAllAction();
      highlightedBookMixerRef.current = null;
    }
    
    // Create a fresh loader for the animated book
    const bookDracoLoader = new DRACOLoader();
    bookDracoLoader.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.6/');
    
    const bookLoader = new GLTFLoader();
    bookLoader.setDRACOLoader(bookDracoLoader);
    
    console.log('Loading animated book from:', ANIMATED_BOOK_GLB_URL);
    
    bookLoader.load(
      ANIMATED_BOOK_GLB_URL,
      (gltf) => {
        console.log('Animated book loaded successfully!', gltf);
        
        if (!sceneRef.current || !cameraRef.current) return;
        
        const bookModel = gltf.scene;
        const camera = cameraRef.current;
        
        // Position the book in front of the camera (centered in view)
        const distanceFromCamera = 0.8; // Closer to camera
        const forward = new THREE.Vector3(0, 0, -1);
        forward.applyQuaternion(camera.quaternion);
        
        const bookPosition = new THREE.Vector3()
          .copy(camera.position)
          .add(forward.multiplyScalar(distanceFromCamera));
        
        // Lower than eye level
        bookPosition.y = camera.position.y - 0.35;
        
        bookModel.position.copy(bookPosition);
        
        // Scale the book - smaller
        bookModel.scale.setScalar(0.08);
        
        // Make the book upright and facing camera (not tilted)
        // Get camera's Y rotation only for horizontal facing
        const cameraDirection = new THREE.Vector3(0, 0, -1);
        cameraDirection.applyQuaternion(camera.quaternion);
        const angle = Math.atan2(cameraDirection.x, cameraDirection.z);
        
        bookModel.rotation.set(0, angle + Math.PI, 0); // Upright, facing camera
        
        // Store book data
        bookModel.userData = {
          isHighlightedBook: true,
          bookId: book.id,
          bookData: book
        };
        
        // Try to apply book cover texture
        if (book.cover_image) {
          const textureLoader = new THREE.TextureLoader();
          textureLoader.load(book.cover_image, (coverTexture) => {
            coverTexture.colorSpace = THREE.SRGBColorSpace;
            coverTexture.flipY = false;
            
            // Apply to meshes that might be the cover
            bookModel.traverse((child) => {
              if (child.isMesh) {
                const meshName = (child.name || '').toLowerCase();
                if (meshName.includes('cover') || meshName.includes('front') || 
                    meshName.includes('face') || meshName.includes('page')) {
                  child.material = child.material.clone();
                  child.material.map = coverTexture;
                  child.material.needsUpdate = true;
                  console.log('Applied cover texture to:', child.name);
                }
              }
            });
          });
        }
        
        // Make meshes clickable and add glow
        bookModel.traverse((child) => {
          if (child.isMesh) {
            child.userData = bookModel.userData;
            bookMeshesRef.current.push(child);
            
            if (child.material) {
              child.material = child.material.clone();
              child.material.emissive = new THREE.Color(bookColor);
              child.material.emissiveIntensity = 0.2;
            }
          }
        });
        
        // Setup animation
        if (gltf.animations && gltf.animations.length > 0) {
          const mixer = new THREE.AnimationMixer(bookModel);
          highlightedBookMixerRef.current = mixer;
          
          gltf.animations.forEach((clip) => {
            const action = mixer.clipAction(clip);
            action.setLoop(THREE.LoopOnce);
            action.clampWhenFinished = true;
            action.play();
          });
        }
        
        sceneRef.current.add(bookModel);
        highlightedBookModelRef.current = bookModel;
        setHighlightedBookGenre(genreName);
        console.log('Book positioned in front of camera:', book.title);
      },
      (progress) => {
        if (progress.total) {
          console.log('Loading book...', Math.round((progress.loaded / progress.total) * 100) + '%');
        }
      },
      (error) => {
        console.error('Error loading book GLB:', error);
        
        if (!sceneRef.current || !cameraRef.current) return;
        
        // Fallback - simple book box with cover texture in front of camera
        const camera = cameraRef.current;
        const forward = new THREE.Vector3(0, 0, -1);
        forward.applyQuaternion(camera.quaternion);
        
        const bookPosition = new THREE.Vector3()
          .copy(camera.position)
          .add(forward.multiplyScalar(0.8));
        bookPosition.y = camera.position.y - 0.35;
        
        // Get camera's Y rotation for facing
        const cameraDirection = new THREE.Vector3(0, 0, -1);
        cameraDirection.applyQuaternion(camera.quaternion);
        const angle = Math.atan2(cameraDirection.x, cameraDirection.z);
        
        const bookGeometry = new THREE.BoxGeometry(0.25, 0.35, 0.04);
        
        let materials;
        if (book.cover_image) {
          const textureLoader = new THREE.TextureLoader();
          const coverTexture = textureLoader.load(book.cover_image);
          coverTexture.colorSpace = THREE.SRGBColorSpace;
          
          const sideMat = new THREE.MeshStandardMaterial({ color: bookColor });
          const coverMat = new THREE.MeshStandardMaterial({ map: coverTexture });
          materials = [sideMat, sideMat, sideMat, sideMat, coverMat, sideMat];
        } else {
          materials = new THREE.MeshStandardMaterial({
            color: new THREE.Color(bookColor),
            emissive: new THREE.Color(bookColor),
            emissiveIntensity: 0.3
          });
        }
        
        const bookMesh = new THREE.Mesh(bookGeometry, materials);
        bookMesh.position.copy(bookPosition);
        bookMesh.rotation.set(0, angle + Math.PI, 0); // Upright, facing camera
        bookMesh.userData = { isHighlightedBook: true, bookId: book.id, bookData: book };
        
        sceneRef.current.add(bookMesh);
        highlightedBookModelRef.current = bookMesh;
        bookMeshesRef.current.push(bookMesh);
        setHighlightedBookGenre(genreName);
      }
    );
  }, []);

  // Mobile touch handlers
  const onTouchStart = useCallback((e) => {
    if (!isExploringRef.current || !isMobileDevice) return;
    
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
  }, [isMobileDevice]);

  const onTouchMove = useCallback((e) => {
    if (!isExploringRef.current || !isMobileDevice) return;
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
    
    // Look around - ANYWHERE on screen (not just right side)
    // This makes it easier to look around on mobile
    if (touchMoveRef.current.active && cameraRef.current) {
      const movementX = touch.clientX - touchStartRef.current.x;
      const movementY = touch.clientY - touchStartRef.current.y;
      
      euler.current.setFromQuaternion(cameraRef.current.quaternion);
      // Increased sensitivity from 0.003 to 0.008 for faster panning
      euler.current.y -= movementX * 0.008;
      euler.current.x -= movementY * 0.008;
      euler.current.x = Math.max(-Math.PI / 2 + 0.1, Math.min(Math.PI / 2 - 0.1, euler.current.x));
      cameraRef.current.quaternion.setFromEuler(euler.current);
      
      touchStartRef.current = { x: touch.clientX, y: touch.clientY };
    }
  }, [isMobileDevice]);

  const onTouchEnd = useCallback(() => {
    joystickRef.current = { active: false, angle: 0, distance: 0 };
    touchMoveRef.current = { active: false, x: 0, y: 0 };
    keysPressed.current = { forward: false, backward: false, left: false, right: false };
  }, []);

  // Click on book in 3D - show info card first
  // Also handles DEBUG MODE - logs click coordinates
  const onCanvasClick = useCallback((e) => {
    if (!isExploringRef.current || !cameraRef.current) return;
    if (isPointerLocked.current) return; // Don't process clicks when pointer is locked
    
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    const mouse = new THREE.Vector2(
      ((e.clientX - rect.left) / rect.width) * 2 - 1,
      -((e.clientY - rect.top) / rect.height) * 2 + 1
    );
    
    raycasterRef.current.setFromCamera(mouse, cameraRef.current);
    
    // DEBUG MODE: Log click coordinates on any mesh
    if (debugMode) {
      const allMeshes = collisionMeshesRef.current;
      raycasterRef.current.far = 100; // Long range for debug clicks
      const hits = raycasterRef.current.intersectObjects(allMeshes, true);
      
      if (hits.length > 0) {
        const hit = hits[0];
        const coords = {
          x: hit.point.x.toFixed(2),
          y: hit.point.y.toFixed(2),
          z: hit.point.z.toFixed(2),
          meshName: hit.object.name || 'unnamed'
        };
        console.log('🎯 DEBUG CLICK:', coords);
        setDebugCoords(coords);
        return; // Don't process book clicks in debug mode
      }
    }
    
    // Check for genre banner clicks first
    if (genreBannersRef.current.length > 0) {
      raycasterRef.current.far = 50;
      const bannerHits = raycasterRef.current.intersectObjects(genreBannersRef.current, true);
      
      if (bannerHits.length > 0) {
        const banner = bannerHits[0].object;
        const genreName = banner.userData?.genreName;
        if (genreName) {
          console.log('Clicked genre banner:', genreName);
          setSelectedGenre(genreName);
          return;
        }
      }
    }
    
    if (isMobileDevice) return; // Skip book click handling on mobile
    
    // Check for Azora click first
    if (azoraRef.current) {
      const azoraHits = raycasterRef.current.intersectObject(azoraRef.current, true);
      if (azoraHits.length > 0) {
        // Clicked on Azora - show chat
        setShowAzoraChat(true);
        return;
      }
    }
    
    // Then check for book clicks - also start rotation if clicking on highlighted book
    const hits = raycasterRef.current.intersectObjects(bookMeshesRef.current, true);
    
    if (hits.length > 0) {
      const bookMesh = hits[0].object;
      console.log('Clicked on book mesh:', bookMesh.userData);
      
      // Use bookData from userData if available (for 3D book models)
      if (bookMesh.userData?.bookData) {
        setSelectedBook(bookMesh.userData.bookData);
        return;
      }
      
      // Fallback: find by bookId
      const bookId = bookMesh.userData?.bookId;
      if (bookId) {
        const bookData = books.find(b => b.id === bookId);
        if (bookData) {
          setSelectedBook(bookData);
        }
      }
    }
  }, [isMobileDevice, books, debugMode]);

  // Initialize Three.js scene
  useEffect(() => {
    if (!canvasRef.current) return;

    let mounted = true;

    // Create scene with warm library atmosphere
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x2a1a1f); // Dark warm brown (distinct from loading screen purple)
    sceneRef.current = scene;
    
    console.log('Scene created with background color');

    // Create camera - first person perspective
    const camera = new THREE.PerspectiveCamera(
      75,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    camera.position.set(0, PLAYER_HEIGHT, 5);
    cameraRef.current = camera;

    // Check if mobile/tablet for performance optimizations
    const isMobileDevice = isMobile();
    const isLowPowerDevice = isMobileDevice || window.navigator.hardwareConcurrency <= 4;

    // Create renderer with mobile-optimized settings
    const renderer = new THREE.WebGLRenderer({
      canvas: canvasRef.current,
      antialias: !isMobileDevice, // Disable antialiasing on mobile for performance
      powerPreference: 'high-performance',
      precision: isMobileDevice ? 'mediump' : 'highp', // Lower precision on mobile
    });
    renderer.setSize(window.innerWidth, window.innerHeight);
    // Lower pixel ratio on mobile/tablet for better performance
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, isMobileDevice ? 1.5 : 2));
    // Disable shadows on mobile for better performance
    renderer.shadowMap.enabled = !isMobileDevice;
    if (!isMobileDevice) {
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    }
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.5;
    rendererRef.current = renderer;

    // Add warm library lighting (reduced on mobile)
    const ambientLight = new THREE.AmbientLight(0xfff5e6, isMobileDevice ? 0.8 : 0.6);
    scene.add(ambientLight);

    const mainLight = new THREE.DirectionalLight(0xffffff, 0.8);
    mainLight.position.set(0, 20, 10);
    mainLight.castShadow = !isMobileDevice; // Disable shadow casting on mobile
    scene.add(mainLight);

    // Warm point lights like candles/lamps (fewer on mobile)
    const warmLightPositions = isMobileDevice 
      ? [[0, 8, 0], [-5, 4, 0], [5, 4, 0]] // 3 lights on mobile
      : [[0, 8, 0], [-5, 4, -5], [5, 4, -5], [-5, 4, 5], [5, 4, 5]]; // 5 lights on desktop
    warmLightPositions.forEach(pos => {
      const light = new THREE.PointLight(0xffaa55, isMobileDevice ? 1.2 : 1.5, 20);
      light.position.set(pos[0], pos[1], pos[2]);
      scene.add(light);
    });

    // Hemisphere light for natural feel
    const hemiLight = new THREE.HemisphereLight(0xffeedd, 0x222211, 0.5);
    scene.add(hemiLight);
    
    // Create teleport portal visuals - glowing blue oval portals with strong glow
    const portalMeshes = [];
    const portalTextureUrl = 'https://customer-assets.emergentagent.com/job_5fcf9a60-2eef-4bf3-9095-3ed240f84fb7/artifacts/nlouqrje_360_F_318019685_EV3M47BKGuK3iFG5cOQmVjPy15bc7CkC.jpg';
    const textureLoader = new THREE.TextureLoader();
    
    TELEPORT_PORTALS.forEach(portal => {
      // Use visualY for rendering, triggerPos.y for detection
      const renderY = portal.visualY !== undefined ? portal.visualY : portal.triggerPos.y;
      
      // Create a smaller vertical oval plane for the portal (70% smaller)
      const portalGeometry = new THREE.PlaneGeometry(0.42, 0.6); // 70% smaller: 1.4*0.3, 2.0*0.3
      
      textureLoader.load(portalTextureUrl, (texture) => {
        const portalMaterial = new THREE.MeshBasicMaterial({
          map: texture,
          transparent: true,
          side: THREE.DoubleSide,
          opacity: 0.9
        });
        const portalMesh = new THREE.Mesh(portalGeometry, portalMaterial);
        portalMesh.position.set(portal.triggerPos.x, renderY + 0.4, portal.triggerPos.z);
        portalMesh.userData = { isPortal: true, portalData: portal };
        scene.add(portalMesh);
        portalMeshes.push(portalMesh);
      });
      
      // Add lights for glow effect (smaller range)
      const portalLight1 = new THREE.PointLight(0x00ffff, 1.5, 3);
      portalLight1.position.set(portal.triggerPos.x, renderY + 0.4, portal.triggerPos.z);
      scene.add(portalLight1);
      
      // Add a smaller, thinner glowing ring on the floor around the portal
      const ringGeometry = new THREE.RingGeometry(0.2, 0.25, 32); // Much smaller and thinner
      const ringMaterial = new THREE.MeshBasicMaterial({
        color: 0x00ffff,
        transparent: true,
        opacity: 0.5,
        side: THREE.DoubleSide
      });
      const ringMesh = new THREE.Mesh(ringGeometry, ringMaterial);
      ringMesh.rotation.x = -Math.PI / 2;
      ringMesh.position.set(portal.triggerPos.x, renderY + 0.05, portal.triggerPos.z);
      ringMesh.userData = { isPortalRing: true };
      scene.add(ringMesh);
    });
    teleportPortalsRef.current = portalMeshes;

    // Load the GLB model
    const dracoLoader = new DRACOLoader();
    dracoLoader.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.6/');
    
    const gltfLoader = new GLTFLoader();
    gltfLoader.setDRACOLoader(dracoLoader);
    
    // Store the loader reference for use in highlighting books
    gltfLoaderRef.current = gltfLoader;

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
        
        // Position camera at user-specified coordinates
        // User coordinates: X: -1.13, Y: 4.72, Z: -0.84 (click on Floor002)
        const startX = -1.13;
        const startZ = -0.84;
        camera.position.set(startX, startY, startZ);
        console.log('Camera positioned at:', startX, startY, startZ);
        
        // Set initial camera rotation - 80 degrees to the left (anticlockwise)
        // 80 degrees = 80 * (Math.PI / 180) ≈ 1.396 radians
        euler.current.set(-0.2, 1.396, 0, 'YXZ'); // Tilt down slightly, rotated 80° left
        camera.quaternion.setFromEuler(euler.current);
        console.log('Camera rotated 80° anticlockwise');
        
        // Initialize empty book meshes array - books are loaded on demand when selected
        const bookMeshes = [];
        bookMeshesRef.current = bookMeshes;
        
        // Add genre text banners floating above each bookcase
        // Height matches the Adventure banner visible in screenshot
        const bannerHeight = floorLevel + 2.2; // Just above bookcase tops
        const genreBanners = [];
        
        GENRE_SECTIONS.forEach((section) => {
          // Create text sprite for the banner
          const canvas = document.createElement('canvas');
          canvas.width = 512;
          canvas.height = 128;
          const ctx = canvas.getContext('2d');
          
          // Clear canvas with transparency
          ctx.clearRect(0, 0, 512, 128);
          
          // Glowing text effect
          ctx.font = 'bold 56px Georgia, serif';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          
          // Outer glow
          ctx.shadowColor = section.color;
          ctx.shadowBlur = 25;
          ctx.fillStyle = section.color;
          ctx.fillText(section.name, 256, 64);
          
          // Inner text (white)
          ctx.shadowBlur = 10;
          ctx.fillStyle = '#ffffff';
          ctx.fillText(section.name, 256, 64);
          
          const texture = new THREE.CanvasTexture(canvas);
          texture.colorSpace = THREE.SRGBColorSpace;
          
          // Use sprite for always-facing-camera text
          const spriteMaterial = new THREE.SpriteMaterial({
            map: texture,
            transparent: true,
            depthWrite: false
          });
          
          const sprite = new THREE.Sprite(spriteMaterial);
          sprite.scale.set(1.6, 0.4, 1); // Smaller banners to avoid wall intersection
          
          // Use explicit Y from bannerPos if available, otherwise use default bannerHeight
          const bannerY = section.bannerPos.y !== undefined ? section.bannerPos.y : bannerHeight;
          
          sprite.position.set(section.bannerPos.x, bannerY, section.bannerPos.z);
          
          // Store genre name for click detection
          sprite.userData = { 
            isGenreBanner: true, 
            genreName: section.name,
            baseY: bannerY,
            phase: Math.random() * Math.PI * 2 
          };
          
          scene.add(sprite);
          genreBanners.push(sprite);
          
          // Add "Click to browse" hint below the banner - closer and triangle pointing up
          const hintCanvas = document.createElement('canvas');
          hintCanvas.width = 256;
          hintCanvas.height = 64;
          const hintCtx = hintCanvas.getContext('2d');
          hintCtx.clearRect(0, 0, 256, 64);
          hintCtx.font = '20px Arial';
          hintCtx.textAlign = 'center';
          hintCtx.textBaseline = 'middle';
          hintCtx.fillStyle = 'rgba(255,255,255,0.6)';
          hintCtx.fillText('▲ Click to browse', 128, 32);
          
          const hintTexture = new THREE.CanvasTexture(hintCanvas);
          const hintSprite = new THREE.Sprite(new THREE.SpriteMaterial({
            map: hintTexture,
            transparent: true,
            depthWrite: false
          }));
          hintSprite.scale.set(0.8, 0.2, 1);
          hintSprite.position.set(section.bannerPos.x, bannerY - 0.25, section.bannerPos.z); // Closer to banner
          hintSprite.userData = { 
            isGenreBanner: true, 
            genreName: section.name,
            baseY: bannerY - 0.25,
            phase: sprite.userData.phase
          };
          scene.add(hintSprite);
          genreBanners.push(hintSprite);
          
          console.log('Added genre banner:', section.name, 'at', section.bannerPos.x, bannerY, section.bannerPos.z, section.calibrated ? '(calibrated)' : '(estimated)');
        });
        
        genreBannersRef.current = genreBanners;
        
        // Azora is disabled for now - will be re-enabled once positioning is calibrated
        console.log('Azora disabled - needs positioning calibration');
        
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
      
      // Use ref instead of state to avoid re-render dependency issues
      if (isExploringRef.current && cameraRef.current) {
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
        
        // ENHANCED wall collision with better stair detection
        // Cast rays at multiple heights to detect stairs vs walls
        const COLLISION_RADIUS = 0.4;
        
        if (collisionMeshes.length > 0 && (playerVelocity.current.x !== 0 || playerVelocity.current.z !== 0)) {
          const moveDir = new THREE.Vector3(
            playerVelocity.current.x,
            0,
            playerVelocity.current.z
          ).normalize();
          
          // Cast rays at multiple heights - knee, waist, and chest level
          // This helps detect stairs at different points
          const rayHeights = [
            camera.position.y - PLAYER_HEIGHT + 0.2,  // Near floor (20cm up)
            camera.position.y - PLAYER_HEIGHT + 0.5,  // Knee level
            camera.position.y - 0.3                    // Chest level
          ];
          
          let blocked = false;
          let stairDetected = false;
          
          for (const rayY of rayHeights) {
            const rayOrigin = new THREE.Vector3(camera.position.x, rayY, camera.position.z);
            
            raycaster.set(rayOrigin, moveDir);
            raycaster.far = COLLISION_RADIUS + 0.3;
            
            const hits = raycaster.intersectObjects(collisionMeshes, true);
            
            if (hits.length > 0 && hits[0].distance < COLLISION_RADIUS + 0.1) {
              const hitMesh = hits[0].object.name?.toLowerCase() || '';
              // Check if it's a stair, ramp, or floor segment
              const isClimbable = hitMesh.includes('stair') || hitMesh.includes('plane05') || 
                                  hitMesh.includes('plane06') || hitMesh.includes('ramp') ||
                                  hitMesh.includes('step') || hitMesh.includes('floor') ||
                                  hitMesh.includes('spiral') || hitMesh.includes('stone') ||
                                  hitMesh.includes('climb');
              
              if (isClimbable) {
                stairDetected = true;
              } else if (rayY > camera.position.y - PLAYER_HEIGHT + 0.5) {
                // Only consider it a wall block at waist level or higher (more permissive)
                blocked = true;
              }
            }
          }
          
          // If we detected climbable surface, allow passage (floor detection handles climbing)
          // Only block if we hit a real wall at waist/chest level without any stairs nearby
          if (blocked && !stairDetected) {
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
        
        // Floor detection with downward raycast - realistic walking with spiral stair support
        const baseFloorY = bounds.floorY || 0;
        const currentFootY = camera.position.y - PLAYER_HEIGHT;
        let detectedFloorY = currentFootY; // Default to staying at current level
        
        if (collisionMeshes.length > 0) {
          // Cast rays in a pattern around and ahead of the player for stair detection
          // More rays = better stair detection on spiral staircases
          const isMoving = playerVelocity.current.x !== 0 || playerVelocity.current.z !== 0;
          const moveDir = isMoving 
            ? new THREE.Vector3(playerVelocity.current.x, 0, playerVelocity.current.z).normalize()
            : new THREE.Vector3(0, 0, -1);
          
          // Get perpendicular direction for side rays
          const sideDir = new THREE.Vector3().crossVectors(new THREE.Vector3(0, 1, 0), moveDir).normalize();
          
          // Multiple ray start heights - cast from higher up to better detect stairs in front
          const rayHeights = [camera.position.y + 0.3, camera.position.y + 1.0];
          
          const rayPositions = [];
          
          for (const rayY of rayHeights) {
            // Center ray
            rayPositions.push(new THREE.Vector3(camera.position.x, rayY, camera.position.z));
            
            // Add forward rays when moving (for stair climbing detection)
            if (isMoving) {
              // Forward rays at different distances
              rayPositions.push(new THREE.Vector3(
                camera.position.x + moveDir.x * 0.3,
                rayY,
                camera.position.z + moveDir.z * 0.3
              ));
              rayPositions.push(new THREE.Vector3(
                camera.position.x + moveDir.x * 0.6,
                rayY,
                camera.position.z + moveDir.z * 0.6
              ));
              // Forward-side rays for spiral stairs
              rayPositions.push(new THREE.Vector3(
                camera.position.x + moveDir.x * 0.3 + sideDir.x * 0.2,
                rayY,
                camera.position.z + moveDir.z * 0.3 + sideDir.z * 0.2
              ));
              rayPositions.push(new THREE.Vector3(
                camera.position.x + moveDir.x * 0.3 - sideDir.x * 0.2,
                rayY,
                camera.position.z + moveDir.z * 0.3 - sideDir.z * 0.2
              ));
            }
          }
          
          let bestFloorY = null;
          let detectedStairMesh = null;
          
          for (const rayPos of rayPositions) {
            raycaster.set(rayPos, new THREE.Vector3(0, -1, 0));
            raycaster.far = PLAYER_HEIGHT + 3; // Extended range for tall stairs
            
            const floorHits = raycaster.intersectObjects(collisionMeshes, true);
            
            for (const hit of floorHits) {
              const hitY = hit.point.y;
              const meshName = hit.object.name?.toLowerCase() || '';
              
              // Check if this is a stair mesh - allow higher step-up for stairs
              const isStair = meshName.includes('stair') || meshName.includes('plane05') || 
                              meshName.includes('plane06') || meshName.includes('step') ||
                              meshName.includes('ramp') || meshName.includes('spiral') ||
                              meshName.includes('stone') || meshName.includes('climb');
              const isFloor = meshName.includes('floor');
              
              // More generous step-up for stairs and when moving
              const maxStepUp = isStair ? 2.0 : (isFloor ? 1.0 : 0.8);
              const maxStepDown = 4.0; // Allow dropping down further
              
              if (hitY <= currentFootY + maxStepUp && hitY >= currentFootY - maxStepDown) {
                // Prioritization logic to prevent sinking:
                // 1. Prefer surfaces close to and slightly ABOVE current foot (within 0.5m)
                // 2. For stairs, allow higher step-up
                // 3. Only go down if no higher surface found
                
                const isAboveAndClose = hitY >= currentFootY - 0.1 && hitY <= currentFootY + 0.5;
                const isStairClimb = isStair && hitY > currentFootY && hitY <= currentFootY + maxStepUp;
                
                if (bestFloorY === null) {
                  bestFloorY = hitY;
                  if (isStair) detectedStairMesh = meshName;
                } else if (isStairClimb && hitY > bestFloorY) {
                  // Climbing stairs - take higher step
                  bestFloorY = hitY;
                  detectedStairMesh = meshName;
                } else if (isAboveAndClose && hitY > bestFloorY) {
                  // Surface close to current level and above - prefer this (prevents sinking)
                  bestFloorY = hitY;
                } else if (bestFloorY < currentFootY - 1.0 && hitY > bestFloorY) {
                  // Current best is way below us, prefer anything higher
                  bestFloorY = hitY;
                }
              }
            }
          }
          
          if (bestFloorY !== null) {
            detectedFloorY = bestFloorY;
          }
        }
        
        const targetY = detectedFloorY + PLAYER_HEIGHT;
        
        // Smoothly interpolate to target height - faster for climbing stairs
        const yDiff = targetY - camera.position.y;
        if (Math.abs(yDiff) > 0.01) {
          // Use faster interpolation when climbing (positive diff) vs descending
          const isClimbing = yDiff > 0;
          // Much faster interpolation for stair climbing to feel responsive
          const interpSpeed = isClimbing ? 0.5 : 0.25; // 50% per frame when climbing
          camera.position.y += yDiff * interpSpeed;
        }
        
        playerOnGround.current = true;
        playerVelocity.current.y = 0;
        
        // Check for teleport portal proximity
        const currentTime = Date.now();
        let foundPortal = null;
        const playerFootY = camera.position.y - PLAYER_HEIGHT;
        
        for (const portal of TELEPORT_PORTALS) {
          const dx = camera.position.x - portal.triggerPos.x;
          const dz = camera.position.z - portal.triggerPos.z;
          const horizontalDist = Math.sqrt(dx * dx + dz * dz);
          
          // Strict floor check: player must be on the same floor as the portal
          // Ground floor: y < 3, Upper floor: y >= 3
          const portalIsGroundFloor = portal.triggerPos.y < 3;
          const playerIsGroundFloor = playerFootY < 3;
          const sameFloor = portalIsGroundFloor === playerIsGroundFloor;
          
          // Only show portal if on same floor AND within horizontal range
          if (sameFloor && horizontalDist < portal.triggerRadius) {
            foundPortal = portal;
            break;
          }
        }
        
        // Update portal state (throttled to prevent rapid updates)
        if (foundPortal !== nearPortal) {
          setNearPortal(foundPortal);
        }
      }
      
      // Update highlighted book animation mixer
      if (highlightedBookMixerRef.current) {
        highlightedBookMixerRef.current.update(delta);
      }
      
      // Animate floating genre banners (if any enabled)
      const time = Date.now() * 0.001;
      scene.traverse((child) => {
        if (child.userData?.isGenreBanner) {
          child.position.y = child.userData.baseY + Math.sin(time + child.userData.phase) * 0.1;
        }
        // Pulsing glow for highlighted book meshes
        if (child.userData?.isHighlightedBook && child.material) {
          const pulse = 0.3 + Math.sin(time * 2) * 0.2;
          child.material.emissiveIntensity = pulse;
        }
        // Animate portal arrows (bobbing)
        if (child.userData?.isPortalArrow) {
          child.position.y = child.userData.baseY + Math.sin(time * 2) * 0.2;
        }
        // Pulse and rotate portal meshes
        if (child.userData?.isPortal && child.material) {
          child.material.opacity = 0.8 + Math.sin(time * 3) * 0.15;
          child.rotation.y += 0.005; // Slow rotation
        }
        // Pulse portal floor ring
        if (child.userData?.isPortalRing && child.material) {
          child.material.opacity = 0.3 + Math.sin(time * 2) * 0.2;
          child.rotation.z += 0.02;
        }
      });
      
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
  }, [onKeyDown, onKeyUp, onMouseMove, onMouseDown, onMouseUp, onPointerLockChange, onTouchStart, onTouchMove, onTouchEnd, books]);

  // Start exploring
  const handleStartExploring = () => {
    setIsExploring(true);
    isExploringRef.current = true; // Update ref for animation loop
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
        onClick={onCanvasClick}
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
                {isMobileDevice 
                  ? "Explore this magical library. Use the joystick to walk, drag to look around."
                  : "Explore this magical library. Click and drag to look around, use keys to walk."
                }
              </p>
              
              {/* Show keyboard controls only on desktop */}
              {!isMobileDevice && (
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
                  </div>
                </div>
              )}
              
              {/* Mobile instructions */}
              {isMobileDevice && (
                <div className="bg-black/30 rounded-lg p-4 mb-6 text-left">
                  <p className="text-sm font-medium text-purple-300 mb-3">Touch Controls:</p>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-purple-300">🕹️</span>
                      <span className="text-white/70">Use joystick (bottom-left) to walk</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-purple-300">👆</span>
                      <span className="text-white/70">Drag anywhere to look around</span>
                    </div>
                  </div>
                </div>
              )}
              
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
          
          {/* Genre navigation */}
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
          
          {/* Bottom controls hint - only on desktop */}
          {!isMobileDevice && (
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
          )}
          
          {/* Teleport Portal Prompt */}
          <AnimatePresence>
            {nearPortal && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                className="fixed bottom-32 left-1/2 -translate-x-1/2 pointer-events-auto z-50"
              >
                <Button
                  onClick={() => activatePortal(nearPortal)}
                  className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-6 py-3 rounded-full shadow-lg shadow-purple-500/50 flex items-center gap-2"
                  data-testid="teleport-portal-btn"
                >
                  <FiChevronUp className={`w-5 h-5 ${nearPortal.id === 'stairs-down' ? 'rotate-180' : ''}`} />
                  {nearPortal.name}
                </Button>
              </motion.div>
            )}
          </AnimatePresence>
          
          {/* Mobile/Tablet Joystick - Enhanced for iPad */}
          {isMobileDevice && (
            <div 
              className="fixed bottom-[env(safe-area-inset-bottom,20px)] left-4 sm:left-6 md:left-8 pointer-events-auto z-50"
              style={{ touchAction: 'none' }}
              data-testid="mobile-joystick"
            >
              <div 
                className="relative w-28 h-28 sm:w-32 sm:h-32 md:w-36 md:h-36 rounded-full bg-black/50 border-2 border-white/30 backdrop-blur-md shadow-xl"
                onTouchStart={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  joystickRef.current.active = true;
                  setJoystickPos({ x: 0, y: 0 });
                }}
                onTouchMove={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  if (!joystickRef.current.active) return;
                  const touch = e.touches[0];
                  const rect = e.currentTarget.getBoundingClientRect();
                  const centerX = rect.left + rect.width / 2;
                  const centerY = rect.top + rect.height / 2;
                  
                  const dx = touch.clientX - centerX;
                  const dy = touch.clientY - centerY;
                  const maxDistance = rect.width / 3; // Dynamic based on joystick size
                  const distance = Math.min(Math.sqrt(dx * dx + dy * dy), maxDistance);
                  const angle = Math.atan2(dy, dx);
                  
                  const clampedX = Math.cos(angle) * distance;
                  const clampedY = Math.sin(angle) * distance;
                  
                  setJoystickPos({ x: clampedX, y: clampedY });
                  
                  joystickRef.current = {
                    active: true,
                    angle: angle,
                    distance: distance / maxDistance
                  };
                  
                  // Update movement keys based on joystick direction
                  const threshold = maxDistance * 0.3;
                  keysPressed.current = {
                    forward: dy < -threshold,
                    backward: dy > threshold,
                    left: dx < -threshold,
                    right: dx > threshold
                  };
                }}
                onTouchEnd={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  joystickRef.current = { active: false, angle: 0, distance: 0 };
                  setJoystickPos({ x: 0, y: 0 });
                  keysPressed.current = { forward: false, backward: false, left: false, right: false };
                }}
              >
                {/* Joystick knob */}
                <div 
                  className="absolute w-12 h-12 sm:w-14 sm:h-14 md:w-16 md:h-16 rounded-full bg-purple-500/90 border-2 border-white/50 shadow-lg transition-transform duration-75"
                  style={{
                    left: '50%',
                    top: '50%',
                    transform: `translate(calc(-50% + ${joystickPos.x}px), calc(-50% + ${joystickPos.y}px))`
                  }}
                />
                {/* Directional hints */}
                <div className="absolute top-2 left-1/2 -translate-x-1/2 text-white/50 text-sm font-bold">▲</div>
                <div className="absolute bottom-2 left-1/2 -translate-x-1/2 text-white/50 text-sm font-bold">▼</div>
                <div className="absolute left-2 top-1/2 -translate-y-1/2 text-white/50 text-sm font-bold">◀</div>
                <div className="absolute right-2 top-1/2 -translate-y-1/2 text-white/50 text-sm font-bold">▶</div>
              </div>
              {/* Joystick label */}
              <div className="text-center mt-2 text-white/60 text-xs">Move</div>
            </div>
          )}
          
          {/* Book Info Card (when a book is selected in 3D view) - RESPONSIVE for tablets/mobile */}
          <AnimatePresence>
            {selectedBook && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 md:absolute md:inset-y-0 md:right-0 md:left-auto md:w-[400px] lg:w-[450px] pointer-events-auto z-40 flex items-center justify-center md:justify-end"
                data-testid="book-info-card"
              >
                {/* Dark overlay for mobile/tablet */}
                <div 
                  className="absolute inset-0 bg-black/60 md:bg-transparent"
                  onClick={() => {
                    setSelectedBook(null);
                    setSelectedGenre(null);
                    removeHighlightedBook();
                  }}
                />
                
                {/* Card Container - Centered on mobile, right-aligned on desktop */}
                <div className="relative flex flex-col md:flex-row items-center max-w-[90vw] md:max-w-none">
                  {/* Animated Book Cover Flying Out - Hidden on mobile for cleaner UI */}
                  <motion.div
                    initial={{ x: 200, rotateY: -90, scale: 0.5 }}
                    animate={{ x: 0, rotateY: -15, scale: 1 }}
                    exit={{ x: 200, rotateY: -90, scale: 0.5 }}
                    transition={{ type: "spring", damping: 20, stiffness: 100 }}
                    className="hidden md:block absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1/2 z-10"
                    style={{ perspective: '1000px', transformStyle: 'preserve-3d' }}
                  >
                    <div 
                      className="w-32 lg:w-40 h-44 lg:h-56 rounded-lg shadow-2xl shadow-purple-500/50 overflow-hidden"
                      style={{ 
                        transform: 'rotateY(-15deg)',
                        boxShadow: '10px 10px 30px rgba(0,0,0,0.5), -5px 0 20px rgba(168,85,247,0.3)'
                      }}
                    >
                      {selectedBook.cover_image ? (
                        <img 
                          src={selectedBook.cover_image} 
                          alt={selectedBook.title}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full bg-gradient-to-br from-purple-700 to-purple-900 flex items-center justify-center">
                          <FiBook className="w-12 h-12 text-purple-300" />
                        </div>
                      )}
                      {/* Book spine effect */}
                      <div className="absolute left-0 top-0 bottom-0 w-2 bg-gradient-to-r from-black/40 to-transparent" />
                    </div>
                  </motion.div>
                  
                  {/* Info Panel - Full width card on mobile, slide-in panel on desktop */}
                  <motion.div
                    initial={{ y: 100, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    exit={{ y: 100, opacity: 0 }}
                    transition={{ delay: 0.1, type: "spring", damping: 25 }}
                    className="relative w-[85vw] max-w-sm md:w-[280px] lg:w-[300px] bg-gradient-to-b md:bg-gradient-to-l from-[#1a1520] via-[#2d1f3d] to-[#1a1520] md:to-transparent rounded-2xl md:rounded-l-2xl md:rounded-r-none p-5 md:p-6 md:pl-16 lg:pl-20 border border-purple-500/30 md:border-l md:border-y md:border-r-0"
                    style={{ 
                      boxShadow: '0 -20px 40px rgba(0,0,0,0.5)',
                      backdropFilter: 'blur(10px)'
                    }}
                  >
                    {/* Book cover for mobile - shown inline */}
                    <div className="md:hidden flex justify-center mb-4">
                      <div className="w-24 h-32 rounded-lg shadow-lg overflow-hidden">
                        {selectedBook.cover_image ? (
                          <img 
                            src={selectedBook.cover_image} 
                            alt={selectedBook.title}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full bg-gradient-to-br from-purple-700 to-purple-900 flex items-center justify-center">
                            <FiBook className="w-8 h-8 text-purple-300" />
                          </div>
                        )}
                      </div>
                    </div>
                    
                    {/* Book Info */}
                    <h3 className="text-lg md:text-xl font-bold text-white mb-1 text-center md:text-left">{selectedBook.title}</h3>
                    <p className="text-sm text-purple-300 mb-3 text-center md:text-left">by {selectedBook.author_name || 'Unknown Author'}</p>
                  
                  {selectedBook.genre && (
                    <div className="mb-3 text-center md:text-left">
                      <span className="px-3 py-1 bg-purple-500/20 rounded-full text-xs text-purple-300">
                        {selectedBook.genre}
                      </span>
                    </div>
                  )}
                  
                  {/* Book Summary/Description - Hidden on small screens */}
                  {(selectedBook.summary || selectedBook.description) && (
                    <div className="hidden sm:block mb-4 max-h-20 overflow-y-auto">
                      <p className="text-[10px] text-purple-400 mb-1 uppercase tracking-wider">Summary</p>
                      <p className="text-xs text-white/70 leading-relaxed">
                        {(selectedBook.summary || selectedBook.description).substring(0, 120)}...
                      </p>
                    </div>
                  )}
                  
                  {/* Stats */}
                  <div className="flex justify-center md:justify-start gap-3 mb-4 text-xs text-white/50">
                    <span className="flex items-center gap-1">
                      <FiBook className="w-3 h-3" />
                      {selectedBook.chapters?.length || 0} chapters
                    </span>
                  </div>
                  
                  {/* Action Buttons */}
                  <div className="flex flex-col gap-2">
                    <Button
                      onClick={() => navigate(`/read/${selectedBook.id || selectedBook._id}`)}
                      className="w-full bg-purple-600 hover:bg-purple-700 rounded-full text-sm py-2"
                      data-testid="read-book-btn"
                    >
                      <FiBookOpen className="mr-2 w-4 h-4" />
                      Read Now
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => {
                        setSelectedBook(null);
                        setSelectedGenre(null);
                        removeHighlightedBook();
                      }}
                      className="w-full border-purple-500/30 text-purple-300 hover:bg-purple-500/10 rounded-full text-sm py-2"
                    >
                      Close
                    </Button>
                  </div>
                  </motion.div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          
          {/* Genre Books Panel - Shows when a genre banner is clicked */}
          <AnimatePresence>
            {selectedGenre && (
              <motion.div
                initial={{ opacity: 0, x: -50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -50 }}
                className="absolute top-20 left-4 bottom-20 w-72 pointer-events-auto"
              >
                <div className="h-full bg-gradient-to-br from-[#2d1f3d]/95 to-[#1a1520]/95 backdrop-blur-lg rounded-2xl border border-purple-500/30 shadow-2xl flex flex-col overflow-hidden">
                  {/* Header */}
                  <div className="p-4 border-b border-purple-500/20 flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-bold text-white">{selectedGenre}</h3>
                      <p className="text-xs text-purple-300">
                        {books.filter(b => b.genre?.toLowerCase() === selectedGenre.toLowerCase() && matchesAgeFilter(b.age_rating, ageFilter)).length} books
                      </p>
                    </div>
                    <button
                      onClick={() => setSelectedGenre(null)}
                      className="text-white/50 hover:text-white p-1"
                    >
                      <FiX className="w-5 h-5" />
                    </button>
                  </div>
                  
                  {/* Age Filter */}
                  <div className="px-3 pb-2">
                    <select
                      value={ageFilter}
                      onChange={(e) => setAgeFilter(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg bg-black/30 border border-purple-500/30 text-white text-sm appearance-none cursor-pointer"
                      style={{ colorScheme: 'dark' }}
                      data-testid="age-filter-select"
                    >
                      {AGE_FILTER_OPTIONS.map(opt => (
                        <option key={opt.value} value={opt.value} className="bg-[#1a1520] text-white">
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  {/* Scrollable Book List */}
                  <div className="flex-1 overflow-y-auto p-3 space-y-2">
                    {books
                      .filter(b => b.genre?.toLowerCase() === selectedGenre.toLowerCase())
                      .filter(b => matchesAgeFilter(b.age_rating, ageFilter))
                      .map((book) => (
                        <button
                          key={book.id}
                          onClick={() => {
                            setSelectedBook(book);
                            highlightBookAtGenre(selectedGenre, book);
                            // Keep genre panel open so user can pick another book
                          }}
                          className={`w-full flex items-center gap-3 p-2 rounded-xl transition-colors text-left group ${
                            selectedBook?.id === book.id 
                              ? 'bg-purple-500/40 ring-2 ring-purple-400' 
                              : 'bg-black/20 hover:bg-purple-500/20'
                          }`}
                        >
                          {/* Book Cover Thumbnail */}
                          <div className="w-12 h-16 rounded-lg overflow-hidden flex-shrink-0 bg-purple-900/50">
                            {book.cover_image ? (
                              <img 
                                src={book.cover_image} 
                                alt={book.title}
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center">
                                <FiBook className="w-5 h-5 text-purple-400" />
                              </div>
                            )}
                          </div>
                          
                          {/* Book Info */}
                          <div className="flex-1 min-w-0">
                            <h4 className="text-sm font-medium text-white truncate group-hover:text-purple-200">
                              {book.title}
                            </h4>
                            <p className="text-xs text-purple-300/70 truncate">
                              by {book.author_name || 'Unknown'}
                            </p>
                          </div>
                          
                          {/* Arrow */}
                          <FiChevronUp className="w-4 h-4 text-purple-400 rotate-90 opacity-0 group-hover:opacity-100 transition-opacity" />
                        </button>
                      ))}
                    
                    {/* Empty State */}
                    {books.filter(b => b.genre?.toLowerCase() === selectedGenre.toLowerCase() && matchesAgeFilter(b.age_rating, ageFilter)).length === 0 && (
                      <div className="text-center py-8">
                        <FiBook className="w-10 h-10 text-purple-500/30 mx-auto mb-2" />
                        <p className="text-sm text-purple-300/50">No books match this filter</p>
                        {ageFilter !== 'all' && (
                          <button
                            onClick={() => setAgeFilter('all')}
                            className="mt-2 text-xs text-purple-400 hover:text-purple-300 underline"
                          >
                            Clear age filter
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                  
                  {/* Footer hint */}
                  <div className="p-3 border-t border-purple-500/20">
                    <p className="text-xs text-purple-300/50 text-center">
                      Click a book to view details
                    </p>
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
          
          {/* AI Librarian - Azora (bottom corner chat - hide on mobile to not overlap joystick) */}
          {!isMobileDevice && (
            <AILibrarian books={books} isVisible={!showAzoraChat} onCallAzora={() => setShowAzoraChat(true)} />
          )}
          
          {/* Debug Mode Panel - for coordinate discovery */}
          <div className="absolute top-16 right-4 pointer-events-auto">
            <Button
              variant="ghost"
              size="sm"
              className={`${debugMode ? 'bg-green-600 hover:bg-green-700' : 'bg-black/50 hover:bg-black/70'} text-white rounded-full px-3 text-xs`}
              onClick={() => {
                setDebugMode(!debugMode);
                setDebugCoords(null);
              }}
            >
              {debugMode ? '🎯 DEBUG ON' : '🔧 Debug'}
            </Button>
          </div>
          
          {/* Debug Coordinates Display */}
          {debugMode && (
            <div className="absolute top-28 right-4 pointer-events-auto bg-black/90 rounded-xl p-4 text-sm font-mono max-w-xs">
              <div className="text-green-400 mb-2 font-bold">📍 Debug Mode Active</div>
              <div className="text-white/70 text-xs mb-3">Click anywhere in the 3D scene to get coordinates</div>
              
              {debugCoords ? (
                <div className="space-y-1">
                  <div className="text-yellow-300">Last Click:</div>
                  <div className="text-white">X: <span className="text-cyan-400">{debugCoords.x}</span></div>
                  <div className="text-white">Y: <span className="text-cyan-400">{debugCoords.y}</span></div>
                  <div className="text-white">Z: <span className="text-cyan-400">{debugCoords.z}</span></div>
                  <div className="text-white/60 text-xs mt-2">Mesh: {debugCoords.meshName}</div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="mt-2 w-full bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 text-xs"
                    onClick={() => {
                      const text = `x: ${debugCoords.x}, y: ${debugCoords.y}, z: ${debugCoords.z}`;
                      navigator.clipboard.writeText(text);
                    }}
                  >
                    📋 Copy Coordinates
                  </Button>
                </div>
              ) : (
                <div className="text-white/50 italic">No clicks recorded yet</div>
              )}
              
              {/* Current camera position */}
              <div className="mt-4 pt-3 border-t border-white/20">
                <div className="text-purple-300 text-xs mb-1">Camera Position:</div>
                <div className="text-white/70 text-xs">
                  {cameraRef.current ? (
                    <>X: {cameraRef.current.position.x.toFixed(2)}, Y: {cameraRef.current.position.y.toFixed(2)}, Z: {cameraRef.current.position.z.toFixed(2)}</>
                  ) : 'Loading...'}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
