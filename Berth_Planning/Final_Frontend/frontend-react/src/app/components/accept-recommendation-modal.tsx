import { X, CheckCircle2, AlertTriangle, Ship, Anchor, Clock, TrendingUp } from 'lucide-react';
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
    type: string;
    capacity: number;
    status: string;
  }>;
  reeferPoints: number;
}

interface AcceptRecommendationModalProps {
  vessel: Vessel;
  recommendedBerth: Berth;
  onAccept: () => void;
  onCancel: () => void;
}

export function AcceptRecommendationModal({
  vessel,
  recommendedBerth,
  onAccept,
  onCancel
}: AcceptRecommendationModalProps) {
  const operationalCranes = recommendedBerth.cranes.filter(c => c.status === 'operational');
  const estimatedTAT = vessel.cargoQuantity > 0
    ? Math.round((vessel.cargoQuantity / 150) * 10) / 10
    : Math.round((vessel.loa / 20) * 10) / 10;
  const confidence = vessel.aiRecommendation?.confidence || 85;

  const impactAnalysis = {
    berthUtilization: Math.round(65 + confidence * 0.25),
    estimatedTAT,
    craneEfficiency: recommendedBerth.cranes.length > 0
      ? Math.round((operationalCranes.length / recommendedBerth.cranes.length) * 100)
      : 90,
    cascadingImpact: confidence >= 90 ? 'Low' : confidence >= 75 ? 'Medium' : 'High',
    nextAvailable: new Date(vessel.predictedETA.getTime() + estimatedTAT * 60 * 60 * 1000),
  };

  const constraints = [
    { name: 'LOA', vessel: vessel.loa, berth: recommendedBerth.maxLOA },
    { name: 'Beam', vessel: vessel.beam, berth: recommendedBerth.maxBeam },
    { name: 'Draft', vessel: vessel.draft, berth: recommendedBerth.maxDraft },
  ];

  const fmtDate = (d: Date) => d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-xl w-full max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: 'var(--border)' }}>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" style={{ color: 'var(--kale-teal)' }} />
            <h3 className="text-sm" style={{ color: 'var(--kale-blue)', fontWeight: 700 }}>Accept AI Recommendation</h3>
          </div>
          <button onClick={onCancel} className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors">
            <X className="w-4 h-4" style={{ color: 'var(--muted-foreground)' }} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto px-4 py-3 space-y-3">
          {/* Allocation Summary */}
          <div className="p-2.5 rounded-lg border" style={{ borderColor: 'var(--kale-teal)', backgroundColor: 'var(--kale-sky)' }}>
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-1.5 text-xs">
                <Ship className="w-3.5 h-3.5" style={{ color: 'var(--kale-blue)' }} />
                <span style={{ fontWeight: 600, color: 'var(--kale-blue)' }}>{vessel.name}</span>
                <span style={{ color: 'var(--muted-foreground)' }}>→</span>
                <Anchor className="w-3.5 h-3.5" style={{ color: 'var(--kale-blue)' }} />
                <span style={{ fontWeight: 600, color: 'var(--kale-blue)' }}>{recommendedBerth.name}</span>
              </div>
              <span className="px-2 py-0.5 rounded-full text-[10px]" style={{ backgroundColor: 'var(--kale-teal)', color: 'white', fontWeight: 700 }}>
                {vessel.aiRecommendation?.confidence}%
              </span>
            </div>
            <div className="flex items-center gap-1 text-[10px]" style={{ color: 'var(--muted-foreground)' }}>
              <Clock className="w-3 h-3" />
              ETA: {fmtDate(vessel.predictedETA)}
            </div>
          </div>

          {/* AI Reasoning */}
          <div className="px-2.5 py-2 rounded-lg text-xs" style={{ backgroundColor: 'var(--muted)' }}>
            <div className="flex items-start gap-1.5">
              <TrendingUp className="w-3 h-3 flex-shrink-0 mt-0.5" style={{ color: 'var(--kale-teal)' }} />
              <span style={{ color: 'var(--foreground)' }}>{vessel.aiRecommendation?.reason}</span>
            </div>
          </div>

          {/* Constraints - inline */}
          <div>
            <div className="text-xs mb-1.5" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>Constraint Validation</div>
            <div className="grid grid-cols-3 gap-1.5">
              {constraints.map((c) => (
                <div key={c.name} className="flex items-center justify-between px-2 py-1.5 rounded text-xs" style={{ backgroundColor: 'var(--kale-sky)' }}>
                  <div className="flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" style={{ color: 'var(--status-on-time)' }} />
                    <span style={{ fontWeight: 500 }}>{c.name}</span>
                  </div>
                  <span className="text-[10px]" style={{ color: 'var(--muted-foreground)' }}>{c.vessel}/{c.berth}m</span>
                </div>
              ))}
            </div>
          </div>

          {/* Impact Analysis - compact grid */}
          <div>
            <div className="text-xs mb-1.5" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>Impact Analysis</div>
            <div className="grid grid-cols-4 gap-1.5">
              {[
                { label: 'Utilization', value: `${impactAnalysis.berthUtilization}%` },
                { label: 'TAT', value: `${impactAnalysis.estimatedTAT}h` },
                { label: 'Crane Eff.', value: `${impactAnalysis.craneEfficiency}%` },
                { label: 'Impact', value: impactAnalysis.cascadingImpact },
              ].map(item => (
                <div key={item.label} className="p-2 rounded text-center" style={{ backgroundColor: 'var(--muted)' }}>
                  <div className="text-[10px]" style={{ color: 'var(--muted-foreground)' }}>{item.label}</div>
                  <div className="text-sm" style={{ fontWeight: 700, color: 'var(--kale-blue)' }}>{item.value}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Next Available */}
          <div className="flex items-center justify-between text-xs px-2.5 py-1.5 rounded" style={{ backgroundColor: 'var(--kale-sky)' }}>
            <span style={{ color: 'var(--muted-foreground)' }}>Next available after operation:</span>
            <span style={{ fontWeight: 600, color: 'var(--kale-blue)' }}>{fmtDate(impactAnalysis.nextAvailable)}</span>
          </div>

          {/* Warning */}
          {vessel.constraints.some(c => c.status === 'warning' || c.status === 'critical') && (
            <div className="flex items-start gap-1.5 px-2.5 py-2 rounded border text-xs" style={{ borderColor: 'var(--status-at-risk)' }}>
              <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" style={{ color: 'var(--status-at-risk)' }} />
              <div>
                <div style={{ fontWeight: 600 }} className="mb-0.5">Constraints Requiring Attention</div>
                {vessel.constraints
                  .filter(c => c.status === 'warning' || c.status === 'critical')
                  .map((c, idx) => (
                    <div key={idx} className="text-[10px]" style={{ color: 'var(--muted-foreground)' }}>• {c.message}</div>
                  ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 px-4 py-2.5 border-t" style={{ borderColor: 'var(--border)' }}>
          <button onClick={onCancel} className="px-4 py-1.5 rounded-lg transition-colors border text-xs"
            style={{ borderColor: 'var(--border)', color: 'var(--kale-blue)', fontWeight: 600 }}>
            Cancel
          </button>
          <button onClick={onAccept} className="px-4 py-1.5 rounded-lg transition-colors text-xs"
            style={{ backgroundColor: 'var(--kale-blue)', color: 'white', fontWeight: 600 }}>
            Confirm Allocation
          </button>
        </div>
      </div>
    </div>
  );
}
