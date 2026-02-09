import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import * as THREE from 'three';

interface VesselModelProps {
  name: string;
  loa: number;
  position: [number, number, number];
  berthWidth: number;
}

export function VesselModel({ name, loa, position, berthWidth }: VesselModelProps) {
  const groupRef = useRef<THREE.Group>(null);
  const scale = Math.min((berthWidth * 0.8) / 30, 1.2);

  // Subtle bobbing
  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 0.8) * 0.08;
    }
  });

  const containerColors = ['#DC2626', '#2563EB', '#059669', '#D97706', '#7C3AED', '#DB2777', '#0891B2'];

  return (
    <group ref={groupRef} position={position} scale={[scale, scale, scale]}>
      {/* Hull - simple box with tapered bow */}
      <mesh position={[0, 0, 0]} castShadow>
        <boxGeometry args={[6, 3.5, 28]} />
        <meshStandardMaterial color="#1F2937" roughness={0.6} metalness={0.2} />
      </mesh>

      {/* Bow taper */}
      <mesh position={[0, 0, 15.5]} rotation={[0, Math.PI / 4, 0]} castShadow>
        <boxGeometry args={[4.2, 3.5, 4.2]} />
        <meshStandardMaterial color="#1F2937" roughness={0.6} metalness={0.2} />
      </mesh>

      {/* Waterline stripe */}
      <mesh position={[0, -0.8, 0]}>
        <boxGeometry args={[6.1, 0.6, 28.1]} />
        <meshStandardMaterial color="#991B1B" roughness={0.7} />
      </mesh>

      {/* Deck */}
      <mesh position={[0, 2, 0]} castShadow>
        <boxGeometry args={[6, 0.2, 28]} />
        <meshStandardMaterial color="#6B7280" roughness={0.7} metalness={0.1} />
      </mesh>

      {/* Container stacks */}
      {Array.from({ length: 5 }).map((_, row) =>
        Array.from({ length: 2 }).map((_, col) =>
          Array.from({ length: 2 + Math.floor(row % 3) }).map((_, layer) => (
            <mesh
              key={`c-${row}-${col}-${layer}`}
              position={[-1.5 + col * 3, 2.7 + layer * 1.1, -9 + row * 5]}
              castShadow
            >
              <boxGeometry args={[2.5, 1, 4.5]} />
              <meshStandardMaterial
                color={containerColors[(row * 2 + col + layer) % containerColors.length]}
                roughness={0.6}
                metalness={0.2}
              />
            </mesh>
          ))
        )
      )}

      {/* Bridge / Superstructure (at stern) */}
      <group position={[0, 2, -12]}>
        <mesh position={[0, 3, 0]} castShadow>
          <boxGeometry args={[5, 6, 4]} />
          <meshStandardMaterial color="#E5E7EB" roughness={0.6} />
        </mesh>
        {/* Bridge windows */}
        <mesh position={[0, 5.5, 2.05]}>
          <boxGeometry args={[4.5, 1.5, 0.1]} />
          <meshStandardMaterial color="#1E3A5F" metalness={0.5} roughness={0.1} />
        </mesh>
        {/* Funnel */}
        <mesh position={[0, 7.5, -0.5]} castShadow>
          <boxGeometry args={[2, 3, 2]} />
          <meshStandardMaterial color="#0A4D8C" roughness={0.5} />
        </mesh>
        <mesh position={[0, 8.5, -0.5]} castShadow>
          <boxGeometry args={[2.1, 0.5, 2.1]} />
          <meshStandardMaterial color="#DC2626" roughness={0.5} />
        </mesh>
      </group>

      {/* Vessel label */}
      <Html position={[0, 10, 0]} center>
        <div style={{
          background: 'rgba(10,77,140,0.9)',
          color: 'white',
          borderRadius: 4,
          padding: '3px 8px',
          fontSize: 10,
          fontWeight: 700,
          whiteSpace: 'nowrap',
          userSelect: 'none',
        }}>
          {name} • LOA: {loa}m
        </div>
      </Html>
    </group>
  );
}

export function ContainerStack({ position, rows = 4, layers = 3 }: {
  position: [number, number, number];
  rows?: number;
  layers?: number;
}) {
  const colors = ['#DC2626', '#2563EB', '#059669', '#D97706', '#7C3AED'];

  return (
    <group position={position}>
      {Array.from({ length: rows }).map((_, row) =>
        Array.from({ length: layers }).map((_, layer) => (
          <mesh
            key={`${row}-${layer}`}
            position={[0, 0.6 + layer * 1.2, row * 2.5]}
            castShadow
          >
            <boxGeometry args={[2, 1, 2.2]} />
            <meshStandardMaterial
              color={colors[(row + layer) % colors.length]}
              roughness={0.7}
              metalness={0.1}
            />
          </mesh>
        ))
      )}
    </group>
  );
}
