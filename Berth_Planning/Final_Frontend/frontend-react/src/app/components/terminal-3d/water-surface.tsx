import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

export function WaterSurface() {
  const meshRef = useRef<THREE.Mesh>(null);

  // Simple wave animation by moving vertices
  useFrame((state) => {
    if (meshRef.current) {
      const geo = meshRef.current.geometry as THREE.PlaneGeometry;
      const positions = geo.attributes.position;
      const time = state.clock.elapsedTime;

      for (let i = 0; i < positions.count; i++) {
        const x = positions.getX(i);
        const z = positions.getY(i); // Y in plane = Z in world (rotated)
        const wave = Math.sin(x * 0.05 + time * 0.8) * 0.3
          + Math.sin(z * 0.08 + time * 0.6) * 0.2
          + Math.sin((x + z) * 0.03 + time * 1.2) * 0.15;
        positions.setZ(i, wave);
      }
      positions.needsUpdate = true;
      geo.computeVertexNormals();
    }
  });

  return (
    <mesh
      ref={meshRef}
      rotation={[-Math.PI / 2, 0, 0]}
      position={[0, -0.5, -150]}
      receiveShadow
    >
      <planeGeometry args={[800, 400, 64, 64]} />
      <meshStandardMaterial
        color="#0C7BBD"
        transparent
        opacity={0.85}
        roughness={0.2}
        metalness={0.3}
        side={THREE.DoubleSide}
      />
    </mesh>
  );
}
