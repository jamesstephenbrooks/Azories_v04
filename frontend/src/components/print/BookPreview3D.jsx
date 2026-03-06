import React, { useRef, Suspense, useState } from 'react';
import { Canvas, useFrame, useLoader } from '@react-three/fiber';
import { OrbitControls, Environment, ContactShadows, Text } from '@react-three/drei';
import * as THREE from 'three';

// Azories mascot for back cover
const AZORA_MASCOT = 'https://res.cloudinary.com/dlbmjqmoy/image/upload/e_background_removal/v1772821413/azories/mascot/azora_blaze_back_cover.png';

function Book({ coverImage, backCoverImage, title, pageCount = 24, autoRotate = true }) {
  const bookRef = useRef();
  const [hovered, setHovered] = useState(false);
  
  // Book dimensions (8x10 aspect ratio)
  const width = 2;
  const height = 2.5;
  const depth = Math.max(0.15, Math.min(0.5, pageCount * 0.008)); // Thickness based on pages
  
  // Load textures
  const frontTexture = useLoader(THREE.TextureLoader, coverImage || '/placeholder-cover.png');
  const backTexture = useLoader(THREE.TextureLoader, backCoverImage || AZORA_MASCOT);
  
  // Auto-rotation
  useFrame((state, delta) => {
    if (bookRef.current && autoRotate && !hovered) {
      bookRef.current.rotation.y += delta * 0.3;
    }
  });

  // Create gradient texture for spine and back
  const createGradientTexture = () => {
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 256;
    const ctx = canvas.getContext('2d');
    const gradient = ctx.createLinearGradient(0, 0, 256, 256);
    gradient.addColorStop(0, '#7c3aed');
    gradient.addColorStop(0.5, '#9333ea');
    gradient.addColorStop(1, '#6b21a8');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 256, 256);
    return new THREE.CanvasTexture(canvas);
  };

  const purpleGradient = createGradientTexture();
  
  // Page edge texture (cream colored)
  const createPageEdgeTexture = () => {
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 256;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#f5f0e6';
    ctx.fillRect(0, 0, 256, 256);
    // Add subtle page lines
    ctx.strokeStyle = '#e8e3d9';
    for (let i = 0; i < 50; i++) {
      const y = (i / 50) * 256;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(256, y);
      ctx.stroke();
    }
    return new THREE.CanvasTexture(canvas);
  };

  const pageEdgeTexture = createPageEdgeTexture();

  return (
    <group 
      ref={bookRef} 
      onPointerOver={() => setHovered(true)}
      onPointerOut={() => setHovered(false)}
    >
      {/* Front Cover */}
      <mesh position={[0, 0, depth / 2 + 0.001]}>
        <planeGeometry args={[width, height]} />
        <meshStandardMaterial map={frontTexture} roughness={0.3} metalness={0.1} />
      </mesh>
      
      {/* Back Cover - Purple gradient with mascot */}
      <mesh position={[0, 0, -depth / 2 - 0.001]} rotation={[0, Math.PI, 0]}>
        <planeGeometry args={[width, height]} />
        <meshStandardMaterial map={purpleGradient} roughness={0.4} />
      </mesh>
      
      {/* Spine (left side) */}
      <mesh position={[-width / 2, 0, 0]} rotation={[0, -Math.PI / 2, 0]}>
        <planeGeometry args={[depth, height]} />
        <meshStandardMaterial map={purpleGradient} roughness={0.4} />
      </mesh>
      
      {/* Spine Title */}
      <Text
        position={[-width / 2 - 0.01, 0, 0]}
        rotation={[0, -Math.PI / 2, Math.PI / 2]}
        fontSize={0.12}
        color="white"
        anchorX="center"
        anchorY="middle"
        maxWidth={height - 0.3}
      >
        {title?.substring(0, 30) || 'My Story Book'}
      </Text>
      
      {/* Page edges (right side) */}
      <mesh position={[width / 2, 0, 0]} rotation={[0, Math.PI / 2, 0]}>
        <planeGeometry args={[depth, height]} />
        <meshStandardMaterial map={pageEdgeTexture} roughness={0.8} />
      </mesh>
      
      {/* Top edge */}
      <mesh position={[0, height / 2, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <planeGeometry args={[width, depth]} />
        <meshStandardMaterial map={pageEdgeTexture} roughness={0.8} />
      </mesh>
      
      {/* Bottom edge */}
      <mesh position={[0, -height / 2, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[width, depth]} />
        <meshStandardMaterial map={pageEdgeTexture} roughness={0.8} />
      </mesh>
      
      {/* Book body (filled box for depth) */}
      <mesh>
        <boxGeometry args={[width - 0.02, height - 0.02, depth]} />
        <meshStandardMaterial color="#f5f0e6" roughness={0.9} />
      </mesh>
    </group>
  );
}

function LoadingFallback() {
  return (
    <mesh>
      <boxGeometry args={[2, 2.5, 0.2]} />
      <meshStandardMaterial color="#9333ea" />
    </mesh>
  );
}

export default function BookPreview3D({ 
  coverImage, 
  backCoverImage,
  title, 
  pageCount = 24,
  className = "" 
}) {
  return (
    <div className={`w-full h-[350px] ${className}`}>
      <Canvas
        camera={{ position: [0, 0, 5], fov: 45 }}
        gl={{ antialias: true, alpha: true }}
        style={{ background: 'transparent' }}
      >
        {/* Warm lighting */}
        <ambientLight intensity={0.5} />
        <directionalLight position={[5, 5, 5]} intensity={1} color="#fff5e6" />
        <directionalLight position={[-5, 3, -5]} intensity={0.3} color="#e6e0ff" />
        <pointLight position={[0, 3, 3]} intensity={0.5} color="#ffeedd" />
        
        <Suspense fallback={<LoadingFallback />}>
          <Book 
            coverImage={coverImage} 
            backCoverImage={backCoverImage}
            title={title}
            pageCount={pageCount}
          />
          
          {/* Soft shadow under the book */}
          <ContactShadows 
            position={[0, -1.5, 0]} 
            opacity={0.4} 
            scale={5} 
            blur={2.5} 
            far={4}
          />
        </Suspense>
        
        {/* User can drag to rotate */}
        <OrbitControls 
          enableZoom={false}
          enablePan={false}
          minPolarAngle={Math.PI / 4}
          maxPolarAngle={Math.PI / 1.5}
          autoRotate={false}
        />
      </Canvas>
      
      <p className="text-center text-xs text-muted-foreground mt-2">
        Drag to rotate • Auto-rotates when idle
      </p>
    </div>
  );
}
