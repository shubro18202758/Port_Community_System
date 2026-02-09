import { useEffect, useState, useCallback, useMemo, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, useMap, CircleMarker } from 'react-leaflet';
import L from 'leaflet';
import { vesselTrackingConnection } from '../../api/signalr';
import type { VesselPosition, PortLocation } from '../../types';
import { Ship, Wifi, WifiOff, Navigation, X, Activity, Clock, Anchor, Target } from 'lucide-react';
import 'leaflet/dist/leaflet.css';

interface WorldVesselMapProps {
  portLocation: PortLocation;
  onVesselClick?: (vessel: VesselPosition) => void;
  className?: string;
}

// Color scheme for dark map - bright neon colors for high contrast
const COLORS = {
  arriving: { main: '#00ff88', glow: 'rgba(0, 255, 136, 0.6)', bg: 'rgba(0, 255, 136, 0.15)' },     // Neon green
  approaching: { main: '#ffa500', glow: 'rgba(255, 165, 0, 0.6)', bg: 'rgba(255, 165, 0, 0.15)' },  // Orange
  en_route: { main: '#00bfff', glow: 'rgba(0, 191, 255, 0.5)', bg: 'rgba(0, 191, 255, 0.15)' },     // Cyan blue
  port: { main: '#ff4466', glow: 'rgba(255, 68, 102, 0.6)', bg: 'rgba(255, 68, 102, 0.2)' },        // Neon pink/red
};

const getVesselColors = (phase?: string) => {
  switch (phase) {
    case 'arriving': return COLORS.arriving;
    case 'approaching': return COLORS.approaching;
    default: return COLORS.en_route;
  }
};

// Vessel SVG with glow effect
const getVesselSVG = (vesselType?: string, color: string = '#0088ff', rotation: number = 0): string => {
  let shipPath = '';

  if (vesselType?.toLowerCase().includes('container')) {
    shipPath = `<rect x="8" y="4" width="8" height="16" rx="1" fill="${color}"/>
      <rect x="9" y="6" width="2" height="3" fill="white" opacity="0.8"/>
      <rect x="13" y="6" width="2" height="3" fill="white" opacity="0.8"/>
      <rect x="9" y="10" width="2" height="3" fill="white" opacity="0.8"/>
      <rect x="13" y="10" width="2" height="3" fill="white" opacity="0.8"/>
      <polygon points="12,2 8,4 16,4" fill="${color}"/>`;
  } else if (vesselType?.toLowerCase().includes('tanker') || vesselType?.toLowerCase().includes('lng')) {
    shipPath = `<ellipse cx="12" cy="12" rx="4" ry="8" fill="${color}"/>
      <ellipse cx="12" cy="8" rx="2.5" ry="2" fill="white" opacity="0.6"/>
      <polygon points="12,2 9,5 15,5" fill="${color}"/>`;
  } else if (vesselType?.toLowerCase().includes('bulk')) {
    shipPath = `<rect x="7" y="4" width="10" height="14" rx="2" fill="${color}"/>
      <rect x="8" y="6" width="8" height="4" fill="white" opacity="0.5"/>
      <rect x="8" y="11" width="8" height="4" fill="white" opacity="0.5"/>
      <polygon points="12,2 7,4 17,4" fill="${color}"/>`;
  } else if (vesselType?.toLowerCase().includes('ro-ro') || vesselType?.toLowerCase().includes('car')) {
    shipPath = `<rect x="8" y="3" width="8" height="15" rx="1" fill="${color}"/>
      <rect x="9" y="5" width="6" height="8" fill="white" opacity="0.5"/>
      <rect x="10" y="14" width="4" height="3" fill="white" opacity="0.7"/>
      <polygon points="12,1 8,3 16,3" fill="${color}"/>`;
  } else {
    shipPath = `<ellipse cx="12" cy="12" rx="4" ry="7" fill="${color}"/>
      <rect x="10" y="6" width="4" height="2" fill="white" opacity="0.7"/>
      <polygon points="12,3 9,6 15,6" fill="${color}"/>`;
  }

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="32" height="32">
    <defs>
      <filter id="vessel-glow" x="-100%" y="-100%" width="300%" height="300%">
        <feGaussianBlur stdDeviation="1.5" result="blur"/>
        <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
    </defs>
    <g transform="rotate(${rotation}, 12, 12)" filter="url(#vessel-glow)">${shipPath}</g>
  </svg>`;
};

// Create vessel icon - threat map style
const createVesselIcon = (vessel: VesselPosition, isSelected: boolean = false): L.DivIcon => {
  const colors = getVesselColors(vessel.phase);
  const rotation = vessel.course || 0;
  const size = isSelected ? 1.4 : 1;

  return L.divIcon({
    className: 'threat-vessel-marker',
    html: `
      <div class="threat-marker-wrapper" style="transform: scale(${size}); transition: transform 0.3s ease;">
        <!-- Static glow background -->
        <div style="
          position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
          width: 36px; height: 36px; border-radius: 50%;
          background: radial-gradient(circle, ${colors.glow} 0%, transparent 70%);
        "></div>

        <!-- Vessel icon -->
        <div style="
          position: absolute; top: 50%; left: 50%;
          transform: translate(-50%, -50%);
          filter: drop-shadow(0 0 6px ${colors.main});
        ">
          ${getVesselSVG(vessel.vesselType, colors.main, rotation)}
        </div>

        <!-- Selection ring (only when selected) -->
        ${isSelected ? `
          <div style="
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            width: 45px; height: 45px; border-radius: 50%;
            border: 2px solid ${colors.main};
            animation: selection-spin 3s linear infinite;
            border-top-color: transparent;
          "></div>
        ` : ''}
      </div>
    `,
    iconSize: [50, 50],
    iconAnchor: [25, 25],
  });
};

// Port marker - clean style with static rings
const createPortIcon = (): L.DivIcon => {
  return L.divIcon({
    className: 'port-marker',
    html: `
      <div style="position: relative; width: 80px; height: 80px;">
        <!-- Static concentric rings -->
        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
          width: 70px; height: 70px; border-radius: 50%; border: 1px solid ${COLORS.port.main}25;"></div>
        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
          width: 50px; height: 50px; border-radius: 50%; border: 1px solid ${COLORS.port.main}40;"></div>
        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
          width: 30px; height: 30px; border-radius: 50%; border: 1px solid ${COLORS.port.main}60;"></div>

        <!-- Central glow -->
        <div style="
          position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
          width: 40px; height: 40px; border-radius: 50%;
          background: radial-gradient(circle, ${COLORS.port.glow} 0%, transparent 70%);
        "></div>

        <!-- Port icon -->
        <div style="
          position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
          filter: drop-shadow(0 0 8px ${COLORS.port.main});
        ">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="${COLORS.port.main}">
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
          </svg>
        </div>
      </div>
    `,
    iconSize: [80, 80],
    iconAnchor: [40, 40],
  });
};

// Sample vessel data generator
const generateSampleVessels = (port: PortLocation): VesselPosition[] => {
  const vessels: VesselPosition[] = [];
  const vesselTypes = ['Container Ship', 'Tanker', 'Bulk Carrier', 'RO-RO', 'LNG Carrier', 'General Cargo'];
  const oceanAngles = [-80, -60, -45, -30, -15, 0, 15, 30, 45, 60, 80, -70, -50, -25, 10, 35, 55, 70, -85, -40, 20, 50];

  for (let i = 0; i < 20; i++) {
    const angleOffset = oceanAngles[i % oceanAngles.length];
    const baseAngle = (180 + angleOffset) * (Math.PI / 180);
    const distance = 2 + (i % 5) * 3.5 + Math.random() * 2;
    const lat = port.latitude + Math.sin(baseAngle) * distance * 0.8;
    const lon = port.longitude + Math.cos(baseAngle) * distance;

    let phase: VesselPosition['phase'];
    if (distance < 5) phase = 'arriving';
    else if (distance < 10) phase = 'approaching';
    else phase = 'en_route';

    const hoursToPort = distance * 4 + Math.random() * 12;
    const courseToPort = Math.atan2(port.latitude - lat, port.longitude - lon) * (180 / Math.PI);

    vessels.push({
      vesselId: 1000 + i,
      mmsi: `${356000000 + i * 1000 + Math.floor(Math.random() * 100)}`,
      vesselName: `MV ${['Maersk', 'MSC', 'COSCO', 'Evergreen', 'Hapag', 'ONE'][i % 6]} ${['Pioneer', 'Voyager', 'Express', 'Fortune', 'Spirit', 'Harmony'][Math.floor(i / 6) % 6]}`,
      vesselType: vesselTypes[i % vesselTypes.length],
      latitude: lat,
      longitude: lon,
      speed: 12 + Math.random() * 10,
      course: ((courseToPort + 90 + 360) % 360),
      destination: port.portName,
      declaredETA: new Date(Date.now() + hoursToPort * 60 * 60 * 1000).toISOString(),
      predictedETA: new Date(Date.now() + (hoursToPort + (Math.random() - 0.5) * 4) * 60 * 60 * 1000).toISOString(),
      distanceToPort: distance * 60,
      phase,
      timestamp: new Date().toISOString(),
    });
  }
  return vessels;
};

// Map controller
function MapController({ center, zoom }: { center: [number, number]; zoom: number }) {
  const map = useMap();
  useEffect(() => { map.setView(center, zoom); }, [map, center, zoom]);
  return null;
}

const formatETA = (eta?: string) => {
  if (!eta) return 'N/A';
  return new Date(eta).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
};

// Animated counter component
function AnimatedCounter({ value, label, color, icon: Icon }: { value: number; label: string; color: string; icon: any }) {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    const duration = 1000;
    const steps = 30;
    const increment = value / steps;
    let current = 0;
    const timer = setInterval(() => {
      current += increment;
      if (current >= value) {
        setDisplayValue(value);
        clearInterval(timer);
      } else {
        setDisplayValue(Math.floor(current));
      }
    }, duration / steps);
    return () => clearInterval(timer);
  }, [value]);

  return (
    <div className="flex items-center gap-2">
      <Icon className="w-4 h-4" style={{ color }} />
      <span className="font-mono text-lg font-bold" style={{ color, textShadow: `0 0 10px ${color}` }}>
        {displayValue}
      </span>
      <span className="text-xs text-slate-400">{label}</span>
    </div>
  );
}

export function WorldVesselMap({ portLocation, onVesselClick, className }: WorldVesselMapProps) {
  const [vessels, setVessels] = useState<VesselPosition[]>(() => generateSampleVessels(portLocation));
  const [isConnected, setIsConnected] = useState(false);
  const [selectedVessel, setSelectedVessel] = useState<VesselPosition | null>(null);
  const [mapZoom, setMapZoom] = useState(5);
  const [currentTime, setCurrentTime] = useState(new Date());

  // Update time every second
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    setVessels(generateSampleVessels(portLocation));
  }, [portLocation.portCode]);

  // SignalR connection
  useEffect(() => {
    let mounted = true;
    const handlePosition = (position: VesselPosition) => {
      if (!mounted || position.phase === 'at_port') return;
      setVessels(prev => {
        const idx = prev.findIndex(v => v.mmsi === position.mmsi);
        if (idx >= 0) { const updated = [...prev]; updated[idx] = position; return updated; }
        return [...prev, position];
      });
    };
    const connect = async () => {
      try {
        await vesselTrackingConnection.connect(handlePosition);
        await vesselTrackingConnection.subscribeToPort(portLocation.portCode, portLocation.boundingBox);
        if (mounted) setIsConnected(true);
      } catch { if (mounted) setIsConnected(false); }
    };
    connect();
    return () => { mounted = false; vesselTrackingConnection.disconnect(); };
  }, [portLocation]);

  const activeVessels = useMemo(() => vessels.filter(v => v.phase !== 'at_port'), [vessels]);
  const arrivingCount = useMemo(() => activeVessels.filter(v => v.phase === 'arriving').length, [activeVessels]);
  const approachingCount = useMemo(() => activeVessels.filter(v => v.phase === 'approaching').length, [activeVessels]);

  const routes = useMemo(() =>
    activeVessels
      .filter(v => v.phase === 'arriving' || v.phase === 'approaching')
      .map(v => ({
        from: [v.latitude, v.longitude] as [number, number],
        to: [portLocation.latitude, portLocation.longitude] as [number, number],
        color: getVesselColors(v.phase).main,
      })),
    [activeVessels, portLocation]
  );

  const handleVesselClick = useCallback((vessel: VesselPosition) => {
    setSelectedVessel(prev => prev?.mmsi === vessel.mmsi ? null : vessel);
    onVesselClick?.(vessel);
  }, [onVesselClick]);

  return (
    <div className={`relative overflow-hidden ${className}`} style={{ minHeight: 400, background: '#0c1929' }}>
      {/* Clean map style CSS - no blinking */}
      <style>{`
        @keyframes selection-spin {
          from { transform: translate(-50%, -50%) rotate(0deg); }
          to { transform: translate(-50%, -50%) rotate(360deg); }
        }
        @keyframes radar-sweep {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .threat-marker-wrapper:hover {
          transform: scale(1.2) !important;
        }
        .leaflet-popup { display: none !important; }
      `}</style>

      {/* Map */}
      <MapContainer
        center={[portLocation.latitude, portLocation.longitude]}
        zoom={mapZoom}
        style={{ height: '100%', width: '100%', minHeight: 400, background: '#1a1a2e' }}
        scrollWheelZoom={true}
        zoomControl={false}
      >
        <MapController center={[portLocation.latitude, portLocation.longitude]} zoom={mapZoom} />
        {/* CartoDB Dark Matter - clean dark theme for vessel tracking */}
        <TileLayer
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />

        {/* Route lines with glow effect */}
        {routes.map((route, idx) => (
          <Polyline
            key={`route-${idx}`}
            positions={[route.from, route.to]}
            color={route.color}
            weight={2}
            opacity={0.8}
            dashArray="8, 16"
            className="data-flow-line"
          />
        ))}

        <Marker position={[portLocation.latitude, portLocation.longitude]} icon={createPortIcon()} />

        {activeVessels.map((vessel) => (
          <Marker
            key={vessel.mmsi}
            position={[vessel.latitude, vessel.longitude]}
            icon={createVesselIcon(vessel, selectedVessel?.mmsi === vessel.mmsi)}
            eventHandlers={{ click: () => handleVesselClick(vessel) }}
          />
        ))}
      </MapContainer>

      {/* Top HUD */}
      <div className="absolute top-0 left-0 right-0 z-[1000] p-4">
        <div className="flex items-center justify-between">
          {/* Status panel */}
          <div className="flex items-center gap-4 px-4 py-3 rounded-lg backdrop-blur-sm"
            style={{ background: 'linear-gradient(135deg, rgba(10, 10, 18, 0.9), rgba(20, 20, 30, 0.9))', border: '1px solid rgba(0, 255, 136, 0.2)' }}>
            <div className="flex items-center gap-2">
              {isConnected ? (
                <div className="relative">
                  <Wifi className="w-5 h-5 text-green-400" />
                  <div className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-green-400 rounded-full animate-ping" />
                </div>
              ) : <WifiOff className="w-5 h-5 text-slate-500" />}
              <span className={`text-sm font-medium ${isConnected ? 'text-green-400' : 'text-slate-500'}`}>
                {isConnected ? 'LIVE' : 'DEMO'}
              </span>
            </div>
            <div className="w-px h-6 bg-slate-600" />
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-slate-400" />
              <span className="font-mono text-sm text-slate-300">
                {currentTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
              </span>
            </div>
          </div>

          {/* Stats panel */}
          <div className="flex items-center gap-6 px-4 py-3 rounded-lg backdrop-blur-sm"
            style={{ background: 'linear-gradient(135deg, rgba(10, 10, 18, 0.9), rgba(20, 20, 30, 0.9))', border: '1px solid rgba(0, 136, 255, 0.2)' }}>
            <AnimatedCounter value={activeVessels.length} label="TRACKING" color="#0088ff" icon={Ship} />
            <div className="w-px h-6 bg-slate-600" />
            <AnimatedCounter value={arrivingCount} label="ARRIVING" color="#00ff88" icon={Target} />
            <div className="w-px h-6 bg-slate-600" />
            <AnimatedCounter value={approachingCount} label="APPROACHING" color="#ffaa00" icon={Activity} />
          </div>
        </div>
      </div>

      {/* Port name display */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-[1000] px-6 py-2 rounded-full backdrop-blur-sm"
        style={{ background: 'rgba(10, 10, 18, 0.8)', border: `1px solid ${COLORS.port.main}40` }}>
        <div className="flex items-center gap-3">
          <Anchor className="w-4 h-4" style={{ color: COLORS.port.main }} />
          <span className="text-sm font-medium" style={{ color: COLORS.port.main }}>{portLocation.portName}</span>
          <span className="text-xs text-slate-500">{portLocation.portCode}</span>
        </div>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-[1000] px-4 py-3 rounded-lg backdrop-blur-sm"
        style={{ background: 'rgba(10, 10, 18, 0.9)', border: '1px solid rgba(100, 100, 120, 0.3)' }}>
        <div className="flex flex-col gap-2 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ background: COLORS.arriving.main, boxShadow: `0 0 8px ${COLORS.arriving.glow}` }} />
            <span className="text-slate-400">Arriving (&lt;6h)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ background: COLORS.approaching.main, boxShadow: `0 0 8px ${COLORS.approaching.glow}` }} />
            <span className="text-slate-400">Approaching</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ background: COLORS.en_route.main, boxShadow: `0 0 8px ${COLORS.en_route.glow}` }} />
            <span className="text-slate-400">En Route</span>
          </div>
        </div>
      </div>

      {/* Zoom controls */}
      <div className="absolute bottom-4 right-4 z-[1000] flex flex-col gap-1">
        {['+', '-', '⌖'].map((label, i) => (
          <button
            key={i}
            onClick={() => i === 0 ? setMapZoom(z => Math.min(10, z + 1)) : i === 1 ? setMapZoom(z => Math.max(2, z - 1)) : setMapZoom(5)}
            className="w-10 h-10 rounded flex items-center justify-center text-lg font-bold transition-all hover:scale-110"
            style={{ background: 'rgba(10, 10, 18, 0.9)', border: '1px solid rgba(0, 136, 255, 0.3)', color: '#0088ff' }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Vessel detail panel */}
      {selectedVessel && (
        <div className="absolute top-20 left-4 z-[1000] w-80 rounded-lg overflow-hidden backdrop-blur-sm"
          style={{ background: 'linear-gradient(135deg, rgba(10, 10, 18, 0.95), rgba(20, 20, 30, 0.95))', border: `1px solid ${getVesselColors(selectedVessel.phase).main}40` }}>
          <div className="px-4 py-3 flex items-center justify-between"
            style={{ background: `linear-gradient(90deg, ${getVesselColors(selectedVessel.phase).bg}, transparent)`, borderBottom: `1px solid ${getVesselColors(selectedVessel.phase).main}30` }}>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded" style={{ background: getVesselColors(selectedVessel.phase).bg }}>
                <Ship className="w-5 h-5" style={{ color: getVesselColors(selectedVessel.phase).main }} />
              </div>
              <div>
                <div className="font-semibold text-white">{selectedVessel.vesselName}</div>
                <div className="text-xs text-slate-400">{selectedVessel.vesselType}</div>
              </div>
            </div>
            <button onClick={() => setSelectedVessel(null)} className="p-1.5 rounded hover:bg-white/10">
              <X className="w-4 h-4 text-slate-400" />
            </button>
          </div>

          <div className="p-4 space-y-4">
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'MMSI', value: selectedVessel.mmsi, mono: true },
                { label: 'Speed', value: `${selectedVessel.speed.toFixed(1)} kn` },
                { label: 'Course', value: `${((selectedVessel.course || 0) - 90 + 360) % 360}°` },
                { label: 'Distance', value: `${selectedVessel.distanceToPort?.toFixed(0) || 'N/A'} nm` },
              ].map((item, i) => (
                <div key={i} className="px-3 py-2 rounded" style={{ background: 'rgba(30, 30, 50, 0.5)' }}>
                  <div className="text-xs text-slate-500 mb-1">{item.label}</div>
                  <div className={`text-white ${item.mono ? 'font-mono' : ''}`}>{item.value}</div>
                </div>
              ))}
            </div>

            <div className="space-y-2 pt-2 border-t border-slate-700/50">
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">Declared ETA</span>
                <span className="text-blue-400 font-medium">{formatETA(selectedVessel.declaredETA)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">Predicted ETA</span>
                <span style={{ color: COLORS.arriving.main }} className="font-medium">{formatETA(selectedVessel.predictedETA)}</span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <div className="px-3 py-1.5 rounded-full text-xs font-medium flex items-center gap-2"
                style={{ background: getVesselColors(selectedVessel.phase).bg, color: getVesselColors(selectedVessel.phase).main }}>
                <Navigation className="w-3.5 h-3.5" />
                {selectedVessel.phase?.replace('_', ' ').toUpperCase()}
              </div>
              <span className="text-xs text-slate-500">→ {selectedVessel.destination}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
