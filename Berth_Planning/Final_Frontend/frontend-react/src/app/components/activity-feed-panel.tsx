import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Activity, 
  Brain, 
  Ship, 
  Anchor, 
  AlertTriangle, 
  CheckCircle2, 
  Clock,
  RefreshCw,
  ChevronRight,
  ChevronDown,
  Eye,
  EyeOff,
  Zap,
  Gauge,
  BarChart3,
  MessageSquare,
  X,
  Filter,
  Play,
  Pause,
  Info,
  TrendingUp,
  Lightbulb
} from 'lucide-react';

// Types
interface ConfidenceFactors {
  data_freshness: number;
  historical_accuracy: number;
  data_completeness: number;
  source_reliability: number;
  weather_certainty: number;
  constraint_satisfaction: number;
}

interface ActivityEntry {
  id: string;
  timestamp: string;
  category: string;
  alert_type: string;
  severity: string;
  title: string;
  message: string;
  explanation: string;
  confidence_score: number;
  confidence_factors: ConfidenceFactors;
  affected_entities: {
    vessels: number[];
    berths: number[];
    schedules: number[];
  };
  metadata: Record<string, any>;
  is_read: boolean;
  is_actionable: boolean;
  recommended_actions: Array<{
    action: string;
    description: string;
  }>;
}

interface MonitoringStatus {
  is_active: boolean;
  interval_seconds: number;
  last_check: string | null;
  alerts_generated_today: number;
}

// API base URL - adjust based on your setup
const AI_SERVICE_URL = import.meta.env.VITE_AI_SERVICE_URL || 'http://localhost:8001';

// API calls
const activityApi = {
  getFeed: async (limit = 50, category?: string, severity?: string): Promise<{
    activities: ActivityEntry[];
    total_count: number;
    unread_counts: Record<string, number>;
  }> => {
    const params = new URLSearchParams({ limit: String(limit) });
    if (category) params.append('category', category);
    if (severity) params.append('severity', severity);
    
    const response = await fetch(`${AI_SERVICE_URL}/monitoring/activity-feed?${params}`);
    if (!response.ok) throw new Error('Failed to fetch activity feed');
    return response.json();
  },
  
  markRead: async (activityId: string): Promise<void> => {
    const response = await fetch(`${AI_SERVICE_URL}/monitoring/activity/${activityId}/read`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to mark as read');
  },
  
  getMonitoringStatus: async (): Promise<MonitoringStatus> => {
    const response = await fetch(`${AI_SERVICE_URL}/monitoring/status`);
    if (!response.ok) throw new Error('Failed to get monitoring status');
    return response.json();
  },
  
  startMonitoring: async (interval = 30): Promise<void> => {
    const response = await fetch(`${AI_SERVICE_URL}/monitoring/start?interval_seconds=${interval}`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to start monitoring');
  },
  
  stopMonitoring: async (): Promise<void> => {
    const response = await fetch(`${AI_SERVICE_URL}/monitoring/stop`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to stop monitoring');
  },
  
  getConfidenceBreakdown: async (entityType: string, entityId: number): Promise<any> => {
    const response = await fetch(`${AI_SERVICE_URL}/monitoring/confidence/${entityType}/${entityId}`);
    if (!response.ok) throw new Error('Failed to get confidence breakdown');
    return response.json();
  }
};

// Helper functions
const getSeverityColor = (severity: string) => {
  switch (severity?.toUpperCase()) {
    case 'CRITICAL': return 'var(--status-critical)';
    case 'HIGH': return 'var(--status-at-risk)';
    case 'WARNING': return 'var(--status-delayed)';
    case 'INFO': return 'var(--kale-blue)';
    case 'DEBUG': return 'var(--muted-foreground)';
    default: return 'var(--muted-foreground)';
  }
};

const getCategoryIcon = (category: string) => {
  switch (category) {
    case 'VESSEL_TRACKING': return <Ship className="w-4 h-4" />;
    case 'ETA_PREDICTION': return <Clock className="w-4 h-4" />;
    case 'BERTH_ALLOCATION': return <Anchor className="w-4 h-4" />;
    case 'CONFLICT_DETECTION': return <AlertTriangle className="w-4 h-4" />;
    case 'REOPTIMIZATION': return <RefreshCw className="w-4 h-4" />;
    case 'WEATHER': return <Activity className="w-4 h-4" />;
    case 'SYSTEM': return <Gauge className="w-4 h-4" />;
    case 'AGENT_ACTION': return <Brain className="w-4 h-4" />;
    default: return <Activity className="w-4 h-4" />;
  }
};

const formatTimestamp = (timestamp: string) => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
  return date.toLocaleDateString();
};

interface ActivityFeedPanelProps {
  onClose: () => void;
  onVesselClick?: (vesselId: string) => void;
  onBerthClick?: (berthId: string) => void;
}

// Confidence Score Breakdown Component
function ConfidenceBreakdown({ factors, score }: { factors: ConfidenceFactors; score: number }) {
  const [expanded, setExpanded] = useState(false);
  
  const factorLabels: Record<keyof ConfidenceFactors, string> = {
    data_freshness: 'Data Freshness',
    historical_accuracy: 'Historical Accuracy',
    data_completeness: 'Data Completeness',
    source_reliability: 'Source Reliability',
    weather_certainty: 'Weather Certainty',
    constraint_satisfaction: 'Constraint Satisfaction'
  };
  
  const getScoreColor = (value: number) => {
    if (value >= 0.8) return 'var(--status-on-time)';
    if (value >= 0.6) return 'var(--status-delayed)';
    return 'var(--status-at-risk)';
  };
  
  return (
    <div className="mt-2 p-2 rounded-lg" style={{ backgroundColor: 'var(--muted)' }}>
      <div 
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2">
          <Gauge className="w-3.5 h-3.5" style={{ color: 'var(--kale-teal)' }} />
          <span className="text-[11px] font-semibold">Confidence: {score.toFixed(1)}%</span>
        </div>
        {expanded ? 
          <ChevronDown className="w-3.5 h-3.5" style={{ color: 'var(--muted-foreground)' }} /> :
          <ChevronRight className="w-3.5 h-3.5" style={{ color: 'var(--muted-foreground)' }} />
        }
      </div>
      
      {expanded && (
        <div className="mt-2 space-y-1.5">
          {Object.entries(factors).map(([key, value]) => (
            <div key={key} className="flex items-center gap-2">
              <span className="text-[10px] w-28 truncate" style={{ color: 'var(--muted-foreground)' }}>
                {factorLabels[key as keyof ConfidenceFactors]}
              </span>
              <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--border)' }}>
                <div 
                  className="h-full rounded-full transition-all"
                  style={{ 
                    width: `${value * 100}%`,
                    backgroundColor: getScoreColor(value)
                  }}
                />
              </div>
              <span className="text-[10px] w-8 text-right" style={{ color: getScoreColor(value) }}>
                {(value * 100).toFixed(0)}%
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Single Activity Item Component
function ActivityItem({ 
  activity, 
  onMarkRead,
  onVesselClick,
  onBerthClick
}: { 
  activity: ActivityEntry;
  onMarkRead: (id: string) => void;
  onVesselClick?: (vesselId: string) => void;
  onBerthClick?: (berthId: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  
  return (
    <div 
      className={`p-3 border-b transition-colors cursor-pointer ${!activity.is_read ? 'bg-blue-50/50' : ''}`}
      style={{ borderColor: 'var(--border)' }}
      onClick={() => {
        setExpanded(!expanded);
        if (!activity.is_read) {
          onMarkRead(activity.id);
        }
      }}
    >
      <div className="flex items-start gap-2">
        {/* Category Icon */}
        <div 
          className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{ backgroundColor: `${getSeverityColor(activity.severity)}15` }}
        >
          <div style={{ color: getSeverityColor(activity.severity) }}>
            {getCategoryIcon(activity.category)}
          </div>
        </div>
        
        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <span className="text-xs font-semibold truncate">{activity.title}</span>
              {!activity.is_read && (
                <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: 'var(--kale-blue)' }} />
              )}
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <span 
                className="text-[9px] px-1.5 py-0.5 rounded font-semibold"
                style={{ 
                  backgroundColor: getSeverityColor(activity.severity),
                  color: 'white'
                }}
              >
                {activity.severity}
              </span>
              <span className="text-[10px]" style={{ color: 'var(--muted-foreground)' }}>
                {formatTimestamp(activity.timestamp)}
              </span>
            </div>
          </div>
          
          <p className="text-[11px] mt-1" style={{ color: 'var(--muted-foreground)' }}>
            {activity.message}
          </p>
          
          {/* Affected Entities */}
          {(activity.affected_entities.vessels.length > 0 || activity.affected_entities.berths.length > 0) && (
            <div className="flex flex-wrap gap-1 mt-2">
              {activity.affected_entities.vessels.map(vesselId => (
                <button
                  key={`v-${vesselId}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    onVesselClick?.(String(vesselId));
                  }}
                  className="text-[10px] px-1.5 py-0.5 rounded-full flex items-center gap-1 hover:opacity-80"
                  style={{ backgroundColor: 'var(--kale-sky)', color: 'var(--kale-blue)' }}
                >
                  <Ship className="w-2.5 h-2.5" />
                  Vessel {vesselId}
                </button>
              ))}
              {activity.affected_entities.berths.map(berthId => (
                <button
                  key={`b-${berthId}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    onBerthClick?.(String(berthId));
                  }}
                  className="text-[10px] px-1.5 py-0.5 rounded-full flex items-center gap-1 hover:opacity-80"
                  style={{ backgroundColor: 'var(--kale-teal)20', color: 'var(--kale-teal)' }}
                >
                  <Anchor className="w-2.5 h-2.5" />
                  Berth {berthId}
                </button>
              ))}
            </div>
          )}
          
          {/* Expanded Content */}
          {expanded && (
            <div className="mt-3 space-y-3">
              {/* AI Explanation */}
              <div className="p-2 rounded-lg border" style={{ borderColor: 'var(--kale-blue)30', backgroundColor: 'var(--kale-blue)05' }}>
                <div className="flex items-center gap-1.5 mb-1.5">
                  <Brain className="w-3.5 h-3.5" style={{ color: 'var(--kale-blue)' }} />
                  <span className="text-[10px] font-semibold" style={{ color: 'var(--kale-blue)' }}>
                    AI Insight
                  </span>
                </div>
                <p className="text-[11px] leading-relaxed" style={{ color: 'var(--foreground)' }}>
                  {activity.explanation}
                </p>
              </div>
              
              {/* Confidence Breakdown */}
              <ConfidenceBreakdown 
                factors={activity.confidence_factors} 
                score={activity.confidence_score} 
              />
              
              {/* Recommended Actions */}
              {activity.is_actionable && activity.recommended_actions.length > 0 && (
                <div className="p-2 rounded-lg" style={{ backgroundColor: 'var(--kale-teal)10' }}>
                  <div className="flex items-center gap-1.5 mb-2">
                    <Lightbulb className="w-3.5 h-3.5" style={{ color: 'var(--kale-teal)' }} />
                    <span className="text-[10px] font-semibold" style={{ color: 'var(--kale-teal)' }}>
                      Recommended Actions
                    </span>
                  </div>
                  <div className="space-y-1.5">
                    {activity.recommended_actions.map((action, idx) => (
                      <button
                        key={idx}
                        className="w-full text-left p-2 rounded-lg hover:bg-white/50 transition-colors flex items-center gap-2"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Zap className="w-3 h-3 flex-shrink-0" style={{ color: 'var(--kale-teal)' }} />
                        <span className="text-[10px]">{action.description}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Metadata */}
              {Object.keys(activity.metadata).length > 0 && (
                <details className="text-[10px]">
                  <summary className="cursor-pointer" style={{ color: 'var(--muted-foreground)' }}>
                    View raw data
                  </summary>
                  <pre className="mt-1 p-2 rounded bg-gray-100 overflow-x-auto text-[9px]">
                    {JSON.stringify(activity.metadata, null, 2)}
                  </pre>
                </details>
              )}
            </div>
          )}
          
          {/* Expand indicator */}
          <div className="flex justify-center mt-2">
            {expanded ? 
              <ChevronDown className="w-4 h-4" style={{ color: 'var(--muted-foreground)' }} /> :
              <ChevronRight className="w-4 h-4" style={{ color: 'var(--muted-foreground)' }} />
            }
          </div>
        </div>
      </div>
    </div>
  );
}

// Main Activity Feed Panel Component
export function ActivityFeedPanel({ onClose, onVesselClick, onBerthClick }: ActivityFeedPanelProps) {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<{ category?: string; severity?: string }>({});
  const [showFilters, setShowFilters] = useState(false);
  
  // Fetch activity feed
  const { data: feedData, isLoading, refetch } = useQuery({
    queryKey: ['activity-feed', filter],
    queryFn: () => activityApi.getFeed(50, filter.category, filter.severity),
    refetchInterval: 15000, // Refresh every 15 seconds
    staleTime: 10000,
  });
  
  // Fetch monitoring status
  const { data: monitoringStatus } = useQuery({
    queryKey: ['monitoring-status'],
    queryFn: activityApi.getMonitoringStatus,
    refetchInterval: 10000,
  });
  
  // Mark as read mutation
  const markReadMutation = useMutation({
    mutationFn: activityApi.markRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['activity-feed'] });
    }
  });
  
  // Start/Stop monitoring mutations
  const startMonitoringMutation = useMutation({
    mutationFn: () => activityApi.startMonitoring(30),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['monitoring-status'] });
    }
  });
  
  const stopMonitoringMutation = useMutation({
    mutationFn: activityApi.stopMonitoring,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['monitoring-status'] });
    }
  });
  
  // WebSocket connection for real-time updates
  useEffect(() => {
    let ws: WebSocket | null = null;
    
    const connectWebSocket = () => {
      ws = new WebSocket(`${AI_SERVICE_URL.replace('http', 'ws')}/monitoring/ws`);
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'new_alert') {
          queryClient.invalidateQueries({ queryKey: ['activity-feed'] });
        }
      };
      
      ws.onerror = () => {
        // Silently fail - will use polling instead
      };
    };
    
    connectWebSocket();
    
    return () => {
      if (ws) ws.close();
    };
  }, [queryClient]);
  
  const totalUnread = feedData?.unread_counts 
    ? Object.values(feedData.unread_counts).reduce((a, b) => a + b, 0)
    : 0;
  
  const categories = [
    'VESSEL_TRACKING', 'ETA_PREDICTION', 'BERTH_ALLOCATION', 
    'CONFLICT_DETECTION', 'REOPTIMIZATION', 'WEATHER', 'SYSTEM'
  ];
  
  const severities = ['DEBUG', 'INFO', 'WARNING', 'HIGH', 'CRITICAL'];
  
  return (
    <div 
      className="fixed inset-y-0 right-0 w-[420px] bg-white shadow-2xl z-50 flex flex-col border-l"
      style={{ borderColor: 'var(--border)' }}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b" style={{ borderColor: 'var(--border)' }}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5" style={{ color: 'var(--kale-blue)' }} />
            <h3 className="text-sm font-bold" style={{ color: 'var(--kale-blue)' }}>
              Activity Feed
            </h3>
            {totalUnread > 0 && (
              <span 
                className="px-2 py-0.5 rounded-full text-[10px] font-bold"
                style={{ backgroundColor: 'var(--kale-blue)', color: 'white' }}
              >
                {totalUnread} new
              </span>
            )}
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
              title="Filter"
            >
              <Filter className="w-4 h-4" style={{ color: 'var(--muted-foreground)' }} />
            </button>
            <button
              onClick={() => refetch()}
              className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
              title="Refresh"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} style={{ color: 'var(--muted-foreground)' }} />
            </button>
            <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors" title="Close">
              <X className="w-4 h-4" style={{ color: 'var(--muted-foreground)' }} />
            </button>
          </div>
        </div>
        
        {/* Monitoring Status */}
        <div className="flex items-center justify-between p-2 rounded-lg" style={{ backgroundColor: 'var(--muted)' }}>
          <div className="flex items-center gap-2">
            <div 
              className={`w-2 h-2 rounded-full ${monitoringStatus?.is_active ? 'animate-pulse' : ''}`}
              style={{ backgroundColor: monitoringStatus?.is_active ? 'var(--status-on-time)' : 'var(--muted-foreground)' }}
            />
            <span className="text-[11px]">
              {monitoringStatus?.is_active ? 'Monitoring Active' : 'Monitoring Inactive'}
            </span>
            {monitoringStatus?.alerts_generated_today !== undefined && (
              <span className="text-[10px]" style={{ color: 'var(--muted-foreground)' }}>
                ({monitoringStatus.alerts_generated_today} today)
              </span>
            )}
          </div>
          <button
            onClick={() => monitoringStatus?.is_active 
              ? stopMonitoringMutation.mutate() 
              : startMonitoringMutation.mutate()
            }
            className="text-[10px] px-2 py-1 rounded-lg flex items-center gap-1"
            style={{ 
              backgroundColor: monitoringStatus?.is_active ? 'var(--status-at-risk)' : 'var(--kale-blue)',
              color: 'white'
            }}
          >
            {monitoringStatus?.is_active ? (
              <>
                <Pause className="w-3 h-3" /> Stop
              </>
            ) : (
              <>
                <Play className="w-3 h-3" /> Start
              </>
            )}
          </button>
        </div>
        
        {/* Filters */}
        {showFilters && (
          <div className="mt-3 p-2 rounded-lg border" style={{ borderColor: 'var(--border)' }}>
            <div className="mb-2">
              <label className="text-[10px] font-semibold mb-1 block" style={{ color: 'var(--muted-foreground)' }}>
                Category
              </label>
              <select 
                className="w-full text-[11px] p-1.5 rounded border"
                style={{ borderColor: 'var(--border)' }}
                value={filter.category || ''}
                onChange={(e) => setFilter(f => ({ ...f, category: e.target.value || undefined }))}
              >
                <option value="">All Categories</option>
                {categories.map(cat => (
                  <option key={cat} value={cat}>{cat.replace(/_/g, ' ')}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-[10px] font-semibold mb-1 block" style={{ color: 'var(--muted-foreground)' }}>
                Severity
              </label>
              <select 
                className="w-full text-[11px] p-1.5 rounded border"
                style={{ borderColor: 'var(--border)' }}
                value={filter.severity || ''}
                onChange={(e) => setFilter(f => ({ ...f, severity: e.target.value || undefined }))}
              >
                <option value="">All Severities</option>
                {severities.map(sev => (
                  <option key={sev} value={sev}>{sev}</option>
                ))}
              </select>
            </div>
            {(filter.category || filter.severity) && (
              <button
                onClick={() => setFilter({})}
                className="mt-2 text-[10px] text-blue-600 hover:underline"
              >
                Clear filters
              </button>
            )}
          </div>
        )}
      </div>
      
      {/* Activity List */}
      <div className="flex-1 overflow-auto">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center h-full">
            <RefreshCw className="w-6 h-6 animate-spin mb-2" style={{ color: 'var(--kale-blue)' }} />
            <p className="text-xs" style={{ color: 'var(--muted-foreground)' }}>Loading activities...</p>
          </div>
        ) : !feedData?.activities?.length ? (
          <div className="flex flex-col items-center justify-center h-full p-6">
            <div 
              className="w-12 h-12 rounded-full flex items-center justify-center mb-3"
              style={{ backgroundColor: 'var(--muted)' }}
            >
              <Activity className="w-6 h-6" style={{ color: 'var(--muted-foreground)' }} />
            </div>
            <p className="text-sm font-medium mb-1">No activities yet</p>
            <p className="text-xs text-center" style={{ color: 'var(--muted-foreground)' }}>
              {monitoringStatus?.is_active 
                ? 'Activities will appear here as events occur'
                : 'Start monitoring to see real-time activities'
              }
            </p>
          </div>
        ) : (
          feedData.activities.map(activity => (
            <ActivityItem
              key={activity.id}
              activity={activity}
              onMarkRead={(id) => markReadMutation.mutate(id)}
              onVesselClick={onVesselClick}
              onBerthClick={onBerthClick}
            />
          ))
        )}
      </div>
      
      {/* Footer */}
      <div className="px-4 py-2 border-t" style={{ borderColor: 'var(--border)' }}>
        <div className="flex items-center justify-between text-[10px]" style={{ color: 'var(--muted-foreground)' }}>
          <span>
            {feedData?.activities?.length || 0} activities
          </span>
          <div className="flex items-center gap-2">
            {Object.entries(feedData?.unread_counts || {}).map(([severity, count]) => {
              if (count === 0) return null;
              return (
                <span 
                  key={severity}
                  className="px-1.5 py-0.5 rounded"
                  style={{ 
                    backgroundColor: `${getSeverityColor(severity)}20`,
                    color: getSeverityColor(severity)
                  }}
                >
                  {count} {severity.toLowerCase()}
                </span>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ActivityFeedPanel;
