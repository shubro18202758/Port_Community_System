import { useState, useEffect } from 'react';
import { X, Anchor, Ship, Calendar, Clock, Zap, TrendingUp, CheckCircle2, AlertTriangle, Construction, Timer, Package } from 'lucide-react';

interface Berth {
  id: string;
  name: string;
  length: number;
  maxDraft: number;
  maxLOA: number;
  maxBeam: number;
  status: 'available' | 'occupied' | 'maintenance';
  cranes: Array<{
    id: string;
    type: 'STS' | 'RTG' | 'MHC';
    capacity: number;
    status: 'operational' | 'maintenance' | 'idle';
  }>;
  reeferPoints: number;
  currentVessel?: {
    name: string;
    eta: Date;
    etd: Date;
    atb?: Date;
    loa: number;
    vesselId?: string;
    cargoType?: string;
    cargoQuantity?: number;
    cargoUnit?: string;
  };
  upcomingVessels?: Array<{
    name: string;
    eta: Date;
    etd: Date;
    loa: number;
    confidence: number;
    reason: string;
  }>;
}

interface BerthDetailDialogProps {
  berth: Berth;
  onClose: () => void;
}

export function BerthDetailDialog({ berth, onClose }: BerthDetailDialogProps) {
  const [now, setNow] = useState(new Date());

  // Update time every second for live countdown
  useEffect(() => {
    const interval = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  const fmtDate = (d: Date) => d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });

  const fmtDuration = (ms: number) => {
    const totalMins = Math.floor(Math.abs(ms) / (1000 * 60));
    const hours = Math.floor(totalMins / 60);
    const mins = totalMins % 60;
    if (hours >= 24) {
      const days = Math.floor(hours / 24);
      const remHours = hours % 24;
      return `${days}d ${remHours}h ${mins}m`;
    }
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'available': return 'Available';
      case 'occupied': return 'Occupied';
      case 'maintenance': return 'Maintenance';
      default: return status;
    }
  };

  const getCraneStatusColor = (status: string) => {
    switch (status) {
      case 'operational': return 'var(--status-on-time)';
      case 'maintenance': return 'var(--status-at-risk)';
      default: return 'var(--muted-foreground)';
    }
  };

  const operationalCranes = berth.cranes.filter(c => c.status === 'operational').length;
  const totalCraneCapacity = berth.cranes.reduce((sum, c) => sum + c.capacity, 0);

  // Calculate time at berth and ETD status
  const currentVessel = berth.currentVessel;
  const timeAtBerth = currentVessel?.atb ? now.getTime() - currentVessel.atb.getTime() : null;
  const timeToETD = currentVessel ? currentVessel.etd.getTime() - now.getTime() : null;
  const isOverstaying = timeToETD !== null && timeToETD < 0;
  const isApproachingETD = timeToETD !== null && timeToETD > 0 && timeToETD < 2 * 60 * 60 * 1000; // < 2 hours

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[85vh] overflow-hidden flex flex-col">
        {/* Header - compact */}
        <div className="px-4 py-3 border-b" style={{
          borderColor: 'var(--border)',
          background: 'linear-gradient(135deg, var(--kale-blue) 0%, var(--kale-teal) 100%)'
        }}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Anchor className="w-4 h-4 text-white" />
              <h3 className="text-sm text-white" style={{ fontWeight: 700 }}>{berth.name}</h3>
              <span className="px-2 py-0.5 rounded-full text-[10px] bg-white/20 text-white" style={{ fontWeight: 600 }}>
                {getStatusLabel(berth.status)}
              </span>
              <span className="text-white/70 text-xs">ID: {berth.id}</span>
            </div>
            <button onClick={onClose} className="p-1.5 rounded-lg bg-white/20 hover:bg-white/30 transition-colors">
              <X className="w-4 h-4 text-white" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto px-4 py-3">
          <div className="space-y-3">
            {/* Specs - 4-column inline */}
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <Anchor className="w-3.5 h-3.5" style={{ color: 'var(--kale-blue)' }} />
                <span className="text-xs" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>Specifications</span>
              </div>
              <div className="grid grid-cols-4 gap-2">
                {[
                  { label: 'Length', value: `${berth.length}m` },
                  { label: 'Max LOA', value: `${berth.maxLOA}m` },
                  { label: 'Max Draft', value: `${berth.maxDraft}m` },
                  { label: 'Max Beam', value: `${berth.maxBeam}m` },
                ].map(spec => (
                  <div key={spec.label} className="p-2 rounded-lg text-center border" style={{ borderColor: 'var(--border)', backgroundColor: 'var(--kale-sky)' }}>
                    <div className="text-[10px]" style={{ color: 'var(--muted-foreground)' }}>{spec.label}</div>
                    <div className="text-sm" style={{ fontWeight: 700, color: 'var(--kale-blue)' }}>{spec.value}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Equipment summary + Reefer - inline */}
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <Construction className="w-3.5 h-3.5" style={{ color: 'var(--kale-blue)' }} />
                <span className="text-xs" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>Equipment</span>
              </div>
              <div className="flex items-center gap-3 mb-2 text-xs">
                <div className="flex items-center gap-4 flex-1 px-3 py-2 rounded-lg border" style={{ borderColor: 'var(--border)' }}>
                  <div>
                    <span style={{ color: 'var(--muted-foreground)' }}>Cranes </span>
                    <span style={{ fontWeight: 700, color: 'var(--kale-blue)' }}>{operationalCranes}/{berth.cranes.length}</span>
                  </div>
                  <div>
                    <span style={{ color: 'var(--muted-foreground)' }}>Capacity </span>
                    <span style={{ fontWeight: 700, color: 'var(--kale-blue)' }}>{totalCraneCapacity}t</span>
                  </div>
                </div>
                <div className="px-3 py-2 rounded-lg border" style={{ borderColor: 'var(--border)' }}>
                  <span style={{ color: 'var(--muted-foreground)' }}>Reefer </span>
                  <span style={{ fontWeight: 700, color: 'var(--kale-blue)' }}>{berth.reeferPoints}</span>
                </div>
              </div>

              {/* Crane list - compact grid */}
              <div className="grid grid-cols-2 gap-1.5">
                {berth.cranes.map((crane) => (
                  <div key={crane.id} className="flex items-center justify-between px-2.5 py-1.5 rounded border"
                    style={{ borderColor: 'var(--border)' }}>
                    <div className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: getCraneStatusColor(crane.status) }} />
                      <span className="text-xs" style={{ fontWeight: 600 }}>{crane.id}</span>
                      <span className="text-[10px]" style={{ color: 'var(--muted-foreground)' }}>{crane.type}</span>
                    </div>
                    <span className="text-xs" style={{ fontWeight: 500 }}>{crane.capacity}t</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Current Vessel - Enhanced with time at berth and ETD status */}
            {currentVessel && (
              <div>
                <div className="flex items-center gap-1.5 mb-2">
                  <Ship className="w-3.5 h-3.5" style={{ color: 'var(--kale-blue)' }} />
                  <span className="text-xs" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>Current Vessel</span>
                </div>
                <div className="p-2.5 rounded-lg border" style={{
                  borderColor: isOverstaying ? 'var(--status-delayed)' : isApproachingETD ? 'var(--status-at-risk)' : 'var(--kale-blue)',
                  backgroundColor: isOverstaying ? 'rgba(239, 68, 68, 0.1)' : isApproachingETD ? 'rgba(251, 191, 36, 0.1)' : 'var(--kale-sky)'
                }}>
                  {/* Overstay Alert Banner */}
                  {isOverstaying && (
                    <div className="flex items-center gap-2 px-2 py-1.5 mb-2 rounded-lg"
                      style={{ backgroundColor: 'var(--status-delayed)', color: 'white' }}>
                      <AlertTriangle className="w-3.5 h-3.5" />
                      <span className="text-xs" style={{ fontWeight: 700 }}>
                        OVERSTAYING: {fmtDuration(Math.abs(timeToETD!))} beyond scheduled ETD
                      </span>
                    </div>
                  )}

                  {/* Approaching ETD Warning */}
                  {isApproachingETD && !isOverstaying && (
                    <div className="flex items-center gap-2 px-2 py-1.5 mb-2 rounded-lg"
                      style={{ backgroundColor: 'var(--status-at-risk)', color: 'white' }}>
                      <Clock className="w-3.5 h-3.5" />
                      <span className="text-xs" style={{ fontWeight: 700 }}>
                        Departure in {fmtDuration(timeToETD!)} - Prepare for undocking
                      </span>
                    </div>
                  )}

                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm" style={{ fontWeight: 700, color: 'var(--kale-blue)' }}>{currentVessel.name}</span>
                      <span className="text-[10px]" style={{ color: 'var(--muted-foreground)' }}>LOA: {currentVessel.loa}m</span>
                    </div>
                    <span className="px-1.5 py-0.5 rounded text-[10px]" style={{
                      backgroundColor: isOverstaying ? 'var(--status-delayed)' : 'var(--kale-blue)',
                      color: 'white',
                      fontWeight: 600
                    }}>
                      {isOverstaying ? 'Overstaying' : 'Berthed'}
                    </span>
                  </div>

                  {/* Time at Berth Stats Grid */}
                  <div className="grid grid-cols-3 gap-2 mb-2">
                    {/* Time at Berth */}
                    <div className="p-2 rounded-lg text-center" style={{ backgroundColor: 'white', border: '1px solid var(--border)' }}>
                      <div className="flex items-center justify-center gap-1 mb-0.5">
                        <Timer className="w-3 h-3" style={{ color: 'var(--kale-blue)' }} />
                        <span className="text-[9px]" style={{ color: 'var(--muted-foreground)' }}>Time at Berth</span>
                      </div>
                      <div className="text-sm" style={{ fontWeight: 700, color: 'var(--kale-blue)' }}>
                        {timeAtBerth !== null ? fmtDuration(timeAtBerth) : '--'}
                      </div>
                    </div>

                    {/* ETD Countdown */}
                    <div className="p-2 rounded-lg text-center" style={{
                      backgroundColor: isOverstaying ? 'rgba(239, 68, 68, 0.15)' : isApproachingETD ? 'rgba(251, 191, 36, 0.15)' : 'white',
                      border: `1px solid ${isOverstaying ? 'var(--status-delayed)' : isApproachingETD ? 'var(--status-at-risk)' : 'var(--border)'}`
                    }}>
                      <div className="flex items-center justify-center gap-1 mb-0.5">
                        <Clock className="w-3 h-3" style={{ color: isOverstaying ? 'var(--status-delayed)' : isApproachingETD ? 'var(--status-at-risk)' : 'var(--kale-blue)' }} />
                        <span className="text-[9px]" style={{ color: 'var(--muted-foreground)' }}>
                          {isOverstaying ? 'Overdue By' : 'Time to ETD'}
                        </span>
                      </div>
                      <div className="text-sm" style={{
                        fontWeight: 700,
                        color: isOverstaying ? 'var(--status-delayed)' : isApproachingETD ? 'var(--status-at-risk)' : 'var(--kale-blue)'
                      }}>
                        {timeToETD !== null ? fmtDuration(timeToETD) : '--'}
                      </div>
                    </div>

                    {/* Cargo Info */}
                    <div className="p-2 rounded-lg text-center" style={{ backgroundColor: 'white', border: '1px solid var(--border)' }}>
                      <div className="flex items-center justify-center gap-1 mb-0.5">
                        <Package className="w-3 h-3" style={{ color: 'var(--kale-blue)' }} />
                        <span className="text-[9px]" style={{ color: 'var(--muted-foreground)' }}>Cargo</span>
                      </div>
                      <div className="text-sm" style={{ fontWeight: 700, color: 'var(--kale-blue)' }}>
                        {currentVessel.cargoQuantity ? `${currentVessel.cargoQuantity.toLocaleString()} ${currentVessel.cargoUnit || 'TEU'}` : currentVessel.cargoType || '--'}
                      </div>
                    </div>
                  </div>

                  {/* Schedule Times */}
                  <div className="flex items-center gap-4 text-xs">
                    {currentVessel.atb && (
                      <div className="flex items-center gap-1">
                        <Anchor className="w-3 h-3" style={{ color: 'var(--kale-blue)' }} />
                        <span style={{ color: 'var(--muted-foreground)' }}>Berthed</span>
                        <span style={{ fontWeight: 600 }}>{fmtDate(currentVessel.atb)}</span>
                      </div>
                    )}
                    {!currentVessel.atb && (
                      <div className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" style={{ color: 'var(--kale-blue)' }} />
                        <span style={{ color: 'var(--muted-foreground)' }}>ETA</span>
                        <span style={{ fontWeight: 600 }}>{fmtDate(currentVessel.eta)}</span>
                      </div>
                    )}
                    <div className="flex items-center gap-1">
                      <Clock className="w-3 h-3" style={{ color: isOverstaying ? 'var(--status-delayed)' : 'var(--kale-blue)' }} />
                      <span style={{ color: 'var(--muted-foreground)' }}>ETD</span>
                      <span style={{ fontWeight: 600, color: isOverstaying ? 'var(--status-delayed)' : undefined }}>{fmtDate(currentVessel.etd)}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Upcoming Vessels - compact */}
            {berth.upcomingVessels && berth.upcomingVessels.length > 0 && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5" style={{ color: 'var(--kale-blue)' }} />
                    <span className="text-xs" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>Upcoming Schedule</span>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded-full" style={{ backgroundColor: 'var(--kale-sky)', color: 'var(--kale-blue)', fontWeight: 600 }}>
                    {berth.upcomingVessels.length} vessel{berth.upcomingVessels.length !== 1 ? 's' : ''}
                  </span>
                </div>

                <div className="space-y-1.5">
                  {berth.upcomingVessels.map((vessel, idx) => (
                    <div key={idx} className="p-2.5 rounded-lg border" style={{ borderColor: 'var(--border)' }}>
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center gap-2">
                          <span className="text-xs" style={{ fontWeight: 700, color: 'var(--kale-blue)' }}>{vessel.name}</span>
                          <span className="text-[10px]" style={{ color: 'var(--muted-foreground)' }}>LOA: {vessel.loa}m</span>
                        </div>
                        <div className="flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px]"
                          style={{
                            backgroundColor: vessel.confidence >= 90 ? 'var(--status-on-time)' : vessel.confidence >= 75 ? 'var(--kale-teal)' : 'var(--status-at-risk)',
                            color: 'white',
                            fontWeight: 700,
                          }}>
                          <Zap className="w-2.5 h-2.5" />
                          {vessel.confidence}%
                        </div>
                      </div>
                      <div className="flex items-center gap-4 text-xs mb-1.5">
                        <div>
                          <span style={{ color: 'var(--muted-foreground)' }}>ETA </span>
                          <span style={{ fontWeight: 600 }}>{fmtDate(vessel.eta)}</span>
                        </div>
                        <div>
                          <span style={{ color: 'var(--muted-foreground)' }}>ETD </span>
                          <span style={{ fontWeight: 600 }}>{fmtDate(vessel.etd)}</span>
                        </div>
                      </div>
                      <div className="text-[10px] px-2 py-1 rounded" style={{ backgroundColor: 'var(--kale-sky)', color: 'var(--foreground)' }}>
                        <Zap className="w-2.5 h-2.5 inline mr-1" style={{ color: 'var(--kale-blue)' }} />
                        {vessel.reason}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* AI Insights - compact */}
            <div className="p-3 rounded-lg border" style={{ borderColor: 'var(--kale-teal)' }}>
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-3.5 h-3.5" style={{ color: 'var(--kale-teal)' }} />
                <span className="text-xs" style={{ fontWeight: 700, color: 'var(--kale-blue)' }}>AI Allocation Insights</span>
              </div>
              <div className="space-y-1 text-[11px]">
                {[
                  { label: 'Utilization', text: berth.status === 'occupied' ? 'Optimized for current vessel' : 'Ready for next allocation' },
                  { label: 'Resources', text: `${operationalCranes} crane${operationalCranes !== 1 ? 's' : ''} operational, ${totalCraneCapacity}t capacity` },
                  { label: 'Turnaround', text: isOverstaying ? 'Schedule delayed - coordinate departure' : 'Schedule optimized to minimize idle time' },
                  { label: 'Safety', text: 'All draft limits and buffer zones compliant' },
                ].map(item => (
                  <div key={item.label} className="flex items-start gap-1.5">
                    <CheckCircle2 className="w-3 h-3 flex-shrink-0 mt-0.5" style={{ color: 'var(--status-on-time)' }} />
                    <span>
                      <span style={{ fontWeight: 600 }}>{item.label}:</span>{' '}
                      <span style={{ color: 'var(--muted-foreground)' }}>{item.text}</span>
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-4 py-2.5 border-t" style={{ borderColor: 'var(--border)' }}>
          <span className="text-xs" style={{ color: 'var(--muted-foreground)' }}>
            {berth.cranes.length} cranes • {berth.reeferPoints} reefer pts
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg transition-colors text-xs"
            style={{ backgroundColor: 'var(--kale-blue)', color: 'white', fontWeight: 600 }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
