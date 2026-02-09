import * as THREE from 'three';
import { useMemo } from 'react';

interface TerminalGroundProps {
  berthCount: number;
}

export function TerminalGround({ berthCount }: TerminalGroundProps) {
  const totalWidth = Math.max(berthCount * 50, 200);
  const halfWidth = totalWidth / 2;

  return (
    <group>
      {/* Main terminal ground (concrete) */}
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, 0, 40]}
        receiveShadow
      >
        <planeGeometry args={[totalWidth + 100, 120]} />
        <meshStandardMaterial
          color="#B8BAB0"
          roughness={0.9}
          metalness={0.05}
        />
      </mesh>

      {/* Quay wall (raised edge along water) */}
      <mesh position={[0, 0.75, -1]} castShadow receiveShadow>
        <boxGeometry args={[totalWidth + 100, 1.5, 3]} />
        <meshStandardMaterial
          color="#6B7280"
          roughness={0.7}
          metalness={0.1}
        />
      </mesh>

      {/* Quay edge cap (concrete lip) */}
      <mesh position={[0, 1.6, -2]} castShadow>
        <boxGeometry args={[totalWidth + 100, 0.3, 1.5]} />
        <meshStandardMaterial
          color="#9CA3AF"
          roughness={0.6}
          metalness={0.15}
        />
      </mesh>

      {/* Rail tracks for STS cranes */}
      <RailTrack length={totalWidth + 80} positionZ={5} />
      <RailTrack length={totalWidth + 80} positionZ={15} />

      {/* Container yard area */}
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, 0.02, 65]}
        receiveShadow
      >
        <planeGeometry args={[totalWidth + 100, 50]} />
        <meshStandardMaterial
          color="#A3A89E"
          roughness={0.95}
          metalness={0.02}
        />
      </mesh>

      {/* Road markings */}
      {Array.from({ length: Math.ceil(totalWidth / 20) }).map((_, i) => (
        <mesh
          key={`marking-${i}`}
          rotation={[-Math.PI / 2, 0, 0]}
          position={[-halfWidth + i * 20 + 10, 0.05, 35]}
        >
          <planeGeometry args={[8, 0.3]} />
          <meshStandardMaterial color="#FBBF24" />
        </mesh>
      ))}

      {/* Terminal building */}
      <mesh position={[halfWidth + 20, 5, 50]} castShadow>
        <boxGeometry args={[20, 10, 20]} />
        <meshStandardMaterial color="#D1D5DB" roughness={0.7} />
      </mesh>
      {/* Building windows */}
      {[0, 1, 2].map(row => (
        [0, 1, 2, 3].map(col => (
          <mesh
            key={`window-${row}-${col}`}
            position={[halfWidth + 10.1, 3 + row * 3, 43 + col * 4]}
          >
            <planeGeometry args={[2, 2]} />
            <meshStandardMaterial color="#87CEEB" metalness={0.5} roughness={0.1} />
          </mesh>
        ))
      ))}
    </group>
  );
}

function RailTrack({ length, positionZ }: { length: number; positionZ: number }) {
  return (
    <group position={[0, 0.1, positionZ]}>
      {/* Left rail */}
      <mesh castShadow>
        <boxGeometry args={[length, 0.15, 0.12]} />
        <meshStandardMaterial color="#4B5563" metalness={0.6} roughness={0.3} />
      </mesh>
      {/* Right rail */}
      <mesh position={[0, 0, 8]} castShadow>
        <boxGeometry args={[length, 0.15, 0.12]} />
        <meshStandardMaterial color="#4B5563" metalness={0.6} roughness={0.3} />
      </mesh>
      {/* Sleepers */}
      {Array.from({ length: Math.ceil(length / 3) }).map((_, i) => (
        <mesh key={i} position={[-length / 2 + i * 3 + 1.5, -0.05, 4]}>
          <boxGeometry args={[1.2, 0.1, 9]} />
          <meshStandardMaterial color="#78716C" roughness={0.9} />
        </mesh>
      ))}
    </group>
  );
}
