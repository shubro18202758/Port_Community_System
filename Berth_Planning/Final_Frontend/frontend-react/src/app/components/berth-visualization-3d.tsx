import { useState, useMemo } from 'react';
import { Ship, Anchor, Calendar, ChevronDown, ChevronRight, Package, Sparkles, Info } from 'lucide-react';

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
  cargoTypes?: string[];
  aiInsight?: {
    score: number;
    recommendation: string;
    factors: string[];
  };
  currentVessel?: {
    name: string;
    eta: Date;
    etd: Date;
    loa: number;
  };
  schedule: BerthSchedule[];
}

interface BerthVisualization3DProps {
  berths: Berth[];
  onBerthClick: (berth: Berth) => void;
  selectedBerthId?: string;
}

interface DateGroup {
  key: string;
  label: string;
  sublabel: string;
  berths: Berth[];
  occupiedCount: number;
  availableCount: number;
}

function toDateKey(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function formatDateLabel(dateKey: string): { label: string; sublabel: string } {
  const today = new Date();
  const todayKey = toDateKey(today);
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);
  const tomorrowKey = toDateKey(tomorrow);

  const [y, m, d] = dateKey.split('-').map(Number);
  const date = new Date(y, m - 1, d);
  const dayName = date.toLocaleDateString('en-US', { weekday: 'long' });
  const fullDate = date.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });

  if (dateKey === todayKey) {
    return { label: 'Today', sublabel: fullDate };
  } else if (dateKey === tomorrowKey) {
    return { label: 'Tomorrow', sublabel: fullDate };
  } else {
    return { label: dayName, sublabel: fullDate };
  }
}

export function BerthVisualization3D({ berths, onBerthClick, selectedBerthId }: BerthVisualization3DProps) {
  const [hoveredBerthId, setHoveredBerthId] = useState<string | null>(null);
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set());

  const toggleGroup = (key: string) => {
    setCollapsedGroups(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  // Group berths by date
  const dateGroups = useMemo<DateGroup[]>(() => {
    const groups = new Map<string, Berth[]>();
    const noScheduleKey = 'no-schedule';

    berths.forEach(berth => {
      let dateKey: string | null = null;

      if (berth.status === 'occupied' && berth.currentVessel) {
        // Use the ETA date of the current vessel
        dateKey = toDateKey(berth.currentVessel.eta);
      } else if (berth.schedule.length > 0) {
        // Use the earliest upcoming schedule date
        const sorted = [...berth.schedule].sort((a, b) => a.startTime.getTime() - b.startTime.getTime());
        dateKey = toDateKey(sorted[0].startTime);
      }

      const key = dateKey || noScheduleKey;
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key)!.push(berth);
    });

    // Sort date keys chronologically, "no-schedule" last
    const sortedKeys = Array.from(groups.keys()).sort((a, b) => {
      if (a === noScheduleKey) return 1;
      if (b === noScheduleKey) return -1;
      return a.localeCompare(b);
    });

    return sortedKeys.map(key => {
      const groupBerths = groups.get(key)!;
      const { label, sublabel } = key === noScheduleKey
        ? { label: 'No Scheduled Activity', sublabel: 'Berths without any upcoming schedule' }
        : formatDateLabel(key);

      return {
        key,
        label,
        sublabel,
        berths: groupBerths,
        occupiedCount: groupBerths.filter(b => b.status === 'occupied').length,
        availableCount: groupBerths.filter(b => b.status === 'available').length,
      };
    });
  }, [berths]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'available': return 'var(--status-on-time)';
      case 'occupied': return 'var(--kale-blue)';
      case 'maintenance': return 'var(--muted-foreground)';
      default: return '#E5E7EB';
    }
  };

  const getCraneIcon = (type: string) => {
    switch (type) {
      case 'STS': return '🏗️';
      case 'RTG': return '🚧';
      case 'MHC': return '⚙️';
      default: return '🏗️';
    }
  };

  const groupCranes = (cranes: Crane[]) => {
    const groups: Record<string, { count: number; capacity: number; operational: number }> = {};
    cranes.forEach(c => {
      if (!groups[c.type]) groups[c.type] = { count: 0, capacity: c.capacity, operational: 0 };
      groups[c.type].count++;
      if (c.status === 'operational') groups[c.type].operational++;
    });
    return groups;
  };

  // Helper to get cargo type color
  const getCargoTypeColor = (cargoType: string) => {
    const colors: Record<string, string> = {
      'Container': '#2563EB',
      'Bulk': '#D97706',
      'Tanker': '#7C3AED',
      'RoRo': '#059669',
      'General': '#6B7280',
      'Reefer': '#0891B2',
    };
    return colors[cargoType] || '#6B7280';
  };

  // Generate AI insight for a berth (simulated based on berth data)
  const getAIInsight = (berth: Berth) => {
    if (berth.aiInsight) return berth.aiInsight;

    // Generate default insights based on berth status and capacity
    const utilization = berth.status === 'occupied' ? 85 : berth.schedule.length > 0 ? 60 : 30;
    const craneEfficiency = berth.cranes.filter(c => c.status === 'operational').length / Math.max(berth.cranes.length, 1) * 100;
    const score = Math.round((utilization * 0.4 + craneEfficiency * 0.6));

    let recommendation = '';
    const factors: string[] = [];

    if (berth.status === 'available' && berth.schedule.length === 0) {
      recommendation = 'High availability - ideal for new allocations';
      factors.push('No scheduling conflicts', 'All resources available');
    } else if (berth.status === 'occupied') {
      recommendation = 'Currently in use - monitor for timely departure';
      factors.push('Active vessel operations', `ETD: ${berth.currentVessel?.etd.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) || 'TBD'}`);
    } else if (berth.status === 'maintenance') {
      recommendation = 'Under maintenance - not available for allocation';
      factors.push('Scheduled maintenance', 'Equipment servicing');
    } else {
      recommendation = 'Schedule upcoming - plan allocation carefully';
      factors.push(`${berth.schedule.length} upcoming bookings`);
    }

    if (craneEfficiency < 100) {
      factors.push(`Crane availability: ${Math.round(craneEfficiency)}%`);
    }

    return { score, recommendation, factors };
  };

  const renderBerthCard = (berth: Berth) => {
    const isSelected = selectedBerthId === berth.id;
    const operationalCranes = berth.cranes.filter(c => c.status === 'operational').length;
    const craneGroups = groupCranes(berth.cranes);
    const aiInsight = getAIInsight(berth);
    const isHovered = hoveredBerthId === berth.id;

    // Default cargo types if not provided
    const cargoTypes = berth.cargoTypes || ['Container', 'General'];

    return (
      <div
        key={berth.id}
        className="transition-all duration-200 hover:scale-[1.01]"
        onMouseEnter={() => setHoveredBerthId(berth.id)}
        onMouseLeave={() => setHoveredBerthId(null)}
      >
        <div
          className="rounded-xl overflow-hidden shadow-sm hover:shadow-lg transition-shadow bg-white h-full"
          style={{
            border: `2px solid ${isSelected ? getStatusColor(berth.status) : 'var(--border)'}`,
          }}
        >
          <div className="p-3">
            {/* Header: Name + Status */}
            <div className="flex items-center justify-between gap-2 mb-3">
              <div className="flex items-center gap-2 min-w-0">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${getStatusColor(berth.status)}15` }}>
                  <Anchor className="w-4 h-4" style={{ color: getStatusColor(berth.status) }} />
                </div>
                <div className="min-w-0">
                  <span className="text-sm font-bold block truncate" style={{ color: 'var(--kale-blue)' }}>
                    {berth.name}
                  </span>
                  <span className="text-[10px]" style={{ color: 'var(--muted-foreground)' }}>
                    {berth.length}m berth
                  </span>
                </div>
              </div>
              <span className="px-2 py-1 rounded-md text-[10px] capitalize whitespace-nowrap flex-shrink-0"
                style={{
                  backgroundColor: `${getStatusColor(berth.status)}15`,
                  color: getStatusColor(berth.status),
                  fontWeight: 600,
                }}>
                {berth.status}
              </span>
            </div>

            {/* AI Allocation Insights */}
            <div
              className="relative mb-3 p-2.5 rounded-lg cursor-help"
              style={{
                backgroundColor: 'rgba(139, 92, 246, 0.08)',
                border: '1px solid rgba(139, 92, 246, 0.2)'
              }}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4" style={{ color: '#8B5CF6' }} />
                  <span className="text-xs font-semibold" style={{ color: '#8B5CF6' }}>AI Insights</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="text-xs font-bold" style={{ color: '#8B5CF6' }}>{aiInsight.score}%</span>
                  <Info className="w-3.5 h-3.5" style={{ color: '#8B5CF6', opacity: 0.6 }} />
                </div>
              </div>
              <p className="text-[11px] mt-1.5 leading-relaxed" style={{ color: '#6D28D9' }}>
                {aiInsight.recommendation}
              </p>

              {/* Tooltip - shows on card hover */}
              {isHovered && (
                <div
                  className="absolute z-50 left-0 right-0 top-full mt-1 p-3 rounded-lg shadow-lg"
                  style={{
                    backgroundColor: 'white',
                    border: '1px solid var(--border)',
                    minWidth: '220px'
                  }}
                >
                  <div className="text-xs font-semibold mb-2" style={{ color: 'var(--kale-blue)' }}>
                    Allocation Factors
                  </div>
                  <ul className="space-y-1.5">
                    {aiInsight.factors.map((factor, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-[11px]" style={{ color: 'var(--muted-foreground)' }}>
                        <span className="w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0" style={{ backgroundColor: '#8B5CF6' }} />
                        {factor}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Cargo Compatibility */}
            <div className="mb-3">
              <div className="flex items-center gap-1.5 mb-2">
                <Package className="w-3.5 h-3.5" style={{ color: 'var(--muted-foreground)' }} />
                <span className="text-[11px] font-semibold" style={{ color: 'var(--muted-foreground)' }}>Cargo Compatibility</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {cargoTypes.map((cargo) => (
                  <span
                    key={cargo}
                    className="px-2 py-1 rounded text-[11px] font-medium"
                    style={{
                      backgroundColor: `${getCargoTypeColor(cargo)}15`,
                      color: getCargoTypeColor(cargo),
                    }}
                  >
                    {cargo}
                  </span>
                ))}
              </div>
            </div>

            {/* Specs */}
            <div className="grid grid-cols-4 gap-1.5 mb-3 px-2.5 py-2.5 rounded-lg" style={{ backgroundColor: 'var(--kale-sky)' }}>
              {[
                { label: 'Length', value: `${berth.length}m` },
                { label: 'Max LOA', value: `${berth.maxLOA}m` },
                { label: 'Max Beam', value: `${berth.maxBeam}m` },
                { label: 'Max Draft', value: `${berth.maxDraft}m` },
              ].map(s => (
                <div key={s.label} className="text-center">
                  <div className="text-[10px]" style={{ color: 'var(--muted-foreground)' }}>{s.label}</div>
                  <div style={{ fontWeight: 700, fontSize: '12px', color: 'var(--foreground)' }}>{s.value}</div>
                </div>
              ))}
            </div>

            {/* Equipment */}
            <div className="flex items-center gap-1.5 mb-3 flex-wrap">
              {Object.entries(craneGroups).map(([type, info]) => (
                <span key={type} className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[11px]"
                  style={{ backgroundColor: 'var(--muted)', border: '1px solid var(--border)' }}>
                  <span style={{ fontSize: '12px' }}>{getCraneIcon(type)}</span>
                  <span style={{ fontWeight: 600 }}>{info.count}x {type}</span>
                  <span style={{ color: 'var(--muted-foreground)' }}>{info.capacity}t</span>
                  <span className="w-1.5 h-1.5 rounded-full inline-block"
                    style={{ backgroundColor: info.operational === info.count ? 'var(--status-on-time)' : 'var(--status-at-risk)' }} />
                </span>
              ))}
              <span className="text-[11px]" style={{ color: 'var(--muted-foreground)' }}>
                {operationalCranes}/{berth.cranes.length} operational
              </span>
            </div>

            {/* Reefer + Schedule count */}
            <div className="flex items-center justify-between text-[11px] mb-3 px-2.5 py-2 rounded-lg" style={{ backgroundColor: 'rgba(8, 145, 178, 0.08)' }}>
              <span style={{ color: 'var(--muted-foreground)' }}>
                Reefer Points: <span style={{ fontWeight: 700, color: '#0891B2' }}>{berth.reeferPoints}</span>
              </span>
              {berth.schedule.length > 0 && (
                <span style={{ color: 'var(--muted-foreground)' }}>
                  <span style={{ fontWeight: 600, color: 'var(--kale-blue)' }}>{berth.schedule.length}</span> scheduled
                </span>
              )}
            </div>

            {/* Current vessel */}
            {berth.currentVessel && (
              <div className="px-3 py-2.5 rounded-lg border" style={{ borderColor: 'var(--kale-blue)', backgroundColor: 'rgba(10, 77, 140, 0.05)' }}>
                <div className="flex items-center gap-2 mb-1.5">
                  <Ship className="w-4 h-4" style={{ color: 'var(--kale-blue)' }} />
                  <span className="text-xs truncate font-bold" style={{ color: 'var(--kale-blue)' }}>{berth.currentVessel.name}</span>
                </div>
                <div className="text-[11px] flex items-center gap-2" style={{ color: 'var(--muted-foreground)' }}>
                  <span>LOA: <b>{berth.currentVessel.loa}m</b></span>
                  <span>•</span>
                  <span>ETD: <b>{berth.currentVessel.etd.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</b></span>
                </div>
              </div>
            )}

            {berth.status === 'available' && berth.schedule.length > 0 && !berth.currentVessel && (
              <div className="text-center text-[11px] px-3 py-2.5 rounded-lg border" style={{ borderColor: 'var(--kale-teal)', backgroundColor: 'rgba(20, 184, 166, 0.08)', color: 'var(--kale-teal)', fontWeight: 600 }}>
                Next booking: {berth.schedule[0].startTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
            )}

            {berth.status === 'available' && berth.schedule.length === 0 && !berth.currentVessel && (
              <div className="text-center text-[11px] px-3 py-2.5 rounded-lg" style={{ backgroundColor: 'rgba(5, 150, 105, 0.1)', color: 'var(--status-on-time)', fontWeight: 600 }}>
                Ready for allocation
              </div>
            )}

            {berth.status === 'maintenance' && (
              <div className="text-center text-[11px] px-3 py-2.5 rounded-lg" style={{ backgroundColor: 'var(--muted)', color: 'var(--muted-foreground)', fontWeight: 600 }}>
                Under maintenance
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="sticky top-0 z-10 flex items-center justify-between px-4 py-3 border-b bg-white" style={{ borderColor: 'var(--border)' }}>
        <div>
          <h3 className="text-sm" style={{ color: 'var(--kale-blue)', fontWeight: 700 }}>Berth Overview</h3>
          <p className="text-[10px]" style={{ color: 'var(--muted-foreground)' }}>
            Terminal capacity and real-time status
          </p>
        </div>
      </div>

      {/* Date-grouped berth sections */}
      <div className="flex-1 overflow-auto p-3 space-y-4">
        {dateGroups.map((group) => {
          const isCollapsed = collapsedGroups.has(group.key);
          const isToday = group.label === 'Today';

          return (
            <div key={group.key}>
              {/* Date group header */}
              <button
                onClick={() => toggleGroup(group.key)}
                className="w-full flex items-center gap-3 px-3 py-2 rounded-lg mb-2 transition-colors hover:opacity-90"
                style={{
                  backgroundColor: isToday ? 'var(--kale-blue)' : 'var(--kale-sky)',
                  border: `1px solid ${isToday ? 'var(--kale-blue)' : 'var(--border)'}`,
                }}
              >
                {isCollapsed
                  ? <ChevronRight className="w-4 h-4 flex-shrink-0" style={{ color: isToday ? 'white' : 'var(--kale-blue)' }} />
                  : <ChevronDown className="w-4 h-4 flex-shrink-0" style={{ color: isToday ? 'white' : 'var(--kale-blue)' }} />
                }
                <Calendar className="w-3.5 h-3.5 flex-shrink-0" style={{ color: isToday ? 'white' : 'var(--kale-blue)' }} />
                <div className="flex-1 text-left">
                  <span className="text-xs font-bold" style={{ color: isToday ? 'white' : 'var(--kale-blue)' }}>
                    {group.label}
                  </span>
                  <span className="text-[10px] ml-2" style={{ color: isToday ? 'rgba(255,255,255,0.8)' : 'var(--muted-foreground)' }}>
                    {group.sublabel}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {group.occupiedCount > 0 && (
                    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px]"
                      style={{
                        backgroundColor: isToday ? 'rgba(255,255,255,0.2)' : 'var(--kale-blue)',
                        color: 'white',
                        fontWeight: 600,
                      }}>
                      <Ship className="w-2.5 h-2.5" />
                      {group.occupiedCount} Occupied
                    </span>
                  )}
                  {group.availableCount > 0 && (
                    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px]"
                      style={{
                        backgroundColor: isToday ? 'rgba(255,255,255,0.2)' : 'var(--status-on-time)',
                        color: 'white',
                        fontWeight: 600,
                      }}>
                      {group.availableCount} Available
                    </span>
                  )}
                  <span className="text-[10px]" style={{ color: isToday ? 'rgba(255,255,255,0.7)' : 'var(--muted-foreground)', fontWeight: 500 }}>
                    {group.berths.length} berths
                  </span>
                </div>
              </button>

              {/* Berth cards grid */}
              {!isCollapsed && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {group.berths.map(renderBerthCard)}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
