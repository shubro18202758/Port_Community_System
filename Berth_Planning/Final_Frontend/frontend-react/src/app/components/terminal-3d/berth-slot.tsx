import { useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import * as THREE from 'three';

interface BerthSlotProps {
  name: string;
  length: number;
  status: 'available' | 'occupied' | 'maintenance';
  position: [number, number, number];
  width: number;
  onClick: () => void;
  isSelected: boolean;
  scheduledCount: number;
}

export function BerthSlot({
  name,
  length,
  status,
  position,
  width,
  onClick,
  isSelected,
  scheduledCount,
}: BerthSlotProps) {
  const [hovered, setHovered] = useState(false);
  const glowRef = useRef<THREE.Mesh>(null);

  const statusColor = {
    available: '#10B981',
    occupied: '#0A4D8C',
    maintenance: '#9CA3AF',
  }[status];

  const statusColorLight = {
    available: '#D1FAE5',
    occupied: '#DBEAFE',
    maintenance: '#E5E7EB',
  }[status];

  useFrame(() => {
    if (glowRef.current) {
      const mat = glowRef.current.material as THREE.MeshStandardMaterial;
      const targetOpacity = hovered || isSelected ? 0.4 : 0;
      mat.opacity += (targetOpacity - mat.opacity) * 0.1;
    }
  });

  const berthDepth = 12;

  return (
    <group position={position}>
      {/* Berth floor */}
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, 0.05, -berthDepth / 2]}
        receiveShadow
        onClick={(e: any) => { e.stopPropagation(); onClick(); }}
        onPointerEnter={(e: any) => { e.stopPropagation(); setHovered(true); document.body.style.cursor = 'pointer'; }}
        onPointerLeave={() => { setHovered(false); document.body.style.cursor = 'default'; }}
      >
        <planeGeometry args={[width - 1, berthDepth]} />
        <meshStandardMaterial color={statusColorLight} roughness={0.8} />
      </mesh>

      {/* Left border */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[-width / 2 + 0.15, 0.06, -berthDepth / 2]}>
        <planeGeometry args={[0.3, berthDepth + 2]} />
        <meshStandardMaterial color={statusColor} />
      </mesh>
      {/* Right border */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[width / 2 - 0.15, 0.06, -berthDepth / 2]}>
        <planeGeometry args={[0.3, berthDepth + 2]} />
        <meshStandardMaterial color={statusColor} />
      </mesh>

      {/* Hover/selection glow */}
      <mesh ref={glowRef} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.07, -berthDepth / 2]}>
        <planeGeometry args={[width - 1, berthDepth]} />
        <meshStandardMaterial
          color={isSelected ? '#FBBF24' : statusColor}
          transparent opacity={0}
          emissive={isSelected ? '#FBBF24' : statusColor}
          emissiveIntensity={0.5}
        />
      </mesh>

      {/* Bollards */}
      {Array.from({ length: Math.max(2, Math.floor(width / 12)) }).map((_, i) => {
        const x = -width / 2 + (i + 1) * (width / (Math.floor(width / 12) + 1));
        return (
          <group key={`b-${i}`} position={[x, 0, -berthDepth + 1]}>
            <mesh position={[0, 0.3, 0]} castShadow>
              <cylinderGeometry args={[0.4, 0.5, 0.6, 8]} />
              <meshStandardMaterial color="#374151" metalness={0.7} roughness={0.3} />
            </mesh>
            <mesh position={[0, 0.7, 0]} castShadow>
              <cylinderGeometry args={[0.55, 0.4, 0.3, 8]} />
              <meshStandardMaterial color="#1F2937" metalness={0.7} roughness={0.3} />
            </mesh>
          </group>
        );
      })}

      {/* Fender */}
      <mesh position={[0, 0.5, -berthDepth + 0.3]} castShadow>
        <boxGeometry args={[width - 2, 1, 0.5]} />
        <meshStandardMaterial color="#1F2937" roughness={0.9} />
      </mesh>

      {/* HTML label (always works, no font loading) */}
      <Html position={[0, 4, -berthDepth / 2]} center>
        <div
          onClick={(e) => { e.stopPropagation(); onClick(); }}
          style={{
            background: 'rgba(255,255,255,0.92)',
            borderRadius: 6,
            padding: '4px 10px',
            textAlign: 'center',
            pointerEvents: 'auto',
            cursor: 'pointer',
            border: `2px solid ${statusColor}`,
            minWidth: 80,
            userSelect: 'none',
          }}
        >
          <div style={{ fontWeight: 700, fontSize: 12, color: statusColor }}>{name}</div>
          <div style={{ fontSize: 9, color: '#6B7280', marginTop: 2 }}>
            {status.charAt(0).toUpperCase() + status.slice(1)} • {length}m
            {scheduledCount > 0 && ` • ${scheduledCount} sched.`}
          </div>
        </div>
      </Html>
    </group>
  );
}
