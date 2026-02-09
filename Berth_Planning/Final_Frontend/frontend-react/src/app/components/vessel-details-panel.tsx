import { X, Ship, Anchor, Calendar, Package, AlertTriangle, CheckCircle2, Clock, Zap, History, Info, Brain, Loader2, RefreshCw } from 'lucide-react';
import type { Vessel } from './upcoming-vessels-timeline';
import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { aiService } from '../../api';

interface VesselDetailsPanelProps {
  vessel: Vessel | null;
  onClose: () => void;
  onAcceptRecommendation?: (vessel: Vessel) => void;
  onModifyAllocation?: (vessel: Vessel) => void;
  onViewHistory?: (vessel: Vessel) => void;
}

export function VesselDetailsPanel({ vessel, onClose, onAcceptRecommendation, onModifyAllocation, onViewHistory }: VesselDetailsPanelProps) {
  if (!vessel) return null;

  const formatDateTime = (date: Date) => {
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getConstraintIcon = (type: string) => {
    switch (type) {
      case 'pilot':
        return '👨‍✈️';
      case 'tug':
        return '🚢';
      case 'tide':
        return '🌊';
      case 'berth':
        return '⚓';
      case 'cargo':
        return '📦';
      case 'weather':
        return '🌤️';
      case 'draft':
        return '📏';
      default:
        return '•';
    }
  };

  const getConstraintStatusColor = (status: string) => {
    switch (status) {
      case 'satisfied':
        return 'var(--status-on-time)';
      case 'warning':
        return 'var(--status-at-risk)';
      case 'critical':
        return 'var(--status-critical)';
      default:
        return 'var(--muted-foreground)';
    }
  };

  const getConstraintStatusIcon = (status: string) => {
    switch (status) {
      case 'satisfied':
        return <CheckCircle2 className="w-4 h-4" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4" />;
      case 'critical':
        return <AlertTriangle className="w-4 h-4 animate-pulse" />;
      default:
        return <Info className="w-4 h-4" />;
    }
  };

  const [isEditing, setIsEditing] = useState(false);
  const [newETA, setNewETA] = useState(vessel.declaredETA);
  const [showPredictedETATooltip, setShowPredictedETATooltip] = useState(false);
  const [showConfidenceTooltip, setShowConfidenceTooltip] = useState(false);
  const [showAIAnalysis, setShowAIAnalysis] = useState(false);
  
  const queryClient = useQueryClient();
  
  // AI Multi-Agent Analysis
  const { 
    data: aiAnalysis, 
    isLoading: aiAnalysisLoading,
    error: aiAnalysisError,
    refetch: refetchAIAnalysis
  } = useQuery({
    queryKey: ['ai-vessel-analysis', vessel.id],
    queryFn: () => aiService.processArrival(parseInt(vessel.id, 10)),
    enabled: showAIAnalysis,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
  
  // AI Berth Suggestions
  const {
    data: berthSuggestions,
    isLoading: suggestionsLoading,
  } = useQuery({
    queryKey: ['ai-berth-suggestions', vessel.id],
    queryFn: () => aiService.getBerthSuggestions(parseInt(vessel.id, 10), undefined, 3),
    enabled: showAIAnalysis,
    staleTime: 5 * 60 * 1000,
  });

  const handleRunAIAnalysis = useCallback(() => {
    setShowAIAnalysis(true);
    if (aiAnalysis) {
      refetchAIAnalysis();
    }
  }, [aiAnalysis, refetchAIAnalysis]);

  return (
    <div className="fixed inset-y-0 right-0 w-full md:w-[480px] bg-white shadow-2xl z-50 flex flex-col animate-slide-in">
      {/* Header */}
      <div className="flex items-start justify-between p-6 border-b" style={{ borderColor: 'var(--border)', backgroundColor: 'var(--kale-sky)' }}>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <Ship className="w-5 h-5" style={{ color: 'var(--kale-blue)' }} />
            <h2 style={{ color: 'var(--kale-blue)' }}>{vessel.name}</h2>
          </div>
          <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--muted-foreground)' }}>
            <span>IMO {vessel.imo}</span>
            <span>•</span>
            <span>{vessel.flag}</span>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-2 rounded-lg hover:bg-white/50 transition-colors"
          aria-label="Close"
        >
          <X className="w-5 h-5" style={{ color: 'var(--kale-blue)' }} />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {/* ETAs - Swapped: AI Predicted first, Declared second */}
        <div className="grid grid-cols-2 gap-3 px-4 pt-4">
          <div className="relative p-3 rounded-lg border" style={{
            borderColor: 'var(--kale-blue)',
            backgroundColor: 'var(--kale-sky)',
          }}>
            <div className="flex items-center gap-1.5 mb-1 cursor-help"
              onMouseEnter={() => setShowPredictedETATooltip(true)}
              onMouseLeave={() => setShowPredictedETATooltip(false)}>
              <Zap className="w-3.5 h-3.5" style={{ color: 'var(--kale-blue)' }} />
              <span className="text-xs" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>AI Predicted ETA</span>
              <Info className="w-3 h-3" style={{ color: 'var(--kale-blue)', opacity: 0.6 }} />
            </div>
            {showPredictedETATooltip && (
              <div className="absolute left-0 top-full mt-1 z-50 w-64">
                <div className="w-3 h-3 rotate-45 ml-6 -mb-1.5" style={{ backgroundColor: 'var(--kale-blue)' }} />
                <div className="rounded-lg shadow-xl p-3" style={{ backgroundColor: 'var(--kale-blue)', color: 'white' }}>
                  <div className="text-xs mb-2" style={{ fontWeight: 700 }}>Prediction Criteria</div>
                  <div className="space-y-1.5">
                    {[
                      { label: 'AIS Tracking Data', pct: 30, icon: '📡' },
                      { label: 'Weather & Sea Conditions', pct: 25, icon: '🌊' },
                      { label: 'Historical Performance', pct: 20, icon: '📊' },
                      { label: 'Port Traffic Analysis', pct: 15, icon: '🚢' },
                      { label: 'Route & Distance', pct: 10, icon: '🗺️' },
                    ].map((item) => (
                      <div key={item.label} className="flex items-center gap-2">
                        <span className="text-[10px]">{item.icon}</span>
                        <div className="flex-1">
                          <div className="flex justify-between text-[10px] mb-0.5">
                            <span style={{ opacity: 0.9 }}>{item.label}</span>
                            <span style={{ fontWeight: 700 }}>{item.pct}%</span>
                          </div>
                          <div className="h-1 rounded-full" style={{ backgroundColor: 'rgba(255,255,255,0.2)' }}>
                            <div className="h-1 rounded-full" style={{ width: `${item.pct}%`, backgroundColor: 'var(--kale-teal)' }} />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
            <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--kale-blue)' }}>
              {formatDateTime(vessel.predictedETA)}
            </div>
            {vessel.etaDeviation !== 0 && (
              <div className="flex items-center gap-1 mt-1 text-[11px]" style={{
                color: vessel.etaDeviation > 0 ? 'var(--status-delayed)' : 'var(--status-on-time)',
              }}>
                <Clock className="w-3 h-3" />
                <span>{vessel.etaDeviation > 0 ? '+' : ''}{vessel.etaDeviation} min</span>
              </div>
            )}
          </div>
          <div className="p-3 rounded-lg bg-white border" style={{ borderColor: 'var(--border)' }}>
            <div className="flex items-center gap-1.5 mb-1">
              <Calendar className="w-3.5 h-3.5" style={{ color: 'var(--muted-foreground)' }} />
              <span className="text-xs" style={{ color: 'var(--muted-foreground)' }}>Declared ETA</span>
            </div>
            <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>
              {formatDateTime(vessel.declaredETA)}
            </div>
          </div>
        </div>

        {/* AI Recommendation - compact */}
        {vessel.aiRecommendation && (
          <div className="mx-4 mt-3 p-3 rounded-lg" style={{ backgroundColor: 'var(--kale-sky)' }}>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4" style={{ color: 'var(--kale-blue)' }} />
                <span className="text-sm" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>AI Recommended Berth</span>
              </div>
              <div className="relative">
                <div className="px-2 py-0.5 rounded-full text-xs cursor-help"
                  style={{
                    backgroundColor: vessel.aiRecommendation.confidence >= 90 ? 'var(--status-on-time)' :
                                   vessel.aiRecommendation.confidence >= 75 ? 'var(--kale-teal)' : 'var(--status-at-risk)',
                    color: 'white',
                    fontWeight: 700,
                  }}
                  onMouseEnter={() => setShowConfidenceTooltip(true)}
                  onMouseLeave={() => setShowConfidenceTooltip(false)}
                >
                  {vessel.aiRecommendation.confidence}%
                </div>
                {showConfidenceTooltip && (
                  <div className="absolute right-0 top-full mt-1 z-50 w-56">
                    <div className="w-3 h-3 rotate-45 mr-3 ml-auto -mb-1.5" style={{ backgroundColor: 'var(--kale-blue)' }} />
                    <div className="rounded-lg shadow-xl p-3" style={{ backgroundColor: 'var(--kale-blue)', color: 'white' }}>
                      <div className="text-xs mb-2" style={{ fontWeight: 700 }}>Confidence Breakdown</div>
                      <div className="space-y-1.5">
                        {[
                          { label: 'Berth Compatibility', pct: 95 },
                          { label: 'Schedule Optimization', pct: 88 },
                          { label: 'Resource Availability', pct: 82 },
                        ].map((item) => (
                          <div key={item.label}>
                            <div className="flex justify-between text-[10px] mb-0.5">
                              <span style={{ opacity: 0.9 }}>{item.label}</span>
                              <span style={{ fontWeight: 700 }}>{item.pct}%</span>
                            </div>
                            <div className="h-1 rounded-full" style={{ backgroundColor: 'rgba(255,255,255,0.2)' }}>
                              <div className="h-1 rounded-full" style={{ width: `${item.pct}%`, backgroundColor: 'var(--kale-teal)' }} />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="p-2.5 rounded bg-white border" style={{ borderColor: 'var(--kale-teal)' }}>
              <div className="flex items-center justify-between mb-2">
                <div style={{ fontWeight: 600, color: 'var(--kale-blue)' }}>
                  {vessel.aiRecommendation.suggestedBerth}
                </div>
              </div>
              <p className="text-xs mb-2" style={{ color: 'var(--muted-foreground)' }}>
                {vessel.aiRecommendation.reason}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => onAcceptRecommendation?.(vessel)}
                  className="flex-1 px-3 py-1.5 rounded-md transition-colors text-xs"
                  style={{ backgroundColor: 'var(--kale-blue)', color: 'white', fontWeight: 600 }}
                >
                  Accept
                </button>
                <button
                  onClick={() => onModifyAllocation?.(vessel)}
                  className="px-3 py-1.5 rounded-md transition-colors text-xs border"
                  style={{ borderColor: 'var(--border)', color: 'var(--kale-blue)', fontWeight: 600 }}
                >
                  Modify
                </button>
              </div>
            </div>
          </div>
        )}

        {/* AI Multi-Agent Analysis Panel */}
        <div className="mx-4 mt-3 p-3 rounded-lg border" style={{ borderColor: 'var(--kale-teal)', backgroundColor: 'white' }}>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Brain className="w-4 h-4" style={{ color: 'var(--kale-teal)' }} />
              <span className="text-sm font-semibold" style={{ color: 'var(--kale-blue)' }}>AI Analysis</span>
            </div>
            <button
              onClick={handleRunAIAnalysis}
              disabled={aiAnalysisLoading}
              className="flex items-center gap-1 px-2 py-1 rounded text-xs transition-colors"
              style={{ 
                backgroundColor: aiAnalysisLoading ? 'var(--muted)' : 'var(--kale-teal)', 
                color: 'white',
                fontWeight: 600 
              }}
            >
              {aiAnalysisLoading ? (
                <>
                  <Loader2 className="w-3 h-3 animate-spin" />
                  Analyzing...
                </>
              ) : showAIAnalysis ? (
                <>
                  <RefreshCw className="w-3 h-3" />
                  Refresh
                </>
              ) : (
                <>
                  <Zap className="w-3 h-3" />
                  Run Analysis
                </>
              )}
            </button>
          </div>
          
          {!showAIAnalysis ? (
            <div className="text-center py-4">
              <Brain className="w-8 h-8 mx-auto mb-2" style={{ color: 'var(--muted-foreground)', opacity: 0.5 }} />
              <p className="text-xs" style={{ color: 'var(--muted-foreground)' }}>
                Click "Run Analysis" to get AI-powered insights from the multi-agent system
              </p>
            </div>
          ) : aiAnalysisLoading || suggestionsLoading ? (
            <div className="text-center py-4">
              <div className="flex items-center justify-center gap-2 mb-2">
                <Loader2 className="w-5 h-5 animate-spin" style={{ color: 'var(--kale-teal)' }} />
              </div>
              <p className="text-xs" style={{ color: 'var(--muted-foreground)' }}>
                Multi-agent system processing...
              </p>
              <div className="mt-2 space-y-1 text-[10px]" style={{ color: 'var(--muted-foreground)' }}>
                <div className="flex items-center gap-1 justify-center">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" /> ETA Prediction Agent
                </div>
                <div className="flex items-center gap-1 justify-center">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" /> Berth Allocation Agent
                </div>
                <div className="flex items-center gap-1 justify-center">
                  <span className="w-1.5 h-1.5 rounded-full bg-purple-500 animate-pulse" /> Constraint Checker Agent
                </div>
              </div>
            </div>
          ) : aiAnalysisError ? (
            <div className="text-center py-4">
              <AlertTriangle className="w-6 h-6 mx-auto mb-2" style={{ color: 'var(--status-at-risk)' }} />
              <p className="text-xs" style={{ color: 'var(--status-at-risk)' }}>
                Failed to get AI analysis
              </p>
              <button
                onClick={() => refetchAIAnalysis()}
                className="mt-2 text-xs px-3 py-1 rounded"
                style={{ backgroundColor: 'var(--kale-blue)', color: 'white' }}
              >
                Retry
              </button>
            </div>
          ) : aiAnalysis ? (
            <div className="space-y-3">
              {/* Agent Recommendations Summary */}
              <div className="grid grid-cols-2 gap-2">
                <div className="p-2 rounded" style={{ backgroundColor: 'var(--kale-sky)' }}>
                  <div className="text-[10px] uppercase font-semibold mb-1" style={{ color: 'var(--muted-foreground)' }}>
                    Predicted ETA
                  </div>
                  <div className="text-sm font-bold" style={{ color: 'var(--kale-blue)' }}>
                    {aiAnalysis.recommendation?.predicted_eta ? new Date(aiAnalysis.recommendation.predicted_eta).toLocaleString('en-US', {
                      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                    }) : 'N/A'}
                  </div>
                </div>
                <div className="p-2 rounded" style={{ backgroundColor: 'var(--kale-sky)' }}>
                  <div className="text-[10px] uppercase font-semibold mb-1" style={{ color: 'var(--muted-foreground)' }}>
                    Confidence
                  </div>
                  <div className="text-sm font-bold" style={{ 
                    color: ((aiAnalysis.recommendation?.eta_confidence || 0) * 100) >= 85 ? 'var(--status-on-time)' : 
                           ((aiAnalysis.recommendation?.eta_confidence || 0) * 100) >= 70 ? 'var(--status-at-risk)' : 'var(--status-delayed)'
                  }}>
                    {aiAnalysis.recommendation?.eta_confidence != null ? (aiAnalysis.recommendation.eta_confidence * 100).toFixed(0) : 'N/A'}%
                  </div>
                </div>
              </div>
              
              {/* Berth Suggestions from AI */}
              {berthSuggestions && berthSuggestions.length > 0 && (
                <div>
                  <div className="text-[10px] uppercase font-semibold mb-2" style={{ color: 'var(--muted-foreground)' }}>
                    AI Berth Suggestions
                  </div>
                  <div className="space-y-1">
                    {berthSuggestions.slice(0, 3).map((suggestion: any, idx: number) => (
                      <div key={idx} className="flex items-center justify-between p-2 rounded text-xs"
                        style={{ backgroundColor: idx === 0 ? 'var(--kale-sky)' : 'var(--muted)' }}>
                        <div className="flex items-center gap-2">
                          <span className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold"
                            style={{ 
                              backgroundColor: idx === 0 ? 'var(--kale-blue)' : 'var(--muted-foreground)',
                              color: 'white'
                            }}>
                            {idx + 1}
                          </span>
                          <span style={{ fontWeight: 600 }}>{suggestion.berthName || suggestion.berth_name}</span>
                        </div>
                        <span className="px-2 py-0.5 rounded text-[10px]" style={{
                          backgroundColor: (suggestion.total_score || suggestion.score || suggestion.confidence || 0) >= 85 ? 'var(--status-on-time)' : 'var(--status-at-risk)',
                          color: 'white',
                          fontWeight: 600
                        }}>
                          {(suggestion.total_score || suggestion.score || suggestion.confidence || 0).toFixed(0)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* AI Reasoning */}
              {aiAnalysis.reasoning && (
                <div className="p-2 rounded text-xs" style={{ backgroundColor: 'var(--muted)' }}>
                  <div className="flex items-center gap-1 mb-1">
                    <Brain className="w-3 h-3" style={{ color: 'var(--kale-teal)' }} />
                    <span className="font-semibold" style={{ color: 'var(--kale-teal)' }}>AI Reasoning</span>
                  </div>
                  <p style={{ color: 'var(--foreground)' }}>{aiAnalysis.reasoning}</p>
                </div>
              )}
              
              {/* Constraints/Alerts from AI */}
              {aiAnalysis.alerts && aiAnalysis.alerts.length > 0 && (
                <div>
                  <div className="text-[10px] uppercase font-semibold mb-1" style={{ color: 'var(--status-at-risk)' }}>
                    AI Alerts
                  </div>
                  {aiAnalysis.alerts.map((alert: string, idx: number) => (
                    <div key={idx} className="flex items-start gap-1 text-xs mb-1">
                      <AlertTriangle className="w-3 h-3 mt-0.5" style={{ color: 'var(--status-at-risk)' }} />
                      <span>{alert}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : null}
        </div>

        {/* Vessel Particulars + Cargo - compact combined */}
        <div className="px-4 pt-3 pb-2 border-b" style={{ borderColor: 'var(--border)' }}>
          <h4 className="text-sm mb-2" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>Vessel Particulars</h4>
          <div className="grid grid-cols-3 gap-x-4 gap-y-2 text-xs">
            <div>
              <div style={{ color: 'var(--muted-foreground)' }}>Type</div>
              <div style={{ fontWeight: 600 }}>{vessel.vesselType}</div>
            </div>
            <div>
              <div style={{ color: 'var(--muted-foreground)' }}>Call Sign</div>
              <div style={{ fontWeight: 600 }}>{vessel.callSign}</div>
            </div>
            <div>
              <div style={{ color: 'var(--muted-foreground)' }}>Flag</div>
              <div style={{ fontWeight: 600 }}>{vessel.flag}</div>
            </div>
            <div>
              <div style={{ color: 'var(--muted-foreground)' }}>LOA</div>
              <div style={{ fontWeight: 600 }}>{vessel.loa}m</div>
            </div>
            <div>
              <div style={{ color: 'var(--muted-foreground)' }}>Beam</div>
              <div style={{ fontWeight: 600 }}>{vessel.beam}m</div>
            </div>
            <div>
              <div style={{ color: 'var(--muted-foreground)' }}>Draft</div>
              <div style={{ fontWeight: 600 }}>{vessel.draft}m</div>
            </div>
          </div>
        </div>

        {/* Cargo - compact inline */}
        <div className="px-4 py-2 border-b" style={{ borderColor: 'var(--border)' }}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Package className="w-3.5 h-3.5" style={{ color: 'var(--kale-blue)' }} />
              <span className="text-sm" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>Cargo</span>
            </div>
            <span className="text-sm" style={{ fontWeight: 600 }}>
              {vessel.cargoType} &middot; {vessel.cargoQuantity.toLocaleString()} {vessel.cargoUnit}
            </span>
          </div>
        </div>

        {/* Operational Constraints - compact */}
        <div className="px-4 py-3">
          <div className="flex items-center gap-2 mb-2">
            <Anchor className="w-3.5 h-3.5" style={{ color: 'var(--kale-blue)' }} />
            <h4 className="text-sm" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>Constraints</h4>
          </div>

          <div className="space-y-1.5">
            {vessel.constraints.map((constraint, index) => (
              <div
                key={index}
                className="flex items-center gap-2 px-2.5 py-1.5 rounded border-l-3"
                style={{
                  backgroundColor: `${getConstraintStatusColor(constraint.status)}08`,
                  borderLeftWidth: '3px',
                  borderLeftColor: getConstraintStatusColor(constraint.status),
                }}
              >
                <span className="text-xs">{getConstraintIcon(constraint.type)}</span>
                <span className="text-xs capitalize flex-1" style={{ fontWeight: 500 }}>{constraint.type}</span>
                <div className="flex items-center gap-1" style={{ color: getConstraintStatusColor(constraint.status) }}>
                  {getConstraintStatusIcon(constraint.status)}
                  <span className="text-[10px] capitalize">{constraint.status}</span>
                </div>
              </div>
            ))}

            {vessel.constraints.length === 0 && (
              <div className="flex items-center gap-2 py-2 text-xs" style={{ color: 'var(--muted-foreground)' }}>
                <CheckCircle2 className="w-4 h-4" style={{ color: 'var(--status-on-time)' }} />
                <span>All constraints satisfied</span>
              </div>
            )}
          </div>
        </div>

        {/* Readiness Status - compact */}
        <div className="mx-4 mb-3 p-3 rounded-lg flex items-center justify-between" style={{ backgroundColor: 'var(--kale-sky)' }}>
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full"
              style={{
                backgroundColor: vessel.readiness === 'ready' ? 'var(--status-on-time)' :
                  vessel.readiness === 'pending' ? 'var(--status-at-risk)' : 'var(--status-delayed)'
              }}
            />
            <span className="text-xs capitalize" style={{ fontWeight: 600, color: 'var(--kale-blue)' }}>
              {vessel.readiness}
            </span>
          </div>
          <div className="px-2.5 py-0.5 rounded-full capitalize text-xs"
            style={{
              backgroundColor: vessel.status === 'on-time' || vessel.status === 'early' ? 'var(--status-on-time)' :
                vessel.status === 'at-risk' ? 'var(--status-at-risk)' : 'var(--status-delayed)',
              color: 'white',
              fontWeight: 600,
            }}>
            {vessel.status}
          </div>
        </div>
      </div>

      {/* Footer Actions */}
      <div className="p-6 border-t flex gap-3" style={{ borderColor: 'var(--border)' }}>
        <button
          onClick={() => onViewHistory && onViewHistory(vessel)}
          className="flex items-center gap-2 px-4 py-3 rounded-lg transition-colors border"
          style={{
            borderColor: 'var(--border)',
            color: 'var(--kale-blue)',
            fontWeight: 600,
          }}
        >
          <History className="w-4 h-4" />
          View History
        </button>
        <button
          onClick={() => onModifyAllocation && onModifyAllocation(vessel)}
          className="flex-1 px-4 py-3 rounded-lg transition-colors"
          style={{
            backgroundColor: 'var(--kale-blue)',
            color: 'white',
            fontWeight: 600,
          }}
        >
          Allocate Berth
        </button>
      </div>

      <style>{`
        @keyframes slide-in {
          from {
            transform: translateX(100%);
          }
          to {
            transform: translateX(0);
          }
        }
        .animate-slide-in {
          animation: slide-in 0.3s ease-out;
        }
      `}</style>
    </div>
  );
}