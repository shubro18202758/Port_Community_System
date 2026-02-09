import { useState } from 'react';
import { Ship, Building2, Globe, ChevronRight, Shield, Users, Anchor, Eye, Settings } from 'lucide-react';

export type UserRole = 'port_operator' | 'terminal_operator';

export interface RoleConfig {
  role: UserRole;
  assignedTerminalId?: string;
  assignedTerminalName?: string;
  operatorName: string;
}

interface RoleSelectionProps {
  terminals: Array<{ id: string; name: string; code: string; terminalType: string }>;
  portName: string;
  onSelect: (config: RoleConfig) => void;
}

export function RoleSelection({ terminals, portName, onSelect }: RoleSelectionProps) {
  const [selectedRole, setSelectedRole] = useState<UserRole | null>(null);
  const [selectedTerminalId, setSelectedTerminalId] = useState<string>('');
  const [operatorName, setOperatorName] = useState('');
  const [step, setStep] = useState<'role' | 'details'>('role');

  const handleContinue = () => {
    if (selectedRole === 'port_operator') {
      onSelect({ role: 'port_operator', operatorName: operatorName || 'Port Operator' });
    } else if (selectedRole === 'terminal_operator' && selectedTerminalId) {
      const terminal = terminals.find(t => t.id === selectedTerminalId);
      onSelect({
        role: 'terminal_operator',
        assignedTerminalId: selectedTerminalId,
        assignedTerminalName: terminal?.name || '',
        operatorName: operatorName || 'Terminal Operator',
      });
    }
  };

  const canProceed =
    selectedRole === 'port_operator' ||
    (selectedRole === 'terminal_operator' && selectedTerminalId !== '');

  return (
    <div className="fixed inset-0 flex items-center justify-center z-50" style={{ background: 'linear-gradient(135deg, #0A4D8C 0%, #0C7BBD 50%, #0A4D8C 100%)' }}>
      {/* Animated background particles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="absolute rounded-full opacity-10" style={{
            width: 200 + i * 80, height: 200 + i * 80,
            left: `${10 + i * 15}%`, top: `${20 + (i % 3) * 25}%`,
            background: 'radial-gradient(circle, rgba(255,255,255,0.15), transparent)',
            animation: `float ${8 + i * 2}s ease-in-out infinite alternate`,
          }} />
        ))}
      </div>

      <div style={{ maxWidth: 720, width: '100%', padding: '0 24px', position: 'relative', zIndex: 1, maxHeight: '90vh', overflowY: 'auto' }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, marginBottom: 16 }}>
            <div style={{ width: 48, height: 48, borderRadius: 12, background: 'rgba(255,255,255,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', backdropFilter: 'blur(8px)' }}>
              <Anchor style={{ width: 28, height: 28, color: 'white' }} />
            </div>
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontSize: 24, fontWeight: 800, color: 'white', letterSpacing: -0.5 }}>SmartBerth AI</div>
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.7)', fontWeight: 500, letterSpacing: 1 }}>BERTH PLANNING SYSTEM</div>
            </div>
          </div>
          <div style={{ fontSize: 14, color: 'rgba(255,255,255,0.8)', fontWeight: 500 }}>
            {portName && <span style={{ color: 'white', fontWeight: 600 }}>{portName}</span>}
          </div>
        </div>

        {step === 'role' ? (
          <>
            <div style={{ textAlign: 'center', marginBottom: 24 }}>
              <h2 style={{ fontSize: 20, fontWeight: 700, color: 'white', marginBottom: 6 }}>Select Your Role</h2>
              <p style={{ fontSize: 13, color: 'rgba(255,255,255,0.7)' }}>Choose how you'll interact with SmartBerth AI</p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 24 }}>
              {/* Port Operator Card */}
              <button
                onClick={() => { setSelectedRole('port_operator'); setStep('details'); }}
                style={{
                  padding: 24, borderRadius: 16, border: '2px solid',
                  borderColor: selectedRole === 'port_operator' ? 'white' : 'rgba(255,255,255,0.2)',
                  background: selectedRole === 'port_operator' ? 'rgba(255,255,255,0.15)' : 'rgba(255,255,255,0.05)',
                  backdropFilter: 'blur(12px)', cursor: 'pointer', textAlign: 'left',
                  transition: 'all 0.2s',
                }}
              >
                <div style={{ width: 52, height: 52, borderRadius: 12, background: 'linear-gradient(135deg, #059669, #10B981)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>
                  <Globe style={{ width: 28, height: 28, color: 'white' }} />
                </div>
                <div style={{ fontSize: 16, fontWeight: 700, color: 'white', marginBottom: 4 }}>Port Operator</div>
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.7)', lineHeight: 1.5, marginBottom: 16 }}>
                  Full visibility across all terminals. Monitor port-wide operations, manage berth allocations, and oversee all terminal activities.
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {['View all terminals & berths', 'Port-wide analytics & KPIs', 'Cross-terminal vessel management', 'Resource allocation oversight'].map(f => (
                    <div key={f} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 10, color: 'rgba(255,255,255,0.8)' }}>
                      <Eye style={{ width: 10, height: 10, flexShrink: 0 }} /> {f}
                    </div>
                  ))}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 4, marginTop: 16, fontSize: 12, fontWeight: 600, color: 'white' }}>
                  Select <ChevronRight style={{ width: 14, height: 14 }} />
                </div>
              </button>

              {/* Terminal Operator Card */}
              <button
                onClick={() => { setSelectedRole('terminal_operator'); setStep('details'); }}
                style={{
                  padding: 24, borderRadius: 16, border: '2px solid',
                  borderColor: selectedRole === 'terminal_operator' ? 'white' : 'rgba(255,255,255,0.2)',
                  background: selectedRole === 'terminal_operator' ? 'rgba(255,255,255,0.15)' : 'rgba(255,255,255,0.05)',
                  backdropFilter: 'blur(12px)', cursor: 'pointer', textAlign: 'left',
                  transition: 'all 0.2s',
                }}
              >
                <div style={{ width: 52, height: 52, borderRadius: 12, background: 'linear-gradient(135deg, #D97706, #F59E0B)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>
                  <Building2 style={{ width: 28, height: 28, color: 'white' }} />
                </div>
                <div style={{ fontSize: 16, fontWeight: 700, color: 'white', marginBottom: 4 }}>Terminal Operator</div>
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.7)', lineHeight: 1.5, marginBottom: 16 }}>
                  Focused view of your assigned terminal. Manage berths, vessels, and resources within your terminal's operations.
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {['Your terminal berths & vessels', 'Terminal-specific dashboard', 'Drag & drop berth allocation', 'Local resource management'].map(f => (
                    <div key={f} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 10, color: 'rgba(255,255,255,0.8)' }}>
                      <Settings style={{ width: 10, height: 10, flexShrink: 0 }} /> {f}
                    </div>
                  ))}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 4, marginTop: 16, fontSize: 12, fontWeight: 600, color: 'white' }}>
                  Select <ChevronRight style={{ width: 14, height: 14 }} />
                </div>
              </button>
            </div>
          </>
        ) : (
          <>
            {/* Details step */}
            <div style={{
              background: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(12px)',
              borderRadius: 16, border: '1px solid rgba(255,255,255,0.2)',
              padding: 32, marginBottom: 24,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
                <div style={{
                  width: 44, height: 44, borderRadius: 10,
                  background: selectedRole === 'port_operator' ? 'linear-gradient(135deg, #059669, #10B981)' : 'linear-gradient(135deg, #D97706, #F59E0B)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  {selectedRole === 'port_operator' ? <Globe style={{ width: 24, height: 24, color: 'white' }} /> : <Building2 style={{ width: 24, height: 24, color: 'white' }} />}
                </div>
                <div>
                  <div style={{ fontSize: 16, fontWeight: 700, color: 'white' }}>
                    {selectedRole === 'port_operator' ? 'Port Operator' : 'Terminal Operator'}
                  </div>
                  <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.6)' }}>
                    {selectedRole === 'port_operator' ? 'Full port access — all terminals visible' : 'Single terminal access'}
                  </div>
                </div>
              </div>

              {/* Operator Name */}
              <div style={{ marginBottom: 20 }}>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'rgba(255,255,255,0.8)', marginBottom: 6 }}>
                  Operator Name
                </label>
                <input
                  type="text"
                  value={operatorName}
                  onChange={e => setOperatorName(e.target.value)}
                  placeholder={selectedRole === 'port_operator' ? 'e.g. Port Authority Control Room' : 'e.g. Terminal A Operations'}
                  style={{
                    width: '100%', padding: '10px 14px', borderRadius: 8,
                    border: '1px solid rgba(255,255,255,0.3)', background: 'rgba(255,255,255,0.1)',
                    color: 'white', fontSize: 13, outline: 'none', boxSizing: 'border-box',
                  }}
                />
              </div>

              {/* Terminal Selection (only for terminal operator) */}
              {selectedRole === 'terminal_operator' && (
                <div style={{ marginBottom: 8 }}>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'rgba(255,255,255,0.8)', marginBottom: 6 }}>
                    Assigned Terminal *
                  </label>
                  {terminals.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 240, overflowY: 'auto', paddingRight: 4 }}>
                      {terminals.map(t => (
                        <button
                          key={t.id}
                          onClick={() => setSelectedTerminalId(t.id)}
                          style={{
                            padding: '12px 16px', borderRadius: 10, border: '2px solid',
                            borderColor: selectedTerminalId === t.id ? '#F59E0B' : 'rgba(255,255,255,0.15)',
                            background: selectedTerminalId === t.id ? 'rgba(245,158,11,0.15)' : 'rgba(255,255,255,0.05)',
                            cursor: 'pointer', textAlign: 'left', transition: 'all 0.15s',
                            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                            <Building2 style={{ width: 18, height: 18, color: selectedTerminalId === t.id ? '#F59E0B' : 'rgba(255,255,255,0.5)' }} />
                            <div>
                              <div style={{ fontSize: 13, fontWeight: 600, color: 'white' }}>{t.name}</div>
                              <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.5)' }}>{t.code} — {t.terminalType}</div>
                            </div>
                          </div>
                          {selectedTerminalId === t.id && (
                            <div style={{ width: 20, height: 20, borderRadius: '50%', background: '#F59E0B', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                              <Shield style={{ width: 12, height: 12, color: 'white' }} />
                            </div>
                          )}
                        </button>
                      ))}
                    </div>
                  ) : (
                    <div style={{ padding: 16, borderRadius: 8, background: 'rgba(255,255,255,0.05)', textAlign: 'center' }}>
                      <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.5)' }}>No terminals configured yet. Complete onboarding first.</div>
                    </div>
                  )}
                </div>
              )}

              {/* Port Operator info */}
              {selectedRole === 'port_operator' && terminals.length > 0 && (
                <div style={{ padding: 12, borderRadius: 8, background: 'rgba(5,150,105,0.15)', border: '1px solid rgba(5,150,105,0.3)' }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: '#6EE7B7', marginBottom: 4 }}>
                    <Users style={{ width: 12, height: 12, display: 'inline', marginRight: 4 }} />
                    You will have access to {terminals.length} terminal{terminals.length !== 1 ? 's' : ''}
                  </div>
                  <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.6)' }}>
                    {terminals.map(t => t.name).join(' • ')}
                  </div>
                </div>
              )}
            </div>

            {/* Actions */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <button
                onClick={() => setStep('role')}
                style={{
                  padding: '10px 20px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.3)',
                  background: 'transparent', color: 'white', fontSize: 13, fontWeight: 600, cursor: 'pointer',
                }}
              >
                Back
              </button>
              <button
                onClick={handleContinue}
                disabled={!canProceed}
                style={{
                  padding: '10px 28px', borderRadius: 8, border: 'none',
                  background: canProceed ? 'white' : 'rgba(255,255,255,0.2)',
                  color: canProceed ? '#0A4D8C' : 'rgba(255,255,255,0.4)',
                  fontSize: 13, fontWeight: 700, cursor: canProceed ? 'pointer' : 'not-allowed',
                  display: 'flex', alignItems: 'center', gap: 6, transition: 'all 0.2s',
                }}
              >
                Enter Operations <ChevronRight style={{ width: 16, height: 16 }} />
              </button>
            </div>
          </>
        )}
      </div>

      <style>{`
        @keyframes float {
          from { transform: translateY(0) rotate(0deg); }
          to { transform: translateY(-30px) rotate(5deg); }
        }
      `}</style>
    </div>
  );
}
