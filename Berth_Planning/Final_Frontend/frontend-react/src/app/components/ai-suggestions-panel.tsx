import { useState } from 'react';
import { Ship, Zap, CheckCircle2, XCircle, AlertTriangle, ChevronDown, ChevronRight, Anchor, Clock, Shield, Brain } from 'lucide-react';
import type { Vessel } from './upcoming-vessels-timeline';

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

interface AISuggestionsPanelProps {
  vessels: Vessel[];
  berths: Berth[];
  onAcceptRecommendation: (vessel: Vessel) => void;
  onRejectRecommendation: (vessel: Vessel) => void;
}

export function AISuggestionsPanel({ vessels, berths, onAcceptRecommendation, onRejectRecommendation }: AISuggestionsPanelProps) {
  const [collapsed, setCollapsed] = useState(false);

  // Filter vessels that have AI recommendations and are not yet arrived/allocated
  const pendingVessels = vessels.filter(
    v => v.aiRecommendation && v.status !== 'arrived' && !v.ata
  );

  if (pendingVessels.length === 0) return null;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'on-time': return 'var(--status-on-time)';
      case 'early': return 'var(--kale-teal)';
      case 'at-risk': return 'var(--status-at-risk)';
      case 'delayed': return 'var(--status-delayed)';
      default: return 'var(--muted-foreground)';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 85) return 'var(--status-on-time)';
    if (confidence >= 70) return 'var(--status-at-risk)';
    return 'var(--status-delayed)';
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 85) return 'HIGH';
    if (confidence >= 70) return 'MEDIUM';
    return 'LOW';
  };

  const findBerth = (name: string) => berths.find(b => b.name === name);

  const formatETA = (date: Date) => {
    try {
      return date.toLocaleDateString('en-US', {
        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
      });
    } catch { return 'N/A'; }
  };

  const checkConstraint = (vesselVal: number, berthMax: number) => vesselVal <= berthMax;

  return (
    <div className="mb-3">
      {/* Panel header */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors hover:opacity-95"
        style={{
          background: 'linear-gradient(135deg, var(--kale-blue), #0C7BBD)',
          border: 'none',
          cursor: 'pointer',
        }}
      >
        <div className="flex items-center gap-2">
          {collapsed
            ? <ChevronRight className="w-4 h-4" style={{ color: 'white' }} />
            : <ChevronDown className="w-4 h-4" style={{ color: 'white' }} />
          }
          <Brain className="w-4 h-4" style={{ color: '#FBBF24' }} />
          <span className="text-xs font-bold" style={{ color: 'white' }}>
            AI Berth Suggestions
          </span>
        </div>
        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold"
          style={{ backgroundColor: 'rgba(251,191,36,0.3)', color: '#FBBF24' }}>
          {pendingVessels.length} pending
        </span>
        <span className="flex-1" />
        <span className="text-[10px]" style={{ color: 'rgba(255,255,255,0.7)' }}>
          Auto-refreshes every 60s
        </span>
      </button>

      {/* Suggestion cards */}
      {!collapsed && (
        <div className="mt-2 space-y-2">
          {pendingVessels.map(vessel => {
            const rec = vessel.aiRecommendation!;
            const suggestedBerth = findBerth(rec.suggestedBerth);
            const confidence = rec.confidence;
            const loaOk = suggestedBerth ? checkConstraint(vessel.loa, suggestedBerth.maxLOA) : true;
            const draftOk = suggestedBerth ? checkConstraint(vessel.draft, suggestedBerth.maxDraft) : true;
            const beamOk = suggestedBerth ? checkConstraint(vessel.beam, suggestedBerth.maxBeam) : true;
            const constraintsPassed = [loaOk, draftOk, beamOk].filter(Boolean).length;

            return (
              <div key={vessel.id} className="rounded-lg overflow-hidden shadow-sm"
                style={{ border: '1.5px solid var(--border)', backgroundColor: 'white' }}>

                {/* Vessel header */}
                <div className="flex items-center justify-between px-3 py-2"
                  style={{ backgroundColor: 'var(--kale-sky)', borderBottom: '1px solid var(--border)' }}>
                  <div className="flex items-center gap-2">
                    <Ship className="w-3.5 h-3.5" style={{ color: 'var(--kale-blue)' }} />
                    <span className="text-xs font-bold" style={{ color: 'var(--kale-blue)' }}>{vessel.name}</span>
                    <span className="text-[9px] px-1.5 py-0.5 rounded capitalize"
                      style={{
                        backgroundColor: `${getStatusColor(vessel.status)}15`,
                        color: getStatusColor(vessel.status),
                        fontWeight: 600,
                      }}>
                      {vessel.status}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-[9px]" style={{ color: 'var(--muted-foreground)' }}>
                    <span>LOA: <b style={{ color: 'var(--foreground)' }}>{vessel.loa}m</b></span>
                    <span>Beam: <b style={{ color: 'var(--foreground)' }}>{vessel.beam}m</b></span>
                    <span>Draft: <b style={{ color: 'var(--foreground)' }}>{vessel.draft}m</b></span>
                    <span>{vessel.vesselType}</span>
                  </div>
                </div>

                {/* Two-column body */}
                <div className="grid grid-cols-2 gap-0" style={{ borderBottom: '1px solid var(--border)' }}>

                  {/* Left: Predicted ETA */}
                  <div className="px-3 py-2" style={{ borderRight: '1px solid var(--border)' }}>
                    <div className="flex items-center gap-1.5 mb-1.5">
                      <Clock className="w-3 h-3" style={{ color: 'var(--kale-teal)' }} />
                      <span className="text-[9px] font-bold uppercase" style={{ color: 'var(--muted-foreground)', letterSpacing: 0.5 }}>
                        Predicted ETA
                      </span>
                    </div>
                    <div className="text-sm font-bold mb-1" style={{ color: 'var(--kale-blue)' }}>
                      {formatETA(vessel.predictedETA)}
                    </div>
                    {vessel.etaDeviation !== 0 && (
                      <div className="flex items-center gap-1 mb-1.5">
                        <span className="text-[9px] px-1.5 py-0.5 rounded"
                          style={{
                            backgroundColor: Math.abs(vessel.etaDeviation) > 60 ? '#FEE2E2' : '#FEF3C7',
                            color: Math.abs(vessel.etaDeviation) > 60 ? '#DC2626' : '#D97706',
                            fontWeight: 600,
                          }}>
                          {vessel.etaDeviation > 0 ? '+' : ''}{vessel.etaDeviation} min deviation
                        </span>
                      </div>
                    )}
                    <div className="text-[9px]" style={{ color: 'var(--muted-foreground)' }}>
                      <span className="font-medium">Declared:</span> {formatETA(vessel.declaredETA)}
                    </div>
                    <div className="flex items-center gap-1.5 mt-2 flex-wrap">
                      {['AIS Tracking', 'Weather', 'Tidal', 'Historical'].map(factor => (
                        <span key={factor} className="inline-flex items-center gap-0.5 px-1 py-px rounded text-[8px]"
                          style={{ backgroundColor: 'var(--muted)', color: 'var(--muted-foreground)', fontWeight: 500 }}>
                          <CheckCircle2 className="w-2 h-2" style={{ color: 'var(--status-on-time)' }} />
                          {factor}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Right: Suggested Berth */}
                  <div className="px-3 py-2">
                    <div className="flex items-center gap-1.5 mb-1.5">
                      <Anchor className="w-3 h-3" style={{ color: 'var(--kale-blue)' }} />
                      <span className="text-[9px] font-bold uppercase" style={{ color: 'var(--muted-foreground)', letterSpacing: 0.5 }}>
                        Suggested Berth
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className="text-sm font-bold" style={{ color: 'var(--kale-blue)' }}>
                        {rec.suggestedBerth}
                      </span>
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-bold"
                        style={{
                          backgroundColor: `${getConfidenceColor(confidence)}15`,
                          color: getConfidenceColor(confidence),
                        }}>
                        {Math.round(confidence)}% — {getConfidenceLabel(confidence)}
                      </span>
                    </div>

                    {/* Constraint checks */}
                    <div className="flex items-center gap-2 mb-1.5">
                      {[
                        { label: 'LOA', ok: loaOk, val: `${vessel.loa}m / ${suggestedBerth?.maxLOA || '?'}m` },
                        { label: 'Draft', ok: draftOk, val: `${vessel.draft}m / ${suggestedBerth?.maxDraft || '?'}m` },
                        { label: 'Beam', ok: beamOk, val: `${vessel.beam}m / ${suggestedBerth?.maxBeam || '?'}m` },
                      ].map(c => (
                        <div key={c.label} className="flex items-center gap-0.5 text-[9px]"
                          title={c.val}>
                          {c.ok
                            ? <CheckCircle2 className="w-2.5 h-2.5" style={{ color: 'var(--status-on-time)' }} />
                            : <XCircle className="w-2.5 h-2.5" style={{ color: 'var(--status-delayed)' }} />
                          }
                          <span style={{ fontWeight: 600, color: c.ok ? 'var(--status-on-time)' : 'var(--status-delayed)' }}>
                            {c.label}
                          </span>
                        </div>
                      ))}
                      <span className="text-[9px] ml-1 px-1 py-px rounded"
                        style={{
                          backgroundColor: constraintsPassed === 3 ? '#D1FAE5' : '#FEF3C7',
                          color: constraintsPassed === 3 ? '#059669' : '#D97706',
                          fontWeight: 600,
                        }}>
                        {constraintsPassed}/3 passed
                      </span>
                    </div>

                    {/* Berth specs */}
                    {suggestedBerth && (
                      <div className="flex items-center gap-3 text-[9px]" style={{ color: 'var(--muted-foreground)' }}>
                        <span>Length: <b>{suggestedBerth.length}m</b></span>
                        <span>Cranes: <b>{suggestedBerth.cranes.filter(c => c.status === 'operational').length}/{suggestedBerth.cranes.length}</b></span>
                        <span className="capitalize">Status: <b>{suggestedBerth.status}</b></span>
                      </div>
                    )}
                  </div>
                </div>

                {/* AI Reasoning */}
                <div className="px-3 py-1.5" style={{ backgroundColor: '#FFFBEB', borderBottom: '1px solid var(--border)' }}>
                  <div className="flex items-start gap-1.5">
                    <Zap className="w-3 h-3 flex-shrink-0 mt-0.5" style={{ color: '#D97706' }} />
                    <p className="text-[10px] leading-relaxed" style={{ color: '#92400E' }}>
                      <span className="font-bold">AI Reasoning: </span>
                      {rec.reason}
                    </p>
                  </div>
                </div>

                {/* Action buttons */}
                <div className="flex items-center justify-end gap-2 px-3 py-2">
                  <button
                    onClick={() => onRejectRecommendation(vessel)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[11px] font-semibold transition-colors"
                    style={{
                      border: '1.5px solid var(--status-delayed)',
                      color: 'var(--status-delayed)',
                      backgroundColor: 'transparent',
                      cursor: 'pointer',
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#FEE2E2'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; }}
                  >
                    <XCircle className="w-3.5 h-3.5" />
                    Reject & Modify
                  </button>
                  <button
                    onClick={() => onAcceptRecommendation(vessel)}
                    className="flex items-center gap-1.5 px-4 py-1.5 rounded-md text-[11px] font-semibold transition-colors"
                    style={{
                      border: 'none',
                      color: 'white',
                      backgroundColor: 'var(--kale-blue)',
                      cursor: 'pointer',
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#083d6e'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'var(--kale-blue)'; }}
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Accept Suggestion
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
