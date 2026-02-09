import { Building2, Anchor, Cpu, Users, Shield, Edit2, ArrowLeft, CheckCircle2, Settings } from 'lucide-react';
import type { OnboardingData } from './onboarding/port-onboarding-wizard';

interface TerminalProfileProps {
  data: OnboardingData;
  onBack: () => void;
  onStartOperations: () => void;
  onOnboarding?: () => void;
}

export function TerminalProfile({ data, onBack, onStartOperations, onOnboarding }: TerminalProfileProps) {
  const totalEquipment = data.equipment.length;
  const operationalEquipment = data.equipment.filter(e => e.status === 'operational').length;
  const totalStaff = data.humanResources.reduce((sum, r) => sum + r.count, 0);

  return (
    <div className="size-full flex flex-col bg-gradient-to-br from-gray-50 to-white overflow-auto">
      {/* Header */}
      <div className="px-6 py-4 border-b bg-white shadow-sm" style={{ borderColor: 'var(--border)' }}>
        <div className="max-w-7xl mx-auto">
          <button
            onClick={onBack}
            className="flex items-center gap-1.5 mb-2 text-xs"
            style={{ color: 'var(--kale-blue)', fontWeight: 600 }}
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back
          </button>
          <div className="flex items-center justify-between">
            <div>
              <h1 style={{ color: 'var(--kale-blue)', fontSize: '1.5rem', fontWeight: 700 }}>
                {data.port?.portName}
              </h1>
              <p className="text-xs mt-0.5" style={{ color: 'var(--muted-foreground)' }}>
                {data.port?.portCode} • {data.port?.country} • {data.port?.timezone}
              </p>
            </div>
            <div className="flex gap-2">
              {onOnboarding && (
                <button
                  onClick={onOnboarding}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs"
                  style={{ borderColor: 'var(--kale-blue)', color: 'var(--kale-blue)', fontWeight: 600 }}>
                  <Settings className="w-3.5 h-3.5" />
                  Onboarding Wizard
                </button>
              )}
              <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs"
                style={{ borderColor: 'var(--border)', color: 'var(--kale-blue)', fontWeight: 600 }}>
                <Edit2 className="w-3.5 h-3.5" />
                Edit Profile
              </button>
              <button
                onClick={onStartOperations}
                className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs"
                style={{ backgroundColor: 'var(--kale-blue)', color: 'white', fontWeight: 600 }}>
                <CheckCircle2 className="w-3.5 h-3.5" />
                Start Operations
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 px-6 py-4">
        <div className="max-w-7xl mx-auto space-y-4">
          {/* Quick Stats */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-white rounded-lg shadow-sm border p-3" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center gap-2 mb-1">
                <div className="w-7 h-7 rounded-full flex items-center justify-center"
                  style={{ backgroundColor: 'var(--kale-sky)' }}>
                  <Building2 className="w-3.5 h-3.5" style={{ color: 'var(--kale-blue)' }} />
                </div>
                <span className="text-xs" style={{ color: 'var(--muted-foreground)' }}>Terminals</span>
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--kale-blue)' }}>
                {data.terminals.length}
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-3" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center gap-2 mb-1">
                <div className="w-7 h-7 rounded-full flex items-center justify-center"
                  style={{ backgroundColor: 'var(--kale-sky)' }}>
                  <Anchor className="w-3.5 h-3.5" style={{ color: 'var(--kale-blue)' }} />
                </div>
                <span className="text-xs" style={{ color: 'var(--muted-foreground)' }}>Berths</span>
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--kale-blue)' }}>
                {data.berths.length}
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-3" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center gap-2 mb-1">
                <div className="w-7 h-7 rounded-full flex items-center justify-center"
                  style={{ backgroundColor: 'var(--kale-sky)' }}>
                  <Cpu className="w-3.5 h-3.5" style={{ color: 'var(--kale-blue)' }} />
                </div>
                <span className="text-xs" style={{ color: 'var(--muted-foreground)' }}>Equipment</span>
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--kale-blue)' }}>
                {operationalEquipment}/{totalEquipment}
              </div>
              <div className="text-[10px]" style={{ color: 'var(--muted-foreground)' }}>Operational</div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-3" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center gap-2 mb-1">
                <div className="w-7 h-7 rounded-full flex items-center justify-center"
                  style={{ backgroundColor: 'var(--kale-sky)' }}>
                  <Users className="w-3.5 h-3.5" style={{ color: 'var(--kale-blue)' }} />
                </div>
                <span className="text-xs" style={{ color: 'var(--muted-foreground)' }}>Personnel</span>
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--kale-blue)' }}>
                {totalStaff}
              </div>
            </div>
          </div>

          {/* Integration Status */}
          <div className="bg-white rounded-lg shadow-sm border p-4" style={{ borderColor: 'var(--border)' }}>
            <div className="text-xs mb-2" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>Integration Status</div>
            <div className="flex items-center gap-3 px-3 py-2 rounded-lg" style={{ backgroundColor: 'var(--kale-sky)' }}>
              <CheckCircle2 className="w-4 h-4" style={{ color: 'var(--status-on-time)' }} />
              <div className="flex-1">
                <div className="text-xs" style={{ fontWeight: 600 }}>
                  {data.integration?.systemType?.replace('_', ' ').toUpperCase()}
                </div>
                <div className="text-[10px]" style={{ color: 'var(--muted-foreground)' }}>
                  Connected • Sync: {data.integration?.syncFrequency}
                </div>
              </div>
              <div className="flex gap-1.5">
                {Object.entries(data.integration?.dataSync || {}).filter(([_, v]) => v).map(([k]) => (
                  <span key={k} className="text-[10px] px-1.5 py-0.5 rounded capitalize"
                    style={{ backgroundColor: 'var(--status-on-time)', color: 'white', fontWeight: 600 }}>
                    {k.replace(/([A-Z])/g, ' $1').trim()}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Terminals */}
          <div className="bg-white rounded-lg shadow-sm border p-4" style={{ borderColor: 'var(--border)' }}>
            <div className="text-xs mb-3" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>Terminal Configuration</div>
            <div className="space-y-3">
              {data.terminals.map((terminal) => {
                const terminalBerths = data.berths.filter(b => b.terminalId === terminal.id);
                const terminalEquipment = data.equipment.filter(e => e.terminalId === terminal.id);

                return (
                  <div key={terminal.id} className="p-3 rounded-lg border" style={{ borderColor: 'var(--border)' }}>
                    <div className="flex items-center gap-2 mb-1">
                      <Building2 className="w-3.5 h-3.5" style={{ color: 'var(--kale-blue)' }} />
                      <span className="text-sm" style={{ fontWeight: 600, color: 'var(--kale-blue)' }}>
                        {terminal.name}
                      </span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded"
                        style={{ backgroundColor: 'var(--muted)', fontWeight: 600 }}>
                        {terminal.code}
                      </span>
                    </div>
                    <div className="text-[11px] mb-2" style={{ color: 'var(--muted-foreground)' }}>
                      {terminal.terminalType.replace('-', ' ')} • {terminal.operatingCompany} • {terminal.operationalHours}
                    </div>

                    <div className="grid grid-cols-3 gap-2">
                      {/* Berths */}
                      <div className="px-2.5 py-2 rounded" style={{ backgroundColor: 'var(--kale-sky)' }}>
                        <div className="text-[10px] mb-1" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
                          BERTHS ({terminalBerths.length})
                        </div>
                        <div className="space-y-0.5">
                          {terminalBerths.map((berth) => (
                            <div key={berth.id} className="text-[11px] flex items-center justify-between">
                              <span style={{ fontWeight: 500 }}>{berth.name}</span>
                              <span className="text-[10px]" style={{ color: 'var(--muted-foreground)' }}>
                                {berth.maxLOA}m
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Equipment */}
                      <div className="px-2.5 py-2 rounded" style={{ backgroundColor: 'var(--muted)' }}>
                        <div className="text-[10px] mb-1" style={{ fontWeight: 600 }}>
                          EQUIPMENT ({terminalEquipment.length})
                        </div>
                        <div className="space-y-0.5">
                          {['STS', 'RTG', 'MHC'].map((type) => {
                            const count = terminalEquipment.filter(e => e.type === type).length;
                            return count > 0 ? (
                              <div key={type} className="text-[11px] flex items-center justify-between">
                                <span>{type}</span>
                                <span className="font-mono text-[10px]">{count}</span>
                              </div>
                            ) : null;
                          })}
                        </div>
                      </div>

                      {/* Capacity */}
                      <div className="px-2.5 py-2 rounded" style={{ backgroundColor: 'var(--kale-sky)' }}>
                        <div className="text-[10px] mb-1" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
                          CAPACITY
                        </div>
                        <div className="space-y-0.5 text-[11px]">
                          <div className="flex justify-between">
                            <span style={{ color: 'var(--muted-foreground)' }}>Max LOA:</span>
                            <span style={{ fontWeight: 600 }}>
                              {Math.max(...terminalBerths.map(b => b.maxLOA))}m
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span style={{ color: 'var(--muted-foreground)' }}>Max Draft:</span>
                            <span style={{ fontWeight: 600 }}>
                              {Math.max(...terminalBerths.map(b => b.maxDraft))}m
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Safety Constraints */}
          {data.constraints.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm border p-4" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center gap-1.5 text-xs mb-2" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
                <Shield className="w-3.5 h-3.5" />
                Active Safety Constraints ({data.constraints.length})
              </div>
              <div className="grid grid-cols-2 gap-2">
                {data.constraints.map((constraint) => (
                  <div key={constraint.id} className="px-2.5 py-2 rounded border" style={{ borderColor: 'var(--border)' }}>
                    <div className="text-xs" style={{ fontWeight: 600 }}>{constraint.name}</div>
                    <div className="text-[10px] mt-0.5" style={{ color: 'var(--muted-foreground)' }}>
                      {constraint.description}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
