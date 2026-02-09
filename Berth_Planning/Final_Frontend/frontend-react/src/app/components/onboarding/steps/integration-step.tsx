import { useState } from 'react';
import { Link2, Database, RefreshCw, CheckCircle2, AlertTriangle, Ship, FileText, Anchor, Users, Package, Shield } from 'lucide-react';
import type { IntegrationData } from '../port-onboarding-wizard';

interface IntegrationStepProps {
  data: IntegrationData | null;
  onChange: (data: IntegrationData) => void;
}

export function IntegrationStep({ data, onChange }: IntegrationStepProps) {
  const [formData, setFormData] = useState<IntegrationData>(
    data || {
      systemType: null,
      apiEndpoint: '',
      apiKey: '',
      dataSync: {
        vesselCalls: true,
        falForms: true,
        cargoManifest: true,
        crewLists: false,
      },
      syncFrequency: 'realtime',
    }
  );
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [fetchingData, setFetchingData] = useState(false);
  const [fetchedData, setFetchedData] = useState<{
    vesselCalls: number; falForms: number; cargoManifests: number; crewLists: number;
  } | null>(null);

  const handleChange = (field: keyof IntegrationData, value: any) => {
    const updated = { ...formData, [field]: value };
    setFormData(updated);
    onChange(updated);
  };

  const handleDataSyncChange = (field: keyof IntegrationData['dataSync'], value: boolean) => {
    const updated = {
      ...formData,
      dataSync: { ...formData.dataSync, [field]: value },
    };
    setFormData(updated);
    onChange(updated);
  };

  const testConnection = async () => {
    setTestingConnection(true);
    setConnectionStatus('idle');
    setFetchedData(null);

    // Simulate API test
    await new Promise((resolve) => setTimeout(resolve, 2000));

    setTestingConnection(false);
    setConnectionStatus('success');

    // Simulate fetching sample data after connection success
    setFetchingData(true);
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setFetchedData({
      vesselCalls: 24 + Math.floor(Math.random() * 20),
      falForms: 18 + Math.floor(Math.random() * 15),
      cargoManifests: 31 + Math.floor(Math.random() * 25),
      crewLists: 12 + Math.floor(Math.random() * 10),
    });
    setFetchingData(false);
  };

  const systemOptions = [
    {
      value: 'maritime_single_window',
      title: 'Maritime Single Window (MSW)',
      description: 'IMO-compliant platform for digital declaration of vessel, cargo, crew, and passenger data',
      features: ['FAL Forms', 'Vessel Calls', 'Cargo Manifest', 'Crew Lists'],
    },
    {
      value: 'port_community_system',
      title: 'Port Community System (PCS)',
      description: 'Electronic platform connecting multiple systems operated by organizations in a seaport',
      features: ['Vessel Planning', 'Cargo Tracking', 'EDI Messages', 'Real-time Updates'],
    },
    {
      value: 'ais',
      title: 'AIS Integration',
      description: 'Automatic Identification System for real-time vessel tracking and movement data',
      features: ['Live Vessel Positions', 'ETA Predictions', 'Route History', 'Vessel Details'],
    },
    {
      value: 'manual',
      title: 'Manual Entry',
      description: 'No integration - manually enter vessel and cargo data as needed',
      features: ['Full Control', 'No Dependencies', 'Custom Workflows'],
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="flex items-center gap-2 mb-2" style={{ color: 'var(--kale-blue)' }}>
          <Link2 className="w-6 h-6" />
          System Integration
        </h2>
        <p style={{ color: 'var(--muted-foreground)' }}>
          Connect SmartBerth AI with your existing maritime systems to automatically fetch vessel call data
        </p>
      </div>

      {/* System Selection */}
      <div className="bg-white rounded-xl shadow-sm border p-6" style={{ borderColor: 'var(--border)' }}>
        <h3 className="mb-4" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
          Select Integration Type
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {systemOptions.map((system) => (
            <div
              key={system.value}
              onClick={() => handleChange('systemType', system.value)}
              className="cursor-pointer rounded-lg border-2 p-4 transition-all"
              style={{
                borderColor:
                  formData.systemType === system.value
                    ? 'var(--kale-blue)'
                    : 'var(--border)',
                backgroundColor:
                  formData.systemType === system.value
                    ? 'var(--kale-sky)'
                    : 'white',
              }}
            >
              <div className="flex items-start justify-between mb-2">
                <div style={{ fontWeight: 600, color: 'var(--kale-blue)' }}>
                  {system.title}
                </div>
                {formData.systemType === system.value && (
                  <CheckCircle2 className="w-5 h-5" style={{ color: 'var(--kale-blue)' }} />
                )}
              </div>
              <p className="text-sm mb-3" style={{ color: 'var(--muted-foreground)' }}>
                {system.description}
              </p>
              <div className="flex flex-wrap gap-1">
                {system.features.map((feature) => (
                  <span
                    key={feature}
                    className="text-xs px-2 py-1 rounded"
                    style={{
                      backgroundColor: 'var(--muted)',
                      color: 'var(--foreground)',
                    }}
                  >
                    {feature}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* API Configuration */}
      {formData.systemType && formData.systemType !== 'manual' && (
        <div className="bg-white rounded-xl shadow-sm border p-6" style={{ borderColor: 'var(--border)' }}>
          <h3 className="flex items-center gap-2 mb-4" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
            <Database className="w-5 h-5" />
            API Configuration
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm mb-2" style={{ color: 'var(--foreground)', fontWeight: 600 }}>
                API Endpoint URL *
              </label>
              <input
                type="url"
                value={formData.apiEndpoint}
                onChange={(e) => handleChange('apiEndpoint', e.target.value)}
                placeholder="https://api.example.com/v1"
                className="w-full px-4 py-3 rounded-lg border"
                style={{
                  borderColor: 'var(--border)',
                  backgroundColor: 'var(--input-background)',
                }}
              />
            </div>
            <div>
              <label className="block text-sm mb-2" style={{ color: 'var(--foreground)', fontWeight: 600 }}>
                API Key / Token *
              </label>
              <input
                type="password"
                value={formData.apiKey}
                onChange={(e) => handleChange('apiKey', e.target.value)}
                placeholder="Enter your API key"
                className="w-full px-4 py-3 rounded-lg border"
                style={{
                  borderColor: 'var(--border)',
                  backgroundColor: 'var(--input-background)',
                }}
              />
            </div>
            <button
              onClick={testConnection}
              disabled={!formData.apiEndpoint || !formData.apiKey || testingConnection}
              className="flex items-center gap-2 px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
              style={{
                backgroundColor: 'var(--kale-teal)',
                color: 'white',
                fontWeight: 600,
              }}
            >
              {testingConnection ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Link2 className="w-4 h-4" />
              )}
              {testingConnection ? 'Testing Connection...' : 'Test Connection'}
            </button>
            {connectionStatus === 'success' && (
              <div className="flex items-center gap-2 p-3 rounded-lg" style={{ backgroundColor: 'var(--status-on-time)', color: 'white' }}>
                <CheckCircle2 className="w-4 h-4" />
                <span className="text-sm">Connection successful! Integration verified.</span>
              </div>
            )}
            {connectionStatus === 'error' && (
              <div className="flex items-center gap-2 p-3 rounded-lg" style={{ backgroundColor: 'var(--status-critical)', color: 'white' }}>
                <AlertTriangle className="w-4 h-4" />
                <span className="text-sm">Connection failed. Please check your credentials.</span>
              </div>
            )}

            {/* Data fetch simulation */}
            {fetchingData && (
              <div className="flex items-center gap-3 p-4 rounded-lg border animate-pulse" style={{ borderColor: 'var(--kale-blue)', backgroundColor: 'var(--kale-sky)' }}>
                <RefreshCw className="w-5 h-5 animate-spin" style={{ color: 'var(--kale-blue)' }} />
                <div>
                  <div className="text-sm font-semibold" style={{ color: 'var(--kale-blue)' }}>Fetching data from {formData.systemType === 'maritime_single_window' ? 'Maritime Single Window' : formData.systemType === 'port_community_system' ? 'Port Community System' : 'AIS'}...</div>
                  <div className="text-xs mt-1" style={{ color: 'var(--muted-foreground)' }}>Retrieving vessel calls, FAL forms, and cargo manifests</div>
                </div>
              </div>
            )}
            {fetchedData && !fetchingData && (
              <div className="rounded-lg border overflow-hidden" style={{ borderColor: '#A7F3D0' }}>
                <div className="px-4 py-2 flex items-center gap-2" style={{ backgroundColor: '#ECFDF5' }}>
                  <CheckCircle2 className="w-4 h-4" style={{ color: '#059669' }} />
                  <span className="text-sm font-semibold" style={{ color: '#059669' }}>Data Retrieved Successfully</span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-0 divide-x" style={{ borderColor: '#E5E7EB' }}>
                  {[
                    { icon: Ship, label: 'Vessel Calls', count: fetchedData.vesselCalls, color: '#0A4D8C' },
                    { icon: FileText, label: 'FAL Forms', count: fetchedData.falForms, color: '#7C3AED' },
                    { icon: Package, label: 'Cargo Manifests', count: fetchedData.cargoManifests, color: '#D97706' },
                    { icon: Users, label: 'Crew Lists', count: fetchedData.crewLists, color: '#059669' },
                  ].map((item) => (
                    <div key={item.label} className="p-3 text-center">
                      <item.icon className="w-5 h-5 mx-auto mb-1" style={{ color: item.color }} />
                      <div className="text-lg font-bold" style={{ color: item.color }}>{item.count}</div>
                      <div className="text-[10px]" style={{ color: 'var(--muted-foreground)' }}>{item.label}</div>
                    </div>
                  ))}
                </div>
                <div className="px-4 py-2 text-xs" style={{ backgroundColor: '#F9FAFB', color: 'var(--muted-foreground)' }}>
                  SmartBerth AI will continuously sync this data based on your selected frequency.
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Data Sync Configuration */}
      {formData.systemType && (
        <div className="bg-white rounded-xl shadow-sm border p-6" style={{ borderColor: 'var(--border)' }}>
          <h3 className="mb-4" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
            Data Synchronization
          </h3>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              {[
                { key: 'vesselCalls', label: 'Vessel Call Data', desc: 'Vessel arrivals, departures, and berth assignments' },
                { key: 'falForms', label: 'FAL Forms', desc: 'IMO FAL Convention forms (1-7)' },
                { key: 'cargoManifest', label: 'Cargo Manifest', desc: 'Container lists, cargo details, and hazmat declarations' },
                { key: 'crewLists', label: 'Crew & Passenger Lists', desc: 'Crew declarations and passenger manifests' },
              ].map((item) => (
                <label
                  key={item.key}
                  className="flex items-start gap-3 p-4 rounded-lg border cursor-pointer"
                  style={{
                    borderColor: formData.dataSync[item.key as keyof typeof formData.dataSync]
                      ? 'var(--kale-blue)'
                      : 'var(--border)',
                    backgroundColor: formData.dataSync[item.key as keyof typeof formData.dataSync]
                      ? 'var(--kale-sky)'
                      : 'white',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={formData.dataSync[item.key as keyof typeof formData.dataSync]}
                    onChange={(e) =>
                      handleDataSyncChange(item.key as keyof typeof formData.dataSync, e.target.checked)
                    }
                    className="mt-1"
                  />
                  <div className="flex-1">
                    <div style={{ fontWeight: 600, color: 'var(--foreground)' }}>{item.label}</div>
                    <div className="text-sm mt-1" style={{ color: 'var(--muted-foreground)' }}>
                      {item.desc}
                    </div>
                  </div>
                </label>
              ))}
            </div>

            <div>
              <label className="block text-sm mb-2" style={{ color: 'var(--foreground)', fontWeight: 600 }}>
                Sync Frequency
              </label>
              <select
                value={formData.syncFrequency}
                onChange={(e) => handleChange('syncFrequency', e.target.value)}
                className="w-full px-4 py-3 rounded-lg border"
                style={{
                  borderColor: 'var(--border)',
                  backgroundColor: 'var(--input-background)',
                }}
              >
                <option value="realtime">Real-time (Recommended)</option>
                <option value="hourly">Every Hour</option>
                <option value="daily">Daily</option>
              </select>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
