import { useMemo, useState, useRef, useEffect, useCallback } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Html } from '@react-three/drei';
import { Anchor, Eye, RotateCcw, Maximize2, Ship, Calendar, CheckCircle2, XCircle, AlertTriangle, X } from 'lucide-react';
import * as THREE from 'three';
import type { Vessel as UIVessel } from './upcoming-vessels-timeline';

// Scale: 1 scene unit ≈ 10 meters
const M2U = 0.1;

interface BerthSchedule {
  vesselId: string;
  vesselName: string;
  startTime: Date;
  endTime: Date;
  status: 'berthed' | 'scheduled' | 'at-risk';
}

interface Crane {
  id: string;
  type: 'STS' | 'RTG' | 'MHC';
  capacity: number;
  status: 'operational' | 'maintenance' | 'idle';
}

interface Berth {
  id: string;
  name: string;
  length: number;
  maxDraft: number;
  maxLOA: number;
  maxBeam: number;
  status: 'available' | 'occupied' | 'maintenance';
  cranes: Crane[];
  reeferPoints: number;
  currentVessel?: {
    name: string;
    eta: Date;
    etd: Date;
    loa: number;
    vesselId?: string;
  };
  schedule: BerthSchedule[];
}

interface Terminal3DViewProps {
  berths: Berth[];
  onBerthClick: (berth: Berth) => void;
  selectedBerthId?: string;
  vessels?: UIVessel[];
  terminalName?: string;
  onAllocateVessel?: (vesselId: string, berthId: string, eta: Date, etd: Date) => Promise<{
    success: boolean; message: string; warnings?: string[]; conflicts?: Array<{ description: string; severity: number }>;
  }>;
}

interface DragState {
  vesselId: string;
  vessel: UIVessel;
  isDragging: boolean;
  hoveredBerthId: string | null;
}

interface ValidationResult {
  visible: boolean;
  vesselName: string;
  berthId: string;
  berthName: string;
  vesselId: string;
  status: 'valid' | 'warning' | 'error';
  checks: Array<{ label: string; ok: boolean; detail: string }>;
  issues: string[];
  warnings: string[];
}

interface AnchoragePopup {
  vessel: UIVessel;
  position: [number, number, number];
}

/* ========== Container colors ========== */
const CONTAINER_COLORS = ['#DC2626', '#2563EB', '#059669', '#D97706', '#7C3AED', '#0891B2', '#BE185D', '#EA580C'];

export function Terminal3DView({ berths, onBerthClick, selectedBerthId, vessels, terminalName, onAllocateVessel }: Terminal3DViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [canvasReady, setCanvasReady] = useState(false);
  const [renderError, setRenderError] = useState<string | null>(null);
  const [cameraPreset, setCameraPreset] = useState<'perspective' | 'top' | 'front'>('perspective');

  // Drag-and-drop state
  const [dragState, setDragState] = useState<DragState | null>(null);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [anchoragePopup, setAnchoragePopup] = useState<AnchoragePopup | null>(null);

  // Anchorage/Queue vessels: those not currently at a berth (arrived and waiting, or approaching)
  const anchorageVessels = useMemo(() => {
    if (!vessels) return [];
    // Get IDs of vessels currently at berths
    const berthedVesselIds = new Set(
      berths.filter(b => b.currentVessel?.vesselId).map(b => b.currentVessel!.vesselId)
    );
    const berthedVesselNames = new Set(
      berths.filter(b => b.currentVessel).map(b => b.currentVessel!.name)
    );
    // Show all vessels not currently occupying a berth (includes arrived/waiting and approaching)
    return vessels.filter(v =>
      !berthedVesselIds.has(v.id) && !berthedVesselNames.has(v.name)
    );
  }, [vessels, berths]);

  // Client-side drop validation
  const validateDrop = useCallback((vessel: UIVessel, berth: Berth): {
    isValid: boolean;
    status: 'valid' | 'warning' | 'error';
    checks: Array<{ label: string; ok: boolean; detail: string }>;
    issues: string[];
    warnings: string[];
  } => {
    const issues: string[] = [];
    const warnings: string[] = [];
    const checks: Array<{ label: string; ok: boolean; detail: string }> = [];

    const loaOk = vessel.loa <= berth.maxLOA;
    checks.push({ label: 'LOA', ok: loaOk, detail: `${vessel.loa}m ${loaOk ? '≤' : '>'} ${berth.maxLOA}m` });
    if (!loaOk) issues.push(`LOA ${vessel.loa}m exceeds berth max ${berth.maxLOA}m`);

    const beamOk = vessel.beam <= berth.maxBeam;
    checks.push({ label: 'Beam', ok: beamOk, detail: `${vessel.beam}m ${beamOk ? '≤' : '>'} ${berth.maxBeam}m` });
    if (!beamOk) issues.push(`Beam ${vessel.beam}m exceeds berth max ${berth.maxBeam}m`);

    const draftOk = vessel.draft <= berth.maxDraft;
    checks.push({ label: 'Draft', ok: draftOk, detail: `${vessel.draft}m ${draftOk ? '≤' : '>'} ${berth.maxDraft}m` });
    if (!draftOk) issues.push(`Draft ${vessel.draft}m exceeds berth max ${berth.maxDraft}m`);

    if (berth.status === 'maintenance') {
      issues.push('Berth is under maintenance');
      checks.push({ label: 'Status', ok: false, detail: 'Under maintenance' });
    } else {
      checks.push({ label: 'Status', ok: true, detail: berth.status === 'available' ? 'Available' : 'Occupied' });
    }

    // Schedule conflict
    if (berth.status === 'occupied' && berth.currentVessel) {
      if (berth.currentVessel.etd > vessel.predictedETA) {
        issues.push(`Berth occupied until ${berth.currentVessel.etd.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`);
      }
    }
    const vesselETA = vessel.predictedETA;
    const vesselETD = new Date(vesselETA.getTime() + 8 * 60 * 60 * 1000);
    berth.schedule.forEach(s => {
      if (s.startTime < vesselETD && s.endTime > vesselETA) {
        issues.push(`Schedule conflict with ${s.vesselName}`);
      }
    });

    // Soft warnings
    if (loaOk && vessel.loa > berth.maxLOA * 0.95) {
      warnings.push(`LOA ${vessel.loa}m is within 5% of limit`);
    }
    const operationalCranes = berth.cranes.filter(c => c.status === 'operational').length;
    if (operationalCranes === 0 && berth.cranes.length > 0) {
      warnings.push('No operational cranes at this berth');
    }

    return {
      isValid: issues.length === 0,
      status: issues.length > 0 ? 'error' : warnings.length > 0 ? 'warning' : 'valid',
      checks,
      issues,
      warnings,
    };
  }, []);

  // Handle drop on berth
  const handleDrop = useCallback((vesselId: string, berthId: string) => {
    const vessel = anchorageVessels.find(v => v.id === vesselId);
    const berth = berths.find(b => b.id === berthId);
    if (!vessel || !berth) {
      setDragState(null);
      return;
    }

    const result = validateDrop(vessel, berth);
    setDragState(null);
    setValidationResult({
      visible: true,
      vesselName: vessel.name,
      berthId: berth.id,
      berthName: berth.name,
      vesselId: vessel.id,
      status: result.status,
      checks: result.checks,
      issues: result.issues,
      warnings: result.warnings,
    });
  }, [anchorageVessels, berths, validateDrop]);

  // Confirm allocation
  const handleConfirmAllocation = useCallback(async () => {
    if (!validationResult || !onAllocateVessel) return;
    const vessel = anchorageVessels.find(v => v.id === validationResult.vesselId);
    if (!vessel) return;

    const eta = vessel.predictedETA;
    const etd = new Date(eta.getTime() + 8 * 60 * 60 * 1000);
    await onAllocateVessel(validationResult.vesselId, validationResult.berthId, eta, etd);
    setValidationResult(null);
  }, [validationResult, onAllocateVessel, anchorageVessels]);

  const cameraPositions = useMemo(() => ({
    perspective: { position: [0, 100, -180] as [number, number, number], target: [0, 0, 20] as [number, number, number] },
    top: { position: [0, 200, 40] as [number, number, number], target: [0, 0, 40] as [number, number, number] },
    front: { position: [0, 60, -200] as [number, number, number], target: [0, 0, 0] as [number, number, number] },
  }), []);

  const currentCamera = cameraPositions[cameraPreset];

  const [dims, setDims] = useState({ w: 0, h: 0 });
  useEffect(() => {
    if (!containerRef.current) return;
    const el = containerRef.current;
    const update = () => setDims({ w: el.clientWidth, h: el.clientHeight });
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  if (renderError) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', flexDirection: 'column', gap: 12, color: '#6B7280', padding: 24 }}>
        <div style={{ fontSize: 16, fontWeight: 600, color: '#DC2626' }}>Digital Twin Rendering Error</div>
        <div style={{ fontSize: 12, maxWidth: 400, textAlign: 'center' }}>{renderError}</div>
        <button onClick={() => { setRenderError(null); setCanvasReady(false); }}
          style={{ padding: '8px 20px', borderRadius: 6, border: '1px solid #D1D5DB', cursor: 'pointer', fontSize: 13 }}>Retry</button>
      </div>
    );
  }

  return (
    <div ref={containerRef} style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, overflow: 'hidden', zIndex: 0 }}>
      <Canvas
        shadows
        gl={{ antialias: true, alpha: false, powerPreference: 'default', failIfMajorPerformanceCaveat: false }}
        style={{ background: '#87CEEB' }}
        onCreated={(state) => { state.gl.setClearColor('#87CEEB'); setCanvasReady(true); }}
      >
        <PerspectiveCamera makeDefault position={currentCamera.position} fov={50} near={0.1} far={2000} />
        <OrbitControls
          target={currentCamera.target}
          maxPolarAngle={Math.PI / 2.1}
          minDistance={15}
          maxDistance={400}
          enableDamping
          dampingFactor={0.08}
          rotateSpeed={0.5}
          zoomSpeed={0.8}
          panSpeed={0.6}
          enabled={!dragState?.isDragging}
        />

        <ambientLight intensity={0.5} color="#b0d4f1" />
        <directionalLight position={[100, 80, 50]} intensity={1.5} color="#fff5e0" castShadow
          shadow-mapSize-width={2048} shadow-mapSize-height={2048}
          shadow-camera-left={-200} shadow-camera-right={200}
          shadow-camera-top={200} shadow-camera-bottom={-200}
        />
        <directionalLight position={[-50, 30, -50]} intensity={0.3} color="#87CEEB" />
        <hemisphereLight args={['#87CEEB', '#3a5f3a', 0.3]} />
        <fog attach="fog" args={['#c8dff5', 300, 900]} />

        {/* Water */}
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.5, -150]} receiveShadow>
          <planeGeometry args={[800, 400]} />
          <meshStandardMaterial color="#0C7BBD" transparent opacity={0.85} roughness={0.2} metalness={0.3} />
        </mesh>

        <TerminalGround berths={berths} />
        <BerthScene
          berths={berths}
          onBerthClick={onBerthClick}
          selectedBerthId={selectedBerthId}
          terminalName={terminalName}
          anchorageVessels={anchorageVessels}
          dragState={dragState}
          onDragStart={(vessel) => {
            setAnchoragePopup(null);
            setDragState({ vesselId: vessel.id, vessel, isDragging: true, hoveredBerthId: null });
          }}
          onDragStateChange={setDragState}
          onDrop={handleDrop}
          onVesselClick={(vessel, pos) => {
            setAnchoragePopup(anchoragePopup?.vessel.id === vessel.id ? null : { vessel, position: pos });
          }}
          validateDrop={validateDrop}
        />
      </Canvas>

      {/* Overlay: Title + Legend */}
      <div style={{ position: 'absolute', top: 12, left: 12, display: 'flex', alignItems: 'center', gap: 8, zIndex: 10 }}>
        <div style={{ backgroundColor: 'rgba(255,255,255,0.95)', backdropFilter: 'blur(8px)', padding: '6px 12px', borderRadius: 8, boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Anchor style={{ width: 14, height: 14, color: '#0A4D8C' }} />
            <span style={{ fontSize: 12, fontWeight: 600, color: '#0A4D8C' }}>Digital Twin</span>
          </div>
        </div>
      </div>

      {/* Terminal zone legend */}
      <div style={{ position: 'absolute', top: 12, right: 60, display: 'flex', gap: 6, zIndex: 10 }}>
        {[
          { color: '#DC2626', label: 'Export Yard' },
          { color: '#2563EB', label: 'Import Yard' },
          { color: '#D97706', label: 'RTG Zone' },
          { color: '#374151', label: 'Truck Lane' },
          { color: '#DC2626', label: 'Security Boundary' },
        ].map(z => (
          <div key={z.label} style={{ backgroundColor: 'rgba(255,255,255,0.95)', backdropFilter: 'blur(8px)', padding: '4px 8px', borderRadius: 6, boxShadow: '0 1px 3px rgba(0,0,0,0.1)', display: 'flex', alignItems: 'center', gap: 4, fontSize: 9 }}>
            <span style={{ width: 8, height: 4, borderRadius: 1, backgroundColor: z.color, display: 'inline-block' }} />
            <span style={{ fontWeight: 500, color: '#374151' }}>{z.label}</span>
          </div>
        ))}
      </div>

      {/* Camera controls */}
      <div style={{ position: 'absolute', bottom: 12, right: 12, display: 'flex', flexDirection: 'column', gap: 4, zIndex: 10 }}>
        {(['perspective', 'top', 'front'] as const).map((preset) => (
          <button key={preset} onClick={() => setCameraPreset(preset)}
            disabled={!!dragState?.isDragging}
            style={{
              padding: 8, borderRadius: 8, border: 'none', cursor: dragState?.isDragging ? 'not-allowed' : 'pointer',
              boxShadow: '0 1px 4px rgba(0,0,0,0.15)',
              backgroundColor: cameraPreset === preset ? '#0A4D8C' : 'rgba(255,255,255,0.95)',
              color: cameraPreset === preset ? 'white' : '#0A4D8C',
              opacity: dragState?.isDragging ? 0.5 : 1,
            }}
            title={`${preset.charAt(0).toUpperCase() + preset.slice(1)} View`}>
            {preset === 'perspective' ? <Eye style={{ width: 16, height: 16 }} /> :
              preset === 'top' ? <Maximize2 style={{ width: 16, height: 16 }} /> :
                <RotateCcw style={{ width: 16, height: 16 }} />}
          </button>
        ))}
      </div>

      <div style={{ position: 'absolute', bottom: 12, left: 12, padding: '6px 10px', borderRadius: 8, boxShadow: '0 1px 4px rgba(0,0,0,0.15)', backgroundColor: 'rgba(255,255,255,0.85)', color: '#6B7280', fontSize: 10, zIndex: 10 }}>
        Drag to rotate &bull; Scroll to zoom &bull; Click vessel at anchorage for details &bull; Drag vessel to berth to allocate
      </div>

      {!canvasReady && (
        <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', zIndex: 20, backgroundColor: 'rgba(0,0,0,0.7)', color: 'white', padding: '12px 24px', borderRadius: 8, fontSize: 13 }}>
          Initializing Digital Twin... (container: {dims.w}x{dims.h})
        </div>
      )}

      {/* Anchorage vessel detail popup */}
      {anchoragePopup && (
        <div style={{
          position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
          zIndex: 25, minWidth: 300, maxWidth: 380,
        }}>
          <div style={{
            background: 'white', borderRadius: 12, overflow: 'hidden',
            boxShadow: '0 8px 32px rgba(0,0,0,0.3)', border: '2px solid #0A4D8C',
          }}>
            {/* Header */}
            <div style={{ background: 'linear-gradient(135deg, #0A4D8C, #0C7BBD)', padding: '10px 14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Ship style={{ width: 16, height: 16, color: 'white' }} />
                <span style={{ fontSize: 13, fontWeight: 700, color: 'white' }}>{anchoragePopup.vessel.name}</span>
              </div>
              <button onClick={() => setAnchoragePopup(null)}
                style={{ border: 'none', background: 'rgba(255,255,255,0.2)', borderRadius: 4, padding: 3, cursor: 'pointer', display: 'flex' }}>
                <X style={{ width: 14, height: 14, color: 'white' }} />
              </button>
            </div>
            {/* Body */}
            <div style={{ padding: '10px 14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <span style={{ fontSize: 10, color: '#6B7280' }}>IMO: <b style={{ color: '#1F2937' }}>{anchoragePopup.vessel.imo}</b></span>
                <span style={{ fontSize: 10, color: '#6B7280' }}>Flag: <b style={{ color: '#1F2937' }}>{anchoragePopup.vessel.flag}</b></span>
                <span style={{
                  fontSize: 9, fontWeight: 600, padding: '1px 6px', borderRadius: 3,
                  backgroundColor: anchoragePopup.vessel.status === 'on-time' ? '#D1FAE5' : anchoragePopup.vessel.status === 'delayed' ? '#FEE2E2' : '#FEF3C7',
                  color: anchoragePopup.vessel.status === 'on-time' ? '#059669' : anchoragePopup.vessel.status === 'delayed' ? '#DC2626' : '#D97706',
                }}>{anchoragePopup.vessel.status}</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '4px 12px', fontSize: 10, color: '#374151', marginBottom: 8 }}>
                <div><span style={{ color: '#9CA3AF' }}>LOA:</span> <b>{anchoragePopup.vessel.loa}m</b></div>
                <div><span style={{ color: '#9CA3AF' }}>Beam:</span> <b>{anchoragePopup.vessel.beam}m</b></div>
                <div><span style={{ color: '#9CA3AF' }}>Draft:</span> <b>{anchoragePopup.vessel.draft}m</b></div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 12px', fontSize: 10, color: '#374151', marginBottom: 8 }}>
                <div><span style={{ color: '#9CA3AF' }}>Type:</span> {anchoragePopup.vessel.vesselType}</div>
                <div><span style={{ color: '#9CA3AF' }}>Cargo:</span> {anchoragePopup.vessel.cargoType}</div>
                <div><span style={{ color: '#9CA3AF' }}>ETA:</span> {anchoragePopup.vessel.predictedETA.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</div>
                {anchoragePopup.vessel.cargoQuantity > 0 && (
                  <div><span style={{ color: '#9CA3AF' }}>Qty:</span> {anchoragePopup.vessel.cargoQuantity.toLocaleString()} {anchoragePopup.vessel.cargoUnit}</div>
                )}
              </div>
              {anchoragePopup.vessel.aiRecommendation && (
                <div style={{ padding: '6px 8px', borderRadius: 6, backgroundColor: '#FFFBEB', border: '1px solid #F59E0B', marginBottom: 8 }}>
                  <div style={{ fontSize: 9, fontWeight: 700, color: '#92400E', marginBottom: 2 }}>AI Recommendation</div>
                  <div style={{ fontSize: 10, color: '#92400E' }}>
                    <b>{anchoragePopup.vessel.aiRecommendation.suggestedBerth}</b> — {Math.round(anchoragePopup.vessel.aiRecommendation.confidence)}% confidence
                  </div>
                </div>
              )}
              <div style={{ fontSize: 9, color: '#9CA3AF', textAlign: 'center', fontStyle: 'italic' }}>
                Drag this vessel to an available berth to allocate
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Validation overlay */}
      {validationResult?.visible && (
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.4)', zIndex: 30,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}
          onClick={() => setValidationResult(null)}
        >
          <div style={{
            background: 'white', borderRadius: 12, overflow: 'hidden',
            boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
            border: `2px solid ${validationResult.status === 'valid' ? '#10B981' : validationResult.status === 'warning' ? '#F59E0B' : '#DC2626'}`,
            maxWidth: 420, minWidth: 340,
          }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div style={{
              padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 10,
              background: validationResult.status === 'valid' ? '#ECFDF5' : validationResult.status === 'warning' ? '#FFFBEB' : '#FEF2F2',
              borderBottom: `1px solid ${validationResult.status === 'valid' ? '#A7F3D0' : validationResult.status === 'warning' ? '#FDE68A' : '#FECACA'}`,
            }}>
              {validationResult.status === 'valid'
                ? <CheckCircle2 style={{ width: 20, height: 20, color: '#059669' }} />
                : validationResult.status === 'warning'
                ? <AlertTriangle style={{ width: 20, height: 20, color: '#D97706' }} />
                : <XCircle style={{ width: 20, height: 20, color: '#DC2626' }} />
              }
              <div>
                <div style={{ fontSize: 13, fontWeight: 700, color: '#1F2937' }}>Berth Allocation Check</div>
                <div style={{ fontSize: 11, color: '#6B7280' }}>
                  {validationResult.vesselName} → {validationResult.berthName}
                </div>
              </div>
            </div>

            {/* Constraint checks */}
            <div style={{ padding: '12px 16px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 12 }}>
                {validationResult.checks.map((c) => (
                  <div key={c.label} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
                    {c.ok
                      ? <CheckCircle2 style={{ width: 16, height: 16, color: '#059669', flexShrink: 0 }} />
                      : <XCircle style={{ width: 16, height: 16, color: '#DC2626', flexShrink: 0 }} />
                    }
                    <span style={{ fontWeight: 600, color: '#374151', minWidth: 50 }}>{c.label}</span>
                    <span style={{ color: c.ok ? '#059669' : '#DC2626', fontWeight: 500 }}>{c.detail}</span>
                  </div>
                ))}
              </div>

              {/* Issues */}
              {validationResult.issues.length > 0 && (
                <div style={{ padding: '8px 10px', borderRadius: 6, backgroundColor: '#FEF2F2', border: '1px solid #FECACA', marginBottom: 8 }}>
                  <div style={{ fontSize: 10, fontWeight: 700, color: '#DC2626', marginBottom: 4 }}>Issues (Allocation Blocked)</div>
                  {validationResult.issues.map((issue, i) => (
                    <div key={i} style={{ fontSize: 11, color: '#991B1B', display: 'flex', alignItems: 'center', gap: 4 }}>
                      <span>•</span> {issue}
                    </div>
                  ))}
                </div>
              )}

              {/* Warnings */}
              {validationResult.warnings.length > 0 && (
                <div style={{ padding: '8px 10px', borderRadius: 6, backgroundColor: '#FFFBEB', border: '1px solid #FDE68A', marginBottom: 8 }}>
                  <div style={{ fontSize: 10, fontWeight: 700, color: '#D97706', marginBottom: 4 }}>Warnings</div>
                  {validationResult.warnings.map((warn, i) => (
                    <div key={i} style={{ fontSize: 11, color: '#92400E', display: 'flex', alignItems: 'center', gap: 4 }}>
                      <span>•</span> {warn}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Actions */}
            <div style={{ padding: '10px 16px', borderTop: '1px solid #E5E7EB', display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
              <button
                onClick={() => setValidationResult(null)}
                style={{
                  padding: '8px 16px', borderRadius: 6, border: '1px solid #D1D5DB',
                  backgroundColor: 'white', color: '#374151', fontSize: 12, fontWeight: 600, cursor: 'pointer',
                }}
              >Cancel</button>
              {validationResult.status !== 'error' && (
                <button
                  onClick={handleConfirmAllocation}
                  style={{
                    padding: '8px 20px', borderRadius: 6, border: 'none',
                    backgroundColor: '#0A4D8C', color: 'white', fontSize: 12, fontWeight: 600, cursor: 'pointer',
                  }}
                >Confirm Allocation</button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ========== Layout helpers ========== */

function computeBerthLayout(berths: Berth[]) {
  const GAP = 4;
  const berthWidths = berths.map(b => Math.max(b.length * M2U, 20));
  const totalWidth = berthWidths.reduce((s, w) => s + w, 0) + GAP * (berths.length - 1);
  let x = -totalWidth / 2;

  return berths.map((berth, i) => {
    const w = berthWidths[i];
    const cx = x + w / 2;
    x += w + GAP;
    return { berth, position: [cx, 0, 0] as [number, number, number], width: w };
  });
}

/* ========== Terminal Ground with zones ========== */
/*
  Z-axis layout (water → land):
  Z < -60   : Anchorage area
  Z < 0     : Water + vessels
  Z = 0     : Quay edge / berths
  Z = 0-12  : Berth area
  Z = 12-15 : Quay apron (STS crane rail)
  Z = 15-38 : Export container yard (near berth)
  Z = 38-44 : Primary truck road
  Z = 44-72 : General / Import container yard
  Z = 72-78 : Secondary truck road
  Z = 78-95 : Import staging area (near gate)
  Z = 95-110: Terminal gate / admin buildings
*/

function TerminalGround({ berths }: { berths: Berth[] }) {
  const layout = computeBerthLayout(berths);
  const totalSpan = layout.length > 0
    ? (layout[layout.length - 1].position[0] + layout[layout.length - 1].width / 2) - (layout[0].position[0] - layout[0].width / 2)
    : 200;
  const tw = totalSpan + 120;

  return (
    <group>
      {/* Quay apron */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 13.5]} receiveShadow>
        <planeGeometry args={[tw, 15]} />
        <meshStandardMaterial color="#B8BAB0" roughness={0.9} metalness={0.05} />
      </mesh>
      {/* Quay wall / edge */}
      <mesh position={[0, 0.75, -1]} castShadow receiveShadow>
        <boxGeometry args={[tw, 1.5, 3]} />
        <meshStandardMaterial color="#6B7280" roughness={0.7} metalness={0.1} />
      </mesh>
      <mesh position={[0, 1.6, -2]} castShadow>
        <boxGeometry args={[tw, 0.3, 1.5]} />
        <meshStandardMaterial color="#9CA3AF" roughness={0.6} metalness={0.15} />
      </mesh>
      {/* Export yard zone */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, 26.5]} receiveShadow>
        <planeGeometry args={[tw, 23]} />
        <meshStandardMaterial color="#A3A89E" roughness={0.95} metalness={0.02} />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.02, 15.5]}>
        <planeGeometry args={[tw, 0.5]} />
        <meshStandardMaterial color="#DC2626" opacity={0.6} transparent />
      </mesh>
      {/* Primary truck road */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, 41]} receiveShadow>
        <planeGeometry args={[tw, 6]} />
        <meshStandardMaterial color="#374151" roughness={0.85} />
      </mesh>
      <RoadMarkings z={41} width={tw} />
      {/* Import yard zone */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, 58]} receiveShadow>
        <planeGeometry args={[tw, 28]} />
        <meshStandardMaterial color="#A0A59B" roughness={0.95} metalness={0.02} />
      </mesh>
      {/* Secondary truck road */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, 75]} receiveShadow>
        <planeGeometry args={[tw, 6]} />
        <meshStandardMaterial color="#374151" roughness={0.85} />
      </mesh>
      <RoadMarkings z={75} width={tw} />
      {/* Import staging area */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, 86.5]} receiveShadow>
        <planeGeometry args={[tw, 17]} />
        <meshStandardMaterial color="#9CA3AF" roughness={0.9} metalness={0.03} />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.02, 94.5]}>
        <planeGeometry args={[tw, 0.5]} />
        <meshStandardMaterial color="#2563EB" opacity={0.6} transparent />
      </mesh>
      {/* Terminal gate area */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, 102]} receiveShadow>
        <planeGeometry args={[tw, 16]} />
        <meshStandardMaterial color="#D1D5DB" roughness={0.8} />
      </mesh>
      <TerminalGate position={[0, 0, 98]} width={tw} />
      {/* Admin building */}
      <mesh position={[tw / 2 - 15, 6, 105]} castShadow>
        <boxGeometry args={[20, 12, 10]} />
        <meshStandardMaterial color="#E5E7EB" roughness={0.6} />
      </mesh>
      <mesh position={[tw / 2 - 15, 6, 100.5]}>
        <boxGeometry args={[18, 8, 0.1]} />
        <meshStandardMaterial color="#1E3A5F" metalness={0.5} roughness={0.1} />
      </mesh>
      {/* Zone labels */}
      <Html position={[-tw / 2 + 10, 2, 26]} zIndexRange={[5, 0]} style={{ pointerEvents: 'none' }}>
        <div style={{ fontSize: 9, fontWeight: 700, color: '#DC2626', textShadow: '0 0 4px white', whiteSpace: 'nowrap', opacity: 0.8 }}>EXPORT YARD</div>
      </Html>
      <Html position={[-tw / 2 + 10, 2, 58]} zIndexRange={[5, 0]} style={{ pointerEvents: 'none' }}>
        <div style={{ fontSize: 9, fontWeight: 700, color: '#D97706', textShadow: '0 0 4px white', whiteSpace: 'nowrap', opacity: 0.8 }}>CONTAINER YARD</div>
      </Html>
      <Html position={[-tw / 2 + 10, 2, 86]} zIndexRange={[5, 0]} style={{ pointerEvents: 'none' }}>
        <div style={{ fontSize: 9, fontWeight: 700, color: '#2563EB', textShadow: '0 0 4px white', whiteSpace: 'nowrap', opacity: 0.8 }}>IMPORT STAGING</div>
      </Html>
      <Html position={[0, 8, 100]} center zIndexRange={[5, 0]} style={{ pointerEvents: 'none' }}>
        <div style={{ fontSize: 10, fontWeight: 800, color: '#0A4D8C', textShadow: '0 0 6px white', whiteSpace: 'nowrap', letterSpacing: 2 }}>TERMINAL GATE</div>
      </Html>
    </group>
  );
}

/* ========== Road markings ========== */

function RoadMarkings({ z, width }: { z: number; width: number }) {
  const dashes = useMemo(() => {
    const arr: number[] = [];
    for (let x = -width / 2 + 3; x < width / 2 - 3; x += 6) arr.push(x);
    return arr;
  }, [width]);
  return (
    <group>
      {dashes.map((x, i) => (
        <mesh key={i} rotation={[-Math.PI / 2, 0, 0]} position={[x, 0.03, z]}>
          <planeGeometry args={[3, 0.2]} />
          <meshStandardMaterial color="#FBBF24" />
        </mesh>
      ))}
    </group>
  );
}

/* ========== Terminal Gate ========== */

function TerminalGate({ position, width }: { position: [number, number, number]; width: number }) {
  const laneCount = Math.max(4, Math.floor(width / 30));
  const laneSpacing = Math.min(20, (width - 20) / laneCount);
  const startX = -(laneCount - 1) * laneSpacing / 2;
  return (
    <group position={position}>
      {Array.from({ length: laneCount }).map((_, i) => {
        const x = startX + i * laneSpacing;
        return (
          <group key={i} position={[x, 0, 0]}>
            <mesh position={[-3, 3, 0]} castShadow><boxGeometry args={[0.5, 6, 0.5]} /><meshStandardMaterial color="#6B7280" roughness={0.6} metalness={0.2} /></mesh>
            <mesh position={[3, 3, 0]} castShadow><boxGeometry args={[0.5, 6, 0.5]} /><meshStandardMaterial color="#6B7280" roughness={0.6} metalness={0.2} /></mesh>
            <mesh position={[0, 6.5, 0]} castShadow><boxGeometry args={[7, 0.8, 1]} /><meshStandardMaterial color="#DC2626" roughness={0.5} metalness={0.1} /></mesh>
            <mesh position={[0, 5, 2]}><boxGeometry args={[6, 0.15, 0.15]} /><meshStandardMaterial color={i % 2 === 0 ? '#DC2626' : '#FBBF24'} /></mesh>
          </group>
        );
      })}
    </group>
  );
}

/* ========== Terminal Boundary ========== */

function TerminalBoundary({ position, depth, leftLabel, rightLabel }: {
  position: [number, number, number]; depth: number; leftLabel: string; rightLabel: string;
}) {
  const fencePanelCount = Math.ceil(depth / 8);
  return (
    <group position={position}>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.04, depth / 2]}><planeGeometry args={[1.2, depth]} /><meshStandardMaterial color="#DC2626" opacity={0.7} transparent /></mesh>
      {Array.from({ length: Math.ceil(depth / 4) }).map((_, i) => (
        <mesh key={`hazard-${i}`} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.05, i * 4 + 2]}><planeGeometry args={[1.2, 1.5]} /><meshStandardMaterial color="#FBBF24" /></mesh>
      ))}
      {Array.from({ length: fencePanelCount }).map((_, i) => {
        const z = i * 8 + 4;
        if (z > depth - 4) return null;
        return (
          <group key={`fence-${i}`}>
            <mesh position={[0, 2.5, z]} castShadow><boxGeometry args={[0.2, 5, 0.2]} /><meshStandardMaterial color="#6B7280" metalness={0.5} roughness={0.4} /></mesh>
            <mesh position={[0, 5.1, z]}><sphereGeometry args={[0.2, 8, 8]} /><meshStandardMaterial color="#9CA3AF" metalness={0.4} roughness={0.4} /></mesh>
            <mesh position={[0, 2.5, z + 4]} castShadow><boxGeometry args={[0.08, 4.5, 8]} /><meshStandardMaterial color="#9CA3AF" transparent opacity={0.35} metalness={0.6} roughness={0.3} /></mesh>
            <mesh position={[0, 4.8, z + 4]}><boxGeometry args={[0.15, 0.15, 8]} /><meshStandardMaterial color="#6B7280" metalness={0.5} roughness={0.4} /></mesh>
            <mesh position={[0, 0.3, z + 4]}><boxGeometry args={[0.15, 0.15, 8]} /><meshStandardMaterial color="#6B7280" metalness={0.5} roughness={0.4} /></mesh>
          </group>
        );
      })}
      <mesh position={[0, 5.3, depth / 2]}><boxGeometry args={[0.5, 0.15, depth - 8]} /><meshStandardMaterial color="#4B5563" metalness={0.6} roughness={0.3} /></mesh>
      <mesh position={[0, 5.5, depth / 2]}><boxGeometry args={[0.3, 0.15, depth - 8]} /><meshStandardMaterial color="#4B5563" metalness={0.6} roughness={0.3} /></mesh>
      {/* Guard posts at road crossings */}
      <group position={[0, 0, 41]}>
        <mesh position={[0, 2, 0]} castShadow><boxGeometry args={[4, 4, 3]} /><meshStandardMaterial color="#E5E7EB" roughness={0.6} /></mesh>
        <mesh position={[0, 4.2, 0]} castShadow><boxGeometry args={[5, 0.4, 3.8]} /><meshStandardMaterial color="#374151" roughness={0.5} metalness={0.2} /></mesh>
        <mesh position={[2.01, 2.5, 0]}><boxGeometry args={[0.05, 1.5, 2]} /><meshStandardMaterial color="#87CEEB" metalness={0.5} roughness={0.1} /></mesh>
        <mesh position={[-2.01, 2.5, 0]}><boxGeometry args={[0.05, 1.5, 2]} /><meshStandardMaterial color="#87CEEB" metalness={0.5} roughness={0.1} /></mesh>
        <mesh position={[5, 3.5, 0]}><boxGeometry args={[6, 0.15, 0.15]} /><meshStandardMaterial color="#DC2626" /></mesh>
        <mesh position={[-5, 3.5, 0]}><boxGeometry args={[6, 0.15, 0.15]} /><meshStandardMaterial color="#DC2626" /></mesh>
        <mesh position={[2.5, 1.75, 0]} castShadow><boxGeometry args={[0.3, 3.5, 0.3]} /><meshStandardMaterial color="#6B7280" metalness={0.4} roughness={0.5} /></mesh>
        <mesh position={[-2.5, 1.75, 0]} castShadow><boxGeometry args={[0.3, 3.5, 0.3]} /><meshStandardMaterial color="#6B7280" metalness={0.4} roughness={0.5} /></mesh>
        <mesh position={[0, 5, 0]}><sphereGeometry args={[0.25, 8, 8]} /><meshStandardMaterial color="#FBBF24" emissive="#FBBF24" emissiveIntensity={0.6} /></mesh>
      </group>
      <group position={[0, 0, 75]}>
        <mesh position={[0, 2, 0]} castShadow><boxGeometry args={[3.5, 3.5, 2.5]} /><meshStandardMaterial color="#E5E7EB" roughness={0.6} /></mesh>
        <mesh position={[0, 3.9, 0]} castShadow><boxGeometry args={[4.2, 0.3, 3.2]} /><meshStandardMaterial color="#374151" roughness={0.5} metalness={0.2} /></mesh>
        <mesh position={[1.76, 2.3, 0]}><boxGeometry args={[0.05, 1.2, 1.8]} /><meshStandardMaterial color="#87CEEB" metalness={0.5} roughness={0.1} /></mesh>
        <mesh position={[4.5, 3, 0]}><boxGeometry args={[5, 0.15, 0.15]} /><meshStandardMaterial color="#FBBF24" /></mesh>
        <mesh position={[-4.5, 3, 0]}><boxGeometry args={[5, 0.15, 0.15]} /><meshStandardMaterial color="#FBBF24" /></mesh>
      </group>
      {/* CCTV cameras */}
      {[15, 55, 90].map((z, i) => (
        <group key={`cctv-${i}`} position={[0, 0, z]}>
          <mesh position={[0, 4, 0]} castShadow><boxGeometry args={[0.15, 8, 0.15]} /><meshStandardMaterial color="#4B5563" metalness={0.5} roughness={0.4} /></mesh>
          <mesh position={[1, 7.5, 0]} castShadow><boxGeometry args={[2, 0.12, 0.12]} /><meshStandardMaterial color="#4B5563" metalness={0.5} roughness={0.4} /></mesh>
          <mesh position={[2, 7.5, 0]} castShadow><boxGeometry args={[0.8, 0.5, 0.5]} /><meshStandardMaterial color="#1F2937" roughness={0.5} metalness={0.3} /></mesh>
          <mesh position={[2.45, 7.5, 0]}><sphereGeometry args={[0.12, 8, 8]} /><meshStandardMaterial color="#DC2626" emissive="#DC2626" emissiveIntensity={0.5} /></mesh>
          <mesh position={[-0.8, 8.2, 0]}><boxGeometry args={[1.2, 0.4, 0.8]} /><meshStandardMaterial color="#E5E7EB" emissive="#FBBF24" emissiveIntensity={0.3} /></mesh>
        </group>
      ))}
      {/* Warning signs */}
      {[10, 50, 85].map((z, i) => (
        <group key={`sign-${i}`} position={[1.5, 0, z]}>
          <mesh position={[0, 1.5, 0]} castShadow><boxGeometry args={[0.1, 3, 0.1]} /><meshStandardMaterial color="#6B7280" metalness={0.4} roughness={0.5} /></mesh>
          <mesh position={[0, 3, 0]} castShadow><boxGeometry args={[2.5, 1.2, 0.08]} /><meshStandardMaterial color="#DC2626" roughness={0.5} /></mesh>
          <mesh position={[0, 3, 0.05]}><boxGeometry args={[2.2, 0.9, 0.02]} /><meshStandardMaterial color="#FBBF24" /></mesh>
          <mesh position={[-0.6, 3, 0.07]}><boxGeometry args={[0.5, 0.5, 0.02]} /><meshStandardMaterial color="#DC2626" /></mesh>
        </group>
      ))}
      {/* Bollards */}
      {Array.from({ length: Math.ceil(depth / 12) }).map((_, i) => {
        const z = i * 12 + 6;
        return (
          <group key={`bollard-${i}`} position={[0, 0, z]}>
            <mesh position={[-1.2, 0.4, 0]} castShadow><cylinderGeometry args={[0.25, 0.3, 0.8, 8]} /><meshStandardMaterial color="#FBBF24" roughness={0.6} /></mesh>
            <mesh position={[1.2, 0.4, 0]} castShadow><cylinderGeometry args={[0.25, 0.3, 0.8, 8]} /><meshStandardMaterial color="#FBBF24" roughness={0.6} /></mesh>
          </group>
        );
      })}
      {/* Terminal labels */}
      <Html position={[-8, 6, 3]} zIndexRange={[5, 0]} style={{ pointerEvents: 'none' }}>
        <div style={{ fontSize: 10, fontWeight: 800, color: '#0A4D8C', letterSpacing: 1.5, textShadow: '0 0 6px white, 0 0 12px white', whiteSpace: 'nowrap', background: 'rgba(255,255,255,0.75)', padding: '2px 8px', borderRadius: 4, border: '1px solid rgba(10,77,140,0.3)' }}>{leftLabel}</div>
      </Html>
      <Html position={[8, 6, 3]} zIndexRange={[5, 0]} style={{ pointerEvents: 'none' }}>
        <div style={{ fontSize: 10, fontWeight: 800, color: '#0A4D8C', letterSpacing: 1.5, textShadow: '0 0 6px white, 0 0 12px white', whiteSpace: 'nowrap', background: 'rgba(255,255,255,0.75)', padding: '2px 8px', borderRadius: 4, border: '1px solid rgba(10,77,140,0.3)' }}>{rightLabel}</div>
      </Html>
      <Html position={[0, 6.5, 41]} center zIndexRange={[5, 0]} style={{ pointerEvents: 'none' }}>
        <div style={{ fontSize: 7, fontWeight: 700, color: '#DC2626', whiteSpace: 'nowrap', background: 'rgba(255,255,255,0.85)', padding: '1px 6px', borderRadius: 3, border: '1px solid #DC2626' }}>SECURITY CHECKPOINT</div>
      </Html>
    </group>
  );
}

/* ========== Container Block ========== */

function ContainerBlock({ position, rows, cols, maxStack, label }: {
  position: [number, number, number]; rows: number; cols: number; maxStack: number; label?: string;
}) {
  const cLen = 3.5; const cWid = 1.8; const cHgt = 1.0; const gapX = 0.3; const gapZ = 0.4;
  const containers = useMemo(() => {
    const arr: { pos: [number, number, number]; color: string }[] = [];
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const stack = Math.max(1, Math.floor(Math.random() * (maxStack + 1)));
        for (let s = 0; s < stack; s++) {
          arr.push({ pos: [r * (cLen + gapX) - (rows * (cLen + gapX)) / 2 + cLen / 2, cHgt / 2 + s * cHgt + 0.1, c * (cWid + gapZ) - (cols * (cWid + gapZ)) / 2 + cWid / 2], color: CONTAINER_COLORS[(r + c + s) % CONTAINER_COLORS.length] });
        }
      }
    }
    return arr;
  }, [rows, cols, maxStack]);
  return (
    <group position={position}>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.02, 0]}><planeGeometry args={[rows * (cLen + gapX) + 2, cols * (cWid + gapZ) + 2]} /><meshStandardMaterial color="#8B8F85" roughness={0.95} /></mesh>
      {containers.map((c, i) => (<mesh key={i} position={c.pos} castShadow><boxGeometry args={[cLen, cHgt, cWid]} /><meshStandardMaterial color={c.color} roughness={0.7} metalness={0.1} /></mesh>))}
      {label && (<Html position={[0, maxStack * cHgt + 2, 0]} center zIndexRange={[5, 0]} style={{ pointerEvents: 'none' }}><div style={{ fontSize: 7, fontWeight: 700, color: '#374151', whiteSpace: 'nowrap', background: 'rgba(255,255,255,0.7)', padding: '1px 4px', borderRadius: 2 }}>{label}</div></Html>)}
    </group>
  );
}

/* ========== RTG Crane ========== */

function RTGCraneYard({ position, blockWidth }: { position: [number, number, number]; blockWidth: number }) {
  const spanZ = blockWidth + 4;
  return (
    <group position={position}>
      <mesh position={[-3, 6, -spanZ / 2]} castShadow><boxGeometry args={[0.4, 12, 0.4]} /><meshStandardMaterial color="#374151" metalness={0.4} roughness={0.5} /></mesh>
      <mesh position={[3, 6, -spanZ / 2]} castShadow><boxGeometry args={[0.4, 12, 0.4]} /><meshStandardMaterial color="#374151" metalness={0.4} roughness={0.5} /></mesh>
      <mesh position={[-3, 6, spanZ / 2]} castShadow><boxGeometry args={[0.4, 12, 0.4]} /><meshStandardMaterial color="#374151" metalness={0.4} roughness={0.5} /></mesh>
      <mesh position={[3, 6, spanZ / 2]} castShadow><boxGeometry args={[0.4, 12, 0.4]} /><meshStandardMaterial color="#374151" metalness={0.4} roughness={0.5} /></mesh>
      <mesh position={[0, 12.5, 0]} castShadow><boxGeometry args={[7, 1, spanZ + 1]} /><meshStandardMaterial color="#D97706" metalness={0.3} roughness={0.5} /></mesh>
      <mesh position={[0, 13.5, 0]} castShadow><boxGeometry args={[4, 1.5, 3]} /><meshStandardMaterial color="#D97706" metalness={0.3} roughness={0.5} /></mesh>
      <mesh position={[0, 7, 0]}><boxGeometry args={[0.1, 12, 0.1]} /><meshStandardMaterial color="#1F2937" /></mesh>
      <mesh position={[0, 1.5, 0]}><boxGeometry args={[3.5, 0.3, 1.8]} /><meshStandardMaterial color="#DC2626" metalness={0.3} roughness={0.5} /></mesh>
      <mesh position={[0, 14.5, 0]}><sphereGeometry args={[0.3, 8, 8]} /><meshStandardMaterial color="#10B981" emissive="#10B981" emissiveIntensity={0.8} /></mesh>
    </group>
  );
}

/* ========== Animated Truck ========== */

function AnimatedTruck({ roadZ, startX, endX, speed, color, hasContainer }: {
  roadZ: number; startX: number; endX: number; speed: number; color: string; hasContainer: boolean;
}) {
  const ref = useRef<THREE.Group>(null);
  const direction = endX > startX ? 1 : -1;
  useFrame((_, delta) => {
    if (!ref.current) return;
    ref.current.position.x += speed * direction * delta;
    if (direction > 0 && ref.current.position.x > endX) ref.current.position.x = startX;
    if (direction < 0 && ref.current.position.x < endX) ref.current.position.x = startX;
  });
  return (
    <group ref={ref} position={[startX, 0, roadZ]} rotation={[0, direction > 0 ? 0 : Math.PI, 0]}>
      <mesh position={[2.5, 1.2, 0]} castShadow><boxGeometry args={[2, 2, 2]} /><meshStandardMaterial color={color} roughness={0.6} metalness={0.1} /></mesh>
      <mesh position={[3.55, 1.6, 0]}><boxGeometry args={[0.05, 0.8, 1.6]} /><meshStandardMaterial color="#1E3A5F" metalness={0.5} roughness={0.1} /></mesh>
      <mesh position={[0, 0.4, 0]} castShadow><boxGeometry args={[6, 0.4, 2.2]} /><meshStandardMaterial color="#1F2937" roughness={0.7} metalness={0.3} /></mesh>
      {[-2, 0, 2].map((wx, i) => (
        <group key={i}>
          <mesh position={[wx, 0.3, 1.2]} rotation={[Math.PI / 2, 0, 0]}><cylinderGeometry args={[0.4, 0.4, 0.3, 8]} /><meshStandardMaterial color="#1F2937" roughness={0.8} /></mesh>
          <mesh position={[wx, 0.3, -1.2]} rotation={[Math.PI / 2, 0, 0]}><cylinderGeometry args={[0.4, 0.4, 0.3, 8]} /><meshStandardMaterial color="#1F2937" roughness={0.8} /></mesh>
        </group>
      ))}
      {hasContainer && (<mesh position={[-1, 1.6, 0]} castShadow><boxGeometry args={[3.5, 1, 1.8]} /><meshStandardMaterial color={CONTAINER_COLORS[Math.abs(Math.floor(startX)) % CONTAINER_COLORS.length]} roughness={0.7} metalness={0.1} /></mesh>)}
    </group>
  );
}

/* ========== Static Truck ========== */

function TruckModel({ position, rotation = 0, color = '#E5E7EB', hasContainer = true }: {
  position: [number, number, number]; rotation?: number; color?: string; hasContainer?: boolean;
}) {
  return (
    <group position={position} rotation={[0, rotation, 0]}>
      <mesh position={[2.5, 1.2, 0]} castShadow><boxGeometry args={[2, 2, 2]} /><meshStandardMaterial color={color} roughness={0.6} metalness={0.1} /></mesh>
      <mesh position={[3.55, 1.6, 0]}><boxGeometry args={[0.05, 0.8, 1.6]} /><meshStandardMaterial color="#1E3A5F" metalness={0.5} roughness={0.1} /></mesh>
      <mesh position={[0, 0.4, 0]} castShadow><boxGeometry args={[6, 0.4, 2.2]} /><meshStandardMaterial color="#1F2937" roughness={0.7} metalness={0.3} /></mesh>
      {[-2, 0, 2].map((wx, i) => (
        <group key={i}>
          <mesh position={[wx, 0.3, 1.2]} rotation={[Math.PI / 2, 0, 0]}><cylinderGeometry args={[0.4, 0.4, 0.3, 8]} /><meshStandardMaterial color="#1F2937" roughness={0.8} /></mesh>
          <mesh position={[wx, 0.3, -1.2]} rotation={[Math.PI / 2, 0, 0]}><cylinderGeometry args={[0.4, 0.4, 0.3, 8]} /><meshStandardMaterial color="#1F2937" roughness={0.8} /></mesh>
        </group>
      ))}
      {hasContainer && (<mesh position={[-1, 1.6, 0]} castShadow><boxGeometry args={[3.5, 1, 1.8]} /><meshStandardMaterial color={CONTAINER_COLORS[Math.floor(Math.random() * 4)]} roughness={0.7} metalness={0.1} /></mesh>)}
    </group>
  );
}

/* ========== STS Crane ========== */

function STSCraneModel({ position, status }: { position: [number, number, number]; status: string }) {
  const bodyColor = status === 'operational' ? '#0A4D8C' : status === 'idle' ? '#D97706' : '#9CA3AF';
  return (
    <group position={position}>
      <mesh position={[-4, 12, 0]} castShadow><boxGeometry args={[0.8, 24, 0.8]} /><meshStandardMaterial color="#1F2937" metalness={0.4} roughness={0.5} /></mesh>
      <mesh position={[4, 12, 0]} castShadow><boxGeometry args={[0.8, 24, 0.8]} /><meshStandardMaterial color="#1F2937" metalness={0.4} roughness={0.5} /></mesh>
      <mesh position={[0, 24, 0]} castShadow><boxGeometry args={[9, 1.5, 1.2]} /><meshStandardMaterial color={bodyColor} metalness={0.3} roughness={0.5} /></mesh>
      <mesh position={[0, 26, 0]} castShadow><boxGeometry args={[6, 3, 3]} /><meshStandardMaterial color={bodyColor} metalness={0.3} roughness={0.5} /></mesh>
      <mesh position={[0, 25.5, -12]} castShadow><boxGeometry args={[1.5, 1, 24]} /><meshStandardMaterial color="#DC2626" metalness={0.2} roughness={0.5} /></mesh>
      <mesh position={[0, 25.5, 8]} castShadow><boxGeometry args={[1.5, 1, 10]} /><meshStandardMaterial color="#DC2626" metalness={0.2} roughness={0.5} /></mesh>
      <mesh position={[0, 28, 0]}><sphereGeometry args={[0.3, 8, 8]} /><meshStandardMaterial color={status === 'operational' ? '#10B981' : '#F59E0B'} emissive={status === 'operational' ? '#10B981' : '#F59E0B'} emissiveIntensity={0.8} /></mesh>
    </group>
  );
}

/* ========== Vessel Body ========== */

function VesselBody({ name, loa, position, berthLength }: {
  name: string; loa: number; position: [number, number, number]; berthLength: number;
}) {
  const vesselLen = loa * M2U;
  const beam = 6;
  const hullHeight = 3.5;
  const containerCols = Math.max(2, Math.floor(vesselLen / 5));
  return (
    <group position={position}>
      <mesh castShadow><boxGeometry args={[vesselLen, hullHeight, beam]} /><meshStandardMaterial color="#1F2937" roughness={0.6} metalness={0.2} /></mesh>
      <mesh position={[vesselLen / 2 + 1.5, 0, 0]} rotation={[0, Math.PI / 4, 0]} castShadow><boxGeometry args={[beam * 0.7, hullHeight, beam * 0.7]} /><meshStandardMaterial color="#1F2937" roughness={0.6} metalness={0.2} /></mesh>
      <mesh position={[0, -0.8, 0]}><boxGeometry args={[vesselLen + 0.1, 0.6, beam + 0.1]} /><meshStandardMaterial color="#991B1B" roughness={0.7} /></mesh>
      <mesh position={[0, hullHeight / 2 + 0.1, 0]} castShadow><boxGeometry args={[vesselLen, 0.2, beam]} /><meshStandardMaterial color="#6B7280" roughness={0.7} metalness={0.1} /></mesh>
      {Array.from({ length: containerCols }).map((_, col) =>
        [0, 1].map(row =>
          [0, 1].map(layer => (
            <mesh key={`c-${col}-${row}-${layer}`} position={[-vesselLen / 2 + 3 + col * (vesselLen - 6) / Math.max(containerCols - 1, 1), hullHeight / 2 + 0.8 + layer * 1.1, -1.2 + row * 2.4]} castShadow>
              <boxGeometry args={[4, 1, 2]} /><meshStandardMaterial color={CONTAINER_COLORS[(col + row + layer) % CONTAINER_COLORS.length]} roughness={0.6} metalness={0.2} />
            </mesh>
          ))
        )
      )}
      <group position={[-vesselLen / 2 + 2.5, hullHeight / 2, 0]}>
        <mesh position={[0, 3, 0]} castShadow><boxGeometry args={[4, 6, beam * 0.85]} /><meshStandardMaterial color="#E5E7EB" roughness={0.6} /></mesh>
        <mesh position={[2.05, 4.5, 0]}><boxGeometry args={[0.1, 1.5, beam * 0.75]} /><meshStandardMaterial color="#1E3A5F" metalness={0.5} roughness={0.1} /></mesh>
        <mesh position={[0, 6.5, 0]} castShadow><boxGeometry args={[2, 3, 2]} /><meshStandardMaterial color="#0A4D8C" roughness={0.5} /></mesh>
        <mesh position={[0, 8, 0]} castShadow><boxGeometry args={[2.1, 0.5, 2.1]} /><meshStandardMaterial color="#DC2626" roughness={0.5} /></mesh>
      </group>
      <Html position={[0, 10, 0]} center zIndexRange={[10, 0]} style={{ pointerEvents: 'none' }}>
        <div style={{ background: 'rgba(10,77,140,0.85)', color: 'white', borderRadius: 3, padding: '2px 6px', fontSize: 8, fontWeight: 600, whiteSpace: 'nowrap', userSelect: 'none', letterSpacing: 0.3 }}>{name}</div>
      </Html>
    </group>
  );
}

/* ========== Anchorage Vessel (interactive, draggable) ========== */

function AnchorageVessel({ vessel, position, onDragStart, onClick, isDragging }: {
  vessel: UIVessel; position: [number, number, number]; onDragStart: () => void; onClick: () => void; isDragging: boolean;
}) {
  const [hovered, setHovered] = useState(false);
  const groupRef = useRef<THREE.Group>(null);
  const vesselLen = Math.max(vessel.loa * M2U, 12);
  const beam = 5;
  const hullHeight = 3;

  useFrame((state) => {
    if (groupRef.current && !isDragging) {
      groupRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 0.5 + parseInt(vessel.id) * 1.7) * 0.15;
    }
  });

  return (
    <group ref={groupRef} position={position} visible={!isDragging}>
      {/* Hull */}
      <mesh castShadow><boxGeometry args={[vesselLen, hullHeight, beam]} /><meshStandardMaterial color="#1F2937" roughness={0.6} metalness={0.2} /></mesh>
      {/* Bow */}
      <mesh position={[vesselLen / 2 + 1, 0, 0]} rotation={[0, Math.PI / 4, 0]} castShadow><boxGeometry args={[beam * 0.6, hullHeight, beam * 0.6]} /><meshStandardMaterial color="#1F2937" roughness={0.6} metalness={0.2} /></mesh>
      {/* Waterline */}
      <mesh position={[0, -0.6, 0]}><boxGeometry args={[vesselLen + 0.1, 0.5, beam + 0.1]} /><meshStandardMaterial color="#991B1B" roughness={0.7} /></mesh>
      {/* Deck */}
      <mesh position={[0, hullHeight / 2 + 0.1, 0]}><boxGeometry args={[vesselLen, 0.15, beam]} /><meshStandardMaterial color="#6B7280" roughness={0.7} /></mesh>
      {/* Bridge */}
      <group position={[-vesselLen / 2 + 2, hullHeight / 2, 0]}>
        <mesh position={[0, 2, 0]} castShadow><boxGeometry args={[3, 4, beam * 0.75]} /><meshStandardMaterial color="#E5E7EB" roughness={0.6} /></mesh>
        <mesh position={[0, 4.5, 0]} castShadow><boxGeometry args={[1.5, 2, 1.5]} /><meshStandardMaterial color="#0A4D8C" roughness={0.5} /></mesh>
      </group>
      {/* Containers */}
      {Array.from({ length: Math.max(2, Math.floor(vesselLen / 6)) }).map((_, i) => (
        <mesh key={i} position={[-vesselLen / 2 + 5 + i * (vesselLen - 8) / Math.max(1, Math.floor(vesselLen / 6) - 1), hullHeight / 2 + 0.7, 0]} castShadow>
          <boxGeometry args={[3.5, 0.9, beam * 0.7]} /><meshStandardMaterial color={CONTAINER_COLORS[i % CONTAINER_COLORS.length]} roughness={0.6} metalness={0.2} />
        </mesh>
      ))}

      {/* Hover ring */}
      {hovered && (
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -hullHeight / 2 - 0.2, 0]}>
          <ringGeometry args={[vesselLen / 2 + 1, vesselLen / 2 + 2, 32]} />
          <meshStandardMaterial color="#FBBF24" transparent opacity={0.4} />
        </mesh>
      )}

      {/* Invisible interaction plane */}
      <mesh
        onPointerDown={(e) => {
          e.stopPropagation();
          const startTime = Date.now();
          const startPos = { x: (e as any).clientX || 0, y: (e as any).clientY || 0 };
          let dragged = false;
          const handleMove = (ev: PointerEvent) => {
            const dx = ev.clientX - startPos.x;
            const dy = ev.clientY - startPos.y;
            if (Math.sqrt(dx * dx + dy * dy) > 8 && !dragged) {
              dragged = true;
              document.removeEventListener('pointermove', handleMove);
              document.removeEventListener('pointerup', handleUp);
              onDragStart();
            }
          };
          const handleUp = () => {
            document.removeEventListener('pointermove', handleMove);
            document.removeEventListener('pointerup', handleUp);
            if (!dragged && Date.now() - startTime < 500) onClick();
          };
          document.addEventListener('pointermove', handleMove);
          document.addEventListener('pointerup', handleUp);
        }}
        onPointerEnter={(e) => { e.stopPropagation(); setHovered(true); document.body.style.cursor = 'grab'; }}
        onPointerLeave={() => { setHovered(false); document.body.style.cursor = 'default'; }}
      >
        <boxGeometry args={[vesselLen + 4, hullHeight + 4, beam + 2]} />
        <meshStandardMaterial transparent opacity={0} depthWrite={false} />
      </mesh>

      {/* Name + IMO label */}
      <Html position={[0, 8, 0]} center zIndexRange={[10, 0]} style={{ pointerEvents: 'none' }}>
        <div style={{
          background: hovered ? 'rgba(217,119,6,0.95)' : 'rgba(10,77,140,0.9)',
          color: 'white', borderRadius: 4, padding: '3px 8px', fontSize: 9, fontWeight: 600,
          whiteSpace: 'nowrap', userSelect: 'none', textAlign: 'center',
          border: hovered ? '1px solid #FBBF24' : '1px solid transparent',
        }}>
          <div>{vessel.name}</div>
          <div style={{ fontSize: 7, opacity: 0.8 }}>IMO: {vessel.imo}</div>
        </div>
      </Html>
    </group>
  );
}

/* ========== Drag Ghost (follows mouse during drag) ========== */

function DragGhostVessel({ vessel, layout, dragState, setDragState, onDrop }: {
  vessel: UIVessel;
  layout: ReturnType<typeof computeBerthLayout>;
  dragState: DragState;
  setDragState: (state: DragState | null) => void;
  onDrop: (vesselId: string, berthId: string) => void;
}) {
  const { camera, raycaster, pointer, gl } = useThree();
  const groupRef = useRef<THREE.Group>(null);
  const waterPlane = useMemo(() => new THREE.Plane(new THREE.Vector3(0, 1, 0), 0.5), []);
  const vesselLen = Math.max(vessel.loa * M2U, 12);

  useFrame(() => {
    if (!groupRef.current) return;
    raycaster.setFromCamera(pointer, camera);
    const intersection = new THREE.Vector3();
    raycaster.ray.intersectPlane(waterPlane, intersection);
    if (intersection) {
      groupRef.current.position.set(intersection.x, 2, intersection.z);

      // Determine hovered berth
      let hoveredBerthId: string | null = null;
      for (const { berth, position, width } of layout) {
        const berthXMin = position[0] - width / 2;
        const berthXMax = position[0] + width / 2;
        if (intersection.x >= berthXMin && intersection.x <= berthXMax && intersection.z >= -25 && intersection.z <= 15) {
          hoveredBerthId = berth.id;
          break;
        }
      }

      if (hoveredBerthId !== dragState.hoveredBerthId) {
        setDragState({ ...dragState, hoveredBerthId });
      }
    }
  });

  useEffect(() => {
    const handlePointerUp = () => {
      if (dragState.hoveredBerthId) {
        onDrop(vessel.id, dragState.hoveredBerthId);
      } else {
        setDragState(null);
      }
      document.body.style.cursor = 'default';
    };
    gl.domElement.addEventListener('pointerup', handlePointerUp);
    document.body.style.cursor = 'grabbing';
    return () => {
      gl.domElement.removeEventListener('pointerup', handlePointerUp);
      document.body.style.cursor = 'default';
    };
  }, [dragState.hoveredBerthId, vessel.id, gl.domElement, onDrop, setDragState]);

  return (
    <group ref={groupRef}>
      <mesh><boxGeometry args={[vesselLen, 3, 5]} /><meshStandardMaterial color="#0A4D8C" transparent opacity={0.5} /></mesh>
      <mesh position={[vesselLen / 2 + 1, 0, 0]} rotation={[0, Math.PI / 4, 0]}><boxGeometry args={[3.5, 3, 3.5]} /><meshStandardMaterial color="#0A4D8C" transparent opacity={0.5} /></mesh>
      <Html position={[0, 6, 0]} center style={{ pointerEvents: 'none' }}>
        <div style={{ background: 'rgba(10,77,140,0.95)', color: 'white', borderRadius: 4, padding: '3px 8px', fontSize: 9, fontWeight: 600, whiteSpace: 'nowrap', border: '1px dashed #FBBF24' }}>
          {vessel.name} (dragging)
        </div>
      </Html>
    </group>
  );
}

/* ========== Berth Marker with drop highlight ========== */

function BerthMarker({ berth, position, width, onClick, isSelected, dropHighlight }: {
  berth: Berth; position: [number, number, number]; width: number;
  onClick: () => void; isSelected: boolean;
  dropHighlight?: 'valid' | 'warning' | 'error' | null;
}) {
  const [hovered, setHovered] = useState(false);
  const statusColor = berth.status === 'available' ? '#10B981' : berth.status === 'occupied' ? '#0A4D8C' : '#9CA3AF';
  const statusColorLight = berth.status === 'available' ? '#D1FAE5' : berth.status === 'occupied' ? '#DBEAFE' : '#E5E7EB';
  const berthDepth = 12;

  const dropColor = dropHighlight === 'valid' ? '#10B981' : dropHighlight === 'warning' ? '#FBBF24' : dropHighlight === 'error' ? '#DC2626' : null;

  const formatDate = (d: Date) => {
    try { return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }); }
    catch { return 'N/A'; }
  };

  return (
    <group position={position}>
      {/* Berth floor */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.05, -berthDepth / 2]} receiveShadow>
        <planeGeometry args={[width - 1, berthDepth]} />
        <meshStandardMaterial color={statusColorLight} roughness={0.8} />
      </mesh>
      {/* Borders */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[-width / 2 + 0.15, 0.06, -berthDepth / 2]}>
        <planeGeometry args={[0.3, berthDepth + 2]} /><meshStandardMaterial color={statusColor} />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[width / 2 - 0.15, 0.06, -berthDepth / 2]}>
        <planeGeometry args={[0.3, berthDepth + 2]} /><meshStandardMaterial color={statusColor} />
      </mesh>
      {/* Hover/Selection glow */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.07, -berthDepth / 2]}>
        <planeGeometry args={[width - 1, berthDepth]} />
        <meshStandardMaterial
          color={isSelected ? '#FBBF24' : statusColor}
          transparent opacity={(hovered || isSelected) ? (isSelected ? 0.4 : 0.25) : 0}
          emissive={isSelected ? '#FBBF24' : statusColor} emissiveIntensity={(hovered || isSelected) ? 0.5 : 0}
        />
      </mesh>
      {/* Drop highlight overlay */}
      {dropColor && (
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.08, -berthDepth / 2]}>
          <planeGeometry args={[width - 1, berthDepth]} />
          <meshStandardMaterial color={dropColor} transparent opacity={0.35} emissive={dropColor} emissiveIntensity={0.8} />
        </mesh>
      )}
      {/* Invisible interaction plane */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.1, -berthDepth / 2]}
        onClick={(e: any) => { e.stopPropagation(); onClick(); }}
        onPointerEnter={(e: any) => { e.stopPropagation(); setHovered(true); document.body.style.cursor = 'pointer'; }}
        onPointerLeave={() => { setHovered(false); document.body.style.cursor = 'default'; }}
      >
        <planeGeometry args={[width - 1, berthDepth]} />
        <meshStandardMaterial transparent opacity={0} depthWrite={false} />
      </mesh>
      {/* Fender */}
      <mesh position={[0, 0.5, -berthDepth + 0.3]} castShadow>
        <boxGeometry args={[width - 2, 1, 0.5]} /><meshStandardMaterial color="#1F2937" roughness={0.9} />
      </mesh>
      {/* Berth name */}
      <Html position={[0, 0.3, 2]} center zIndexRange={[5, 0]} style={{ pointerEvents: 'none' }}>
        <div style={{ fontSize: 8, fontWeight: 700, color: statusColor, textShadow: '0 0 3px rgba(255,255,255,0.9), 0 0 6px rgba(255,255,255,0.6)', whiteSpace: 'nowrap', userSelect: 'none', letterSpacing: 0.5 }}>{berth.name}</div>
      </Html>
      {/* Drop indicator label */}
      {dropHighlight && (
        <Html position={[0, 4, -berthDepth / 2]} center zIndexRange={[12, 0]} style={{ pointerEvents: 'none' }}>
          <div style={{
            padding: '3px 10px', borderRadius: 4, fontSize: 10, fontWeight: 700,
            backgroundColor: dropHighlight === 'valid' ? '#D1FAE5' : dropHighlight === 'warning' ? '#FEF3C7' : '#FEE2E2',
            color: dropHighlight === 'valid' ? '#059669' : dropHighlight === 'warning' ? '#D97706' : '#DC2626',
            border: `1.5px solid ${dropColor}`, whiteSpace: 'nowrap',
          }}>
            {dropHighlight === 'valid' ? 'Compatible' : dropHighlight === 'warning' ? 'Warning' : 'Incompatible'}
          </div>
        </Html>
      )}
      {/* Hover detail card */}
      {hovered && !dropHighlight && (
        <Html position={[0, 10, -berthDepth / 2]} center zIndexRange={[10, 0]} style={{ pointerEvents: 'none' }}>
          {berth.status === 'occupied' && berth.currentVessel ? (
            <div style={{ background: 'rgba(255,255,255,0.97)', borderRadius: 8, padding: '10px 14px', boxShadow: '0 4px 16px rgba(0,0,0,0.25)', border: '2px solid #0A4D8C', minWidth: 200, userSelect: 'none' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}><Ship style={{ width: 13, height: 13, color: '#0A4D8C' }} /><span style={{ fontWeight: 700, fontSize: 12, color: '#0A4D8C' }}>{berth.name}</span></div>
                <span style={{ fontSize: 8, fontWeight: 600, color: 'white', background: '#0A4D8C', borderRadius: 3, padding: '1px 5px' }}>Occupied</span>
              </div>
              <div style={{ fontSize: 11, fontWeight: 600, color: '#1F2937', marginBottom: 4 }}>{berth.currentVessel.name}</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '3px 12px', fontSize: 10, color: '#374151' }}>
                <div><span style={{ color: '#9CA3AF' }}>LOA:</span> {berth.currentVessel.loa}m</div>
                <div><span style={{ color: '#9CA3AF' }}>Berth:</span> {berth.length}m</div>
                <div><span style={{ color: '#9CA3AF' }}>ETA:</span> {formatDate(berth.currentVessel.eta)}</div>
                <div><span style={{ color: '#9CA3AF' }}>ETD:</span> {formatDate(berth.currentVessel.etd)}</div>
                <div><span style={{ color: '#9CA3AF' }}>Draft:</span> {berth.maxDraft}m</div>
                <div><span style={{ color: '#9CA3AF' }}>Cranes:</span> {berth.cranes.filter(c => c.status === 'operational').length}/{berth.cranes.length}</div>
              </div>
            </div>
          ) : (
            <div style={{ background: 'rgba(255,255,255,0.97)', borderRadius: 8, padding: '10px 14px', boxShadow: '0 4px 16px rgba(0,0,0,0.25)', border: `2px solid ${berth.status === 'available' ? '#10B981' : '#9CA3AF'}`, minWidth: 180, userSelect: 'none' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}><Calendar style={{ width: 13, height: 13, color: berth.status === 'available' ? '#10B981' : '#9CA3AF' }} /><span style={{ fontWeight: 700, fontSize: 12, color: berth.status === 'available' ? '#059669' : '#6B7280' }}>{berth.name}</span></div>
                <span style={{ fontSize: 8, fontWeight: 600, color: 'white', background: berth.status === 'available' ? '#10B981' : '#9CA3AF', borderRadius: 3, padding: '1px 5px' }}>{berth.status === 'available' ? 'Available' : 'Maintenance'}</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '3px 12px', fontSize: 10, color: '#374151' }}>
                <div><span style={{ color: '#9CA3AF' }}>Length:</span> {berth.length}m</div>
                <div><span style={{ color: '#9CA3AF' }}>Max LOA:</span> {berth.maxLOA}m</div>
                <div><span style={{ color: '#9CA3AF' }}>Max Draft:</span> {berth.maxDraft}m</div>
                <div><span style={{ color: '#9CA3AF' }}>Max Beam:</span> {berth.maxBeam}m</div>
                <div><span style={{ color: '#9CA3AF' }}>Cranes:</span> {berth.cranes.length}</div>
                <div><span style={{ color: '#9CA3AF' }}>Reefer:</span> {berth.reeferPoints} pts</div>
              </div>
            </div>
          )}
        </Html>
      )}
    </group>
  );
}

/* ========== Anchorage Area (zone boundary + vessels) ========== */

function AnchorageArea({ vessels, layout, onDragStart, onClick, dragVesselId }: {
  vessels: UIVessel[];
  layout: ReturnType<typeof computeBerthLayout>;
  onDragStart: (vessel: UIVessel) => void;
  onClick: (vessel: UIVessel, pos: [number, number, number]) => void;
  dragVesselId: string | null;
}) {
  const totalSpan = layout.length > 0
    ? (layout[layout.length - 1].position[0] + layout[layout.length - 1].width / 2) - (layout[0].position[0] - layout[0].width / 2)
    : 200;
  const anchorageWidth = Math.max(totalSpan + 80, 200);
  const centerZ = -80;
  const halfW = anchorageWidth / 2;
  const halfD = 20;
  const borderThickness = 0.5;

  if (vessels.length === 0) return null;

  const colCount = Math.max(1, Math.floor(anchorageWidth / 28));

  return (
    <group>
      {/* Boundary rectangle (4 edges) on water surface */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.3, centerZ - halfD]}><planeGeometry args={[anchorageWidth, borderThickness]} /><meshStandardMaterial color="#D97706" transparent opacity={0.6} /></mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.3, centerZ + halfD]}><planeGeometry args={[anchorageWidth, borderThickness]} /><meshStandardMaterial color="#D97706" transparent opacity={0.6} /></mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[-halfW, -0.3, centerZ]}><planeGeometry args={[borderThickness, halfD * 2]} /><meshStandardMaterial color="#D97706" transparent opacity={0.6} /></mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[halfW, -0.3, centerZ]}><planeGeometry args={[borderThickness, halfD * 2]} /><meshStandardMaterial color="#D97706" transparent opacity={0.6} /></mesh>

      {/* Subtle fill on water */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.35, centerZ]}>
        <planeGeometry args={[anchorageWidth, halfD * 2]} />
        <meshStandardMaterial color="#D97706" transparent opacity={0.06} />
      </mesh>

      {/* Corner buoys */}
      {[[-halfW, centerZ - halfD], [halfW, centerZ - halfD], [-halfW, centerZ + halfD], [halfW, centerZ + halfD]].map(([bx, bz], i) => (
        <group key={`buoy-${i}`} position={[bx, 0, bz]}>
          <mesh position={[0, 0.5, 0]}><sphereGeometry args={[1, 8, 8]} /><meshStandardMaterial color="#DC2626" emissive="#DC2626" emissiveIntensity={0.3} /></mesh>
          <mesh position={[0, -0.5, 0]}><cylinderGeometry args={[0.15, 0.15, 2, 6]} /><meshStandardMaterial color="#6B7280" /></mesh>
        </group>
      ))}

      {/* Label */}
      <Html position={[0, 3, centerZ + halfD + 3]} center zIndexRange={[8, 0]} style={{ pointerEvents: 'none' }}>
        <div style={{
          background: 'rgba(217,119,6,0.9)', color: 'white', borderRadius: 6, padding: '4px 12px',
          fontSize: 10, fontWeight: 700, letterSpacing: 1, whiteSpace: 'nowrap', userSelect: 'none',
        }}>
          ANCHORAGE AREA — {vessels.length} vessel{vessels.length !== 1 ? 's' : ''} waiting
        </div>
      </Html>

      {/* Vessels arranged in grid */}
      {vessels.map((vessel, idx) => {
        const col = idx % colCount;
        const row = Math.floor(idx / colCount);
        const vx = -anchorageWidth / 2 + 20 + col * 28;
        const vz = centerZ - 10 + row * 18;
        return (
          <AnchorageVessel
            key={vessel.id}
            vessel={vessel}
            position={[vx, 0, vz]}
            onDragStart={() => onDragStart(vessel)}
            onClick={() => onClick(vessel, [vx, 0, vz])}
            isDragging={dragVesselId === vessel.id}
          />
        );
      })}
    </group>
  );
}

/* ========== Full berth + terminal scene ========== */

function BerthScene({ berths, onBerthClick, selectedBerthId, terminalName, anchorageVessels, dragState, onDragStart, onDragStateChange, onDrop, onVesselClick, validateDrop }: Terminal3DViewProps & {
  anchorageVessels: UIVessel[];
  dragState: DragState | null;
  onDragStart: (vessel: UIVessel) => void;
  onDragStateChange: (state: DragState | null) => void;
  onDrop: (vesselId: string, berthId: string) => void;
  onVesselClick: (vessel: UIVessel, position: [number, number, number]) => void;
  validateDrop: (vessel: UIVessel, berth: Berth) => { status: 'valid' | 'warning' | 'error' };
}) {
  const layout = useMemo(() => computeBerthLayout(berths), [berths]);

  const totalSpan = useMemo(() => {
    if (layout.length === 0) return 200;
    return (layout[layout.length - 1].position[0] + layout[layout.length - 1].width / 2) - (layout[0].position[0] - layout[0].width / 2);
  }, [layout]);

  // Pre-compute berth validations during drag
  const berthValidations = useMemo(() => {
    if (!dragState?.isDragging) return new Map<string, 'valid' | 'warning' | 'error'>();
    const map = new Map<string, 'valid' | 'warning' | 'error'>();
    berths.forEach(b => {
      const result = validateDrop(dragState.vessel, b);
      map.set(b.id, result.status);
    });
    return map;
  }, [dragState?.isDragging, dragState?.vessel, berths, validateDrop]);

  // Terminal name position (center of the layout)
  const terminalNamePosition = useMemo(() => {
    if (layout.length === 0) return [0, 0, 50] as [number, number, number];
    const centerX = (layout[0].position[0] + layout[layout.length - 1].position[0]) / 2;
    return [centerX, 0, 50] as [number, number, number];
  }, [layout]);

  const exportBlocks = useMemo(() => {
    const blocks: { x: number; z: number; rows: number; cols: number; stack: number; label: string }[] = [];
    const blockSpacing = 22; const startX = -totalSpan / 2 + 15; const count = Math.max(3, Math.floor(totalSpan / blockSpacing));
    for (let i = 0; i < count; i++) blocks.push({ x: startX + i * blockSpacing, z: 22 + (i % 2) * 6, rows: 4 + (i % 3), cols: 3, stack: 3 + (i % 2), label: `E-${String(i + 1).padStart(2, '0')}` });
    return blocks;
  }, [totalSpan]);

  const importBlocks = useMemo(() => {
    const blocks: { x: number; z: number; rows: number; cols: number; stack: number; label: string }[] = [];
    const blockSpacing = 22; const startX = -totalSpan / 2 + 15; const count = Math.max(3, Math.floor(totalSpan / blockSpacing));
    for (let i = 0; i < count; i++) blocks.push({ x: startX + i * blockSpacing, z: 83 + (i % 2) * 5, rows: 4 + (i % 2), cols: 3, stack: 2 + (i % 3), label: `I-${String(i + 1).padStart(2, '0')}` });
    return blocks;
  }, [totalSpan]);

  const generalBlocks = useMemo(() => {
    const blocks: { x: number; z: number; rows: number; cols: number; stack: number; label: string }[] = [];
    const blockSpacing = 20; const startX = -totalSpan / 2 + 12; const count = Math.max(4, Math.floor(totalSpan / blockSpacing));
    for (let i = 0; i < count; i++) blocks.push({ x: startX + i * blockSpacing, z: 52 + (i % 3) * 5, rows: 5 + (i % 2), cols: 4, stack: 3 + (i % 2), label: `Y-${String(i + 1).padStart(2, '0')}` });
    return blocks;
  }, [totalSpan]);

  const staticTrucks = useMemo(() => {
    const trucks: { x: number; z: number; rot: number; color: string; hasContainer: boolean }[] = [];
    const tc = ['#E5E7EB', '#F3F4F6', '#D1D5DB', '#FBBF24', '#0891B2'];
    for (let i = 0; i < 4; i++) trucks.push({ x: -totalSpan / 3 + i * 25, z: 32, rot: 0, color: tc[i % tc.length], hasContainer: i % 2 === 0 });
    for (let i = 0; i < 3; i++) trucks.push({ x: totalSpan / 4 - i * 30, z: 92, rot: Math.PI, color: tc[(i + 2) % tc.length], hasContainer: true });
    return trucks;
  }, [totalSpan]);

  const halfSpan = totalSpan / 2;

  return (
    <>
      {/* Berth markers with drop highlight */}
      {layout.map(({ berth, position, width }) => {
        const dropHL = dragState?.isDragging
          ? (dragState.hoveredBerthId === berth.id ? berthValidations.get(berth.id) || null : (berthValidations.get(berth.id) ? (() => { const v = berthValidations.get(berth.id)!; return v; })() : null))
          : null;
        // Only show strong highlight on hovered berth, subtle on others during drag
        const highlight = dragState?.isDragging
          ? (dragState.hoveredBerthId === berth.id ? berthValidations.get(berth.id) || null : null)
          : null;

        return (
          <BerthMarker
            key={berth.id}
            berth={berth}
            position={position}
            width={width}
            onClick={() => onBerthClick(berth)}
            isSelected={berth.id === selectedBerthId}
            dropHighlight={highlight}
          />
        );
      })}

      {/* STS Cranes */}
      {layout.flatMap(({ berth, position, width }) => {
        const stsCranes = berth.cranes.filter(c => c.type === 'STS');
        return stsCranes.map((crane, i) => {
          const spacing = width / (stsCranes.length + 1);
          return (<STSCraneModel key={crane.id} position={[position[0] - width / 2 + spacing * (i + 1), 0, 8]} status={crane.status} />);
        });
      })}

      {/* Vessels at occupied berths */}
      {layout.filter(({ berth }) => berth.currentVessel && berth.status === 'occupied').map(({ berth, position }) => (
        <VesselBody key={`vessel-${berth.id}`} name={berth.currentVessel!.name} loa={berth.currentVessel!.loa} position={[position[0], 0, -15]} berthLength={berth.length} />
      ))}

      {/* Anchorage area with vessels */}
      <AnchorageArea
        vessels={anchorageVessels}
        layout={layout}
        onDragStart={onDragStart}
        onClick={onVesselClick}
        dragVesselId={dragState?.vesselId || null}
      />

      {/* Drag ghost */}
      {dragState?.isDragging && (
        <DragGhostVessel
          vessel={dragState.vessel}
          layout={layout}
          dragState={dragState}
          setDragState={onDragStateChange}
          onDrop={onDrop}
        />
      )}

      {/* Container yards */}
      {exportBlocks.map((block, i) => (<ContainerBlock key={`export-${i}`} position={[block.x, 0, block.z]} rows={block.rows} cols={block.cols} maxStack={block.stack} label={block.label} />))}
      {exportBlocks.filter((_, i) => i % 2 === 0).map((block, i) => (<RTGCraneYard key={`rtg-export-${i}`} position={[block.x, 0, block.z]} blockWidth={block.cols * 2.2 + 2} />))}
      {generalBlocks.map((block, i) => (<ContainerBlock key={`general-${i}`} position={[block.x, 0, block.z]} rows={block.rows} cols={block.cols} maxStack={block.stack} label={block.label} />))}
      {generalBlocks.filter((_, i) => i % 2 === 0).map((block, i) => (<RTGCraneYard key={`rtg-general-${i}`} position={[block.x, 0, block.z]} blockWidth={block.cols * 2.2 + 2} />))}
      {importBlocks.map((block, i) => (<ContainerBlock key={`import-${i}`} position={[block.x, 0, block.z]} rows={block.rows} cols={block.cols} maxStack={block.stack} label={block.label} />))}
      {importBlocks.filter((_, i) => i % 2 === 1).map((block, i) => (<RTGCraneYard key={`rtg-import-${i}`} position={[block.x, 0, block.z]} blockWidth={block.cols * 2.2 + 2} />))}

      {/* Animated trucks */}
      <AnimatedTruck roadZ={40} startX={-halfSpan - 20} endX={halfSpan + 20} speed={8} color="#E5E7EB" hasContainer={true} />
      <AnimatedTruck roadZ={42} startX={halfSpan + 20} endX={-halfSpan - 20} speed={6} color="#FBBF24" hasContainer={true} />
      <AnimatedTruck roadZ={39.5} startX={-halfSpan + 30} endX={halfSpan + 20} speed={10} color="#F3F4F6" hasContainer={false} />
      <AnimatedTruck roadZ={74} startX={halfSpan + 10} endX={-halfSpan - 10} speed={7} color="#D1D5DB" hasContainer={true} />
      <AnimatedTruck roadZ={76} startX={-halfSpan - 10} endX={halfSpan + 10} speed={9} color="#0891B2" hasContainer={true} />

      {/* Static trucks */}
      {staticTrucks.map((t, i) => (<TruckModel key={`truck-${i}`} position={[t.x, 0, t.z]} rotation={t.rot} color={t.color} hasContainer={t.hasContainer} />))}

      {/* Terminal name label */}
      {terminalName && (
        <Html position={terminalNamePosition} center zIndexRange={[5, 0]} style={{ pointerEvents: 'none' }}>
          <div style={{
            fontSize: 14,
            fontWeight: 800,
            color: '#0A4D8C',
            textShadow: '0 0 8px white, 0 0 16px white',
            whiteSpace: 'nowrap',
            letterSpacing: 2,
            textTransform: 'uppercase',
            padding: '6px 16px',
            backgroundColor: 'rgba(255,255,255,0.85)',
            borderRadius: 8,
            border: '2px solid #0A4D8C',
          }}>
            {terminalName}
          </div>
        </Html>
      )}
    </>
  );
}
