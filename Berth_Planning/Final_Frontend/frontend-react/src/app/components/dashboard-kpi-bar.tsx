import { useMemo } from 'react';
import { Anchor, Ship, Clock, TrendingUp, ArrowDownRight, ArrowUpRight, Wrench, Activity, Brain, Zap } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { aiService } from '../../api';
import type { DashboardMetrics } from '../../types';

interface Vessel {
  id: string;
  status: string;
  ata?: Date;
}

interface Berth {
  id: string;
  status: string;
}

interface DashboardKPIBarProps {
  metrics: DashboardMetrics | undefined;
  vessels: Vessel[];
  berths: Berth[];
  lastRefreshTime: Date;
  isRefreshing: boolean;
}

export function DashboardKPIBar({ metrics, vessels, berths, lastRefreshTime, isRefreshing }: DashboardKPIBarProps) {
  // AI Dashboard Overview query
  const { data: aiDashboard, isLoading: aiLoading } = useQuery({
    queryKey: ['ai-dashboard-overview'],
    queryFn: aiService.getDashboard,
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // Refetch every minute
  });

  const kpis = useMemo(() => {
    const totalBerths = metrics?.totalBerths ?? berths.length;
    const occupiedBerths = metrics?.occupiedBerths ?? berths.filter(b => b.status === 'occupied').length;
    const availableBerths = metrics?.availableBerths ?? (totalBerths - occupiedBerths);
    const maintenanceBerths = berths.filter(b => b.status === 'maintenance').length;
    const utilization = metrics?.berthUtilization ?? (totalBerths > 0 ? Math.round((occupiedBerths / totalBerths) * 100) : 0);
    const arrivingVessels = metrics?.vesselsApproaching ?? vessels.filter(v => v.status === 'on-time' || v.status === 'early' || v.status === 'delayed').length;
    const berthed = metrics?.vesselsBerthed ?? vessels.filter(v => v.ata).length;
    const inQueue = metrics?.vesselsInQueue ?? 0;
    const departingVessels = metrics?.todayDepartures ?? vessels.filter(v => v.status === 'departing').length;
    const avgWait = metrics?.averageWaitingTime ?? 0;

    return { totalBerths, occupiedBerths, availableBerths, maintenanceBerths, utilization, arrivingVessels, berthed, inQueue, departingVessels, avgWait };
  }, [metrics, vessels, berths]);

  const getUtilColor = (pct: number) => {
    if (pct >= 85) return '#DC2626';
    if (pct >= 65) return '#F59E0B';
    return '#059669';
  };

  const timeSinceRefresh = useMemo(() => {
    const sec = Math.floor((Date.now() - lastRefreshTime.getTime()) / 1000);
    if (sec < 10) return 'Just now';
    if (sec < 60) return `${sec}s ago`;
    return `${Math.floor(sec / 60)}m ago`;
  }, [lastRefreshTime]);

  return (
    <div className="flex items-center gap-2 px-4 py-2 border-b overflow-x-auto" style={{ backgroundColor: 'var(--kale-sky)', borderColor: 'var(--border)' }}>
      {/* Berth Utilization - primary KPI */}
      <div className="flex items-center gap-2 pr-3" style={{ borderRight: '1px solid var(--border)' }}>
        <div className="relative w-10 h-10">
          <svg viewBox="0 0 36 36" className="w-10 h-10 -rotate-90">
            <circle cx="18" cy="18" r="14" fill="none" stroke="var(--border)" strokeWidth="3" />
            <circle cx="18" cy="18" r="14" fill="none" stroke={getUtilColor(kpis.utilization)} strokeWidth="3"
              strokeDasharray={`${kpis.utilization * 0.88} 88`} strokeLinecap="round" />
          </svg>
          <span className="absolute inset-0 flex items-center justify-center text-[9px] font-bold" style={{ color: getUtilColor(kpis.utilization) }}>
            {kpis.utilization}%
          </span>
        </div>
        <div>
          <div className="text-[9px] font-semibold uppercase" style={{ color: 'var(--muted-foreground)', letterSpacing: 0.5 }}>Berth Util.</div>
          <div className="text-[10px]" style={{ color: 'var(--foreground)' }}>
            <b>{kpis.occupiedBerths}</b> Occupied <span style={{ color: 'var(--muted-foreground)' }}>of {kpis.totalBerths}</span>
          </div>
        </div>
      </div>

      {/* Available Berths */}
      <KPIChip
        icon={<Anchor className="w-3 h-3" />}
        label="Available"
        value={String(kpis.availableBerths)}
        color="var(--status-on-time)"
      />

      {/* Berthed Vessels */}
      <KPIChip
        icon={<Anchor className="w-3 h-3" />}
        label="Berthed"
        value={String(kpis.berthed)}
        color="var(--kale-teal)"
      />

      {/* In Queue */}
      <KPIChip
        icon={<Clock className="w-3 h-3" />}
        label="In Queue"
        value={String(kpis.inQueue)}
        color="var(--status-at-risk)"
      />

      {/* Maintenance */}
      <KPIChip
        icon={<Wrench className="w-3 h-3" />}
        label="Maintenance"
        value={String(kpis.maintenanceBerths)}
        color="var(--muted-foreground)"
      />

      {/* Separator */}
      <div className="w-px h-6 mx-1" style={{ backgroundColor: 'var(--border)' }} />

      {/* Arriving Vessels */}
      <KPIChip
        icon={<ArrowDownRight className="w-3 h-3" />}
        label="Arriving Vessels"
        value={String(kpis.arrivingVessels)}
        color="#059669"
      />

      {/* Departing Vessels */}
      <KPIChip
        icon={<ArrowUpRight className="w-3 h-3" />}
        label="Departing Vessels"
        value={String(kpis.departingVessels)}
        color="#2563EB"
      />

      {/* Avg Wait Time */}
      <div className="flex items-center gap-1 px-2 py-1 rounded-md" style={{ backgroundColor: 'rgba(245,158,11,0.08)' }}>
        <TrendingUp className="w-3 h-3" style={{ color: '#D97706' }} />
        <span className="text-[10px]" style={{ color: 'var(--muted-foreground)' }}>Avg Wait</span>
        <span className="text-xs font-bold" style={{ color: '#D97706' }}>
          {kpis.avgWait > 0 ? `${Math.round(kpis.avgWait)}m` : '--'}
        </span>
      </div>

      {/* Spacer */}
      <div className="flex-1" />

      {/* AI Service Status */}
      <div className="flex items-center gap-2 px-2 py-1 rounded-md" style={{ 
        backgroundColor: aiDashboard?.aiServiceStatus === 'active' ? 'rgba(16,185,129,0.08)' : 'rgba(220,38,38,0.08)' 
      }}>
        <div className="flex items-center gap-1">
          <Brain className={`w-3.5 h-3.5 ${aiLoading ? 'animate-pulse' : ''}`} 
            style={{ color: aiDashboard?.aiServiceStatus === 'active' ? '#10B981' : '#DC2626' }} />
          <span className="text-[9px] font-semibold" style={{ 
            color: aiDashboard?.aiServiceStatus === 'active' ? '#10B981' : '#DC2626' 
          }}>
            {aiLoading ? 'AI...' : aiDashboard?.aiServiceStatus === 'active' ? 'AI Active' : 'AI Offline'}
          </span>
        </div>
        {aiDashboard && aiDashboard.aiServiceStatus === 'active' && (
          <div className="flex items-center gap-1.5 pl-2 border-l" style={{ borderColor: 'var(--border)' }}>
            {aiDashboard.activeConflicts > 0 && (
              <span className="px-1.5 py-0.5 rounded text-[9px] font-bold" style={{ 
                backgroundColor: 'rgba(220,38,38,0.15)', 
                color: '#DC2626' 
              }}>
                {aiDashboard.activeConflicts} conflicts
              </span>
            )}
            <span className="text-[9px]" style={{ color: 'var(--muted-foreground)' }}>
              <Zap className="w-2.5 h-2.5 inline" style={{ color: 'var(--kale-teal)' }} /> {aiDashboard.etaPredictions} predictions
            </span>
          </div>
        )}
      </div>

      {/* Auto-refresh indicator */}
      <div className="flex items-center gap-1.5 px-2 py-1 rounded-md" style={{ backgroundColor: 'rgba(10,77,140,0.06)' }}>
        <Activity className={`w-3 h-3 ${isRefreshing ? 'animate-pulse' : ''}`} style={{ color: isRefreshing ? 'var(--status-on-time)' : 'var(--muted-foreground)' }} />
        <span className="text-[9px]" style={{ color: 'var(--muted-foreground)' }}>
          {isRefreshing ? 'Refreshing...' : timeSinceRefresh}
        </span>
      </div>
    </div>
  );
}

function KPIChip({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: string; color: string }) {
  return (
    <div className="flex items-center gap-1.5 px-2 py-1 rounded-md min-w-fit" style={{ backgroundColor: `${color}08` }}>
      <span style={{ color }}>{icon}</span>
      <span className="text-[10px]" style={{ color: 'var(--muted-foreground)' }}>{label}</span>
      <span className="text-xs font-bold" style={{ color }}>{value}</span>
    </div>
  );
}
