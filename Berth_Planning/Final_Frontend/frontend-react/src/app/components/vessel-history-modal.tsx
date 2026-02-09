import { X, Ship, Anchor, Clock, TrendingUp, Calendar, CheckCircle2, AlertTriangle } from 'lucide-react';
import type { Vessel } from './upcoming-vessels-timeline';

interface HistoryEvent {
  id: string;
  timestamp: Date;
  type: 'eta_update' | 'berth_allocation' | 'status_change' | 'constraint_update' | 'arrival' | 'departure';
  description: string;
  user?: string;
  details?: Record<string, any>;
}

interface VesselHistoryModalProps {
  vessel: Vessel;
  onClose: () => void;
}

export function VesselHistoryModal({ vessel, onClose }: VesselHistoryModalProps) {
  // Build history from actual vessel data
  const assignedBerth = vessel.aiRecommendation?.suggestedBerth || 'Pending';
  const deviationInfo = vessel.etaDeviation
    ? `${Math.abs(vessel.etaDeviation)} min ${vessel.etaDeviation > 0 ? 'late' : 'early'}`
    : 'On schedule';

  const history: HistoryEvent[] = [
    {
      id: '1',
      timestamp: new Date(vessel.predictedETA.getTime() - 48 * 60 * 60 * 1000),
      type: 'eta_update',
      description: `Initial ETA declared for ${vessel.name}`,
      details: {
        declaredETA: vessel.declaredETA,
      }
    },
    {
      id: '2',
      timestamp: new Date(vessel.predictedETA.getTime() - 36 * 60 * 60 * 1000),
      type: 'eta_update',
      description: `AI predicted ETA updated — ${deviationInfo}`,
      details: {
        previousPredicted: vessel.declaredETA,
        newPredicted: vessel.predictedETA,
        reason: vessel.etaDeviation && vessel.etaDeviation < 0
          ? 'Favorable conditions detected — vessel ahead of schedule'
          : vessel.etaDeviation && vessel.etaDeviation > 0
          ? 'Weather/traffic conditions causing delay'
          : 'Prediction confirmed — vessel on schedule'
      }
    },
    {
      id: '3',
      timestamp: new Date(vessel.predictedETA.getTime() - 24 * 60 * 60 * 1000),
      type: 'constraint_update',
      description: vessel.constraints.length > 0
        ? `Constraint identified: ${vessel.constraints[0]?.type || 'operational'}`
        : 'No active constraints — all checks passed',
      details: {
        constraint: vessel.constraints[0]?.type || 'none',
        status: vessel.constraints.length > 0 ? 'warning' : 'satisfied',
        message: vessel.constraints[0]?.message || 'All operational constraints satisfied'
      }
    },
    ...(vessel.aiRecommendation ? [{
      id: '4',
      timestamp: new Date(vessel.predictedETA.getTime() - 12 * 60 * 60 * 1000),
      type: 'berth_allocation' as const,
      description: `AI recommended ${assignedBerth} allocation`,
      user: 'SmartBerth AI',
      details: {
        berth: assignedBerth,
        confidence: vessel.aiRecommendation.confidence,
        reason: vessel.aiRecommendation.reason
      }
    }] : []),
    {
      id: '5',
      timestamp: new Date(vessel.predictedETA.getTime() - 6 * 60 * 60 * 1000),
      type: 'status_change',
      description: `Status: ${vessel.status.replace('-', ' ')}`,
      details: {
        previousStatus: 'on-time',
        newStatus: vessel.status,
        reason: vessel.status === 'delayed' ? 'Schedule deviation detected'
          : vessel.status === 'at-risk' ? 'Approaching constraint window'
          : vessel.status === 'arrived' ? 'Vessel arrived at port'
          : 'Vessel tracking on schedule'
      }
    },
  ];

  if (vessel.ata) {
    history.push({
      id: '6',
      timestamp: vessel.ata,
      type: 'arrival',
      description: 'Vessel arrived at port',
      details: {
        ata: vessel.ata,
        predictedETA: vessel.predictedETA,
        accuracy: Math.abs(Math.round((vessel.ata.getTime() - vessel.predictedETA.getTime()) / (1000 * 60)))
      }
    });
  }

  // Sort by timestamp descending (newest first)
  const sortedHistory = [...history].sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'eta_update':
        return <Clock className="w-3.5 h-3.5" />;
      case 'berth_allocation':
        return <Anchor className="w-3.5 h-3.5" />;
      case 'status_change':
        return <AlertTriangle className="w-3.5 h-3.5" />;
      case 'constraint_update':
        return <AlertTriangle className="w-3.5 h-3.5" />;
      case 'arrival':
        return <CheckCircle2 className="w-3.5 h-3.5" />;
      case 'departure':
        return <Ship className="w-3.5 h-3.5" />;
      default:
        return <Calendar className="w-3.5 h-3.5" />;
    }
  };

  const getEventColor = (type: string) => {
    switch (type) {
      case 'arrival':
        return 'var(--status-on-time)';
      case 'berth_allocation':
        return 'var(--kale-blue)';
      case 'status_change':
        return 'var(--status-at-risk)';
      case 'constraint_update':
        return 'var(--status-at-risk)';
      case 'eta_update':
        return 'var(--kale-teal)';
      default:
        return 'var(--muted-foreground)';
    }
  };

  const fmtDate = (d: Date) => d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: 'var(--border)' }}>
          <div className="flex items-center gap-2">
            <Ship className="w-4 h-4" style={{ color: 'var(--kale-blue)' }} />
            <h3 className="text-sm" style={{ color: 'var(--kale-blue)', fontWeight: 700 }}>{vessel.name}</h3>
            <span className="text-xs" style={{ color: 'var(--muted-foreground)' }}>• IMO {vessel.imo}</span>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors">
            <X className="w-4 h-4" style={{ color: 'var(--muted-foreground)' }} />
          </button>
        </div>

        {/* Summary Stats - inline */}
        <div className="flex items-center gap-6 px-4 py-2.5 border-b text-xs" style={{ borderColor: 'var(--border)', backgroundColor: 'var(--kale-sky)' }}>
          <div>
            <span style={{ color: 'var(--muted-foreground)' }}>Declared </span>
            <span style={{ fontWeight: 600, color: 'var(--kale-blue)' }}>{fmtDate(vessel.declaredETA)}</span>
          </div>
          <div>
            <span style={{ color: 'var(--muted-foreground)' }}>Predicted </span>
            <span style={{ fontWeight: 600, color: 'var(--kale-blue)' }}>{fmtDate(vessel.predictedETA)}</span>
          </div>
          <div>
            <span style={{ color: 'var(--muted-foreground)' }}>{vessel.ata ? 'Actual ' : 'Status '}</span>
            <span style={{ fontWeight: 600, color: vessel.ata ? 'var(--status-berthed)' : 'var(--kale-blue)' }}>
              {vessel.ata ? fmtDate(vessel.ata) : vessel.status.toUpperCase().replace('-', ' ')}
            </span>
          </div>
        </div>

        {/* Timeline */}
        <div className="flex-1 overflow-auto px-4 py-3">
          <div className="relative">
            {/* Timeline line */}
            <div className="absolute left-[13px] top-0 bottom-0 w-0.5" style={{ backgroundColor: 'var(--border)' }} />

            {/* Events */}
            <div className="space-y-1">
              {sortedHistory.map((event) => (
                <div key={event.id} className="relative pl-9">
                  {/* Icon */}
                  <div
                    className="absolute left-0 w-[26px] h-[26px] rounded-full flex items-center justify-center"
                    style={{
                      backgroundColor: `${getEventColor(event.type)}15`,
                      color: getEventColor(event.type),
                      border: `1.5px solid ${getEventColor(event.type)}`,
                    }}
                  >
                    {getEventIcon(event.type)}
                  </div>

                  {/* Content */}
                  <div className="py-2">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-1.5 min-w-0">
                        <span className="text-xs truncate" style={{ fontWeight: 600 }}>{event.description}</span>
                        {event.user && (
                          <span className="text-[10px] flex-shrink-0" style={{ color: 'var(--muted-foreground)' }}>
                            by {event.user}
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] flex-shrink-0" style={{ color: 'var(--muted-foreground)' }}>
                        {fmtDate(event.timestamp)}
                      </span>
                    </div>

                    {/* Event Details - compact */}
                    {event.details && (
                      <div className="mt-1.5 px-2.5 py-1.5 rounded text-xs" style={{ backgroundColor: 'var(--muted)' }}>
                        {event.type === 'eta_update' && event.details.reason && (
                          <span style={{ color: 'var(--foreground)' }}>{event.details.reason}</span>
                        )}
                        {event.type === 'berth_allocation' && (
                          <div className="flex items-center gap-3 flex-wrap">
                            <span>
                              <span style={{ color: 'var(--muted-foreground)' }}>Berth: </span>
                              <span style={{ fontWeight: 600 }}>{event.details.berth}</span>
                            </span>
                            <span>
                              <span style={{ color: 'var(--muted-foreground)' }}>Confidence: </span>
                              <span style={{ fontWeight: 600, color: 'var(--kale-teal)' }}>{event.details.confidence}%</span>
                            </span>
                            {event.details.reason && (
                              <span style={{ color: 'var(--muted-foreground)' }}>— {event.details.reason}</span>
                            )}
                          </div>
                        )}
                        {event.type === 'status_change' && (
                          <div className="flex items-center gap-2">
                            <span className="px-1.5 py-0.5 rounded text-[10px] capitalize"
                              style={{ backgroundColor: 'var(--status-on-time)', color: 'white' }}>
                              {event.details.previousStatus}
                            </span>
                            <span className="text-[10px]">→</span>
                            <span className="px-1.5 py-0.5 rounded text-[10px] capitalize"
                              style={{ backgroundColor: 'var(--status-at-risk)', color: 'white' }}>
                              {event.details.newStatus}
                            </span>
                          </div>
                        )}
                        {event.type === 'constraint_update' && event.details.message && (
                          <span style={{ color: 'var(--foreground)' }}>{event.details.message}</span>
                        )}
                        {event.type === 'arrival' && (
                          <div className="flex items-center gap-3">
                            <div className="flex items-center gap-1">
                              <TrendingUp className="w-3 h-3" style={{ color: 'var(--status-on-time)' }} />
                              <span style={{ fontWeight: 600, color: 'var(--status-on-time)' }}>
                                Within {event.details.accuracy} min
                              </span>
                            </div>
                            <span style={{ color: 'var(--muted-foreground)' }}>
                              Predicted {new Date(event.details.predictedETA).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                            <span style={{ color: 'var(--muted-foreground)' }}>
                              Actual {new Date(event.details.ata).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-4 py-2.5 border-t" style={{ borderColor: 'var(--border)' }}>
          <span className="text-xs" style={{ color: 'var(--muted-foreground)' }}>
            {sortedHistory.length} events
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
