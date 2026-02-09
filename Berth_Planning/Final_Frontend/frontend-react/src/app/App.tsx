import { useState, useEffect, useMemo, useRef, lazy, Suspense } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Routes, Route, useNavigate, useLocation, Navigate } from 'react-router-dom';
import { SmartBerthLogo } from './components/smart-berth-logo';
import { BerthVisualization3D } from './components/berth-visualization-3d';
import { UpcomingVesselsTimeline, Vessel } from './components/upcoming-vessels-timeline';
import { Terminal3DView } from './components/terminal-3d-view';
import { VesselDetailsPanel } from './components/vessel-details-panel';
import { AcceptRecommendationModal } from './components/accept-recommendation-modal';
import { ModifyAllocationModal } from './components/modify-allocation-modal';
import { VesselHistoryModal } from './components/vessel-history-modal';
import { PortOnboardingWizard, OnboardingData } from './components/onboarding/port-onboarding-wizard';
import { TerminalProfile } from './components/terminal-profile';
import { NotificationsPanel } from './components/notifications-panel';
import { ActivityFeedPanel } from './components/activity-feed-panel';
import { BerthDetailDialog } from './components/berth-detail-dialog';
import { Chatbot } from './components/chatbot';
import { BrowserAgentPanel } from './components/browser-agent-panel';
import { DashboardKPIBar } from './components/dashboard-kpi-bar';
import { GanttChart } from './components/gantt-chart';
import { ToastProvider, useToast } from './components/toast-container';
import { RoleSelection, RoleConfig } from './components/role-selection';
import { RefreshCw, Bell, LayoutGrid, Ship, Building2, Box, BarChart3, ChevronDown, LogOut, Globe, Activity } from 'lucide-react';

// Lazy load WorldVesselMap (heavy 3D component - only loads when World Map tab is clicked)
const WorldVesselMap = lazy(() => import('./components/world-vessel-map').then(m => ({ default: m.WorldVesselMap })));
import {
  vesselService,
  berthService,
  scheduleService,
  dashboardService,
  predictionService,
  suggestionService,
  aiService,
  createSchedule,
  portService,
  terminalService,
  resourceService,
} from '../api';
import type {
  Vessel as APIVessel,
  Berth as APIBerth,
  Schedule as APISchedule,
  BerthStatus,
  ETAPrediction,
  SuggestionResponse,
  BerthSuggestion,
  AIBerthSuggestion,
  Port as APIPort,
  Terminal as APITerminal,
  Resource as APIResource,
} from '../types';

interface UIBerth {
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
  schedule: any[];
  upcomingVessels?: Array<{
    name: string;
    eta: Date;
    etd: Date;
    loa: number;
    confidence: number;
    reason: string;
  }>;
}

// Transform API vessel + schedule + prediction data into UI Vessel format
function transformVesselToUI(
  apiVessel: APIVessel,
  schedule?: APISchedule,
  prediction?: ETAPrediction,
  suggestion?: any
): Vessel {
  const eta = schedule?.eta ? new Date(schedule.eta) : new Date();
  const etd = schedule?.etd ? new Date(schedule.etd) : new Date(eta.getTime() + 8 * 60 * 60 * 1000);
  const predictedETA = prediction?.predictedETA
    ? new Date(prediction.predictedETA)
    : schedule?.predictedETA
      ? new Date(schedule.predictedETA)
      : eta;
  const deviationMinutes = prediction?.deviationMinutes ?? 0;

  let status: Vessel['status'] = 'on-time';
  if (schedule?.ata) {
    status = 'arrived';
  } else if (schedule?.status === 'Delayed' || Math.abs(deviationMinutes) > 60) {
    status = 'delayed';
  } else if (Math.abs(deviationMinutes) > 15) {
    status = deviationMinutes > 0 ? 'at-risk' : 'early';
  }

  let readiness: Vessel['readiness'] = 'ready';
  if (apiVessel.status === 'Pending') readiness = 'pending';
  else if (apiVessel.status === 'Incomplete') readiness = 'incomplete';

  return {
    id: String(apiVessel.vesselId),
    name: apiVessel.vesselName,
    imo: apiVessel.imo || '',
    callSign: apiVessel.mmsi || '',
    flag: apiVessel.flagStateName || apiVessel.flagState || apiVessel.flag || '',
    vesselType: apiVessel.vesselType || 'Container Ship',
    loa: apiVessel.loa,
    beam: apiVessel.beam,
    draft: apiVessel.draft,
    declaredETA: eta,
    predictedETA: predictedETA,
    etaDeviation: deviationMinutes,
    ata: schedule?.ata ? new Date(schedule.ata) : undefined,
    status,
    readiness,
    cargoType: schedule?.cargoType || apiVessel.cargoType || 'General Cargo',
    cargoQuantity: schedule?.cargoQuantity ?? schedule?.cargoVolume ?? apiVessel.cargoVolume ?? 0,
    cargoUnit: schedule?.cargoUnit || apiVessel.cargoUnit || 'TEU',
    constraints: [],
    aiRecommendation: suggestion
      ? {
          suggestedBerth: suggestion.berthName || `Berth ${suggestion.berthId}`,
          confidence: suggestion.score ?? 0,
          reason: suggestion.reasoning?.join('. ') || 'AI-optimized berth assignment',
        }
      : undefined,
  };
}

// Transform API berth + schedule data into UI Berth format
function transformBerthToUI(
  apiBerth: APIBerth,
  berthStatus?: BerthStatus,
  schedules?: APISchedule[],
  allVessels?: APIVessel[]
): UIBerth {
  const now = new Date();
  const berthSchedules = schedules?.filter(s => s.berthId === apiBerth.berthId) || [];
  const activeSchedule = berthSchedules.find(
    s => s.status === 'Berthed' || s.status === 'Active' || s.status === 'InProgress'
  );
  const upcomingSchedules = berthSchedules.filter(s => {
    const eta = new Date(s.eta);
    return eta > now && s.status !== 'Cancelled' && s.status !== 'Completed';
  });
  // Check if berth has ANY active/scheduled vessel (not cancelled/completed)
  const hasScheduledVessel = berthSchedules.some(
    s => s.status !== 'Cancelled' && s.status !== 'Completed' && s.status !== 'Departed'
  );

  let berthStatusVal: UIBerth['status'] = 'available';
  const statusLower = (berthStatus?.status || apiBerth.status || '').toLowerCase();
  if (statusLower.includes('occupied') || statusLower.includes('active') || activeSchedule || hasScheduledVessel) {
    berthStatusVal = 'occupied';
  } else if (statusLower.includes('maintenance')) {
    berthStatusVal = 'maintenance';
  }

  // Generate crane info from numberOfCranes
  const cranes: UIBerth['cranes'] = [];
  const craneCount = apiBerth.numberOfCranes || 0;
  for (let i = 0; i < craneCount; i++) {
    const type = i < Math.ceil(craneCount / 2) ? 'STS' : (i % 2 === 0 ? 'RTG' : 'MHC');
    cranes.push({
      id: `${type}-${apiBerth.berthId}-${i + 1}`,
      type: type as 'STS' | 'RTG' | 'MHC',
      capacity: type === 'STS' ? 65 : type === 'MHC' ? 100 : 40,
      status: berthStatusVal === 'maintenance' ? 'maintenance' : 'operational',
    });
  }

  // Build currentVessel from active schedule OR next scheduled vessel
  let currentVessel: UIBerth['currentVessel'] | undefined;
  // First try active (berthed) schedule
  const scheduleForCurrentVessel = activeSchedule || berthSchedules.find(
    s => s.status !== 'Cancelled' && s.status !== 'Completed' && s.status !== 'Departed'
  );
  if (scheduleForCurrentVessel) {
    const vesselData = allVessels?.find(v => v.vesselId === scheduleForCurrentVessel.vesselId);
    currentVessel = {
      name: scheduleForCurrentVessel.vesselName || vesselData?.vesselName || 'Unknown',
      eta: new Date(scheduleForCurrentVessel.eta),
      etd: new Date(scheduleForCurrentVessel.etd),
      atb: scheduleForCurrentVessel.atb ? new Date(scheduleForCurrentVessel.atb) : undefined,
      loa: vesselData?.loa || 300,
      vesselId: String(scheduleForCurrentVessel.vesselId),
      cargoType: scheduleForCurrentVessel.cargoType || vesselData?.cargoType,
      cargoQuantity: scheduleForCurrentVessel.cargoQuantity ?? scheduleForCurrentVessel.cargoVolume ?? vesselData?.cargoVolume ?? 0,
      cargoUnit: scheduleForCurrentVessel.cargoUnit || vesselData?.cargoUnit || 'TEU',
    };
  } else if (berthStatus?.currentVessel) {
    currentVessel = {
      name: berthStatus.currentVessel,
      eta: new Date(),
      etd: berthStatus.vesselETD ? new Date(berthStatus.vesselETD) : new Date(now.getTime() + 4 * 60 * 60 * 1000),
      loa: 300,
    };
  }

  // Build upcomingVessels from upcoming schedules
  const upcomingVessels = upcomingSchedules.slice(0, 3).map(s => {
    const vesselData = allVessels?.find(v => v.vesselId === s.vesselId);
    return {
      name: s.vesselName || vesselData?.vesselName || 'Unknown',
      eta: new Date(s.eta),
      etd: new Date(s.etd),
      loa: vesselData?.loa || 300,
      confidence: 85 + Math.floor(Math.random() * 10),
      reason: `Scheduled berth assignment based on vessel compatibility and berth availability.`,
    };
  });

  return {
    id: String(apiBerth.berthId),
    name: apiBerth.berthName || apiBerth.berthCode,
    length: apiBerth.length || 300,
    maxDraft: apiBerth.maxDraft || 13,
    maxLOA: apiBerth.maxLOA || 310,
    maxBeam: 48,
    status: berthStatusVal,
    cranes,
    reeferPoints: 80,
    currentVessel,
    schedule: berthSchedules.map(s => ({
      vesselId: String(s.vesselId),
      vesselName: s.vesselName || 'Unknown',
      startTime: new Date(s.eta),
      endTime: new Date(s.etd),
      status: s.status === 'Berthed' ? 'berthed' : 'scheduled',
    })),
    upcomingVessels: upcomingVessels.length > 0 ? upcomingVessels : undefined,
  };
}

export default function App() {
  return (
    <ToastProvider>
      <AppInner />
    </ToastProvider>
  );
}

function AppInner() {
  const { addToast } = useToast();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const location = useLocation();
  const [onboardingData, setOnboardingData] = useState<OnboardingData | null>(null);

  // Role-based access
  const [roleConfig, setRoleConfig] = useState<RoleConfig | null>(() => {
    try { const stored = localStorage.getItem('smartberth_role'); return stored ? JSON.parse(stored) : null; } catch { return null; }
  });
  const [activeTerminalId, setActiveTerminalId] = useState<string | null>(() => {
    try { const stored = localStorage.getItem('smartberth_active_terminal'); return stored || null; } catch { return null; }
  });
  const [showTerminalDropdown, setShowTerminalDropdown] = useState(false);

  const handleRoleSelect = (config: RoleConfig) => {
    setRoleConfig(config);
    localStorage.setItem('smartberth_role', JSON.stringify(config));
    if (config.role === 'terminal_operator' && config.assignedTerminalId) {
      setActiveTerminalId(config.assignedTerminalId);
      localStorage.setItem('smartberth_active_terminal', config.assignedTerminalId);
    }
    // Port operator: activeTerminalId will be auto-set by useEffect once terminals load
  };

  const handleSwitchRole = () => {
    setRoleConfig(null);
    setActiveTerminalId(null);
    localStorage.removeItem('smartberth_role');
    localStorage.removeItem('smartberth_active_terminal');
  };

  const handleTerminalSwitch = (terminalId: string | null) => {
    setActiveTerminalId(terminalId);
    if (terminalId) localStorage.setItem('smartberth_active_terminal', terminalId);
    else localStorage.removeItem('smartberth_active_terminal');
    setShowTerminalDropdown(false);
  };

  const [selectedVesselId, setSelectedVesselId] = useState<string | undefined>();
  const [selectedBerthId, setSelectedBerthId] = useState<string | undefined>();
  const [timeWindow, setTimeWindow] = useState<'7days' | 'year'>('7days');
  const [currentTime, setCurrentTime] = useState(new Date());
  const [viewMode, setViewMode] = useState<'berths' | 'vessels' | 'terminal3d' | 'gantt' | 'worldmap'>('vessels');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastRefreshTime, setLastRefreshTime] = useState(new Date());
  const [showNotifications, setShowNotifications] = useState(false);
  const [showActivityFeed, setShowActivityFeed] = useState(false);
  const [notificationCount, setNotificationCount] = useState(0);
  const prevAlertCountRef = useRef(0);
  const [showTerminalProfile, setShowTerminalProfile] = useState(false);
  const [showBerthDetail, setShowBerthDetail] = useState(false);
  const [selectedBerth, setSelectedBerth] = useState<UIBerth | null>(null);

  // Modal states
  const [showAcceptModal, setShowAcceptModal] = useState(false);
  const [showModifyModal, setShowModifyModal] = useState(false);
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [vesselForAction, setVesselForAction] = useState<Vessel | null>(null);

  // API Queries
  const { data: apiVessels = [], isLoading: loadingVessels } = useQuery({
    queryKey: ['vessels'],
    queryFn: vesselService.getAll,
    refetchInterval: 30000,
  });

  const activeTerminalIdNum = activeTerminalId ? parseInt(activeTerminalId) : undefined;

  const { data: apiBerths = [], isLoading: loadingBerths } = useQuery({
    queryKey: ['berths', activeTerminalIdNum],
    queryFn: () => berthService.getAll(activeTerminalIdNum),
  });

  const { data: apiSchedules = [] } = useQuery({
    queryKey: ['schedules-active', activeTerminalIdNum],
    queryFn: () => scheduleService.getActive(activeTerminalIdNum),
    refetchInterval: 30000,
  });

  const { data: berthStatuses = [] } = useQuery({
    queryKey: ['berth-status', activeTerminalIdNum],
    queryFn: () => dashboardService.getBerthStatus(activeTerminalIdNum),
    refetchInterval: 30000,
  });

  const { data: dashboardMetrics } = useQuery({
    queryKey: ['dashboard-metrics', activeTerminalIdNum],
    queryFn: () => dashboardService.getMetrics(activeTerminalIdNum),
    refetchInterval: 30000,
  });

  const { data: etaPredictions = [] } = useQuery({
    queryKey: ['eta-predictions'],
    queryFn: predictionService.getAllActiveETA,
    refetchInterval: 60000,
  });

  // Fetch AI berth suggestions for unassigned vessels
  const { data: suggestionsMap = new Map<number, BerthSuggestion>() } = useQuery({
    queryKey: ['suggestions', apiVessels.length, apiSchedules.length],
    queryFn: async () => {
      const assignedVesselIds = new Set(
        apiSchedules
          .filter((s: APISchedule) => s.status === 'Berthed' || s.status === 'Active' || s.status === 'InProgress')
          .map((s: APISchedule) => s.vesselId)
      );
      const unassigned = apiVessels.filter(
        (v: APIVessel) => !assignedVesselIds.has(v.vesselId) && v.status !== 'Departed'
      );
      const map = new Map<number, BerthSuggestion>();
      const results = await Promise.allSettled(
        unassigned.slice(0, 15).map((v: APIVessel) =>
          aiService.getBerthSuggestions(v.vesselId).then((aiSuggestions: any[]) => ({
            vesselId: v.vesselId,
            // Map from Python snake_case response fields
            suggestions: aiSuggestions.map((s: any, idx: number) => ({
              berthId: s.berth_id || s.berthId,
              berthName: s.berth_name || s.berthName,
              terminalName: s.terminal_name || s.terminalName || '',
              score: s.total_score || s.score || 0,
              rank: idx + 1,
              explanation: s.explanation || (Array.isArray(s.reasoning) ? s.reasoning.join('. ') : 'AI-generated recommendation'),
              eta: s.proposed_eta || s.proposedEta,
              etd: s.proposed_etd || s.proposedEtd,
              waitTime: s.estimated_wait_minutes || s.estimatedWaitMinutes,
            }))
          }))
        )
      );
      results.forEach((result) => {
        if (result.status === 'fulfilled' && result.value?.suggestions?.length > 0) {
          const resp = result.value;
          map.set(resp.vesselId, resp.suggestions[0]); // top-ranked suggestion
        }
      });
      return map;
    },
    enabled: apiVessels.length > 0,
    refetchInterval: 60000,
    staleTime: 30000,
  });

  const { data: apiPorts = [] } = useQuery({
    queryKey: ['ports'],
    queryFn: portService.getAll,
  });

  const { data: apiTerminals = [] } = useQuery({
    queryKey: ['terminals'],
    queryFn: terminalService.getAll,
  });

  const { data: apiResources = [] } = useQuery({
    queryKey: ['resources'],
    queryFn: resourceService.getAll,
  });

  // Auto-select first terminal for Port Operator (must always have one terminal selected)
  useEffect(() => {
    if (roleConfig?.role === 'port_operator' && !activeTerminalId && apiTerminals.length > 0) {
      const firstId = String(apiTerminals[0].terminalId);
      setActiveTerminalId(firstId);
      localStorage.setItem('smartberth_active_terminal', firstId);
    }
  }, [roleConfig, activeTerminalId, apiTerminals]);

  // Poll alerts for real-time notification badge & toasts
  const { data: alertsData } = useQuery({
    queryKey: ['alerts'],
    queryFn: dashboardService.getAlerts,
    refetchInterval: 15000,
  });

  // Fire toasts for new alerts
  useEffect(() => {
    if (!alertsData) return;
    const alerts = Array.isArray(alertsData) ? alertsData : [];
    const newCount = alerts.length;
    if (prevAlertCountRef.current > 0 && newCount > prevAlertCountRef.current) {
      const diff = alerts.slice(0, newCount - prevAlertCountRef.current);
      diff.forEach((alert: any) => {
        const type = alert.alertType?.includes('Departed') ? 'vessel-departure'
          : alert.alertType?.includes('Berthed') ? 'vessel-arrival'
          : alert.alertType?.includes('Approaching') ? 'info'
          : alert.alertType?.includes('Schedule') ? 'berth-update'
          : 'info';
        addToast({
          type: type as any,
          title: alert.alertType?.replace(/([A-Z])/g, ' $1').trim() || 'Update',
          message: alert.message || 'System update',
          duration: 6000,
        });
      });
    }
    prevAlertCountRef.current = newCount;
    setNotificationCount(Math.min(newCount, 99));
  }, [alertsData, addToast]);

  // Track last refresh time
  useEffect(() => {
    setLastRefreshTime(new Date());
  }, [apiVessels, apiSchedules, berthStatuses]);

  // Track overstaying vessels and approaching ETD - fire alerts
  const overstayAlertsRef = useRef<Set<number>>(new Set());
  const approachingETDAlertsRef = useRef<Set<number>>(new Set());

  useEffect(() => {
    if (apiSchedules.length === 0) return;
    const now = new Date();
    const berthedSchedules = apiSchedules.filter((s: APISchedule) => s.status === 'Berthed');

    berthedSchedules.forEach((schedule: APISchedule) => {
      const etd = new Date(schedule.etd);
      const timeToETD = etd.getTime() - now.getTime();
      const twoHoursMs = 2 * 60 * 60 * 1000;

      // Overstaying alert (past ETD)
      if (timeToETD < 0 && !overstayAlertsRef.current.has(schedule.scheduleId)) {
        overstayAlertsRef.current.add(schedule.scheduleId);
        const overdueMins = Math.floor(Math.abs(timeToETD) / (1000 * 60));
        const overdueText = overdueMins >= 60 ? `${Math.floor(overdueMins / 60)}h ${overdueMins % 60}m` : `${overdueMins}m`;
        addToast({
          type: 'warning',
          title: 'Vessel Overstaying',
          message: `${schedule.vesselName} is ${overdueText} beyond scheduled ETD at ${schedule.berthName}`,
          duration: 10000,
        });
      }

      // Approaching ETD alert (< 2 hours)
      if (timeToETD > 0 && timeToETD < twoHoursMs && !approachingETDAlertsRef.current.has(schedule.scheduleId)) {
        approachingETDAlertsRef.current.add(schedule.scheduleId);
        const remainingMins = Math.floor(timeToETD / (1000 * 60));
        const remainingText = remainingMins >= 60 ? `${Math.floor(remainingMins / 60)}h ${remainingMins % 60}m` : `${remainingMins}m`;
        addToast({
          type: 'info',
          title: 'Departure Approaching',
          message: `${schedule.vesselName} scheduled to depart in ${remainingText} from ${schedule.berthName}`,
          duration: 8000,
        });
      }
    });

    // Clean up departed vessels from tracking sets
    const activeScheduleIds = new Set(berthedSchedules.map((s: APISchedule) => s.scheduleId));
    overstayAlertsRef.current.forEach(id => {
      if (!activeScheduleIds.has(id)) overstayAlertsRef.current.delete(id);
    });
    approachingETDAlertsRef.current.forEach(id => {
      if (!activeScheduleIds.has(id)) approachingETDAlertsRef.current.delete(id);
    });
  }, [apiSchedules, addToast]);

  // Transform API data to UI format
  // Only show vessels that have schedules in the selected terminal
  const uiVessels = useMemo<Vessel[]>(() => {
    if (apiVessels.length === 0) return [];

    // Get vessel IDs from schedules (already filtered by terminal via apiSchedules query)
    const scheduledVesselIds = new Set(apiSchedules.map((s: APISchedule) => s.vesselId));

    // Only include vessels that have schedules in this terminal
    return apiVessels
      .filter((v: APIVessel) => scheduledVesselIds.has(v.vesselId))
      .map((v: APIVessel) => {
        const schedule = apiSchedules.find((s: APISchedule) => s.vesselId === v.vesselId);
        const prediction = etaPredictions.find((p: ETAPrediction) => p.vesselId === v.vesselId);
        const suggestion = suggestionsMap.get(v.vesselId);
        return transformVesselToUI(v, schedule, prediction, suggestion);
      });
  }, [apiVessels, apiSchedules, etaPredictions, suggestionsMap]);

  const uiBerths = useMemo<UIBerth[]>(() => {
    if (apiBerths.length === 0) return [];
    return apiBerths.map((b: APIBerth) => {
      const status = berthStatuses.find((bs: BerthStatus) => bs.berthId === b.berthId);
      return transformBerthToUI(b, status, apiSchedules, apiVessels);
    });
  }, [apiBerths, berthStatuses, apiSchedules, apiVessels]);

  // Active terminal info for display
  const activeTerminalInfo = useMemo(() => {
    if (!activeTerminalId) return null;
    return apiTerminals.find((t: APITerminal) => String(t.terminalId) === activeTerminalId);
  }, [activeTerminalId, apiTerminals]);

  // Gantt chart data
  const ganttSchedules = useMemo(() => {
    return apiSchedules.map((s: APISchedule) => {
      const vessel = apiVessels.find((v: APIVessel) => v.vesselId === s.vesselId);
      return {
        scheduleId: String(s.scheduleId),
        vesselId: String(s.vesselId),
        vesselName: s.vesselName || vessel?.vesselName || 'Unknown',
        berthId: String(s.berthId),
        berthName: s.berthName || `Berth ${s.berthId}`,
        eta: new Date(s.eta),
        etd: new Date(s.etd),
        status: s.status,
        vesselType: vessel?.vesselType,
        loa: vessel?.loa,
      };
    });
  }, [apiSchedules, apiVessels]);

  const ganttBerths = useMemo(() => {
    return uiBerths.map(b => ({
      id: b.id,
      name: b.name,
      length: b.length,
      status: b.status,
    }));
  }, [uiBerths]);

  // Build terminal profile data from API (works without onboarding)
  const terminalProfileData = useMemo<OnboardingData | null>(() => {
    if (onboardingData) return onboardingData;
    if (apiPorts.length === 0 && apiBerths.length === 0) return null;

    const port = apiPorts[0];
    return {
      port: port ? {
        portName: port.portName,
        portCode: port.portCode,
        unlocode: port.portCode,
        country: port.country,
        timezone: port.timeZone || 'UTC',
        coordinates: { latitude: port.latitude || 0, longitude: port.longitude || 0 },
        contactEmail: '',
        contactPhone: '',
      } : {
        portName: 'Default Port',
        portCode: 'DEF',
        unlocode: 'DEF',
        country: 'India',
        timezone: 'UTC',
        coordinates: { latitude: 0, longitude: 0 },
        contactEmail: '',
        contactPhone: '',
      },
      integration: {
        systemType: 'port_community_system',
        dataSync: { vesselCalls: true, falForms: false, cargoManifest: true, crewLists: false },
        syncFrequency: 'realtime',
      },
      terminals: apiTerminals.map((t: APITerminal) => ({
        id: String(t.terminalId),
        name: t.terminalName,
        code: t.terminalCode,
        terminalType: (t.terminalType?.toLowerCase() || 'multi-purpose') as 'container' | 'bulk' | 'ro-ro' | 'multi-purpose',
        operatingCompany: 'Port Authority',
        operationalHours: t.operatingHours || '24/7',
      })),
      berths: apiBerths.map((b: APIBerth) => ({
        id: String(b.berthId),
        terminalId: String(b.terminalId),
        name: b.berthName || b.berthCode,
        length: b.length || 300,
        maxDraft: b.maxDraft || 13,
        maxLOA: b.maxLOA || 310,
        maxBeam: 48,
        maxDWT: 100000,
        bollards: 20,
        fenders: 10,
        reeferPoints: 80,
        freshWater: true,
        bunkering: false,
      })),
      equipment: apiResources.map((r: APIResource) => ({
        id: String(r.resourceId),
        terminalId: apiTerminals.length > 0 ? String(apiTerminals[0].terminalId) : '1',
        type: (r.resourceType || 'STS') as 'STS' | 'RTG' | 'MHC' | 'RMG' | 'Reach Stacker',
        name: r.resourceName,
        capacity: r.capacity || 0,
        status: (r.isAvailable ? 'operational' : 'idle') as 'operational' | 'maintenance' | 'idle',
      })),
      humanResources: [],
      constraints: [],
    };
  }, [onboardingData, apiPorts, apiTerminals, apiBerths, apiResources]);

  // Close terminal dropdown on outside click
  useEffect(() => {
    if (!showTerminalDropdown) return;
    const handleClick = () => setShowTerminalDropdown(false);
    document.addEventListener('click', handleClick);
    return () => document.removeEventListener('click', handleClick);
  }, [showTerminalDropdown]);

  // Update time every minute
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000);
    return () => clearInterval(timer);
  }, []);

  // Refresh data function
  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await queryClient.invalidateQueries();
    } catch (error) {
      console.error('Failed to refresh data:', error);
    }
    setIsRefreshing(false);
    setLastRefreshTime(new Date());
    addToast({ type: 'success', title: 'Data Refreshed', message: 'All data has been refreshed successfully', duration: 3000 });
  };

  // Gantt drag-and-drop reschedule handler
  const handleGanttReschedule = async (scheduleId: string, newBerthId: string, newEta: Date, newEtd: Date) => {
    try {
      const schedule = apiSchedules.find((s: APISchedule) => s.scheduleId === parseInt(scheduleId));
      if (!schedule) return;
      await createSchedule({
        vesselId: schedule.vesselId,
        berthId: parseInt(newBerthId),
        eta: newEta.toISOString(),
        etd: newEtd.toISOString(),
        priority: schedule.priority || 1,
      });
      queryClient.invalidateQueries({ queryKey: ['schedules-active'] });
      queryClient.invalidateQueries({ queryKey: ['berth-status'] });
      const berth = uiBerths.find(b => b.id === newBerthId);
      addToast({
        type: 'berth-update',
        title: 'Schedule Updated',
        message: `${schedule.vesselName || 'Vessel'} rescheduled to ${berth?.name || 'berth'}`,
        duration: 5000,
      });
    } catch (error) {
      console.error('Failed to reschedule:', error);
      addToast({ type: 'error', title: 'Reschedule Failed', message: 'Could not update the schedule. Please try again.', duration: 5000 });
    }
  };

  const selectedVessel = uiVessels.find(v => v.id === selectedVesselId);

  // Generate sample vessels for future months (March through December) for Full Year view demo
  const futureMonthsVessels = useMemo<Vessel[]>(() => {
    const vesselNames = [
      'MV Northern Star', 'MV Ocean Voyager', 'MV Eastern Wind', 'MV Pacific Dream',
      'MV Maritime Fortune', 'MV Global Carrier', 'MV Sea Champion', 'MV Trade Master',
      'MV Port Runner', 'MV Cargo Express', 'MV Swift Mariner', 'MV Blue Horizon',
      'MV Coastal Spirit', 'MV Liberty Belle', 'MV Golden Gate', 'MV Silver Wave',
      'MV Neptune King', 'MV Atlantic Gem', 'MV Bay Trader', 'MV Harbor Pride',
      'MV Crystal Sea', 'MV Emerald Star', 'MV Phoenix Rising', 'MV Thunder Bay',
      'MV Sunset Glory', 'MV Dawn Breaker', 'MV Storm Rider', 'MV Coral Queen',
      'MV Arctic Explorer', 'MV Tropical Sun', 'MV Winter Pride', 'MV Summer Breeze',
      'MV Autumn Leaf', 'MV Spring Bloom', 'MV Monsoon Wave', 'MV Desert Storm',
      'MV Mountain Peak', 'MV River Delta', 'MV Island Hopper', 'MV Coastal Runner',
      'MV Deep Blue', 'MV High Seas', 'MV Open Water', 'MV Calm Harbor',
      'MV Fast Current', 'MV Steady Voyage', 'MV Long Journey', 'MV Safe Passage',
      'MV Red Dragon', 'MV Blue Phoenix', 'MV Green Tiger', 'MV White Eagle',
      'MV Black Pearl', 'MV Gold Star', 'MV Silver Moon', 'MV Bronze Sun'
    ];
    const vesselTypes = ['Container Ship', 'Bulk Carrier', 'Tanker', 'RO-RO', 'General Cargo', 'LNG Carrier'];
    const cargoTypes = ['Container', 'Dry Bulk', 'Crude Oil', 'Vehicles', 'General', 'LNG'];
    const flags = ['Singapore', 'Panama', 'Liberia', 'Marshall Islands', 'Hong Kong', 'Malta', 'Greece', 'Japan', 'China', 'Norway'];
    const statuses: Array<'on-time' | 'at-risk' | 'early' | 'delayed'> = ['on-time', 'on-time', 'on-time', 'at-risk', 'early', 'delayed'];

    const vessels: Vessel[] = [];
    const year = currentTime.getFullYear();

    // Generate vessels for March (2) through December (11) - skip past months
    for (let monthIndex = 2; monthIndex <= 11; monthIndex++) {
      const mi = monthIndex - 2; // Index starting from 0 for March
      const numVessels = 5 + (monthIndex % 4); // 5-8 vessels per month, varies by month
      for (let i = 0; i < numVessels; i++) {
        const day = 1 + Math.floor(Math.random() * 27);
        const hour = 6 + Math.floor(Math.random() * 14);
        const eta = new Date(year, monthIndex, day, hour, 0, 0);
        const vesselIndex = mi * 6 + i;
        const typeIndex = (mi + i) % vesselTypes.length;

        vessels.push({
          id: `future-${monthIndex}-${i}`,
          name: vesselNames[vesselIndex % vesselNames.length],
          imo: `${9400000 + monthIndex * 100 + i}`,
          callSign: `V${String.fromCharCode(65 + (mi % 26))}${100 + i}`,
          flag: flags[(mi + i) % flags.length],
          vesselType: vesselTypes[typeIndex],
          loa: 200 + Math.floor(Math.random() * 150),
          beam: 28 + Math.floor(Math.random() * 20),
          draft: 10 + Math.floor(Math.random() * 6),
          declaredETA: eta,
          predictedETA: new Date(eta.getTime() + (Math.random() - 0.5) * 2 * 60 * 60 * 1000),
          etaDeviation: Math.floor((Math.random() - 0.3) * 120),
          status: statuses[Math.floor(Math.random() * statuses.length)],
          readiness: 'pending' as const,
          cargoType: cargoTypes[typeIndex],
          cargoQuantity: 5000 + Math.floor(Math.random() * 20000),
          cargoUnit: typeIndex === 0 ? 'TEU' : 'MT',
          constraints: [],
        });
      }
    }

    return vessels;
  }, [currentTime]);

  // Filter vessels for 7-day view
  const filteredVessels = timeWindow === '7days'
    ? uiVessels.filter(v => {
        // Always show vessels that have arrived or are berthed
        if (v.ata || v.status === 'arrived') return true;
        const daysUntilArrival = (v.predictedETA.getTime() - currentTime.getTime()) / (1000 * 60 * 60 * 24);
        return daysUntilArrival >= -1 && daysUntilArrival <= 7;
      })
    : [...uiVessels, ...futureMonthsVessels]; // Include future months for Full Year view

  // Handler functions
  const handleAcceptRecommendation = (vessel: Vessel) => {
    setVesselForAction(vessel);
    setShowAcceptModal(true);
  };

  const handleModifyAllocation = (vessel: Vessel) => {
    setVesselForAction(vessel);
    setShowModifyModal(true);
  };

  const handleRejectRecommendation = (vessel: Vessel) => {
    setVesselForAction(vessel);
    setShowModifyModal(true);
  };

  const handleRequestAISuggestion = async (vessel: Vessel) => {
    try {
      addToast({
        type: 'info',
        title: 'Requesting AI Suggestion',
        message: `Fetching berth recommendation for ${vessel.name}...`,
        duration: 3000,
      });
      const aiSuggestions = await aiService.getBerthSuggestions(parseInt(vessel.id), vessel.predictedETA?.toISOString(), 5);
      if (aiSuggestions && aiSuggestions.length > 0) {
        // Transform AI suggestion to BerthSuggestion format
      const aiResp: any = aiSuggestions[0];
        // Map from Python snake_case response fields
        const topSuggestion: BerthSuggestion = {
          berthId: aiResp.berth_id || aiResp.berthId,
          berthName: aiResp.berth_name || aiResp.berthName,
          terminalName: aiResp.terminal_name || aiResp.terminalName || '',
          score: aiResp.total_score || aiResp.score || 0,
          rank: 1,
          explanation: aiResp.explanation || (Array.isArray(aiResp.reasoning) ? aiResp.reasoning.join('. ') : 'AI-generated recommendation'),
          eta: aiResp.proposed_eta || aiResp.proposedEta,
          etd: aiResp.proposed_etd || aiResp.proposedEtd,
          waitTime: aiResp.estimated_wait_minutes || aiResp.estimatedWaitMinutes,
        };
        // Update the suggestions cache to trigger UI refresh
        queryClient.setQueryData(
          ['suggestions', apiVessels.length, apiSchedules.length],
          (oldData: Map<number, BerthSuggestion> | undefined) => {
            const newMap = new Map(oldData || new Map());
            newMap.set(parseInt(vessel.id), topSuggestion);
            return newMap;
          }
        );
        addToast({
          type: 'vessel-arrival',
          title: 'AI Suggestion Ready',
          message: `Recommended: ${topSuggestion.berthName} with ${Math.round(topSuggestion.score)}% confidence`,
          duration: 5000,
        });
      } else {
        addToast({
          type: 'warning',
          title: 'No Suggestions Available',
          message: `Unable to find suitable berth for ${vessel.name}. All berths may be occupied or incompatible.`,
          duration: 5000,
        });
      }
    } catch (error: any) {
      addToast({
        type: 'error',
        title: 'Suggestion Failed',
        message: error?.response?.data?.message || error?.message || 'Failed to get AI suggestion',
        duration: 5000,
      });
    }
  };

  const handleViewHistory = (vessel: Vessel) => {
    setVesselForAction(vessel);
    setShowHistoryModal(true);
  };

  const handleConfirmAccept = async () => {
    if (vesselForAction?.aiRecommendation) {
      try {
        const berthMatch = uiBerths.find(b => b.name === vesselForAction.aiRecommendation?.suggestedBerth);
        if (berthMatch) {
          await createSchedule({
            vesselId: parseInt(vesselForAction.id),
            berthId: parseInt(berthMatch.id),
            eta: vesselForAction.predictedETA.toISOString(),
            etd: new Date(vesselForAction.predictedETA.getTime() + 8 * 60 * 60 * 1000).toISOString(),
            priority: 1,
          });
          queryClient.invalidateQueries({ queryKey: ['schedules-active'] });
          queryClient.invalidateQueries({ queryKey: ['berth-status'] });
          queryClient.invalidateQueries({ queryKey: ['suggestions'] });
        }
      } catch (error) {
        console.error('Failed to allocate berth:', error);
      }
    }
    setShowAcceptModal(false);
    addToast({
      type: 'vessel-arrival',
      title: 'Berth Allocated',
      message: `${vesselForAction?.name} successfully allocated to ${vesselForAction?.aiRecommendation?.suggestedBerth}`,
      duration: 5000,
    });
  };

  const handleConfirmModify = async (berthId: string, reason: string) => {
    try {
      await createSchedule({
        vesselId: parseInt(vesselForAction?.id || '0'),
        berthId: parseInt(berthId),
        eta: vesselForAction?.predictedETA.toISOString(),
        etd: new Date((vesselForAction?.predictedETA.getTime() || Date.now()) + 8 * 60 * 60 * 1000).toISOString(),
        priority: 1,
        notes: reason,
      });
      queryClient.invalidateQueries({ queryKey: ['schedules-active'] });
      queryClient.invalidateQueries({ queryKey: ['berth-status'] });
      queryClient.invalidateQueries({ queryKey: ['suggestions'] });
    } catch (error) {
      console.error('Failed to modify allocation:', error);
    }
    setShowModifyModal(false);
    const berth = uiBerths.find(b => b.id === berthId);
    addToast({
      type: 'berth-update',
      title: 'Manual Allocation',
      message: `${vesselForAction?.name} manually allocated to ${berth?.name}${reason ? ` — ${reason}` : ''}`,
      duration: 5000,
    });
  };

  const handleCompleteOnboarding = async (data: OnboardingData) => {
    setOnboardingData(data);

    // Save onboarding data to API
    try {
      if (data.port) {
        const port = await portService.create({
          portName: data.port.portName,
          portCode: data.port.portCode,
          country: data.port.country,
          latitude: data.port.coordinates.latitude,
          longitude: data.port.coordinates.longitude,
          timeZone: data.port.timezone,
          isActive: true,
        });

        const portId = port.portId;

        for (const terminal of data.terminals) {
          const createdTerminal = await terminalService.create({
            terminalName: terminal.name,
            terminalCode: terminal.code,
            portId: portId,
            terminalType: terminal.terminalType,
            operatingHours: terminal.operationalHours,
            isActive: true,
          });

          const terminalBerths = data.berths.filter(b => b.terminalId === terminal.id);
          for (const berth of terminalBerths) {
            await berthService.create({
              berthName: berth.name,
              berthCode: berth.name.replace(/\s+/g, '-').toUpperCase(),
              terminalId: createdTerminal.terminalId,
              length: berth.length,
              maxDraft: berth.maxDraft,
              maxLOA: berth.maxLOA,
              numberOfCranes: 0,
              cargoTypes: 'General',
              status: 'Available',
              isActive: true,
            });
          }
        }

        for (const eq of data.equipment) {
          await resourceService.create({
            resourceType: eq.type,
            resourceName: eq.name,
            capacity: eq.capacity,
            isAvailable: eq.status === 'operational',
          });
        }
      }

      await queryClient.invalidateQueries();
    } catch (error) {
      console.error('Failed to save onboarding data to API:', error);
    }

    navigate('/role-select');
  };

  const handleStartOperations = () => {
    navigate('/role-select');
  };

  // Loading state
  const isLoading = loadingVessels || loadingBerths;

  // Operations page content
  const operationsContent = (
    <div className="size-full flex flex-col bg-gradient-to-br from-gray-50 to-white">
      {/* Header */}
      <header className="flex items-center justify-between px-3 md:px-6 py-3 md:py-4 border-b bg-white shadow-sm flex-wrap gap-3" style={{ borderColor: 'var(--border)' }}>
        <div className="flex items-center gap-3">
          <SmartBerthLogo size={36} className="hidden md:block" />
          <SmartBerthLogo size={28} className="md:hidden" />

          {/* Terminal selector / Role indicator */}
          {roleConfig && (
            <div className="relative">
              <button
                onClick={(e) => { e.stopPropagation(); setShowTerminalDropdown(!showTerminalDropdown); }}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all"
                style={{
                  backgroundColor: roleConfig.role === 'port_operator' ? '#ECFDF5' : '#FFFBEB',
                  border: '1px solid',
                  borderColor: roleConfig.role === 'port_operator' ? '#A7F3D0' : '#FDE68A',
                  cursor: 'pointer',
                }}
              >
                <Building2 className="w-3.5 h-3.5" style={{ color: roleConfig.role === 'port_operator' ? '#059669' : '#D97706' }} />
                <span className="text-xs font-semibold" style={{ color: roleConfig.role === 'port_operator' ? '#059669' : '#92400E' }}>
                  {activeTerminalInfo
                    ? activeTerminalInfo.terminalName
                    : roleConfig.assignedTerminalName || 'Select Terminal'}
                </span>
                <ChevronDown className="w-3 h-3" style={{ color: roleConfig.role === 'port_operator' ? '#059669' : '#D97706' }} />
              </button>

              {/* Terminal dropdown */}
              {showTerminalDropdown && (
                <div
                  className="absolute top-full left-0 mt-1 rounded-lg shadow-xl border bg-white z-50"
                  style={{ minWidth: 240, borderColor: '#E5E7EB' }}
                  onClick={(e) => e.stopPropagation()}
                >
                  <div className="px-3 py-2 border-b" style={{ borderColor: '#F3F4F6' }}>
                    <div className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: '#9CA3AF' }}>
                      {roleConfig.role === 'port_operator' ? 'Switch Terminal' : 'Current Terminal'}
                    </div>
                  </div>
                  <div className="p-2" style={{ maxHeight: 280, overflowY: 'auto' }}>
                    {apiTerminals.map((t: APITerminal) => {
                      const isSelected = activeTerminalId === String(t.terminalId);
                      const isDisabled = roleConfig.role === 'terminal_operator' && roleConfig.assignedTerminalId !== String(t.terminalId);
                      return (
                        <button
                          key={t.terminalId}
                          onClick={() => {
                            if (!isDisabled) handleTerminalSwitch(String(t.terminalId));
                          }}
                          disabled={isDisabled}
                          className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-left transition-all hover:bg-gray-50"
                          style={{
                            backgroundColor: isSelected ? '#FFFBEB' : 'transparent',
                            opacity: isDisabled ? 0.4 : 1,
                            cursor: isDisabled ? 'not-allowed' : 'pointer',
                          }}
                        >
                          <Building2 className="w-4 h-4" style={{ color: isSelected ? '#D97706' : '#6B7280' }} />
                          <div className="flex-1 min-w-0">
                            <div className="text-xs font-semibold truncate" style={{ color: '#1F2937' }}>{t.terminalName}</div>
                            <div className="text-[10px]" style={{ color: '#9CA3AF' }}>
                              {t.terminalCode} — {t.terminalType}
                            </div>
                          </div>
                          {isSelected && <div className="ml-auto w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: '#D97706' }} />}
                        </button>
                      );
                    })}
                  </div>

                  <div className="border-t p-2" style={{ borderColor: '#F3F4F6' }}>
                    <button
                      onClick={handleSwitchRole}
                      className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-left transition-all hover:bg-red-50"
                    >
                      <LogOut className="w-4 h-4" style={{ color: '#DC2626' }} />
                      <div className="text-xs font-medium" style={{ color: '#DC2626' }}>Switch Role</div>
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2 md:gap-6 flex-wrap flex-1 justify-end">
          {/* View toggle */}
          <div className="flex gap-1 p-1 rounded-lg order-1 w-full sm:w-auto" style={{ backgroundColor: 'var(--muted)' }}>
            <button
              onClick={() => setViewMode('vessels')}
              className="flex items-center justify-center gap-1 md:gap-2 px-2 md:px-4 py-2 rounded-md transition-all flex-1 sm:flex-initial"
              style={{
                backgroundColor: viewMode === 'vessels' ? 'white' : 'transparent',
                color: viewMode === 'vessels' ? 'var(--kale-blue)' : 'var(--muted-foreground)',
                fontWeight: viewMode === 'vessels' ? 600 : 400,
                boxShadow: viewMode === 'vessels' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
              }}
            >
              <Ship className="w-4 h-4" />
              <span className="text-xs md:text-sm">Upcoming Vessels</span>
            </button>
            <button
              onClick={() => setViewMode('worldmap')}
              className="flex items-center justify-center gap-1 md:gap-2 px-2 md:px-4 py-2 rounded-md transition-all flex-1 sm:flex-initial"
              style={{
                backgroundColor: viewMode === 'worldmap' ? 'white' : 'transparent',
                color: viewMode === 'worldmap' ? 'var(--kale-blue)' : 'var(--muted-foreground)',
                fontWeight: viewMode === 'worldmap' ? 600 : 400,
                boxShadow: viewMode === 'worldmap' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
              }}
            >
              <Globe className="w-4 h-4" />
              <span className="text-xs md:text-sm">Vessels Tracking</span>
            </button>
            <button
              onClick={() => setViewMode('berths')}
              className="flex items-center justify-center gap-1 md:gap-2 px-2 md:px-4 py-2 rounded-md transition-all flex-1 sm:flex-initial"
              style={{
                backgroundColor: viewMode === 'berths' ? 'white' : 'transparent',
                color: viewMode === 'berths' ? 'var(--kale-blue)' : 'var(--muted-foreground)',
                fontWeight: viewMode === 'berths' ? 600 : 400,
                boxShadow: viewMode === 'berths' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
              }}
            >
              <LayoutGrid className="w-4 h-4" />
              <span className="text-xs md:text-sm">Berth Overview</span>
            </button>
            <button
              onClick={() => setViewMode('terminal3d')}
              className="flex items-center justify-center gap-1 md:gap-2 px-2 md:px-4 py-2 rounded-md transition-all flex-1 sm:flex-initial"
              style={{
                backgroundColor: viewMode === 'terminal3d' ? 'white' : 'transparent',
                color: viewMode === 'terminal3d' ? 'var(--kale-blue)' : 'var(--muted-foreground)',
                fontWeight: viewMode === 'terminal3d' ? 600 : 400,
                boxShadow: viewMode === 'terminal3d' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
              }}
            >
              <Box className="w-4 h-4" />
              <span className="text-xs md:text-sm">Digital Twin</span>
            </button>
            <button
              onClick={() => setViewMode('gantt')}
              className="flex items-center justify-center gap-1 md:gap-2 px-2 md:px-4 py-2 rounded-md transition-all flex-1 sm:flex-initial"
              style={{
                backgroundColor: viewMode === 'gantt' ? 'white' : 'transparent',
                color: viewMode === 'gantt' ? 'var(--kale-blue)' : 'var(--muted-foreground)',
                fontWeight: viewMode === 'gantt' ? 600 : 400,
                boxShadow: viewMode === 'gantt' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
              }}
            >
              <BarChart3 className="w-4 h-4" />
              <span className="text-xs md:text-sm">Gantt</span>
            </button>
          </div>

          {/* Real-time indicator */}
          <div className="flex items-center gap-2 px-2 md:px-3 py-1.5 rounded-lg order-2" style={{ backgroundColor: 'var(--kale-sky)' }}>
            <div className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: 'var(--status-on-time)' }} />
            <span className="text-xs md:text-sm" style={{ color: 'var(--kale-blue)', fontWeight: 500 }}>Live</span>
            <span className="text-xs hidden sm:inline" style={{ color: 'var(--muted-foreground)' }}>
              {currentTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2 md:gap-3 order-3">
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="flex items-center gap-2 p-2 md:px-3 md:py-2 rounded-lg transition-all hover:bg-gray-100"
              style={{ color: 'var(--kale-blue)' }}
              title="Refresh data"
            >
              <RefreshCw className={`w-4 h-4 md:w-5 md:h-5 ${isRefreshing ? 'animate-spin' : ''}`} />
            </button>

            <button
              onClick={() => { setShowNotifications(true); setNotificationCount(0); }}
              className="relative flex items-center gap-2 p-2 md:px-3 md:py-2 rounded-lg transition-all hover:bg-gray-100"
              style={{ color: 'var(--kale-blue)' }}
              title="Notifications"
            >
              <Bell className={`w-4 h-4 md:w-5 md:h-5 ${notificationCount > 0 ? 'animate-bounce' : ''}`} />
              {notificationCount > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 md:w-5 md:h-5 rounded-full flex items-center justify-center text-[10px] animate-pulse"
                  style={{ backgroundColor: 'var(--status-critical)', color: 'white', fontWeight: 700 }}>
                  {notificationCount > 9 ? '9+' : notificationCount}
                </span>
              )}
            </button>

            <button
              onClick={() => setShowActivityFeed(true)}
              className="flex items-center gap-2 p-2 md:px-3 md:py-2 rounded-lg transition-all hover:bg-gray-100"
              style={{ color: 'var(--kale-teal)' }}
              title="Activity Feed - AI Insights"
            >
              <Activity className="w-4 h-4 md:w-5 md:h-5" />
            </button>

            <button
              onClick={() => setShowTerminalProfile(true)}
              className="flex items-center gap-2 p-2 md:px-3 md:py-2 rounded-lg transition-all hover:bg-gray-100"
              style={{ color: 'var(--kale-blue)' }}
              title="Terminal Profile"
            >
              <Building2 className="w-4 h-4 md:w-5 md:h-5" />
            </button>

          </div>
        </div>
      </header>

      {/* Dashboard KPI Bar */}
      <DashboardKPIBar
        metrics={dashboardMetrics}
        vessels={uiVessels}
        berths={uiBerths}
        lastRefreshTime={lastRefreshTime}
        isRefreshing={isRefreshing}
      />

      {/* Loading overlay */}
      {isLoading && uiVessels.length === 0 && uiBerths.length === 0 && (
        <div className="flex items-center justify-center p-8">
          <div className="flex items-center gap-3">
            <RefreshCw className="w-5 h-5 animate-spin" style={{ color: 'var(--kale-blue)' }} />
            <span className="text-sm" style={{ color: 'var(--muted-foreground)' }}>Loading data...</span>
          </div>
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 overflow-hidden relative">
        {viewMode === 'berths' ? (
          <BerthVisualization3D
            berths={uiBerths}
            onBerthClick={(berth) => {
              setSelectedBerth(berth as UIBerth);
              setShowBerthDetail(true);
            }}
            selectedBerthId={selectedBerthId}
          />
        ) : viewMode === 'terminal3d' ? (
          <Terminal3DView
            berths={uiBerths}
            onBerthClick={(berth) => {
              setSelectedBerth(berth as UIBerth);
              setShowBerthDetail(true);
            }}
            selectedBerthId={selectedBerthId}
            terminalName={activeTerminalInfo?.terminalName}
            vessels={filteredVessels}
            onAllocateVessel={async (vesselId, berthId, eta, etd) => {
              try {
                await createSchedule({
                  vesselId: parseInt(vesselId),
                  berthId: parseInt(berthId),
                  eta: eta.toISOString(),
                  etd: etd.toISOString(),
                  priority: 1,
                });
                queryClient.invalidateQueries({ queryKey: ['schedules-active'] });
                queryClient.invalidateQueries({ queryKey: ['berth-status'] });
                queryClient.invalidateQueries({ queryKey: ['suggestions'] });
                queryClient.invalidateQueries({ queryKey: ['dashboard-metrics'] });
                addToast({
                  type: 'berth-update',
                  title: 'Berth Allocated',
                  message: `Vessel allocated to ${uiBerths.find(b => b.id === berthId)?.name || 'berth'} successfully`,
                  duration: 5000,
                });
                return { success: true, message: 'Berth allocated successfully' };
              } catch (error: any) {
                const msg = error?.response?.data?.message || error?.message || 'Allocation failed';
                addToast({ type: 'error', title: 'Allocation Failed', message: msg, duration: 5000 });
                return { success: false, message: msg };
              }
            }}
          />
        ) : viewMode === 'gantt' ? (
          <GanttChart
            berths={ganttBerths}
            schedules={ganttSchedules}
            onReschedule={handleGanttReschedule}
            onVesselClick={(vesselId) => setSelectedVesselId(vesselId)}
          />
        ) : viewMode === 'worldmap' ? (
          <Suspense fallback={
            <div className="h-full flex items-center justify-center bg-gradient-to-b from-slate-900 to-slate-800">
              <div className="flex flex-col items-center gap-4">
                <Globe className="w-12 h-12 text-blue-400 animate-pulse" />
                <div className="text-white text-sm">Loading Vessels Tracking...</div>
              </div>
            </div>
          }>
            <WorldVesselMap
              portLocation={{
                portCode: apiPorts[0]?.portCode || 'INMUN',
                portName: apiPorts[0]?.portName || 'Mundra Port',
                latitude: apiPorts[0]?.latitude || 22.7396,
                longitude: apiPorts[0]?.longitude || 69.7194,
                boundingBox: {
                  minLat: (apiPorts[0]?.latitude || 22.7396) - 15,
                  minLon: (apiPorts[0]?.longitude || 69.7194) - 15,
                  maxLat: (apiPorts[0]?.latitude || 22.7396) + 15,
                  maxLon: (apiPorts[0]?.longitude || 69.7194) + 15,
                },
              }}
              onVesselClick={(vessel) => {
                const matchedVessel = uiVessels.find(
                  v => v.id === String(vessel.vesselId) || v.callSign === vessel.mmsi
                );
                if (matchedVessel) {
                  setSelectedVesselId(matchedVessel.id);
                }
              }}
              className="h-full"
            />
          </Suspense>
        ) : (
          <UpcomingVesselsTimeline
            vessels={filteredVessels}
            onVesselClick={(vessel) => setSelectedVesselId(vessel.id)}
            selectedVesselId={selectedVesselId}
            timeWindow={timeWindow}
            onTimeWindowChange={setTimeWindow}
            onAcceptRecommendation={handleAcceptRecommendation}
            onRejectRecommendation={handleRejectRecommendation}
            onRequestAISuggestion={handleRequestAISuggestion}
            berths={uiBerths}
          />
        )}
      </div>

      {/* Vessel details panel */}
      <VesselDetailsPanel
        vessel={selectedVessel || null}
        onClose={() => setSelectedVesselId(undefined)}
        onAcceptRecommendation={handleAcceptRecommendation}
        onModifyAllocation={handleModifyAllocation}
        onViewHistory={handleViewHistory}
      />

      {/* Modals */}
      {showAcceptModal && vesselForAction && (() => {
        const recommendedBerthName = vesselForAction.aiRecommendation?.suggestedBerth;
        const recommendedBerth = uiBerths.find(b => b.name === recommendedBerthName) || uiBerths[0];
        return recommendedBerth ? (
          <AcceptRecommendationModal
            vessel={vesselForAction}
            recommendedBerth={recommendedBerth}
            onAccept={handleConfirmAccept}
            onCancel={() => setShowAcceptModal(false)}
          />
        ) : null;
      })()}

      {showModifyModal && vesselForAction && (
        <ModifyAllocationModal
          vessel={vesselForAction}
          berths={uiBerths}
          onAllocate={handleConfirmModify}
          onCancel={() => setShowModifyModal(false)}
        />
      )}

      {showHistoryModal && vesselForAction && (
        <VesselHistoryModal
          vessel={vesselForAction}
          onClose={() => setShowHistoryModal(false)}
        />
      )}

      {/* Panels */}
      {showNotifications && (
        <NotificationsPanel onClose={() => setShowNotifications(false)} />
      )}

      {showActivityFeed && (
        <ActivityFeedPanel 
          onClose={() => setShowActivityFeed(false)}
          onVesselClick={(vesselId) => {
            setSelectedVesselId(vesselId);
            setShowActivityFeed(false);
          }}
          onBerthClick={(berthId) => {
            const berth = uiBerths.find(b => b.id === berthId);
            if (berth) {
              setSelectedBerth(berth);
              setShowBerthDetail(true);
            }
            setShowActivityFeed(false);
          }}
        />
      )}

      {showTerminalProfile && terminalProfileData && (
        <div className="fixed inset-0 bg-white z-50">
          <TerminalProfile
            data={terminalProfileData}
            onBack={() => setShowTerminalProfile(false)}
            onStartOperations={() => setShowTerminalProfile(false)}
            onOnboarding={() => { setShowTerminalProfile(false); navigate('/onboarding'); }}
          />
        </div>
      )}

      {/* Berth Detail Dialog */}
      {showBerthDetail && selectedBerth && (
        <BerthDetailDialog
          berth={selectedBerth}
          onClose={() => {
            setShowBerthDetail(false);
            setSelectedBerth(null);
          }}
        />
      )}

      {/* Chatbot */}
      <Chatbot
        vessels={uiVessels}
        berths={uiBerths}
        currentView={viewMode === 'gantt' || viewMode === 'worldmap' ? 'berths' : viewMode}
        selectedVessel={selectedVessel}
        selectedBerth={selectedBerth}
        onVesselClick={(vesselId) => {
          setSelectedVesselId(vesselId);
        }}
        onBerthClick={(berthId) => {
          const berth = uiBerths.find(b => b.id === berthId);
          if (berth) {
            setSelectedBerth(berth);
            setShowBerthDetail(true);
          }
        }}
        onViewChange={(view) => {
          setViewMode(view);
        }}
      />

      {/* Browser Agent - Autonomous AI Navigator */}
      <BrowserAgentPanel />

      <style>{`
        @keyframes slide-down {
          from { transform: translateY(-100%); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
        .animate-slide-down { animation: slide-down 0.3s ease-out; }
        @keyframes toast-progress {
          from { width: 100%; }
          to { width: 0%; }
        }
      `}</style>
    </div>
  );

  return (
    <Routes>
      <Route path="/onboarding" element={
        <PortOnboardingWizard
          onComplete={handleCompleteOnboarding}
          onCancel={() => navigate('/operations')}
        />
      } />
      <Route path="/profile" element={
        terminalProfileData ? (
          <TerminalProfile
            data={terminalProfileData}
            onBack={() => navigate('/role-select')}
            onStartOperations={handleStartOperations}
            onOnboarding={() => navigate('/onboarding')}
          />
        ) : (
          <Navigate to="/role-select" replace />
        )
      } />
      <Route path="/role-select" element={
        <RoleSelection
          terminals={apiTerminals.map((t: APITerminal) => ({
            id: String(t.terminalId),
            name: t.terminalName,
            code: t.terminalCode,
            terminalType: t.terminalType,
          }))}
          portName={apiPorts.length > 0 ? apiPorts[0].portName : terminalProfileData?.port?.portName || 'SmartBerth AI'}
          onSelect={(config) => {
            handleRoleSelect(config);
            navigate('/operations');
          }}
        />
      } />
      <Route path="/operations" element={
        !roleConfig && apiTerminals.length > 0 ? <Navigate to="/role-select" replace /> : operationsContent
      } />
      <Route path="/" element={<Navigate to="/role-select" replace />} />
      <Route path="*" element={<Navigate to="/role-select" replace />} />
    </Routes>
  );
}
