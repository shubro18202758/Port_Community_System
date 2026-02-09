import { CheckCircle2, Anchor, Building2, Link2, Cpu, Users, Shield } from 'lucide-react';
import type { OnboardingData } from '../port-onboarding-wizard';

interface ReviewStepProps {
  data: OnboardingData;
}

export function ReviewStep({ data }: ReviewStepProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="flex items-center gap-2 mb-2" style={{ color: 'var(--kale-blue)' }}>
          <CheckCircle2 className="w-6 h-6" />
          Review & Confirm
        </h2>
        <p style={{ color: 'var(--muted-foreground)' }}>
          Review your configuration before completing the onboarding process
        </p>
      </div>

      {/* Port Details */}
      <div className="bg-white rounded-xl shadow-sm border p-6" style={{ borderColor: 'var(--border)' }}>
        <h3 className="flex items-center gap-2 mb-4" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
          <Anchor className="w-5 h-5" />
          Port Information
        </h3>
        {data.port && (
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span style={{ color: 'var(--muted-foreground)' }}>Port Name:</span>
              <div style={{ fontWeight: 600 }}>{data.port.portName}</div>
            </div>
            <div>
              <span style={{ color: 'var(--muted-foreground)' }}>Port Code:</span>
              <div style={{ fontWeight: 600 }}>{data.port.portCode}</div>
            </div>
            <div>
              <span style={{ color: 'var(--muted-foreground)' }}>UN/LOCODE:</span>
              <div style={{ fontWeight: 600 }}>{data.port.unlocode}</div>
            </div>
            <div>
              <span style={{ color: 'var(--muted-foreground)' }}>Country:</span>
              <div style={{ fontWeight: 600 }}>{data.port.country}</div>
            </div>
            <div>
              <span style={{ color: 'var(--muted-foreground)' }}>Coordinates:</span>
              <div style={{ fontWeight: 600 }}>
                {data.port.coordinates.latitude.toFixed(6)}, {data.port.coordinates.longitude.toFixed(6)}
              </div>
            </div>
            <div>
              <span style={{ color: 'var(--muted-foreground)' }}>Timezone:</span>
              <div style={{ fontWeight: 600 }}>{data.port.timezone}</div>
            </div>
          </div>
        )}
      </div>

      {/* Integration */}
      <div className="bg-white rounded-xl shadow-sm border p-6" style={{ borderColor: 'var(--border)' }}>
        <h3 className="flex items-center gap-2 mb-4" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
          <Link2 className="w-5 h-5" />
          System Integration
        </h3>
        {data.integration && (
          <div className="space-y-3">
            <div>
              <span style={{ color: 'var(--muted-foreground)' }}>Integration Type:</span>
              <div style={{ fontWeight: 600 }} className="capitalize">
                {data.integration.systemType?.replace('_', ' ')}
              </div>
            </div>
            <div>
              <span style={{ color: 'var(--muted-foreground)' }}>Data Sync:</span>
              <div className="flex gap-2 mt-1">
                {Object.entries(data.integration.dataSync).filter(([_, v]) => v).map(([k]) => (
                  <span key={k} className="text-xs px-2 py-1 rounded capitalize"
                    style={{ backgroundColor: 'var(--kale-sky)', color: 'var(--kale-blue)' }}>
                    {k.replace(/([A-Z])/g, ' $1').trim()}
                  </span>
                ))}
              </div>
            </div>
            <div>
              <span style={{ color: 'var(--muted-foreground)' }}>Sync Frequency:</span>
              <div style={{ fontWeight: 600 }} className="capitalize">{data.integration.syncFrequency}</div>
            </div>
          </div>
        )}
      </div>

      {/* Terminals & Berths */}
      <div className="bg-white rounded-xl shadow-sm border p-6" style={{ borderColor: 'var(--border)' }}>
        <h3 className="flex items-center gap-2 mb-4" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
          <Building2 className="w-5 h-5" />
          Terminals & Berths
        </h3>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="p-4 rounded-lg text-center" style={{ backgroundColor: 'var(--kale-sky)' }}>
            <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--kale-blue)' }}>
              {data.terminals.length}
            </div>
            <div className="text-sm" style={{ color: 'var(--muted-foreground)' }}>Terminals Configured</div>
          </div>
          <div className="p-4 rounded-lg text-center" style={{ backgroundColor: 'var(--kale-sky)' }}>
            <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--kale-blue)' }}>
              {data.berths.length}
            </div>
            <div className="text-sm" style={{ color: 'var(--muted-foreground)' }}>Berths Configured</div>
          </div>
        </div>
        <div className="space-y-2">
          {data.terminals.map((terminal) => (
            <div key={terminal.id} className="p-3 rounded-lg" style={{ backgroundColor: 'var(--muted)' }}>
              <div style={{ fontWeight: 600 }}>{terminal.name}</div>
              <div className="text-sm" style={{ color: 'var(--muted-foreground)' }}>
                {data.berths.filter(b => b.terminalId === terminal.id).length} berths
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Equipment */}
      <div className="bg-white rounded-xl shadow-sm border p-6" style={{ borderColor: 'var(--border)' }}>
        <h3 className="flex items-center gap-2 mb-4" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
          <Cpu className="w-5 h-5" />
          Equipment Summary
        </h3>
        <div className="grid grid-cols-3 gap-3">
          {['STS', 'RTG', 'MHC', 'RMG', 'Reach Stacker'].map((type) => {
            const count = data.equipment.filter(e => e.type === type).length;
            return count > 0 ? (
              <div key={type} className="p-3 rounded-lg text-center" style={{ backgroundColor: 'var(--muted)' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{count}</div>
                <div className="text-sm" style={{ color: 'var(--muted-foreground)' }}>{type}</div>
              </div>
            ) : null;
          })}
        </div>
      </div>

      {/* Human Resources */}
      <div className="bg-white rounded-xl shadow-sm border p-6" style={{ borderColor: 'var(--border)' }}>
        <h3 className="flex items-center gap-2 mb-4" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
          <Users className="w-5 h-5" />
          Human Resources
        </h3>
        <div className="space-y-2">
          {data.humanResources.filter(r => r.count > 0).map((resource) => (
            <div key={resource.role} className="flex items-center justify-between p-3 rounded-lg"
              style={{ backgroundColor: 'var(--muted)' }}>
              <span style={{ fontWeight: 600 }}>{resource.role}</span>
              <span className="text-sm">{resource.count} personnel • {resource.shifts} shifts</span>
            </div>
          ))}
        </div>
      </div>

      {/* Constraints */}
      {data.constraints.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border p-6" style={{ borderColor: 'var(--border)' }}>
          <h3 className="flex items-center gap-2 mb-4" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
            <Shield className="w-5 h-5" />
            Safety & Constraints
          </h3>
          <div className="text-center p-4 rounded-lg" style={{ backgroundColor: 'var(--kale-sky)' }}>
            <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--kale-blue)' }}>
              {data.constraints.length}
            </div>
            <div className="text-sm" style={{ color: 'var(--muted-foreground)' }}>Constraints Configured</div>
          </div>
        </div>
      )}

      {/* Ready to Go */}
      <div className="p-6 rounded-xl border-2 text-center" style={{
        borderColor: 'var(--kale-teal)',
        backgroundColor: `var(--kale-teal)10`
      }}>
        <CheckCircle2 className="w-12 h-12 mx-auto mb-3" style={{ color: 'var(--kale-teal)' }} />
        <h3 style={{ color: 'var(--kale-blue)', fontWeight: 600, marginBottom: '0.5rem' }}>
          Ready to Complete Onboarding
        </h3>
        <p style={{ color: 'var(--muted-foreground)' }}>
          Click "Complete Onboarding" to activate SmartBerth AI for your port
        </p>
      </div>
    </div>
  );
}
