import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface STSCraneProps {
  position: [number, number, number];
  status: 'operational' | 'maintenance' | 'idle';
  isActive?: boolean;
}

/**
 * Ship-to-Shore (STS) Gantry Crane
 * Tall crane that loads/unloads containers from ships
 */
export function STSCrane({ position, status, isActive = false }: STSCraneProps) {
  const trolleyRef = useRef<THREE.Group>(null);

  const bodyColor = status === 'operational' ? '#0A4D8C' : status === 'idle' ? '#D97706' : '#9CA3AF';
  const boomColor = '#DC2626';
  const legColor = '#1F2937';

  // Animate trolley movement when operational
  useFrame((state) => {
    if (trolleyRef.current && isActive) {
      trolleyRef.current.position.z = Math.sin(state.clock.elapsedTime * 0.3) * 8;
    }
  });

  return (
    <group position={position}>
      {/* Left leg */}
      <mesh position={[-4, 12, 0]} castShadow>
        <boxGeometry args={[0.8, 24, 0.8]} />
        <meshStandardMaterial color={legColor} metalness={0.4} roughness={0.5} />
      </mesh>
      {/* Right leg */}
      <mesh position={[4, 12, 0]} castShadow>
        <boxGeometry args={[0.8, 24, 0.8]} />
        <meshStandardMaterial color={legColor} metalness={0.4} roughness={0.5} />
      </mesh>

      {/* Cross beam (portal frame top) */}
      <mesh position={[0, 24, 0]} castShadow>
        <boxGeometry args={[9, 1.5, 1.2]} />
        <meshStandardMaterial color={bodyColor} metalness={0.3} roughness={0.5} />
      </mesh>

      {/* Machinery house on top */}
      <mesh position={[0, 26, 0]} castShadow>
        <boxGeometry args={[6, 3, 3]} />
        <meshStandardMaterial color={bodyColor} metalness={0.3} roughness={0.5} />
      </mesh>

      {/* Sea-side boom (extends over water) */}
      <mesh position={[0, 25.5, -12]} castShadow>
        <boxGeometry args={[1.5, 1, 24]} />
        <meshStandardMaterial color={boomColor} metalness={0.2} roughness={0.5} />
      </mesh>

      {/* Land-side boom (shorter, over terminal) */}
      <mesh position={[0, 25.5, 8]} castShadow>
        <boxGeometry args={[1.5, 1, 10]} />
        <meshStandardMaterial color={boomColor} metalness={0.2} roughness={0.5} />
      </mesh>

      {/* Boom diagonal supports (sea-side) */}
      <mesh position={[0, 28, -6]} rotation={[0.25, 0, 0]} castShadow>
        <boxGeometry args={[0.3, 0.3, 16]} />
        <meshStandardMaterial color={legColor} metalness={0.4} roughness={0.5} />
      </mesh>

      {/* Trolley (moves along boom) */}
      <group ref={trolleyRef} position={[0, 24.5, -5]}>
        {/* Trolley body */}
        <mesh castShadow>
          <boxGeometry args={[2, 0.8, 2]} />
          <meshStandardMaterial color="#FBBF24" metalness={0.3} roughness={0.5} />
        </mesh>
        {/* Spreader cables */}
        <mesh position={[0, -4, 0]}>
          <cylinderGeometry args={[0.05, 0.05, 8, 4]} />
          <meshStandardMaterial color="#374151" />
        </mesh>
        {/* Spreader (container grabber) */}
        <mesh position={[0, -8.5, 0]} castShadow>
          <boxGeometry args={[2.5, 0.4, 1.2]} />
          <meshStandardMaterial color="#FBBF24" metalness={0.4} roughness={0.4} />
        </mesh>
      </group>

      {/* Left leg base (rail wheels) */}
      <mesh position={[-4, 0.3, 0]}>
        <boxGeometry args={[1.5, 0.6, 2]} />
        <meshStandardMaterial color={legColor} metalness={0.5} roughness={0.4} />
      </mesh>
      {/* Right leg base */}
      <mesh position={[4, 0.3, 0]}>
        <boxGeometry args={[1.5, 0.6, 2]} />
        <meshStandardMaterial color={legColor} metalness={0.5} roughness={0.4} />
      </mesh>

      {/* Status light */}
      <mesh position={[0, 28, 0]}>
        <sphereGeometry args={[0.3, 8, 8]} />
        <meshStandardMaterial
          color={status === 'operational' ? '#10B981' : status === 'idle' ? '#F59E0B' : '#EF4444'}
          emissive={status === 'operational' ? '#10B981' : status === 'idle' ? '#F59E0B' : '#EF4444'}
          emissiveIntensity={0.8}
        />
      </mesh>
    </group>
  );
}

interface RTGCraneProps {
  position: [number, number, number];
  status: 'operational' | 'maintenance' | 'idle';
}

/**
 * Rubber Tyred Gantry (RTG) Crane
 * Shorter crane in the container yard
 */
export function RTGCrane({ position, status }: RTGCraneProps) {
  const bodyColor = '#D97706';
  const legColor = '#374151';

  return (
    <group position={position}>
      {/* Left leg */}
      <mesh position={[-3, 5, 0]} castShadow>
        <boxGeometry args={[0.5, 10, 0.5]} />
        <meshStandardMaterial color={legColor} metalness={0.4} roughness={0.5} />
      </mesh>
      {/* Right leg */}
      <mesh position={[3, 5, 0]} castShadow>
        <boxGeometry args={[0.5, 10, 0.5]} />
        <meshStandardMaterial color={legColor} metalness={0.4} roughness={0.5} />
      </mesh>

      {/* Cross beam */}
      <mesh position={[0, 10.5, 0]} castShadow>
        <boxGeometry args={[7, 1, 1]} />
        <meshStandardMaterial color={bodyColor} metalness={0.3} roughness={0.5} />
      </mesh>

      {/* Horizontal boom */}
      <mesh position={[0, 11, 0]} castShadow>
        <boxGeometry args={[1, 0.5, 12]} />
        <meshStandardMaterial color={bodyColor} metalness={0.3} roughness={0.5} />
      </mesh>

      {/* Wheels (4 per side) */}
      {[-1.5, -0.5, 0.5, 1.5].map((z, i) => (
        <group key={i}>
          <mesh position={[-3, 0.4, z]} rotation={[Math.PI / 2, 0, 0]}>
            <cylinderGeometry args={[0.4, 0.4, 0.3, 8]} />
            <meshStandardMaterial color="#1F2937" metalness={0.6} roughness={0.3} />
          </mesh>
          <mesh position={[3, 0.4, z]} rotation={[Math.PI / 2, 0, 0]}>
            <cylinderGeometry args={[0.4, 0.4, 0.3, 8]} />
            <meshStandardMaterial color="#1F2937" metalness={0.6} roughness={0.3} />
          </mesh>
        </group>
      ))}

      {/* Status light */}
      <mesh position={[0, 12, 0]}>
        <sphereGeometry args={[0.2, 8, 8]} />
        <meshStandardMaterial
          color={status === 'operational' ? '#10B981' : status === 'idle' ? '#F59E0B' : '#EF4444'}
          emissive={status === 'operational' ? '#10B981' : status === 'idle' ? '#F59E0B' : '#EF4444'}
          emissiveIntensity={0.8}
        />
      </mesh>
    </group>
  );
}

interface MHCCraneProps {
  position: [number, number, number];
  status: 'operational' | 'maintenance' | 'idle';
}

/**
 * Mobile Harbor Crane (MHC)
 * Wheeled crane on the quay
 */
export function MHCCrane({ position, status }: MHCCraneProps) {
  return (
    <group position={position}>
      {/* Base platform */}
      <mesh position={[0, 0.5, 0]} castShadow>
        <boxGeometry args={[4, 1, 3]} />
        <meshStandardMaterial color="#374151" metalness={0.4} roughness={0.5} />
      </mesh>

      {/* Cabin */}
      <mesh position={[0, 2.5, 0]} castShadow>
        <boxGeometry args={[3, 3, 2.5]} />
        <meshStandardMaterial color="#0A4D8C" metalness={0.3} roughness={0.5} />
      </mesh>

      {/* Boom (angled) */}
      <mesh position={[0, 8, -6]} rotation={[0.6, 0, 0]} castShadow>
        <boxGeometry args={[0.6, 14, 0.6]} />
        <meshStandardMaterial color="#DC2626" metalness={0.3} roughness={0.5} />
      </mesh>

      {/* Wheels */}
      {[-1.2, 1.2].map((x, i) => (
        <mesh key={i} position={[x, 0.3, 0]} rotation={[Math.PI / 2, 0, 0]}>
          <cylinderGeometry args={[0.3, 0.3, 0.5, 8]} />
          <meshStandardMaterial color="#1F2937" metalness={0.6} roughness={0.3} />
        </mesh>
      ))}

      {/* Status light */}
      <mesh position={[0, 4.5, 0]}>
        <sphereGeometry args={[0.15, 8, 8]} />
        <meshStandardMaterial
          color={status === 'operational' ? '#10B981' : status === 'idle' ? '#F59E0B' : '#EF4444'}
          emissive={status === 'operational' ? '#10B981' : status === 'idle' ? '#F59E0B' : '#EF4444'}
          emissiveIntensity={0.8}
        />
      </mesh>
    </group>
  );
}
