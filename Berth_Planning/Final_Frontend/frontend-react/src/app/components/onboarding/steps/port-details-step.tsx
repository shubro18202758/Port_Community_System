import { useState } from 'react';
import { Anchor, MapPin, Globe, Mail, Phone } from 'lucide-react';
import type { PortData } from '../port-onboarding-wizard';

interface PortDetailsStepProps {
  data: PortData | null;
  onChange: (data: PortData) => void;
}

export function PortDetailsStep({ data, onChange }: PortDetailsStepProps) {
  const [formData, setFormData] = useState<PortData>(
    data || {
      portName: '',
      portCode: '',
      unlocode: '',
      country: '',
      timezone: '',
      coordinates: { latitude: 0, longitude: 0 },
      contactEmail: '',
      contactPhone: '',
    }
  );

  const handleChange = (field: keyof PortData, value: any) => {
    const updated = { ...formData, [field]: value };
    setFormData(updated);
    onChange(updated);
  };

  const handleCoordinateChange = (coord: 'latitude' | 'longitude', value: string) => {
    const updated = {
      ...formData,
      coordinates: {
        ...formData.coordinates,
        [coord]: parseFloat(value) || 0,
      },
    };
    setFormData(updated);
    onChange(updated);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="flex items-center gap-2 mb-2" style={{ color: 'var(--kale-blue)' }}>
          <Anchor className="w-6 h-6" />
          Port Details
        </h2>
        <p style={{ color: 'var(--muted-foreground)' }}>
          Enter the basic information about your port facility
        </p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border p-6" style={{ borderColor: 'var(--border)' }}>
        <div className="grid grid-cols-2 gap-6">
          {/* Port Name */}
          <div className="col-span-2">
            <label className="block text-sm mb-2" style={{ color: 'var(--foreground)', fontWeight: 600 }}>
              Port Name *
            </label>
            <input
              type="text"
              value={formData.portName}
              onChange={(e) => handleChange('portName', e.target.value)}
              placeholder="e.g., Port of Singapore"
              className="w-full px-4 py-3 rounded-lg border"
              style={{
                borderColor: 'var(--border)',
                backgroundColor: 'var(--input-background)',
              }}
            />
          </div>

          {/* Port Code */}
          <div>
            <label className="block text-sm mb-2" style={{ color: 'var(--foreground)', fontWeight: 600 }}>
              Port Code *
            </label>
            <input
              type="text"
              value={formData.portCode}
              onChange={(e) => handleChange('portCode', e.target.value.toUpperCase())}
              placeholder="e.g., SGSIN"
              className="w-full px-4 py-3 rounded-lg border"
              style={{
                borderColor: 'var(--border)',
                backgroundColor: 'var(--input-background)',
              }}
            />
          </div>

          {/* UN/LOCODE */}
          <div>
            <label className="block text-sm mb-2" style={{ color: 'var(--foreground)', fontWeight: 600 }}>
              UN/LOCODE *
            </label>
            <input
              type="text"
              value={formData.unlocode}
              onChange={(e) => handleChange('unlocode', e.target.value.toUpperCase())}
              placeholder="e.g., SGSIN"
              className="w-full px-4 py-3 rounded-lg border"
              style={{
                borderColor: 'var(--border)',
                backgroundColor: 'var(--input-background)',
              }}
            />
          </div>

          {/* Country */}
          <div>
            <label className="block text-sm mb-2" style={{ color: 'var(--foreground)', fontWeight: 600 }}>
              Country *
            </label>
            <input
              type="text"
              value={formData.country}
              onChange={(e) => handleChange('country', e.target.value)}
              placeholder="e.g., Singapore"
              className="w-full px-4 py-3 rounded-lg border"
              style={{
                borderColor: 'var(--border)',
                backgroundColor: 'var(--input-background)',
              }}
            />
          </div>

          {/* Timezone */}
          <div>
            <label className="block text-sm mb-2" style={{ color: 'var(--foreground)', fontWeight: 600 }}>
              Timezone *
            </label>
            <select
              value={formData.timezone}
              onChange={(e) => handleChange('timezone', e.target.value)}
              className="w-full px-4 py-3 rounded-lg border"
              style={{
                borderColor: 'var(--border)',
                backgroundColor: 'var(--input-background)',
              }}
            >
              <option value="">Select timezone</option>
              <option value="UTC">UTC</option>
              <option value="Asia/Singapore">Asia/Singapore (UTC+8)</option>
              <option value="Europe/London">Europe/London (UTC+0/+1)</option>
              <option value="America/New_York">America/New York (UTC-5/-4)</option>
              <option value="Asia/Dubai">Asia/Dubai (UTC+4)</option>
              <option value="Europe/Rotterdam">Europe/Rotterdam (UTC+1/+2)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Coordinates */}
      <div className="bg-white rounded-xl shadow-sm border p-6" style={{ borderColor: 'var(--border)' }}>
        <h3 className="flex items-center gap-2 mb-4" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
          <MapPin className="w-5 h-5" />
          Geographic Coordinates
        </h3>
        <div className="grid grid-cols-2 gap-6">
          <div>
            <label className="block text-sm mb-2" style={{ color: 'var(--foreground)', fontWeight: 600 }}>
              Latitude *
            </label>
            <input
              type="number"
              step="0.000001"
              value={formData.coordinates.latitude}
              onChange={(e) => handleCoordinateChange('latitude', e.target.value)}
              placeholder="e.g., 1.2644"
              className="w-full px-4 py-3 rounded-lg border"
              style={{
                borderColor: 'var(--border)',
                backgroundColor: 'var(--input-background)',
              }}
            />
          </div>
          <div>
            <label className="block text-sm mb-2" style={{ color: 'var(--foreground)', fontWeight: 600 }}>
              Longitude *
            </label>
            <input
              type="number"
              step="0.000001"
              value={formData.coordinates.longitude}
              onChange={(e) => handleCoordinateChange('longitude', e.target.value)}
              placeholder="e.g., 103.8227"
              className="w-full px-4 py-3 rounded-lg border"
              style={{
                borderColor: 'var(--border)',
                backgroundColor: 'var(--input-background)',
              }}
            />
          </div>
        </div>
      </div>

      {/* Contact Information */}
      <div className="bg-white rounded-xl shadow-sm border p-6" style={{ borderColor: 'var(--border)' }}>
        <h3 className="flex items-center gap-2 mb-4" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
          <Globe className="w-5 h-5" />
          Contact Information
        </h3>
        <div className="grid grid-cols-2 gap-6">
          <div>
            <label className="block text-sm mb-2" style={{ color: 'var(--foreground)', fontWeight: 600 }}>
              <Mail className="w-4 h-4 inline mr-1" />
              Contact Email *
            </label>
            <input
              type="email"
              value={formData.contactEmail}
              onChange={(e) => handleChange('contactEmail', e.target.value)}
              placeholder="operations@port.com"
              className="w-full px-4 py-3 rounded-lg border"
              style={{
                borderColor: 'var(--border)',
                backgroundColor: 'var(--input-background)',
              }}
            />
          </div>
          <div>
            <label className="block text-sm mb-2" style={{ color: 'var(--foreground)', fontWeight: 600 }}>
              <Phone className="w-4 h-4 inline mr-1" />
              Contact Phone *
            </label>
            <input
              type="tel"
              value={formData.contactPhone}
              onChange={(e) => handleChange('contactPhone', e.target.value)}
              placeholder="+65 6123 4567"
              className="w-full px-4 py-3 rounded-lg border"
              style={{
                borderColor: 'var(--border)',
                backgroundColor: 'var(--input-background)',
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
