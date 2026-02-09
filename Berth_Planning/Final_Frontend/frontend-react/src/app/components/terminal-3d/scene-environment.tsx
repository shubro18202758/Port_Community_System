export function SceneEnvironment() {
  return (
    <>
      {/* Ambient light for overall illumination */}
      <ambientLight intensity={0.5} color="#b0d4f1" />

      {/* Main directional light (sun) */}
      <directionalLight
        position={[100, 80, 50]}
        intensity={1.5}
        color="#fff5e0"
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
        shadow-camera-far={500}
        shadow-camera-left={-200}
        shadow-camera-right={200}
        shadow-camera-top={200}
        shadow-camera-bottom={-200}
      />

      {/* Fill light from opposite side */}
      <directionalLight
        position={[-50, 30, -50]}
        intensity={0.3}
        color="#87CEEB"
      />

      {/* Hemisphere light for natural sky/ground color */}
      <hemisphereLight
        args={['#87CEEB', '#3a5f3a', 0.3]}
      />

      {/* Fog for depth */}
      <fog attach="fog" args={['#c8dff5', 200, 800]} />
    </>
  );
}
