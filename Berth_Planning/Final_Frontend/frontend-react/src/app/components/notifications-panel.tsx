import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { X, AlertTriangle, Clock, CheckCircle2, Ship, AlertCircle, Zap, RefreshCw, Brain, ChevronRight, Shield, Loader2 } from 'lucide-react';
import { dashboardService, aiService } from '../../api';
import type { AIConflict } from '../../types';

interface Alert {
  id: string;
  type: 'arrival' | 'delay' | 'constraint' | 'success' | 'warning';
  vessel?: string;
  title: string;
  message: string;
  timestamp: Date;
  isRead: boolean;
}

interface NotificationsPanelProps {
  onClose: () => void;
  onVesselClick?: (vesselId: string) => void;
  onBerthClick?: (berthId: string) => void;
}

function mapAPIAlertType(alertType: string): Alert['type'] {
  const t = alertType?.toLowerCase() || '';
  if (t.includes('arrival') || t.includes('eta')) return 'arrival';
  if (t.includes('delay')) return 'delay';
  if (t.includes('constraint') || t.includes('conflict')) return 'constraint';
  if (t.includes('success') || t.includes('complete')) return 'success';
  return 'warning';
}

export function NotificationsPanel({ onClose, onVesselClick, onBerthClick }: NotificationsPanelProps) {
  const queryClient = useQueryClient();
  
  const { data: apiAlerts } = useQuery({
    queryKey: ['alerts'],
    queryFn: dashboardService.getAlerts,
  });

  // AI Conflict Detection Query
  const { 
    data: conflictsData, 
    isLoading: conflictsLoading,
    error: conflictsError,
    refetch: refetchConflicts 
  } = useQuery({
    queryKey: ['ai-conflicts'],
    queryFn: () => aiService.detectConflicts(48),
    refetchInterval: 60000, // Refresh every minute
    staleTime: 30000,
  });

  // Resolve Conflict Mutation
  const resolveConflictMutation = useMutation({
    mutationFn: ({ conflictId, action }: { conflictId: number; action: string }) => 
      aiService.resolveConflict(conflictId, action),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-conflicts'] });
    },
  });

  const [alerts, setAlerts] = useState<Alert[]>(generateSampleAlerts());

  useEffect(() => {
    if (apiAlerts && Array.isArray(apiAlerts) && apiAlerts.length > 0) {
      const mapped: Alert[] = apiAlerts.map((a: any, i: number) => ({
        id: String(a.alertId ?? a.id ?? `api-${i}`),
        type: mapAPIAlertType(a.alertType ?? a.type ?? ''),
        vessel: a.vesselName ?? a.vessel,
        title: a.title ?? a.alertType ?? 'Alert',
        message: a.message ?? a.description ?? '',
        timestamp: a.createdAt ? new Date(a.createdAt) : new Date(),
        isRead: a.isResolved ?? a.isRead ?? false,
      }));
      setAlerts(mapped);
    }
  }, [apiAlerts]);
  const [filter, setFilter] = useState<'all' | 'unread' | 'conflicts'>('all');

  const unreadCount = alerts.filter(a => !a.isRead).length;
  const conflictsCount = conflictsData?.conflicts?.length || 0;

  const handleMarkAsRead = (id: string) => {
    setAlerts(prev => prev.map(a => a.id === id ? { ...a, isRead: true } : a));
  };

  const handleMarkAllAsRead = () => {
    setAlerts(prev => prev.map(a => ({ ...a, isRead: true })));
  };

  const handleClearAll = () => {
    setAlerts([]);
  };

  const handleResolveConflict = (conflictId: string, action: string) => {
    resolveConflictMutation.mutate({ 
      conflictId: parseInt(conflictId), 
      action 
    });
  };

  const filteredAlerts = filter === 'unread' ? alerts.filter(a => !a.isRead) : alerts;

  const getSeverityColor = (severity: string) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL': return 'var(--status-critical)';
      case 'HIGH': return 'var(--status-at-risk)';
      case 'MEDIUM': return 'var(--status-delayed)';
      case 'LOW': return 'var(--kale-blue)';
      default: return 'var(--muted-foreground)';
    }
  };

  const getAlertIcon = (type: Alert['type']) => {
    switch (type) {
      case 'arrival': return <Ship className="w-3.5 h-3.5" />;
      case 'delay': return <Clock className="w-3.5 h-3.5" />;
      case 'constraint': return <AlertTriangle className="w-3.5 h-3.5" />;
      case 'success': return <CheckCircle2 className="w-3.5 h-3.5" />;
      case 'warning': return <AlertCircle className="w-3.5 h-3.5" />;
    }
  };

  const getAlertColor = (type: Alert['type']) => {
    switch (type) {
      case 'arrival': return 'var(--kale-blue)';
      case 'delay': return 'var(--status-at-risk)';
      case 'constraint': return 'var(--status-critical)';
      case 'success': return 'var(--status-on-time)';
      case 'warning': return 'var(--status-at-risk)';
    }
  };

  const formatTimestamp = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-white shadow-2xl z-50 flex flex-col border-l"
      style={{ borderColor: 'var(--border)' }}>
      {/* Header */}
      <div className="px-3 py-2.5 border-b" style={{ borderColor: 'var(--border)' }}>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <h3 className="text-sm" style={{ color: 'var(--kale-blue)', fontWeight: 700 }}>Notifications & Conflicts</h3>
            <span className="px-1.5 py-0.5 rounded-full text-[10px]" style={{ backgroundColor: 'var(--kale-blue)', color: 'white', fontWeight: 700 }}>
              {unreadCount + conflictsCount}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <button 
              onClick={() => refetchConflicts()} 
              className="p-1 rounded-lg hover:bg-gray-100 transition-colors"
              title="Refresh Conflicts"
            >
              <RefreshCw className={`w-4 h-4 ${conflictsLoading ? 'animate-spin' : ''}`} style={{ color: 'var(--muted-foreground)' }} />
            </button>
            <button onClick={onClose} className="p-1 rounded-lg hover:bg-gray-100 transition-colors" title="Close">
              <X className="w-4 h-4" style={{ color: 'var(--muted-foreground)' }} />
            </button>
          </div>
        </div>

        {/* Filter Tabs + Actions inline */}
        <div className="flex items-center justify-between">
          <div className="flex gap-1">
            <button
              onClick={() => setFilter('all')}
              className="px-2 py-1 rounded text-[11px] transition-colors"
              style={{
                backgroundColor: filter === 'all' ? 'var(--kale-blue)' : 'transparent',
                color: filter === 'all' ? 'white' : 'var(--foreground)',
                fontWeight: filter === 'all' ? 600 : 400,
              }}
            >
              All ({alerts.length})
            </button>
            <button
              onClick={() => setFilter('conflicts')}
              className="px-2 py-1 rounded text-[11px] transition-colors flex items-center gap-1"
              style={{
                backgroundColor: filter === 'conflicts' ? 'var(--status-at-risk)' : 'transparent',
                color: filter === 'conflicts' ? 'white' : 'var(--foreground)',
                fontWeight: filter === 'conflicts' ? 600 : 400,
              }}
            >
              <Shield className="w-3 h-3" />
              Conflicts ({conflictsCount})
            </button>
            <button
              onClick={() => setFilter('unread')}
              className="px-2 py-1 rounded text-[11px] transition-colors"
              style={{
                backgroundColor: filter === 'unread' ? 'var(--kale-blue)' : 'transparent',
                color: filter === 'unread' ? 'white' : 'var(--foreground)',
                fontWeight: filter === 'unread' ? 600 : 400,
              }}
            >
              Unread ({unreadCount})
            </button>
          </div>
          {filteredAlerts.length > 0 && (
            <div className="flex gap-1">
              <button onClick={handleMarkAllAsRead} className="text-[10px] px-1.5 py-0.5 rounded hover:bg-gray-100"
                style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
                Read all
              </button>
              <button onClick={handleClearAll} className="text-[10px] px-1.5 py-0.5 rounded hover:bg-gray-100"
                style={{ color: 'var(--muted-foreground)' }}>
                Clear
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Alerts List */}
      <div className="flex-1 overflow-auto">
        {/* AI Conflicts Section */}
        {filter === 'conflicts' && (
          <div className="p-3">
            {conflictsLoading ? (
              <div className="flex flex-col items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin mb-2" style={{ color: 'var(--kale-blue)' }} />
                <p className="text-xs" style={{ color: 'var(--muted-foreground)' }}>Detecting conflicts...</p>
              </div>
            ) : conflictsError ? (
              <div className="flex flex-col items-center justify-center py-8">
                <AlertCircle className="w-6 h-6 mb-2" style={{ color: 'var(--status-at-risk)' }} />
                <p className="text-xs" style={{ color: 'var(--muted-foreground)' }}>Failed to load conflicts</p>
                <button 
                  onClick={() => refetchConflicts()} 
                  className="mt-2 text-xs px-3 py-1 rounded-lg"
                  style={{ backgroundColor: 'var(--kale-blue)', color: 'white' }}
                >
                  Retry
                </button>
              </div>
            ) : conflictsCount === 0 ? (
              <div className="flex flex-col items-center justify-center py-8">
                <div className="w-12 h-12 rounded-full flex items-center justify-center mb-2"
                  style={{ backgroundColor: 'var(--status-on-time)20' }}>
                  <CheckCircle2 className="w-6 h-6" style={{ color: 'var(--status-on-time)' }} />
                </div>
                <p className="text-sm font-semibold" style={{ color: 'var(--status-on-time)' }}>No Conflicts Detected</p>
                <p className="text-xs mt-1" style={{ color: 'var(--muted-foreground)' }}>
                  AI monitoring 48-hour window
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Brain className="w-4 h-4" style={{ color: 'var(--kale-blue)' }} />
                    <span className="text-xs font-semibold">AI Conflict Analysis</span>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded-full" 
                    style={{ backgroundColor: 'var(--status-at-risk)20', color: 'var(--status-at-risk)' }}>
                    {conflictsData?.time_window_hours}h window
                  </span>
                </div>
                
                {conflictsData?.conflicts?.map((conflict: AIConflict) => (
                  <div 
                    key={conflict.conflictId}
                    className="p-3 rounded-xl border"
                    style={{ 
                      borderColor: getSeverityColor(conflict.severity),
                      backgroundColor: `${getSeverityColor(conflict.severity)}08`
                    }}
                  >
                    <div className="flex items-start gap-2">
                      <div 
                        className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0"
                        style={{ backgroundColor: `${getSeverityColor(conflict.severity)}20` }}
                      >
                        <AlertTriangle className="w-3.5 h-3.5" style={{ color: getSeverityColor(conflict.severity) }} />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-semibold">{conflict.type}</span>
                          <span 
                            className="text-[10px] px-1.5 py-0.5 rounded font-semibold"
                            style={{ 
                              backgroundColor: getSeverityColor(conflict.severity),
                              color: 'white'
                            }}
                          >
                            {conflict.severity}
                          </span>
                        </div>
                        <p className="text-[11px] mb-2" style={{ color: 'var(--muted-foreground)' }}>
                          {conflict.description}
                        </p>
                        
                        {/* Affected Entities */}
                        {conflict.affectedVessels?.length > 0 && (
                          <div className="flex flex-wrap gap-1 mb-2">
                            {conflict.affectedVessels.map((vesselId: number) => (
                              <button
                                key={vesselId}
                                onClick={() => onVesselClick?.(vesselId.toString())}
                                className="text-[10px] px-1.5 py-0.5 rounded-full flex items-center gap-1 hover:opacity-80"
                                style={{ backgroundColor: 'var(--kale-sky)', color: 'var(--kale-blue)' }}
                              >
                                <Ship className="w-2.5 h-2.5" />
                                Vessel {vesselId}
                              </button>
                            ))}
                          </div>
                        )}
                        
                        {/* Suggested Resolution */}
                        {conflict.suggestedResolution && (
                          <div className="p-2 rounded-lg mb-2" style={{ backgroundColor: 'var(--muted)' }}>
                            <div className="flex items-center gap-1 mb-1">
                              <Zap className="w-3 h-3" style={{ color: 'var(--kale-teal)' }} />
                              <span className="text-[10px] font-semibold" style={{ color: 'var(--kale-teal)' }}>
                                AI Recommendation
                              </span>
                            </div>
                            <p className="text-[10px]" style={{ color: 'var(--foreground)' }}>
                              {conflict.suggestedResolution}
                            </p>
                          </div>
                        )}
                        
                        {/* Action Buttons */}
                        <div className="flex gap-2">
                          {conflict.autoResolvable && (
                            <button
                              onClick={() => handleResolveConflict(conflict.conflictId, 'auto')}
                              disabled={resolveConflictMutation.isPending}
                              className="text-[10px] px-2 py-1 rounded-lg flex items-center gap-1"
                              style={{ backgroundColor: 'var(--kale-blue)', color: 'white' }}
                            >
                              {resolveConflictMutation.isPending ? (
                                <Loader2 className="w-3 h-3 animate-spin" />
                              ) : (
                                <Zap className="w-3 h-3" />
                              )}
                              Auto-Resolve
                            </button>
                          )}
                          <button
                            onClick={() => handleResolveConflict(conflict.conflictId, 'acknowledge')}
                            className="text-[10px] px-2 py-1 rounded-lg"
                            style={{ backgroundColor: 'var(--muted)', color: 'var(--foreground)' }}
                          >
                            Acknowledge
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Standard Alerts Section */}
        {filter !== 'conflicts' && (
          <>
            {filteredAlerts.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full p-6 text-center">
                <div className="w-10 h-10 rounded-full flex items-center justify-center mb-2"
                  style={{ backgroundColor: 'var(--muted)' }}>
                  <CheckCircle2 className="w-5 h-5" style={{ color: 'var(--muted-foreground)' }} />
                </div>
                <p className="text-xs" style={{ color: 'var(--muted-foreground)' }}>
                  {filter === 'unread' ? 'No unread notifications' : 'No notifications'}
                </p>
              </div>
            ) : (
              <div className="divide-y" style={{ borderColor: 'var(--border)' }}>
                {filteredAlerts.map((alert) => (
                  <div
                    key={alert.id}
                    onClick={() => handleMarkAsRead(alert.id)}
                    className="px-3 py-2 cursor-pointer hover:bg-gray-50 transition-colors"
                    style={{
                      backgroundColor: alert.isRead ? 'transparent' : 'var(--kale-sky)',
                    }}
                  >
                    <div className="flex gap-2">
                      <div
                        className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
                        style={{ backgroundColor: `${getAlertColor(alert.type)}20` }}
                      >
                        <div style={{ color: getAlertColor(alert.type) }}>
                          {getAlertIcon(alert.type)}
                        </div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-1 mb-0.5">
                          <div className="flex items-center gap-1 min-w-0">
                            <span className="text-xs truncate" style={{ fontWeight: 600 }}>{alert.title}</span>
                            {!alert.isRead && (
                              <div className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                                style={{ backgroundColor: 'var(--kale-blue)' }} />
                            )}
                          </div>
                          <span className="text-[10px] flex-shrink-0" style={{ color: 'var(--muted-foreground)' }}>
                            {formatTimestamp(alert.timestamp)}
                          </span>
                        </div>
                        {alert.vessel && (
                          <div className="text-[10px] mb-0.5" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
                            {alert.vessel}
                          </div>
                        )}
                        <p className="text-[11px] leading-tight" style={{ color: 'var(--muted-foreground)' }}>
                          {alert.message}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function generateSampleAlerts(): Alert[] {
  const now = new Date();
  return [
    {
      id: 'A1',
      type: 'arrival',
      vessel: 'MSC GULSUN',
      title: 'Vessel Arrival Update',
      message: 'Updated ETA: Feb 4, 14:30 (30 min early). Berth 1 prepared.',
      timestamp: new Date(now.getTime() - 2 * 60000),
      isRead: false,
    },
    {
      id: 'A2',
      type: 'delay',
      vessel: 'MAERSK ESSEX',
      title: 'Berthing Delay',
      message: 'Delayed by 45 minutes due to tug availability. New ETA: Feb 4, 16:15.',
      timestamp: new Date(now.getTime() - 15 * 60000),
      isRead: false,
    },
    {
      id: 'A3',
      type: 'constraint',
      vessel: 'CMA CGM MARCO POLO',
      title: 'Wind Speed Constraint',
      message: 'Wind speed 28 knots. Crane operations suspended. Monitoring conditions.',
      timestamp: new Date(now.getTime() - 22 * 60000),
      isRead: false,
    },
    {
      id: 'A4',
      type: 'warning',
      vessel: 'EVER GIVEN',
      title: 'Draft Restriction Warning',
      message: 'Vessel draft 15.8m exceeds low tide limit. Berthing scheduled for high tide at 18:30.',
      timestamp: new Date(now.getTime() - 35 * 60000),
      isRead: true,
    },
    {
      id: 'A5',
      type: 'success',
      vessel: 'COSCO SHIPPING UNIVERSE',
      title: 'Berthing Completed',
      message: 'Successfully berthed at Berth 3. Cargo operations commenced. ATA accuracy: 98%.',
      timestamp: new Date(now.getTime() - 48 * 60000),
      isRead: true,
    },
    {
      id: 'A6',
      type: 'constraint',
      title: 'Night-time Noise Restriction',
      message: 'Night hours (22:00-06:00) noise restriction in effect. Reduce cargo operations.',
      timestamp: new Date(now.getTime() - 62 * 60000),
      isRead: true,
    },
    {
      id: 'A7',
      type: 'arrival',
      vessel: 'OOCL HONG KONG',
      title: 'Vessel ETA Confirmed',
      message: 'ETA confirmed: Feb 5, 08:45. AI recommended Berth 2 (confidence: 94%).',
      timestamp: new Date(now.getTime() - 95 * 60000),
      isRead: true,
    },
    {
      id: 'A8',
      type: 'warning',
      vessel: 'MOL TRIUMPH',
      title: 'Hazmat Cargo Alert',
      message: 'Vessel carrying IMDG Class 1 dangerous goods. Allocated to dedicated Berth 5 with 50m buffer.',
      timestamp: new Date(now.getTime() - 120 * 60000),
      isRead: true,
    },
    {
      id: 'A9',
      type: 'success',
      title: 'System Integration Update',
      message: 'Maritime Single Window sync completed. 12 new vessel calls imported.',
      timestamp: new Date(now.getTime() - 180 * 60000),
      isRead: true,
    },
    {
      id: 'A10',
      type: 'arrival',
      vessel: 'HAMBURG SÜD CAP SAN LORENZO',
      title: 'Early Arrival Alert',
      message: 'Vessel arriving 2 hours early. Berth 4 currently occupied. Estimated berth ready: Feb 4, 20:00.',
      timestamp: new Date(now.getTime() - 240 * 60000),
      isRead: true,
    },
  ];
}
