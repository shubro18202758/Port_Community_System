import { useState, useRef, useMemo, useCallback } from 'react';
import { Ship, Clock, GripHorizontal, ZoomIn, ZoomOut, ChevronLeft, ChevronRight, Anchor } from 'lucide-react';

interface GanttVessel {
  scheduleId: string;
  vesselId: string;
  vesselName: string;
  berthId: string;
  berthName: string;
  eta: Date;
  etd: Date;
  status: 'Scheduled' | 'Approaching' | 'Berthed' | 'Departed' | string;
  vesselType?: string;
  loa?: number;
}

interface GanttBerth {
  id: string;
  name: string;
  length: number;
  status: string;
}

interface GanttChartProps {
  berths: GanttBerth[];
  schedules: GanttVessel[];
  onReschedule?: (scheduleId: string, newBerthId: string, newEta: Date, newEtd: Date) => void;
  onVesselClick?: (vesselId: string) => void;
}

const STATUS_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  Berthed: { bg: '#059669', border: '#047857', text: '#ECFDF5' },
  Scheduled: { bg: '#7C3AED', border: '#6D28D9', text: '#F5F3FF' },
  Departed: { bg: '#6B7280', border: '#4B5563', text: '#F3F4F6' },
};

const HOUR_WIDTH = 60; // px per hour at 1x zoom
const ROW_HEIGHT = 48;
const HEADER_HEIGHT = 40;
const LABEL_WIDTH = 140;

export function GanttChart({ berths, schedules, onReschedule, onVesselClick }: GanttChartProps) {
  const [zoom, setZoom] = useState(1);
  const [dayOffset, setDayOffset] = useState(0);
  const [dragState, setDragState] = useState<{
    scheduleId: string;
    originalBerthId: string;
    originalEta: Date;
    originalEtd: Date;
    startX: number;
    startY: number;
    currentBerthId: string;
    offsetHours: number;
  } | null>(null);
  const [hoveredVessel, setHoveredVessel] = useState<string | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const scrollRef = useRef<HTMLDivElement>(null);

  const hourWidth = HOUR_WIDTH * zoom;
  const totalWidth = 24 * hourWidth;

  const baseDate = useMemo(() => {
    const d = new Date();
    d.setHours(0, 0, 0, 0);
    d.setDate(d.getDate() + dayOffset);
    return d;
  }, [dayOffset]);

  const endDate = useMemo(() => new Date(baseDate.getTime() + 24 * 60 * 60 * 1000), [baseDate]);

  const now = useMemo(() => new Date(), []);
  const nowOffset = useMemo(() => {
    const diff = (now.getTime() - baseDate.getTime()) / (1000 * 60 * 60);
    return diff * hourWidth;
  }, [now, baseDate, hourWidth]);

  const hours = useMemo(() => Array.from({ length: 24 }, (_, i) => i), []);

  // Filter schedules that overlap with current day view (exclude Approaching)
  const visibleSchedules = useMemo(() => {
    return schedules.filter(s => {
      return s.eta < endDate && s.etd > baseDate && s.status !== 'Approaching';
    });
  }, [schedules, baseDate, endDate]);

  const getBarPosition = useCallback((eta: Date, etd: Date) => {
    const startHours = Math.max(0, (eta.getTime() - baseDate.getTime()) / (1000 * 60 * 60));
    const endHours = Math.min(24, (etd.getTime() - baseDate.getTime()) / (1000 * 60 * 60));
    const left = startHours * hourWidth;
    const width = Math.max(20, (endHours - startHours) * hourWidth);
    return { left, width };
  }, [baseDate, hourWidth]);

  const handleDragStart = (e: React.MouseEvent, schedule: GanttVessel) => {
    if (schedule.status === 'Departed' || schedule.status === 'Berthed') return;
    e.preventDefault();
    e.stopPropagation();
    setDragState({
      scheduleId: schedule.scheduleId,
      originalBerthId: schedule.berthId,
      originalEta: schedule.eta,
      originalEtd: schedule.etd,
      startX: e.clientX,
      startY: e.clientY,
      currentBerthId: schedule.berthId,
      offsetHours: 0,
    });

    const handleMouseMove = (ev: MouseEvent) => {
      const dx = ev.clientX - e.clientX;
      const dy = ev.clientY - e.clientY;
      const offsetHours = dx / hourWidth;
      const rowShift = Math.round(dy / ROW_HEIGHT);
      const berthIdx = berths.findIndex(b => b.id === schedule.berthId);
      const newIdx = Math.max(0, Math.min(berths.length - 1, berthIdx + rowShift));
      setDragState(prev => prev ? {
        ...prev,
        currentBerthId: berths[newIdx].id,
        offsetHours,
      } : null);
    };

    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      setDragState(prev => {
        if (prev && onReschedule) {
          const shiftMs = prev.offsetHours * 60 * 60 * 1000;
          const newEta = new Date(prev.originalEta.getTime() + shiftMs);
          const newEtd = new Date(prev.originalEtd.getTime() + shiftMs);
          if (prev.currentBerthId !== prev.originalBerthId || Math.abs(prev.offsetHours) > 0.25) {
            onReschedule(prev.scheduleId, prev.currentBerthId, newEta, newEtd);
          }
        }
        return null;
      });
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  const formatDateHeader = (d: Date) => {
    return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  };

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b" style={{ backgroundColor: 'white', borderColor: 'var(--border)' }}>
        <div className="flex items-center gap-2">
          <button onClick={() => setDayOffset(d => d - 1)} className="p-1.5 rounded hover:bg-gray-100 transition-colors" style={{ border: '1px solid var(--border)' }}>
            <ChevronLeft className="w-4 h-4" style={{ color: 'var(--foreground)' }} />
          </button>
          <button
            onClick={() => setDayOffset(0)}
            className="px-3 py-1.5 rounded text-xs font-semibold transition-colors hover:bg-gray-100"
            style={{ border: '1px solid var(--border)', color: 'var(--kale-blue)' }}
          >
            Today
          </button>
          <button onClick={() => setDayOffset(d => d + 1)} className="p-1.5 rounded hover:bg-gray-100 transition-colors" style={{ border: '1px solid var(--border)' }}>
            <ChevronRight className="w-4 h-4" style={{ color: 'var(--foreground)' }} />
          </button>
          <span className="text-sm font-semibold ml-2" style={{ color: 'var(--kale-blue)' }}>
            {formatDateHeader(baseDate)}
          </span>
        </div>

        <div className="flex items-center gap-3">
          {/* Legend */}
          <div className="flex items-center gap-2">
            {Object.entries(STATUS_COLORS).map(([status, colors]) => (
              <div key={status} className="flex items-center gap-1">
                <div className="w-3 h-2 rounded-sm" style={{ backgroundColor: colors.bg }} />
                <span className="text-[10px]" style={{ color: 'var(--muted-foreground)' }}>{status}</span>
              </div>
            ))}
          </div>

          <div className="w-px h-5" style={{ backgroundColor: 'var(--border)' }} />

          {/* Zoom controls */}
          <div className="flex items-center gap-1">
            <button onClick={() => setZoom(z => Math.max(0.5, z - 0.25))} className="p-1 rounded hover:bg-gray-100" title="Zoom out">
              <ZoomOut className="w-4 h-4" style={{ color: 'var(--muted-foreground)' }} />
            </button>
            <span className="text-[10px] w-8 text-center font-medium" style={{ color: 'var(--muted-foreground)' }}>{zoom}x</span>
            <button onClick={() => setZoom(z => Math.min(3, z + 0.25))} className="p-1 rounded hover:bg-gray-100" title="Zoom in">
              <ZoomIn className="w-4 h-4" style={{ color: 'var(--muted-foreground)' }} />
            </button>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="flex-1 overflow-hidden flex">
        {/* Berth labels (fixed) */}
        <div className="flex-shrink-0 border-r" style={{ width: LABEL_WIDTH, borderColor: 'var(--border)', backgroundColor: 'white' }}>
          <div className="flex items-center px-3 font-semibold text-[10px] uppercase border-b"
            style={{ height: HEADER_HEIGHT, color: 'var(--muted-foreground)', borderColor: 'var(--border)', letterSpacing: 0.5 }}>
            <Anchor className="w-3 h-3 mr-1.5" /> Berths
          </div>
          {berths.map(berth => (
            <div key={berth.id} className="flex items-center px-3 border-b"
              style={{ height: ROW_HEIGHT, borderColor: 'var(--border)' }}>
              <div>
                <div className="text-xs font-semibold" style={{ color: 'var(--foreground)' }}>{berth.name}</div>
                <div className="text-[9px]" style={{ color: 'var(--muted-foreground)' }}>{berth.length}m</div>
              </div>
              <div className="ml-auto">
                <div className={`w-2 h-2 rounded-full`} style={{
                  backgroundColor: berth.status === 'occupied' ? '#DC2626' : berth.status === 'maintenance' ? '#F59E0B' : '#059669'
                }} />
              </div>
            </div>
          ))}
        </div>

        {/* Scrollable timeline */}
        <div ref={scrollRef} className="flex-1 overflow-x-auto overflow-y-hidden">
          <div style={{ width: totalWidth, minHeight: '100%' }}>
            {/* Time header */}
            <div className="flex border-b sticky top-0 z-10" style={{ height: HEADER_HEIGHT, borderColor: 'var(--border)', backgroundColor: 'white' }}>
              {hours.map(h => (
                <div key={h} className="flex-shrink-0 flex items-center justify-center border-r text-[10px] font-medium"
                  style={{ width: hourWidth, borderColor: 'var(--border)', color: h >= 6 && h <= 18 ? 'var(--foreground)' : 'var(--muted-foreground)' }}>
                  {String(h).padStart(2, '0')}:00
                </div>
              ))}
            </div>

            {/* Berth rows */}
            <div className="relative">
              {berths.map((berth, berthIdx) => (
                <div key={berth.id} className="flex border-b relative"
                  style={{
                    height: ROW_HEIGHT,
                    borderColor: 'var(--border)',
                    backgroundColor: berthIdx % 2 === 0 ? 'white' : '#FAFAFA',
                  }}>
                  {/* Hour grid lines */}
                  {hours.map(h => (
                    <div key={h} className="flex-shrink-0 border-r"
                      style={{
                        width: hourWidth,
                        borderColor: h % 6 === 0 ? 'rgba(0,0,0,0.08)' : 'rgba(0,0,0,0.03)',
                      }}
                    />
                  ))}

                  {/* Vessel bars */}
                  {visibleSchedules
                    .filter(s => {
                      if (dragState?.scheduleId === s.scheduleId) return false;
                      return s.berthId === berth.id;
                    })
                    .map(schedule => {
                      const { left, width } = getBarPosition(schedule.eta, schedule.etd);
                      const colors = STATUS_COLORS[schedule.status] || STATUS_COLORS.Scheduled;
                      const isDraggable = schedule.status !== 'Departed' && schedule.status !== 'Berthed';

                      return (
                        <div
                          key={schedule.scheduleId}
                          className={`absolute top-1 rounded-md flex items-center gap-1 px-2 overflow-hidden transition-shadow ${isDraggable ? 'cursor-grab hover:shadow-lg' : 'cursor-pointer'}`}
                          style={{
                            left, width,
                            height: ROW_HEIGHT - 8,
                            backgroundColor: colors.bg,
                            border: `1.5px solid ${colors.border}`,
                            zIndex: hoveredVessel === schedule.scheduleId ? 20 : 1,
                          }}
                          onMouseDown={(e) => isDraggable && handleDragStart(e, schedule)}
                          onClick={() => onVesselClick?.(schedule.vesselId)}
                          onMouseEnter={(e) => {
                            setHoveredVessel(schedule.scheduleId);
                            setTooltipPos({ x: e.clientX, y: e.clientY });
                          }}
                          onMouseLeave={() => setHoveredVessel(null)}
                        >
                          {isDraggable && <GripHorizontal className="w-3 h-3 flex-shrink-0 opacity-50" style={{ color: colors.text }} />}
                          <Ship className="w-3 h-3 flex-shrink-0" style={{ color: colors.text }} />
                          <span className="text-[10px] font-semibold truncate" style={{ color: colors.text }}>
                            {schedule.vesselName}
                          </span>
                          {width > 120 && (
                            <span className="text-[8px] opacity-70 ml-auto flex-shrink-0" style={{ color: colors.text }}>
                              {schedule.eta.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              -
                              {schedule.etd.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                          )}
                        </div>
                      );
                    })}

                  {/* Dragged vessel ghost on target berth */}
                  {dragState && dragState.currentBerthId === berth.id && (() => {
                    const shiftMs = dragState.offsetHours * 60 * 60 * 1000;
                    const newEta = new Date(dragState.originalEta.getTime() + shiftMs);
                    const newEtd = new Date(dragState.originalEtd.getTime() + shiftMs);
                    const { left, width } = getBarPosition(newEta, newEtd);
                    const original = schedules.find(s => s.scheduleId === dragState.scheduleId);
                    if (!original) return null;
                    const colors = STATUS_COLORS[original.status] || STATUS_COLORS.Scheduled;

                    return (
                      <div
                        className="absolute top-1 rounded-md flex items-center gap-1 px-2 overflow-hidden shadow-2xl"
                        style={{
                          left, width,
                          height: ROW_HEIGHT - 8,
                          backgroundColor: colors.bg,
                          border: `2px dashed ${colors.border}`,
                          opacity: 0.85,
                          zIndex: 30,
                        }}
                      >
                        <Ship className="w-3 h-3 flex-shrink-0" style={{ color: colors.text }} />
                        <span className="text-[10px] font-semibold truncate" style={{ color: colors.text }}>
                          {original.vesselName}
                        </span>
                      </div>
                    );
                  })()}
                </div>
              ))}

              {/* Current time indicator */}
              {nowOffset >= 0 && nowOffset <= totalWidth && (
                <div className="absolute top-0 bottom-0" style={{ left: nowOffset, zIndex: 25 }}>
                  <div className="w-0.5 h-full" style={{ backgroundColor: '#DC2626' }} />
                  <div className="absolute -top-1 -left-1.5 w-3 h-3 rounded-full" style={{ backgroundColor: '#DC2626' }} />
                  <div className="absolute top-3 -left-8 text-[9px] font-bold px-1 rounded" style={{ backgroundColor: '#DC2626', color: 'white' }}>
                    {now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Tooltip */}
      {hoveredVessel && (() => {
        const s = schedules.find(sc => sc.scheduleId === hoveredVessel);
        if (!s) return null;
        const colors = STATUS_COLORS[s.status] || STATUS_COLORS.Scheduled;
        return (
          <div className="fixed z-[100] pointer-events-none" style={{ left: tooltipPos.x + 12, top: tooltipPos.y - 10 }}>
            <div className="rounded-lg shadow-xl overflow-hidden" style={{ border: '1px solid var(--border)', backgroundColor: 'white', minWidth: 200 }}>
              <div className="px-3 py-1.5 flex items-center gap-2" style={{ backgroundColor: colors.bg }}>
                <Ship className="w-3 h-3" style={{ color: colors.text }} />
                <span className="text-[11px] font-bold" style={{ color: colors.text }}>{s.vesselName}</span>
              </div>
              <div className="px-3 py-2 space-y-1">
                <div className="flex justify-between text-[10px]">
                  <span style={{ color: 'var(--muted-foreground)' }}>Berth</span>
                  <span style={{ fontWeight: 600, color: 'var(--foreground)' }}>{s.berthName}</span>
                </div>
                <div className="flex justify-between text-[10px]">
                  <span style={{ color: 'var(--muted-foreground)' }}>ETA</span>
                  <span style={{ fontWeight: 600, color: 'var(--foreground)' }}>{s.eta.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</span>
                </div>
                <div className="flex justify-between text-[10px]">
                  <span style={{ color: 'var(--muted-foreground)' }}>ETD</span>
                  <span style={{ fontWeight: 600, color: 'var(--foreground)' }}>{s.etd.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</span>
                </div>
                <div className="flex justify-between text-[10px]">
                  <span style={{ color: 'var(--muted-foreground)' }}>Status</span>
                  <span className="px-1.5 py-0.5 rounded text-[9px] font-bold" style={{ backgroundColor: colors.bg, color: colors.text }}>{s.status}</span>
                </div>
                {s.vesselType && (
                  <div className="flex justify-between text-[10px]">
                    <span style={{ color: 'var(--muted-foreground)' }}>Type</span>
                    <span style={{ fontWeight: 500, color: 'var(--foreground)' }}>{s.vesselType}</span>
                  </div>
                )}
                {s.loa && (
                  <div className="flex justify-between text-[10px]">
                    <span style={{ color: 'var(--muted-foreground)' }}>LOA</span>
                    <span style={{ fontWeight: 500, color: 'var(--foreground)' }}>{s.loa}m</span>
                  </div>
                )}
                <div className="flex justify-between text-[10px]">
                  <span style={{ color: 'var(--muted-foreground)' }}>Duration</span>
                  <span style={{ fontWeight: 500, color: 'var(--foreground)' }}>
                    {Math.round((s.etd.getTime() - s.eta.getTime()) / (1000 * 60 * 60))}h
                  </span>
                </div>
              </div>
              {s.status !== 'Departed' && s.status !== 'Berthed' && (
                <div className="px-3 py-1.5 text-[9px] flex items-center gap-1" style={{ backgroundColor: '#FFFBEB', borderTop: '1px solid var(--border)', color: '#92400E' }}>
                  <GripHorizontal className="w-3 h-3" /> Drag to reschedule
                </div>
              )}
            </div>
          </div>
        );
      })()}
    </div>
  );
}
