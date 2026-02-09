import { useState } from 'react';
import { X, Settings, Bell, Database, Clock, Shield, Zap, Building2, Anchor } from 'lucide-react';

interface SettingsPanelProps {
  onClose: () => void;
  terminalData?: {
    terminals: Array<{ id: string; name: string }>;
  };
}

export function SettingsPanel({ onClose, terminalData }: SettingsPanelProps) {
  const [activeTab, setActiveTab] = useState<'general' | 'terminal'>('general');

  // General Settings
  const [notifications, setNotifications] = useState({
    arrivalUpdates: true,
    delayAlerts: true,
    constraintWarnings: true,
    berthingComplete: true,
    emailDigest: false,
  });

  const [systemSettings, setSystemSettings] = useState({
    autoRefresh: true,
    refreshInterval: 30,
    aiRecommendations: true,
    confidenceThreshold: 85,
    showPredictedETA: true,
  });

  // Terminal Settings
  const [terminalSettings, setTerminalSettings] = useState({
    defaultView: 'vessels' as 'vessels' | 'berths',
    timeWindow: '7days' as '7days' | 'year',
    enableAutoAllocation: false,
    requireApproval: true,
    showHistoricalAccuracy: true,
  });

  const [operationalSettings, setOperationalSettings] = useState({
    pilotLeadTime: 120, // minutes
    tugLeadTime: 90,
    bufferTime: 30,
    maxConcurrentBerthings: 3,
  });

  return (
    <div className="fixed inset-y-0 right-0 w-[500px] bg-white shadow-2xl z-50 flex flex-col border-l"
      style={{ borderColor: 'var(--border)' }}>
      {/* Header */}
      <div className="p-6 border-b" style={{ borderColor: 'var(--border)' }}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Settings className="w-6 h-6" style={{ color: 'var(--kale-blue)' }} />
            <h2 style={{ color: 'var(--kale-blue)', fontWeight: 700, fontSize: '1.25rem' }}>
              Settings
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <X className="w-5 h-5" style={{ color: 'var(--muted-foreground)' }} />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mt-4">
          <button
            onClick={() => setActiveTab('general')}
            className="flex-1 px-4 py-2 rounded-lg text-sm transition-colors"
            style={{
              backgroundColor: activeTab === 'general' ? 'var(--kale-blue)' : 'transparent',
              color: activeTab === 'general' ? 'white' : 'var(--foreground)',
              fontWeight: activeTab === 'general' ? 600 : 400,
            }}
          >
            General Settings
          </button>
          <button
            onClick={() => setActiveTab('terminal')}
            className="flex-1 px-4 py-2 rounded-lg text-sm transition-colors"
            style={{
              backgroundColor: activeTab === 'terminal' ? 'var(--kale-blue)' : 'transparent',
              color: activeTab === 'terminal' ? 'white' : 'var(--foreground)',
              fontWeight: activeTab === 'terminal' ? 600 : 400,
            }}
          >
            Terminal Settings
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        {activeTab === 'general' && (
          <div className="space-y-6">
            {/* Notification Settings */}
            <div className="bg-white rounded-xl border p-5" style={{ borderColor: 'var(--border)' }}>
              <h3 className="flex items-center gap-2 mb-4" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
                <Bell className="w-5 h-5" />
                Notification Preferences
              </h3>
              <div className="space-y-3">
                {[
                  { key: 'arrivalUpdates', label: 'Vessel Arrival Updates', desc: 'ETA changes and confirmations' },
                  { key: 'delayAlerts', label: 'Delay Alerts', desc: 'Berthing delays and schedule changes' },
                  { key: 'constraintWarnings', label: 'Constraint Warnings', desc: 'Weather, tide, and safety constraints' },
                  { key: 'berthingComplete', label: 'Berthing Completed', desc: 'Successful berthing notifications' },
                  { key: 'emailDigest', label: 'Daily Email Digest', desc: 'Summary of daily operations' },
                ].map((item) => (
                  <label key={item.key} className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={notifications[item.key as keyof typeof notifications]}
                      onChange={(e) => setNotifications(prev => ({ ...prev, [item.key]: e.target.checked }))}
                      className="mt-1"
                    />
                    <div className="flex-1">
                      <div style={{ fontWeight: 500 }}>{item.label}</div>
                      <div className="text-sm" style={{ color: 'var(--muted-foreground)' }}>{item.desc}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* System Settings */}
            <div className="bg-white rounded-xl border p-5" style={{ borderColor: 'var(--border)' }}>
              <h3 className="flex items-center gap-2 mb-4" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
                <Database className="w-5 h-5" />
                System Configuration
              </h3>
              <div className="space-y-4">
                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={systemSettings.autoRefresh}
                    onChange={(e) => setSystemSettings(prev => ({ ...prev, autoRefresh: e.target.checked }))}
                    className="mt-1"
                  />
                  <div className="flex-1">
                    <div style={{ fontWeight: 500 }}>Auto-refresh Data</div>
                    <div className="text-sm" style={{ color: 'var(--muted-foreground)' }}>
                      Automatically update vessel and berth data
                    </div>
                  </div>
                </label>

                {systemSettings.autoRefresh && (
                  <div className="ml-7">
                    <label className="block text-sm mb-2" style={{ color: 'var(--foreground)', fontWeight: 500 }}>
                      Refresh Interval (seconds)
                    </label>
                    <input
                      type="number"
                      value={systemSettings.refreshInterval}
                      onChange={(e) => setSystemSettings(prev => ({ ...prev, refreshInterval: parseInt(e.target.value) || 30 }))}
                      min="10"
                      max="300"
                      className="w-full px-3 py-2 rounded-lg border"
                      style={{ borderColor: 'var(--border)', backgroundColor: 'var(--input-background)' }}
                    />
                  </div>
                )}

                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={systemSettings.aiRecommendations}
                    onChange={(e) => setSystemSettings(prev => ({ ...prev, aiRecommendations: e.target.checked }))}
                    className="mt-1"
                  />
                  <div className="flex-1">
                    <div style={{ fontWeight: 500 }}>AI Recommendations</div>
                    <div className="text-sm" style={{ color: 'var(--muted-foreground)' }}>
                      Show AI-powered berthing suggestions
                    </div>
                  </div>
                </label>

                {systemSettings.aiRecommendations && (
                  <div className="ml-7">
                    <label className="block text-sm mb-2" style={{ color: 'var(--foreground)', fontWeight: 500 }}>
                      Confidence Threshold (%)
                    </label>
                    <input
                      type="range"
                      value={systemSettings.confidenceThreshold}
                      onChange={(e) => setSystemSettings(prev => ({ ...prev, confidenceThreshold: parseInt(e.target.value) }))}
                      min="50"
                      max="99"
                      className="w-full"
                    />
                    <div className="text-sm text-center" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
                      {systemSettings.confidenceThreshold}%
                    </div>
                  </div>
                )}

                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={systemSettings.showPredictedETA}
                    onChange={(e) => setSystemSettings(prev => ({ ...prev, showPredictedETA: e.target.checked }))}
                    className="mt-1"
                  />
                  <div className="flex-1">
                    <div style={{ fontWeight: 500 }}>Show Predicted ETA</div>
                    <div className="text-sm" style={{ color: 'var(--muted-foreground)' }}>
                      Display AI-predicted arrival times alongside declared
                    </div>
                  </div>
                </label>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'terminal' && (
          <div className="space-y-6">
            {/* Display Settings */}
            <div className="bg-white rounded-xl border p-5" style={{ borderColor: 'var(--border)' }}>
              <h3 className="flex items-center gap-2 mb-4" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
                <Building2 className="w-5 h-5" />
                Display Preferences
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm mb-2" style={{ color: 'var(--foreground)', fontWeight: 500 }}>
                    Default View
                  </label>
                  <select
                    value={terminalSettings.defaultView}
                    onChange={(e) => setTerminalSettings(prev => ({ ...prev, defaultView: e.target.value as 'vessels' | 'berths' }))}
                    className="w-full px-3 py-2 rounded-lg border"
                    style={{ borderColor: 'var(--border)', backgroundColor: 'var(--input-background)' }}
                  >
                    <option value="vessels">Upcoming Vessels Timeline</option>
                    <option value="berths">Berth Overview</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm mb-2" style={{ color: 'var(--foreground)', fontWeight: 500 }}>
                    Time Window
                  </label>
                  <select
                    value={terminalSettings.timeWindow}
                    onChange={(e) => setTerminalSettings(prev => ({ ...prev, timeWindow: e.target.value as '7days' | 'year' }))}
                    className="w-full px-3 py-2 rounded-lg border"
                    style={{ borderColor: 'var(--border)', backgroundColor: 'var(--input-background)' }}
                  >
                    <option value="7days">7 Days</option>
                    <option value="year">Full Year</option>
                  </select>
                </div>

                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={terminalSettings.showHistoricalAccuracy}
                    onChange={(e) => setTerminalSettings(prev => ({ ...prev, showHistoricalAccuracy: e.target.checked }))}
                    className="mt-1"
                  />
                  <div className="flex-1">
                    <div style={{ fontWeight: 500 }}>Show ATA Accuracy Scores</div>
                    <div className="text-sm" style={{ color: 'var(--muted-foreground)' }}>
                      Display historical arrival time accuracy
                    </div>
                  </div>
                </label>
              </div>
            </div>

            {/* Berth Allocation */}
            <div className="bg-white rounded-xl border p-5" style={{ borderColor: 'var(--border)' }}>
              <h3 className="flex items-center gap-2 mb-4" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
                <Anchor className="w-5 h-5" />
                Berth Allocation
              </h3>
              <div className="space-y-4">
                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={terminalSettings.enableAutoAllocation}
                    onChange={(e) => setTerminalSettings(prev => ({ ...prev, enableAutoAllocation: e.target.checked }))}
                    className="mt-1"
                  />
                  <div className="flex-1">
                    <div style={{ fontWeight: 500 }}>Enable Auto-allocation</div>
                    <div className="text-sm" style={{ color: 'var(--muted-foreground)' }}>
                      Automatically assign berths based on AI recommendations
                    </div>
                  </div>
                </label>

                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={terminalSettings.requireApproval}
                    onChange={(e) => setTerminalSettings(prev => ({ ...prev, requireApproval: e.target.checked }))}
                    className="mt-1"
                  />
                  <div className="flex-1">
                    <div style={{ fontWeight: 500 }}>Require Manual Approval</div>
                    <div className="text-sm" style={{ color: 'var(--muted-foreground)' }}>
                      All allocations require operator confirmation
                    </div>
                  </div>
                </label>
              </div>
            </div>

            {/* Operational Parameters */}
            <div className="bg-white rounded-xl border p-5" style={{ borderColor: 'var(--border)' }}>
              <h3 className="flex items-center gap-2 mb-4" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
                <Clock className="w-5 h-5" />
                Operational Parameters
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm mb-2" style={{ color: 'var(--foreground)', fontWeight: 500 }}>
                    Pilot Lead Time (minutes)
                  </label>
                  <input
                    type="number"
                    value={operationalSettings.pilotLeadTime}
                    onChange={(e) => setOperationalSettings(prev => ({ ...prev, pilotLeadTime: parseInt(e.target.value) || 120 }))}
                    className="w-full px-3 py-2 rounded-lg border"
                    style={{ borderColor: 'var(--border)', backgroundColor: 'var(--input-background)' }}
                  />
                </div>

                <div>
                  <label className="block text-sm mb-2" style={{ color: 'var(--foreground)', fontWeight: 500 }}>
                    Tug Lead Time (minutes)
                  </label>
                  <input
                    type="number"
                    value={operationalSettings.tugLeadTime}
                    onChange={(e) => setOperationalSettings(prev => ({ ...prev, tugLeadTime: parseInt(e.target.value) || 90 }))}
                    className="w-full px-3 py-2 rounded-lg border"
                    style={{ borderColor: 'var(--border)', backgroundColor: 'var(--input-background)' }}
                  />
                </div>

                <div>
                  <label className="block text-sm mb-2" style={{ color: 'var(--foreground)', fontWeight: 500 }}>
                    Buffer Time (minutes)
                  </label>
                  <input
                    type="number"
                    value={operationalSettings.bufferTime}
                    onChange={(e) => setOperationalSettings(prev => ({ ...prev, bufferTime: parseInt(e.target.value) || 30 }))}
                    className="w-full px-3 py-2 rounded-lg border"
                    style={{ borderColor: 'var(--border)', backgroundColor: 'var(--input-background)' }}
                  />
                </div>

                <div>
                  <label className="block text-sm mb-2" style={{ color: 'var(--foreground)', fontWeight: 500 }}>
                    Max Concurrent Berthings
                  </label>
                  <input
                    type="number"
                    value={operationalSettings.maxConcurrentBerthings}
                    onChange={(e) => setOperationalSettings(prev => ({ ...prev, maxConcurrentBerthings: parseInt(e.target.value) || 3 }))}
                    className="w-full px-3 py-2 rounded-lg border"
                    style={{ borderColor: 'var(--border)', backgroundColor: 'var(--input-background)' }}
                  />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-6 border-t" style={{ borderColor: 'var(--border)' }}>
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-3 rounded-lg border transition-colors"
            style={{ borderColor: 'var(--border)', color: 'var(--kale-blue)', fontWeight: 600 }}
          >
            Cancel
          </button>
          <button
            onClick={onClose}
            className="flex-1 px-4 py-3 rounded-lg transition-colors"
            style={{ backgroundColor: 'var(--kale-blue)', color: 'white', fontWeight: 600 }}
          >
            Save Settings
          </button>
        </div>
      </div>
    </div>
  );
}
