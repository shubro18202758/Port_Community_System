import { useState, useRef, useEffect } from 'react';
import { Ship, Clock, AlertTriangle, TrendingUp, TrendingDown, Calendar, CheckCircle2, Zap, Info, Brain, ChevronDown, ChevronRight } from 'lucide-react';

export interface Vessel {
  id: string;
  name: string;
  imo: string;
  callSign: string;
  flag: string;
  vesselType: string;

  // Dimensions
  loa: number;
  beam: number;
  draft: number;

  // Timing
  declaredETA: Date;
  predictedETA: Date;
  etaDeviation: number; // minutes
  ata?: Date; // Actual Time of Arrival - only when vessel has arrived

  // Status
  status: 'on-time' | 'at-risk' | 'delayed' | 'early' | 'arrived';
  readiness: 'ready' | 'pending' | 'incomplete';

  // Cargo
  cargoType: string;
  cargoQuantity: number;
  cargoUnit: string;

  // Constraints
  constraints: Array<{
    type: 'pilot' | 'tug' | 'tide' | 'berth' | 'cargo' | 'weather' | 'draft';
    status: 'satisfied' | 'warning' | 'critical';
    message: string;
  }>;

  // AI recommendations
  aiRecommendation?: {
    suggestedBerth: string;
    confidence: number;
    reason: string;
  };
}

interface Berth {
  id: string;
  name: string;
  length: number;
  maxDraft: number;
  maxLOA: number;
  maxBeam: number;
  status: string;
  cranes: Array<{ type: string; capacity: number; status: string }>;
}

interface UpcomingVesselsTimelineProps {
  vessels: Vessel[];
  onVesselClick: (vessel: Vessel) => void;
  selectedVesselId?: string;
  timeWindow: '7days' | 'year';
  onTimeWindowChange: (window: '7days' | 'year') => void;
  onAcceptRecommendation?: (vessel: Vessel) => void;
  onRejectRecommendation?: (vessel: Vessel) => void;
  onRequestAISuggestion?: (vessel: Vessel) => void;
  berths?: Berth[];
}

export function UpcomingVesselsTimeline({ vessels, onVesselClick, selectedVesselId, timeWindow, onTimeWindowChange, onAcceptRecommendation, onRejectRecommendation, onRequestAISuggestion, berths = [] }: UpcomingVesselsTimelineProps) {
  const [hoveredETAVesselId, setHoveredETAVesselId] = useState<string | null>(null);
  const [openSuggestionId, setOpenSuggestionId] = useState<string | null>(null);
  const [collapsedDays, setCollapsedDays] = useState<Set<string>>(new Set());
  // Track which vessels have their AI panel VISIBLE (shown after clicking "Get AI Berth Suggestion")
  const [visibleAIPanels, setVisibleAIPanels] = useState<Set<string>>(new Set());
  const suggestionPopupRef = useRef<HTMLDivElement>(null);

  // Show AI panel for a vessel (called after fetching suggestion)
  const showAIPanel = (vesselId: string) => {
    setVisibleAIPanels(prev => {
      const next = new Set(prev);
      next.add(vesselId);
      return next;
    });
  };

  // Hide AI panel (show button again)
  const hideAIPanel = (vesselId: string) => {
    setVisibleAIPanels(prev => {
      const next = new Set(prev);
      next.delete(vesselId);
      return next;
    });
  };

  const toggleDay = (key: string) => {
    setCollapsedDays(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  // Close popup when clicking outside
  useEffect(() => {
    if (!openSuggestionId) return;
    const handleClickOutside = (e: MouseEvent) => {
      if (suggestionPopupRef.current && !suggestionPopupRef.current.contains(e.target as Node)) {
        setOpenSuggestionId(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [openSuggestionId]);

  const findBerth = (name: string) => berths.find(b => b.name === name);

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 85) return 'var(--status-on-time)';
    if (confidence >= 70) return 'var(--status-at-risk)';
    return 'var(--status-delayed)';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'on-time':
        return 'var(--status-on-time)';
      case 'early':
        return 'var(--kale-teal)';
      case 'at-risk':
        return 'var(--status-at-risk)';
      case 'delayed':
        return 'var(--status-delayed)';
      case 'arrived':
        return 'var(--status-berthed)';
      default:
        return 'var(--muted-foreground)';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'on-time':
        return 'On Time';
      case 'early':
        return 'Early';
      case 'at-risk':
        return 'At Risk';
      case 'delayed':
        return 'Delayed';
      case 'arrived':
        return 'Arrived';
      default:
        return status;
    }
  };

  const formatDeviation = (minutes: number) => {
    const hours = Math.floor(Math.abs(minutes) / 60);
    const mins = Math.abs(minutes) % 60;
    const sign = minutes >= 0 ? '+' : '-';
    return `${sign}${hours}h ${mins}m`;
  };

  // Dynamic accuracy calculation based on multiple realistic factors
  const calculateAccuracy = (predicted: Date, actual: Date, vessel?: Vessel): number => {
    const diffMinutes = Math.abs((actual.getTime() - predicted.getTime()) / (1000 * 60));
    
    // Base accuracy from time difference (smoother decay curve)
    let baseAccuracy: number;
    if (diffMinutes <= 10) {
      baseAccuracy = 98 - (diffMinutes * 0.2); // 98-96% for very accurate
    } else if (diffMinutes <= 30) {
      baseAccuracy = 96 - ((diffMinutes - 10) * 0.6); // 96-84%
    } else if (diffMinutes <= 60) {
      baseAccuracy = 84 - ((diffMinutes - 30) * 0.4); // 84-72%
    } else if (diffMinutes <= 120) {
      baseAccuracy = 72 - ((diffMinutes - 60) * 0.25); // 72-57%
    } else {
      baseAccuracy = Math.max(35, 57 - ((diffMinutes - 120) * 0.1)); // 57-35% floor
    }
    
    if (!vessel) {
      return Math.round(baseAccuracy * 10) / 10;
    }
    
    // Vessel type modifier: Container ships are more precise, bulk carriers less so
    const vesselTypeModifiers: Record<string, number> = {
      'container': 1.08,
      'tanker': 1.04,
      'cargo': 1.02,
      'bulk carrier': 0.96,
      'general cargo': 0.98,
      'roro': 1.05,
      'lng carrier': 1.06,
      'lpg carrier': 1.05,
      'chemical tanker': 1.03,
    };
    const typeKey = vessel.vesselType?.toLowerCase() || 'cargo';
    const typeModifier = vesselTypeModifiers[typeKey] || 1.0;
    
    // Size modifier: Larger vessels tend to be more consistent
    const sizeScore = Math.min(1.05, 0.95 + (vessel.loa / 4000)); // LOA up to 400m contributes
    
    // Constraint satisfaction modifier
    const constraintCount = vessel.constraints?.length || 0;
    const satisfiedCount = vessel.constraints?.filter(c => c.status === 'satisfied').length || 0;
    const constraintRatio = constraintCount > 0 ? satisfiedCount / constraintCount : 0.9;
    const constraintModifier = 0.92 + (constraintRatio * 0.12); // 0.92-1.04 range
    
    // Generate consistent pseudo-random variation based on vessel ID
    const vesselSeed = vessel.id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    const dailySeed = Math.floor(actual.getTime() / (24 * 60 * 60 * 1000));
    const combinedSeed = vesselSeed + dailySeed;
    const variation = ((Math.sin(combinedSeed) + 1) / 2) * 0.08 - 0.04; // ±4% variation
    
    // Calculate final accuracy with all modifiers
    let finalAccuracy = baseAccuracy * typeModifier * sizeScore * constraintModifier * (1 + variation);
    
    // Clamp to realistic range (45-99%)
    finalAccuracy = Math.max(45, Math.min(99, finalAccuracy));
    
    return Math.round(finalAccuracy * 10) / 10;
  };

  const getAccuracyColor = (score: number): string => {
    if (score >= 95) return 'var(--status-on-time)';
    if (score >= 85) return 'var(--kale-teal)';
    if (score >= 70) return 'var(--status-at-risk)';
    return 'var(--status-delayed)';
  };

  // Group vessels by day for 7-day view
  const groupVesselsByDay = () => {
    const grouped: { dateKey: string; label: string; sublabel: string; vessels: Vessel[] }[] = [];
    const map = new Map<string, Vessel[]>();
    const today = new Date();
    const todayKey = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    const tomorrowKey = `${tomorrow.getFullYear()}-${String(tomorrow.getMonth() + 1).padStart(2, '0')}-${String(tomorrow.getDate()).padStart(2, '0')}`;

    vessels.forEach(vessel => {
      const d = vessel.predictedETA;
      const dateKey = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
      if (!map.has(dateKey)) map.set(dateKey, []);
      map.get(dateKey)!.push(vessel);
    });

    const sortedKeys = Array.from(map.keys()).sort();
    sortedKeys.forEach(dateKey => {
      const [y, m, d] = dateKey.split('-').map(Number);
      const date = new Date(y, m - 1, d);
      const fullDate = date.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
      let label: string;
      if (dateKey === todayKey) label = 'Today';
      else if (dateKey === tomorrowKey) label = 'Tomorrow';
      else label = date.toLocaleDateString('en-US', { weekday: 'long' });

      grouped.push({ dateKey, label, sublabel: fullDate, vessels: map.get(dateKey)! });
    });

    return grouped;
  };

  const renderSevenDayView = () => {
    const groups = groupVesselsByDay();

    return (
      <div className="space-y-4 p-3">
        {groups.map((group) => {
          const isCollapsed = collapsedDays.has(group.dateKey);
          const isToday = group.label === 'Today';
          const onTimeCount = group.vessels.filter(v => v.status === 'on-time' || v.status === 'early').length;
          const atRiskCount = group.vessels.filter(v => v.status === 'at-risk' || v.status === 'delayed').length;

          return (
            <div key={group.dateKey}>
              {/* Collapsible date header */}
              <button
                onClick={() => toggleDay(group.dateKey)}
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
                  {onTimeCount > 0 && (
                    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px]"
                      style={{
                        backgroundColor: isToday ? 'rgba(255,255,255,0.2)' : 'var(--status-on-time)',
                        color: 'white',
                        fontWeight: 600,
                      }}>
                      {onTimeCount} On Time
                    </span>
                  )}
                  {atRiskCount > 0 && (
                    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px]"
                      style={{
                        backgroundColor: isToday ? 'rgba(255,255,255,0.2)' : 'var(--status-at-risk)',
                        color: 'white',
                        fontWeight: 600,
                      }}>
                      <AlertTriangle className="w-2.5 h-2.5" />
                      {atRiskCount} At Risk
                    </span>
                  )}
                  <span className="text-[10px]" style={{ color: isToday ? 'rgba(255,255,255,0.7)' : 'var(--muted-foreground)', fontWeight: 500 }}>
                    {group.vessels.length} vessel{group.vessels.length !== 1 ? 's' : ''}
                  </span>
                </div>
              </button>

              {/* Vessels grid */}
              {!isCollapsed && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2">
                  {group.vessels
                    .sort((a, b) => a.predictedETA.getTime() - b.predictedETA.getTime())
                    .map(vessel => renderVesselCard(vessel))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  const renderYearView = () => {
    const vesselsByMonth: { [key: string]: { vessels: Vessel[]; monthDate: Date } } = {};

    vessels.forEach(vessel => {
      const monthKey = vessel.declaredETA.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long'
      });
      if (!vesselsByMonth[monthKey]) {
        vesselsByMonth[monthKey] = { vessels: [], monthDate: vessel.declaredETA };
      }
      vesselsByMonth[monthKey].vessels.push(vessel);
    });

    // Sort months chronologically
    const sortedMonths = Object.entries(vesselsByMonth).sort(
      (a, b) => a[1].monthDate.getTime() - b[1].monthDate.getTime()
    );

    return (
      <div className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {sortedMonths.map(([month, { vessels: monthVessels }]) => {
            // Sort vessels within month by date
            const sortedVessels = [...monthVessels].sort(
              (a, b) => a.declaredETA.getTime() - b.declaredETA.getTime()
            );
            const onTimeCount = sortedVessels.filter(v => v.status === 'on-time' || v.status === 'early').length;
            const atRiskCount = sortedVessels.filter(v => v.status === 'at-risk' || v.status === 'delayed').length;

            return (
              <div
                key={month}
                className="rounded-xl shadow-sm hover:shadow-md transition-shadow overflow-hidden"
                style={{ backgroundColor: 'white', border: '1px solid var(--border)' }}
              >
                {/* Month Header */}
                <div className="flex items-center justify-between px-4 py-3"
                  style={{ borderBottom: '1px solid var(--border)', backgroundColor: 'var(--kale-sky)' }}>
                  <h4 className="text-sm" style={{ color: 'var(--kale-blue)', fontWeight: 700 }}>{month}</h4>
                  <span className="text-xs px-2 py-1 rounded-md"
                    style={{ backgroundColor: 'var(--kale-blue)', color: 'white', fontWeight: 700 }}>
                    {monthVessels.length}
                  </span>
                </div>

                {/* Status Summary */}
                <div className="flex items-center gap-3 px-4 py-2" style={{ borderBottom: '1px solid var(--border)', backgroundColor: '#FAFAFA' }}>
                  {onTimeCount > 0 && (
                    <div className="flex items-center gap-1">
                      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--status-on-time)' }} />
                      <span className="text-[10px]" style={{ color: 'var(--muted-foreground)' }}>{onTimeCount} on time</span>
                    </div>
                  )}
                  {atRiskCount > 0 && (
                    <div className="flex items-center gap-1">
                      <AlertTriangle className="w-2.5 h-2.5" style={{ color: 'var(--status-at-risk)' }} />
                      <span className="text-[10px]" style={{ color: 'var(--status-at-risk)' }}>{atRiskCount} at risk</span>
                    </div>
                  )}
                </div>

                {/* Vessels List */}
                <div className="px-3 py-2 space-y-1">
                  {sortedVessels.slice(0, 5).map(vessel => (
                    <div
                      key={vessel.id}
                      className="flex items-center gap-2 p-2 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
                      onClick={() => onVesselClick(vessel)}
                    >
                      <div
                        className="w-1 h-10 rounded-full flex-shrink-0"
                        style={{ backgroundColor: getStatusColor(vessel.status) }}
                      />
                      <div className="flex-1 min-w-0">
                        <div className="text-xs truncate" style={{ fontWeight: 600, color: 'var(--foreground)' }}>
                          {vessel.name}
                        </div>
                        <div className="text-[10px]" style={{ color: 'var(--muted-foreground)' }}>
                          {vessel.declaredETA.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                        </div>
                      </div>
                      <ChevronRight className="w-3.5 h-3.5 flex-shrink-0" style={{ color: 'var(--muted-foreground)' }} />
                    </div>
                  ))}
                </div>

                {/* More link */}
                {monthVessels.length > 5 && (
                  <div className="px-4 py-2" style={{ borderTop: '1px solid var(--border)' }}>
                    <button
                      className="text-[11px] w-full text-center py-1 rounded hover:bg-gray-50 transition-colors"
                      style={{ color: 'var(--kale-blue)', fontWeight: 500 }}
                    >
                      +{monthVessels.length - 5} more vessels
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderVesselCard = (vessel: Vessel) => {
    const isSelected = selectedVesselId === vessel.id;
    const criticalConstraints = vessel.constraints.filter(c => c.status === 'critical');

    return (
      <div
        key={vessel.id}
        className={`relative cursor-pointer transition-all duration-200 hover:scale-[1.01] ${openSuggestionId === vessel.id ? 'z-40' : ''}`}
        onClick={() => onVesselClick(vessel)}
      >
        <div
          className="rounded-lg shadow-sm hover:shadow-md transition-shadow h-full"
          style={{
            border: `1.5px solid ${isSelected ? getStatusColor(vessel.status) : 'var(--border)'}`,
            backgroundColor: 'white',
          }}
        >
          <div className="p-2">
            {/* Header: Name + Status */}
            <div className="flex items-center justify-between gap-1 mb-1">
              <div className="flex items-center gap-1 min-w-0 flex-1">
                <Ship className="w-3 h-3 flex-shrink-0" style={{ color: 'var(--kale-blue)' }} />
                <span className="text-xs truncate" style={{ fontWeight: 600, color: 'var(--kale-blue)' }}>
                  {vessel.name}
                </span>
                {vessel.aiRecommendation && (
                  <div className="flex-shrink-0 w-1.5 h-1.5 rounded-full animate-pulse"
                    style={{ backgroundColor: 'var(--kale-teal)' }}
                    title="AI Recommendation Available"
                  />
                )}
              </div>
              <span className="px-1 py-px rounded text-[9px] whitespace-nowrap flex-shrink-0"
                style={{
                  backgroundColor: `${getStatusColor(vessel.status)}20`,
                  color: getStatusColor(vessel.status),
                  fontWeight: 600,
                }}>
                {getStatusLabel(vessel.status)}
              </span>
            </div>

            {/* Vessel type */}
            <div className="text-[10px] mb-1" style={{ color: 'var(--muted-foreground)' }}>
              {vessel.vesselType} • {vessel.flag}
            </div>

            {/* ETA row */}
            <div className="flex items-center justify-between mb-1 px-1.5 py-1 rounded"
              style={{ backgroundColor: 'var(--kale-sky)' }}>
              <div
                className="relative"
                onMouseEnter={() => setHoveredETAVesselId(vessel.id)}
                onMouseLeave={() => setHoveredETAVesselId(null)}
              >
                <div className="flex items-center gap-0.5">
                  <Clock className="w-2.5 h-2.5" style={{ color: 'var(--kale-blue)' }} />
                  <span className="text-[11px]" style={{ fontWeight: 600, color: 'var(--kale-blue)' }}>
                    {vessel.predictedETA.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                  <Info className="w-2 h-2" style={{ color: 'var(--kale-blue)', opacity: 0.4 }} />
                </div>
                <div className="text-[9px]" style={{ color: 'var(--muted-foreground)' }}>
                  {vessel.ata ? 'Predicted' : 'AI Predicted'}
                </div>

                {hoveredETAVesselId === vessel.id && (
                  <div className="absolute left-0 bottom-full mb-1 z-50 pointer-events-none">
                    <div className="px-2 py-1 rounded shadow-lg text-[9px] whitespace-nowrap"
                      style={{ backgroundColor: 'var(--kale-blue)', color: 'white' }}>
                      <div style={{ fontWeight: 600 }}>AI Predicted ETA</div>
                      <div style={{ opacity: 0.85 }}>Based on AIS, weather, history & port traffic</div>
                    </div>
                    <div className="w-1.5 h-1.5 rotate-45 ml-3 -mt-0.5"
                      style={{ backgroundColor: 'var(--kale-blue)' }} />
                  </div>
                )}
              </div>

              {vessel.ata ? (
                <div className="text-right">
                  <div className="flex items-center gap-0.5 justify-end">
                    <CheckCircle2 className="w-2.5 h-2.5" style={{ color: 'var(--status-berthed)' }} />
                    <span className="text-[11px]" style={{ fontWeight: 600, color: 'var(--status-berthed)' }}>
                      {vessel.ata.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <div className="text-[9px]" style={{ color: 'var(--muted-foreground)' }}>Actual</div>
                </div>
              ) : (
                <div className="text-right">
                  <span className="text-[11px]" style={{ fontWeight: 500 }}>
                    {vessel.declaredETA.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                  <div className="text-[9px]" style={{ color: 'var(--muted-foreground)' }}>Declared</div>
                </div>
              )}
            </div>

            {/* Accuracy badge for arrived vessels */}
            {vessel.ata && (
              <div className="flex items-center justify-between mb-1 px-1.5 py-0.5 rounded border"
                style={{
                  borderColor: getAccuracyColor(calculateAccuracy(vessel.predictedETA, vessel.ata, vessel)),
                  backgroundColor: `${getAccuracyColor(calculateAccuracy(vessel.predictedETA, vessel.ata, vessel))}10`,
                }}>
                <div className="flex items-center gap-0.5">
                  <TrendingUp className="w-2.5 h-2.5" style={{ color: getAccuracyColor(calculateAccuracy(vessel.predictedETA, vessel.ata, vessel)) }} />
                  <span className="text-[9px]" style={{ fontWeight: 500 }}>Accuracy</span>
                </div>
                <span className="text-[11px]" style={{
                  fontWeight: 700,
                  color: getAccuracyColor(calculateAccuracy(vessel.predictedETA, vessel.ata, vessel))
                }}>
                  {calculateAccuracy(vessel.predictedETA, vessel.ata, vessel)}%
                </span>
              </div>
            )}

            {/* Deviation badge */}
            {vessel.etaDeviation !== 0 && !vessel.ata && (
              <div className="flex items-center gap-1 mb-1 px-1.5 py-0.5 rounded text-[10px]"
                style={{
                  backgroundColor: Math.abs(vessel.etaDeviation) > 60 ? 'var(--status-at-risk)' : 'var(--kale-teal)',
                  color: 'white',
                  fontWeight: 500,
                }}>
                {vessel.etaDeviation > 0 ? <TrendingUp className="w-2.5 h-2.5" /> : <TrendingDown className="w-2.5 h-2.5" />}
                {formatDeviation(vessel.etaDeviation)}
              </div>
            )}

            {/* Dimensions + cargo */}
            <div className="flex items-center justify-between text-[9px]" style={{ color: 'var(--muted-foreground)' }}>
              <span>{vessel.loa}m x {vessel.beam}m x {vessel.draft}m</span>
              <span style={{ fontWeight: 500 }}>{vessel.cargoQuantity > 0 ? `${vessel.cargoQuantity.toLocaleString()} ${vessel.cargoUnit}` : vessel.cargoType}</span>
            </div>

            {/* Constraints (compact) */}
            {criticalConstraints.length > 0 && (
              <div className="flex items-center gap-0.5 mt-1 text-[9px]">
                <AlertTriangle className="w-2.5 h-2.5" style={{ color: 'var(--status-critical)' }} />
                <span style={{ color: 'var(--status-critical)', fontWeight: 500 }}>
                  {criticalConstraints.length} critical
                </span>
              </div>
            )}

            {/* Show AI panel if visible, otherwise show button */}
            {vessel.aiRecommendation && visibleAIPanels.has(vessel.id) ? (() => {
              const rec = vessel.aiRecommendation;
              const suggestedBerth = findBerth(rec.suggestedBerth);
              const loaMargin = suggestedBerth ? ((suggestedBerth.maxLOA - vessel.loa) / suggestedBerth.maxLOA * 100).toFixed(1) : '0';
              const draftClearance = suggestedBerth ? (suggestedBerth.maxDraft - vessel.draft).toFixed(1) : '0';
              const craneCount = suggestedBerth?.cranes?.filter(c => c.status === 'operational').length || 0;

              return (
                <div className="mt-2 rounded-lg overflow-hidden" style={{ border: '1.5px solid var(--kale-blue)' }} onClick={(e) => e.stopPropagation()}>
                  {/* Header - Clickable to hide panel and show button again */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      hideAIPanel(vessel.id);
                    }}
                    className="w-full flex items-center justify-between px-2 py-1.5 transition-colors hover:opacity-90"
                    style={{ backgroundColor: 'var(--kale-sky)', border: 'none', cursor: 'pointer' }}
                  >
                    <div className="flex items-center gap-1.5">
                      <ChevronDown className="w-3 h-3" style={{ color: 'var(--kale-blue)' }} />
                      <Zap className="w-3 h-3" style={{ color: 'var(--kale-blue)' }} />
                      <span className="text-[10px]" style={{ fontWeight: 600, color: 'var(--kale-blue)' }}>AI Recommended Berth</span>
                    </div>
                    <span className="px-1.5 py-0.5 rounded text-[10px]" style={{
                      fontWeight: 700,
                      backgroundColor: getConfidenceColor(rec.confidence),
                      color: 'white',
                    }}>
                      {Math.round(rec.confidence)}%
                    </span>
                  </button>

                  {/* Panel Content */}
                  <div className="px-2 py-1.5" style={{ borderBottom: '1px solid var(--border)' }}>
                    <div className="text-sm" style={{ fontWeight: 700, color: 'var(--kale-blue)' }}>
                      {rec.suggestedBerth}
                    </div>
                    <div className="text-[9px] mt-1" style={{ color: 'var(--muted-foreground)', lineHeight: 1.4 }}>
                      Physical fit: {vessel.loa}m vessel in {suggestedBerth?.maxLOA || '?'}m berth ({loaMargin}% margin).
                      Draft clearance: {draftClearance}m safety margin.
                      Compatible: {vessel.vesselType} at {suggestedBerth?.cranes?.[0]?.type || 'Container'} berth.
                      {craneCount} crane(s) available at this berth.
                      {rec.confidence >= 80 ? 'Good match - recommended.' : rec.confidence >= 60 ? 'Acceptable match - some constraints to consider.' : 'Limited options - review constraints.'}
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex items-center gap-2 p-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onAcceptRecommendation?.(vessel);
                      }}
                      className="flex-1 flex items-center justify-center gap-1 py-1.5 rounded text-[10px] transition-colors"
                      style={{
                        backgroundColor: 'var(--kale-teal)',
                        color: 'white',
                        fontWeight: 600,
                        border: 'none',
                        cursor: 'pointer',
                      }}
                      onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#0E9488'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'var(--kale-teal)'; }}
                    >
                      <CheckCircle2 className="w-3 h-3" />
                      Accept
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onRejectRecommendation?.(vessel);
                      }}
                      className="flex items-center justify-center gap-1 px-3 py-1.5 rounded text-[10px] transition-colors"
                      style={{
                        backgroundColor: 'white',
                        color: 'var(--muted-foreground)',
                        fontWeight: 600,
                        border: '1px solid var(--border)',
                        cursor: 'pointer',
                      }}
                      onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--muted)'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'white'; }}
                    >
                      Modify
                    </button>
                  </div>
                </div>
              );
            })() : (
              /* Default: Get AI Berth Suggestion button */
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  // If already has recommendation, just show the panel
                  if (vessel.aiRecommendation) {
                    showAIPanel(vessel.id);
                  } else {
                    // Request new suggestion and show panel when ready
                    onRequestAISuggestion?.(vessel);
                    showAIPanel(vessel.id);
                  }
                }}
                className="w-full flex items-center justify-center gap-1.5 text-[10px] px-2 py-1.5 rounded transition-colors mt-1"
                style={{
                  background: 'linear-gradient(135deg, var(--kale-blue), var(--kale-teal))',
                  border: 'none',
                  color: 'white',
                  cursor: 'pointer',
                  fontWeight: 600,
                }}
                onMouseEnter={(e) => { e.currentTarget.style.opacity = '0.9'; }}
                onMouseLeave={(e) => { e.currentTarget.style.opacity = '1'; }}
              >
                <Brain className="w-3.5 h-3.5" />
                Get AI Berth Suggestion
              </button>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="sticky top-0 z-10 flex items-center justify-between px-4 py-2 border-b bg-white" style={{ borderColor: 'var(--border)' }}>
        <div className="flex items-center gap-4">
          <div>
            <h3 className="text-sm" style={{ color: 'var(--kale-blue)', fontWeight: 700 }}>Upcoming Vessels</h3>
            <p className="text-[10px]" style={{ color: 'var(--muted-foreground)' }}>
              {timeWindow === '7days' ? 'Next 7 days by predicted ETA' : 'Full year by declared ETA'}
            </p>
          </div>

          {/* Status counts */}
          <div className="hidden md:flex items-center gap-3 text-[11px]">
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--status-on-time)' }} />
              <span style={{ fontWeight: 500 }}>{vessels.filter(v => v.status === 'on-time').length} On Time</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--status-at-risk)' }} />
              <span style={{ fontWeight: 500 }}>{vessels.filter(v => v.status === 'at-risk').length} At Risk</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--status-delayed)' }} />
              <span style={{ fontWeight: 500 }}>{vessels.filter(v => v.status === 'delayed').length} Delayed</span>
            </div>
          </div>
        </div>

        <div className="flex gap-0.5 p-0.5 rounded-lg" style={{ backgroundColor: 'var(--muted)' }}>
          <button
            onClick={() => onTimeWindowChange('7days')}
            className="px-2.5 py-1 text-[11px] rounded transition-all"
            style={{
              backgroundColor: timeWindow === '7days' ? 'white' : 'transparent',
              color: timeWindow === '7days' ? 'var(--kale-blue)' : 'var(--muted-foreground)',
              fontWeight: timeWindow === '7days' ? 600 : 400,
            }}
          >
            7 Days
          </button>
          <button
            onClick={() => onTimeWindowChange('year')}
            className="px-2.5 py-1 text-[11px] rounded transition-all"
            style={{
              backgroundColor: timeWindow === 'year' ? 'white' : 'transparent',
              color: timeWindow === 'year' ? 'var(--kale-blue)' : 'var(--muted-foreground)',
              fontWeight: timeWindow === 'year' ? 600 : 400,
            }}
          >
            Full Year
          </button>
        </div>
      </div>

      {/* Vessels list */}
      <div className="flex-1 overflow-auto">
        {timeWindow === '7days' ? renderSevenDayView() : renderYearView()}
      </div>
    </div>
  );
}
