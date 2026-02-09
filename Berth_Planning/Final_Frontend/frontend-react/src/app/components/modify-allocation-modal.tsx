import { useState } from 'react';
import { X, AlertTriangle, CheckCircle2, XCircle, Ship, Anchor, Search } from 'lucide-react';
import type { Vessel } from './upcoming-vessels-timeline';

interface Berth {
  id: string;
  name: string;
  length: number;
  maxDraft: number;
  maxLOA: number;
  maxBeam: number;
  status: string;
  cranes: Array<{
    id: string;
    type: string;
    capacity: number;
    status: string;
  }>;
  reeferPoints: number;
  currentVessel?: {
    name: string;
    etd: Date;
  };
}

interface ModifyAllocationModalProps {
  vessel: Vessel;
  berths: Berth[];
  onAllocate: (berthId: string, reason: string) => void;
  onCancel: () => void;
}

export function ModifyAllocationModal({
  vessel,
  berths,
  onAllocate,
  onCancel
}: ModifyAllocationModalProps) {
  const [selectedBerthId, setSelectedBerthId] = useState<string | null>(null);
  const [reason, setReason] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const checkConstraint = (berth: Berth, constraint: 'loa' | 'beam' | 'draft') => {
    const value = vessel[constraint];
    const max = constraint === 'loa' ? berth.maxLOA :
                constraint === 'beam' ? berth.maxBeam :
                berth.maxDraft;

    if (value <= max) return 'satisfied';
    if (value <= max * 1.05) return 'warning';
    return 'critical';
  };

  const getBerthCompatibility = (berth: Berth): {
    score: number;
    status: 'excellent' | 'good' | 'marginal' | 'incompatible';
    issues: string[];
  } => {
    const issues: string[] = [];
    let score = 100;

    if (vessel.loa > berth.maxLOA) {
      issues.push(`LOA exceeds by ${(vessel.loa - berth.maxLOA).toFixed(1)}m`);
      score -= 50;
    }
    if (vessel.beam > berth.maxBeam) {
      issues.push(`Beam exceeds by ${(vessel.beam - berth.maxBeam).toFixed(1)}m`);
      score -= 50;
    }
    if (vessel.draft > berth.maxDraft) {
      issues.push(`Draft exceeds by ${(vessel.draft - berth.maxDraft).toFixed(1)}m`);
      score -= 50;
    }
    if (berth.status === 'occupied') {
      if (berth.currentVessel && berth.currentVessel.etd > vessel.predictedETA) {
        issues.push(`Occupied until ${berth.currentVessel.etd.toLocaleTimeString()}`);
        score -= 30;
      }
    }
    if (berth.status === 'maintenance') {
      issues.push('Under maintenance');
      score -= 40;
    }
    const operationalCranes = berth.cranes.filter(c => c.status === 'operational').length;
    if (operationalCranes === 0) {
      issues.push('No operational cranes');
      score -= 20;
    }

    let status: 'excellent' | 'good' | 'marginal' | 'incompatible';
    if (score >= 90) status = 'excellent';
    else if (score >= 70) status = 'good';
    else if (score >= 50) status = 'marginal';
    else status = 'incompatible';

    return { score, status, issues };
  };

  const getCompatibilityColor = (status: string) => {
    switch (status) {
      case 'excellent': return 'var(--status-on-time)';
      case 'good': return 'var(--kale-teal)';
      case 'marginal': return 'var(--status-at-risk)';
      case 'incompatible': return 'var(--status-critical)';
      default: return 'var(--muted-foreground)';
    }
  };

  const filteredBerths = berths.filter(berth =>
    berth.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    berth.id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const selectedBerth = berths.find(b => b.id === selectedBerthId);
  const selectedCompatibility = selectedBerth ? getBerthCompatibility(selectedBerth) : null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-3xl w-full max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-2.5 border-b" style={{ borderColor: 'var(--border)' }}>
          <div className="flex items-center gap-2">
            <Anchor className="w-4 h-4" style={{ color: 'var(--kale-blue)' }} />
            <h3 className="text-sm" style={{ color: 'var(--kale-blue)', fontWeight: 700 }}>Manual Berth Allocation</h3>
            <span className="text-xs" style={{ color: 'var(--muted-foreground)' }}>• {vessel.name}</span>
          </div>
          <button onClick={onCancel} className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors">
            <X className="w-4 h-4" style={{ color: 'var(--muted-foreground)' }} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden flex min-h-0">
          {/* Left: Berth Selection */}
          <div className="w-1/2 border-r flex flex-col" style={{ borderColor: 'var(--border)' }}>
            {/* Search */}
            <div className="px-3 py-2 border-b" style={{ borderColor: 'var(--border)' }}>
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 transform -translate-y-1/2 w-3.5 h-3.5"
                  style={{ color: 'var(--muted-foreground)' }} />
                <input
                  type="text"
                  placeholder="Search berths..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 rounded-lg border text-xs"
                  style={{
                    borderColor: 'var(--border)',
                    backgroundColor: 'var(--input-background)',
                  }}
                />
              </div>
            </div>

            {/* Berth List */}
            <div className="flex-1 overflow-auto p-2 space-y-1.5">
              {filteredBerths.map((berth) => {
                const compatibility = getBerthCompatibility(berth);
                const isSelected = selectedBerthId === berth.id;

                return (
                  <div
                    key={berth.id}
                    onClick={() => setSelectedBerthId(berth.id)}
                    className="cursor-pointer rounded-lg border transition-all"
                    style={{
                      borderColor: isSelected ? getCompatibilityColor(compatibility.status) : 'var(--border)',
                      backgroundColor: isSelected ? `${getCompatibilityColor(compatibility.status)}10` : 'white',
                    }}
                  >
                    <div className="px-2.5 py-2">
                      {/* Header */}
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center gap-1.5">
                          <Anchor className="w-3 h-3" style={{ color: 'var(--kale-blue)' }} />
                          <span className="text-xs" style={{ fontWeight: 600, color: 'var(--kale-blue)' }}>
                            {berth.name}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <span className="px-1.5 py-0.5 rounded text-[10px] capitalize"
                            style={{
                              backgroundColor: `${getCompatibilityColor(compatibility.status)}20`,
                              color: getCompatibilityColor(compatibility.status),
                              fontWeight: 600,
                            }}>
                            {compatibility.status}
                          </span>
                          <span className="text-xs" style={{
                            fontWeight: 700,
                            color: getCompatibilityColor(compatibility.status)
                          }}>
                            {compatibility.score}%
                          </span>
                        </div>
                      </div>

                      {/* Specs + Status inline */}
                      <div className="flex items-center justify-between text-[10px]">
                        <div className="flex items-center gap-2" style={{ color: 'var(--muted-foreground)' }}>
                          <span>LOA: <span style={{ fontWeight: 600, color: 'var(--foreground)' }}>{berth.maxLOA}m</span></span>
                          <span>Beam: <span style={{ fontWeight: 600, color: 'var(--foreground)' }}>{berth.maxBeam}m</span></span>
                          <span>Draft: <span style={{ fontWeight: 600, color: 'var(--foreground)' }}>{berth.maxDraft}m</span></span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <span className="px-1 py-0.5 rounded capitalize"
                            style={{
                              backgroundColor: berth.status === 'available' ? 'var(--status-on-time)' :
                                berth.status === 'occupied' ? 'var(--kale-blue)' :
                                'var(--muted-foreground)',
                              color: 'white',
                              fontSize: '9px',
                              fontWeight: 600,
                            }}>
                            {berth.status}
                          </span>
                          {compatibility.issues.length > 0 && (
                            <span className="text-[10px]" style={{ color: 'var(--status-at-risk)' }}>
                              {compatibility.issues.length} issue{compatibility.issues.length !== 1 ? 's' : ''}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right: Details & Validation */}
          <div className="w-1/2 flex flex-col">
            {selectedBerth && selectedCompatibility ? (
              <div className="flex-1 overflow-auto px-3 py-2.5 space-y-2.5">
                {/* Selected Berth + Compatibility inline */}
                <div className="flex items-center justify-between p-2.5 rounded-lg" style={{ backgroundColor: 'var(--kale-sky)' }}>
                  <div>
                    <div className="text-xs" style={{ fontWeight: 600, color: 'var(--kale-blue)' }}>{selectedBerth.name}</div>
                    <div className="text-[10px]" style={{ color: 'var(--muted-foreground)' }}>
                      {selectedBerth.length}m • {selectedBerth.cranes.length} cranes
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg" style={{ fontWeight: 700, color: getCompatibilityColor(selectedCompatibility.status) }}>
                      {selectedCompatibility.score}%
                    </div>
                    <div className="text-[10px] uppercase" style={{ color: getCompatibilityColor(selectedCompatibility.status), fontWeight: 600 }}>
                      {selectedCompatibility.status}
                    </div>
                  </div>
                </div>

                {/* Constraint Checks - inline grid */}
                <div>
                  <div className="text-xs mb-1.5" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>Constraints</div>
                  <div className="grid grid-cols-3 gap-1.5">
                    {[
                      { name: 'LOA', vessel: vessel.loa, berth: selectedBerth.maxLOA, type: 'loa' as const },
                      { name: 'Beam', vessel: vessel.beam, berth: selectedBerth.maxBeam, type: 'beam' as const },
                      { name: 'Draft', vessel: vessel.draft, berth: selectedBerth.maxDraft, type: 'draft' as const },
                    ].map((constraint) => {
                      const status = checkConstraint(selectedBerth, constraint.type);
                      return (
                        <div key={constraint.name} className="flex items-center justify-between px-2 py-1.5 rounded text-xs"
                          style={{ backgroundColor: 'var(--muted)' }}>
                          <div className="flex items-center gap-1">
                            {status === 'satisfied' ? (
                              <CheckCircle2 className="w-3 h-3" style={{ color: 'var(--status-on-time)' }} />
                            ) : status === 'warning' ? (
                              <AlertTriangle className="w-3 h-3" style={{ color: 'var(--status-at-risk)' }} />
                            ) : (
                              <XCircle className="w-3 h-3" style={{ color: 'var(--status-critical)' }} />
                            )}
                            <span style={{ fontWeight: 500 }}>{constraint.name}</span>
                          </div>
                          <span className="text-[10px]" style={{ color: 'var(--muted-foreground)' }}>
                            {constraint.vessel}/{constraint.berth}m
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Issues - compact */}
                {selectedCompatibility.issues.length > 0 && (
                  <div className="flex items-start gap-1.5 px-2.5 py-2 rounded border text-xs" style={{ borderColor: 'var(--status-at-risk)' }}>
                    <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" style={{ color: 'var(--status-at-risk)' }} />
                    <div>
                      <div style={{ fontWeight: 600 }} className="mb-0.5">Issues</div>
                      {selectedCompatibility.issues.map((issue, idx) => (
                        <div key={idx} className="text-[10px]" style={{ color: 'var(--muted-foreground)' }}>• {issue}</div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Reason */}
                <div>
                  <div className="text-xs mb-1" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
                    Reason for Manual Allocation
                    {(selectedCompatibility.status === 'marginal' || selectedCompatibility.status === 'incompatible') && (
                      <span style={{ color: 'var(--status-critical)' }}> *</span>
                    )}
                  </div>
                  <textarea
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    placeholder="Enter reason for manual allocation..."
                    rows={2}
                    className="w-full px-2.5 py-1.5 rounded-lg border resize-none text-xs"
                    style={{
                      borderColor: 'var(--border)',
                      backgroundColor: 'var(--input-background)',
                    }}
                  />
                </div>
              </div>
            ) : (
              <div className="flex-1 flex items-center justify-center p-4">
                <div className="text-center">
                  <Ship className="w-8 h-8 mx-auto mb-2" style={{ color: 'var(--muted-foreground)', opacity: 0.5 }} />
                  <p className="text-xs" style={{ color: 'var(--muted-foreground)' }}>
                    Select a berth to view details
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-4 py-2.5 border-t" style={{ borderColor: 'var(--border)' }}>
          <div className="text-xs" style={{ color: 'var(--muted-foreground)' }}>
            {selectedCompatibility && selectedCompatibility.status !== 'excellent' && selectedCompatibility.status !== 'good' && (
              <span style={{ color: 'var(--status-at-risk)' }}>
                Manual override requires justification
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button onClick={onCancel} className="px-4 py-1.5 rounded-lg transition-colors border text-xs"
              style={{ borderColor: 'var(--border)', color: 'var(--kale-blue)', fontWeight: 600 }}>
              Cancel
            </button>
            <button
              onClick={() => selectedBerthId && onAllocate(selectedBerthId, reason)}
              disabled={!selectedBerthId || (selectedCompatibility?.status === 'incompatible' && !reason.trim())}
              className="px-4 py-1.5 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-xs"
              style={{
                backgroundColor: selectedBerthId ? 'var(--kale-blue)' : 'var(--muted)',
                color: 'white',
                fontWeight: 600,
              }}
            >
              Allocate Berth
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
