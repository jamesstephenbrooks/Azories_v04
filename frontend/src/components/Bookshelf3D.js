import { useRef, useState, useEffect, Suspense } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Text, useTexture, Html } from '@react-three/drei';
import * as THREE from 'three';

// Single book on the shelf
function Book({ book, position, index, onSelect, isSelected }) {
  const meshRef = useRef();
  const [hovered, setHovered] = useState(false);
  
  // Book dimensions (slightly vary by index for realism)
  const width = 0.15 + (index % 3) * 0.02;
  const height = 1.0 + (index % 4) * 0.1;
  const depth = 0.8;
  
  // Animation state
  const targetZ = isSelected ? position[2] + 1.5 : hovered ? position[2] + 0.3 : position[2];
  const targetRotY = isSelected ? Math.PI / 6 : 0;
  
  useFrame((state, delta) => {
    if (meshRef.current) {
      // Smooth animation
      meshRef.current.position.z = THREE.MathUtils.lerp(meshRef.current.position.z, targetZ, 0.1);
      meshRef.current.rotation.y = THREE.MathUtils.lerp(meshRef.current.rotation.y, targetRotY, 0.1);
    }
  });

  // Generate color based on genre
  const getBookColor = () => {
    const colors = {
      'Adventure': '#e74c3c',
      'Fantasy': '#9b59b6',
      'Science Fiction': '#3498db',
      'Mystery': '#2c3e50',
      'Fairy Tales': '#f39c12',
      'Animals': '#27ae60',
      'Friendship': '#e91e63',
      'Family': '#ff9800',
      'Educational': '#00bcd4',
      'Humor': '#ffeb3b',
      'Nature': '#4caf50',
      'default': '#8b4513'
    };
    return colors[book.genre] || colors.default;
  };

  return (
    <group position={position} ref={meshRef}>
      {/* Book spine (what you see on shelf) */}
      <mesh
        onPointerOver={(e) => { e.stopPropagation(); setHovered(true); }}
        onPointerOut={() => setHovered(false)}
        onClick={(e) => { e.stopPropagation(); onSelect(book); }}
        castShadow
      >
        <boxGeometry args={[width, height, depth]} />
        <meshStandardMaterial 
          color={getBookColor()} 
          roughness={0.8}
          metalness={0.1}
        />
      </mesh>
      
      {/* Book title on spine */}
      <Text
        position={[width / 2 + 0.001, 0, 0]}
        rotation={[0, Math.PI / 2, Math.PI / 2]}
        fontSize={0.08}
        color="#ffffff"
        maxWidth={height - 0.2}
        textAlign="center"
        anchorX="center"
        anchorY="middle"
      >
        {book.title.length > 20 ? book.title.substring(0, 18) + '...' : book.title}
      </Text>
      
      {/* Gold text decoration on spine */}
      <mesh position={[width / 2 + 0.001, height / 2 - 0.1, 0]}>
        <planeGeometry args={[0.05, 0.02]} />
        <meshStandardMaterial color="#ffd700" metalness={0.8} roughness={0.2} />
      </mesh>
      <mesh position={[width / 2 + 0.001, -height / 2 + 0.1, 0]}>
        <planeGeometry args={[0.05, 0.02]} />
        <meshStandardMaterial color="#ffd700" metalness={0.8} roughness={0.2} />
      </mesh>
      
      {/* Show cover when selected/hovered */}
      {(isSelected || hovered) && book.cover_image && (
        <Html
          position={[0, 0, depth / 2 + 0.01]}
          transform
          distanceFactor={2}
          style={{ pointerEvents: 'none' }}
        >
          <div 
            className="rounded-lg overflow-hidden shadow-2xl"
            style={{ 
              width: '120px', 
              height: '180px',
              transform: 'scale(0.8)',
              opacity: isSelected ? 1 : 0.9
            }}
          >
            <img 
              src={book.cover_image} 
              alt={book.title}
              className="w-full h-full object-cover"
            />
          </div>
        </Html>
      )}
    </group>
  );
}

// Bookshelf structure
function Shelf({ yPosition }) {
  return (
    <group position={[0, yPosition, 0]}>
      {/* Main shelf board */}
      <mesh receiveShadow position={[0, -0.6, 0]}>
        <boxGeometry args={[8, 0.1, 1]} />
        <meshStandardMaterial color="#5d4037" roughness={0.9} />
      </mesh>
      
      {/* Shelf lip (front edge) */}
      <mesh position={[0, -0.55, 0.45]}>
        <boxGeometry args={[8.1, 0.15, 0.1]} />
        <meshStandardMaterial color="#4e342e" roughness={0.9} />
      </mesh>
    </group>
  );
}

// Full bookcase
function Bookcase({ books, onSelectBook, selectedBook }) {
  const booksPerShelf = 12;
  const shelves = 3;
  const shelfSpacing = 1.4;
  
  return (
    <group>
      {/* Bookcase frame - Left */}
      <mesh position={[-4.1, 0.5, 0]}>
        <boxGeometry args={[0.2, 4.5, 1.1]} />
        <meshStandardMaterial color="#3e2723" roughness={0.9} />
      </mesh>
      
      {/* Bookcase frame - Right */}
      <mesh position={[4.1, 0.5, 0]}>
        <boxGeometry args={[0.2, 4.5, 1.1]} />
        <meshStandardMaterial color="#3e2723" roughness={0.9} />
      </mesh>
      
      {/* Bookcase frame - Top */}
      <mesh position={[0, 2.8, 0]}>
        <boxGeometry args={[8.4, 0.15, 1.1]} />
        <meshStandardMaterial color="#3e2723" roughness={0.9} />
      </mesh>
      
      {/* Bookcase frame - Back */}
      <mesh position={[0, 0.5, -0.5]}>
        <boxGeometry args={[8, 4.5, 0.05]} />
        <meshStandardMaterial color="#1a1a2e" roughness={1} />
      </mesh>
      
      {/* Decorative top trim */}
      <mesh position={[0, 2.95, 0.1]}>
        <boxGeometry args={[8.6, 0.1, 0.3]} />
        <meshStandardMaterial color="#4e342e" roughness={0.8} />
      </mesh>
      
      {/* Shelves */}
      {[...Array(shelves)].map((_, i) => (
        <Shelf key={i} yPosition={i * shelfSpacing} />
      ))}
      
      {/* Books on shelves */}
      {books.map((book, index) => {
        const shelfIndex = Math.floor(index / booksPerShelf);
        const positionInShelf = index % booksPerShelf;
        
        if (shelfIndex >= shelves) return null;
        
        const xPos = -3.5 + positionInShelf * 0.6;
        const yPos = shelfIndex * shelfSpacing;
        const zPos = 0;
        
        return (
          <Book
            key={book.id}
            book={book}
            position={[xPos, yPos, zPos]}
            index={index}
            onSelect={onSelectBook}
            isSelected={selectedBook?.id === book.id}
          />
        );
      })}
    </group>
  );
}

// Camera controller
function CameraController({ selectedBook }) {
  const { camera } = useThree();
  const targetPos = selectedBook ? new THREE.Vector3(0, 1, 6) : new THREE.Vector3(0, 1, 8);
  
  useFrame(() => {
    camera.position.lerp(targetPos, 0.02);
    camera.lookAt(0, 0.5, 0);
  });
  
  return null;
}

// Main component
export default function Bookshelf3D({ books, onSelectBook, selectedBook }) {
  return (
    <div className="w-full h-[600px] rounded-3xl overflow-hidden bg-gradient-to-b from-[#0a0a1a] to-[#1a1a3e]">
      <Canvas
        shadows
        camera={{ position: [0, 1, 8], fov: 50 }}
        gl={{ antialias: true }}
      >
        <Suspense fallback={null}>
          {/* Ambient light */}
          <ambientLight intensity={0.3} />
          
          {/* Warm overhead light */}
          <spotLight
            position={[0, 5, 3]}
            angle={0.5}
            penumbra={1}
            intensity={1}
            color="#fff5e6"
            castShadow
            shadow-mapSize-width={1024}
            shadow-mapSize-height={1024}
          />
          
          {/* Side lights for depth */}
          <pointLight position={[-5, 2, 2]} intensity={0.3} color="#ffe0b2" />
          <pointLight position={[5, 2, 2]} intensity={0.3} color="#ffe0b2" />
          
          {/* Bookcase */}
          <Bookcase 
            books={books.slice(0, 36)} // Max 36 books (3 shelves x 12)
            onSelectBook={onSelectBook}
            selectedBook={selectedBook}
          />
          
          {/* Floor */}
          <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -1.1, 0]} receiveShadow>
            <planeGeometry args={[20, 20]} />
            <meshStandardMaterial color="#1a1a2e" roughness={0.8} />
          </mesh>
          
          {/* Camera controls */}
          <CameraController selectedBook={selectedBook} />
          <OrbitControls 
            enablePan={false}
            enableZoom={true}
            minDistance={4}
            maxDistance={12}
            minPolarAngle={Math.PI / 4}
            maxPolarAngle={Math.PI / 2}
          />
        </Suspense>
      </Canvas>
    </div>
  );
}
