import { useState } from 'react';
import { Shield, Plus, Edit2, Trash2 } from 'lucide-react';
import type { Constraint } from '../port-onboarding-wizard';

interface ConstraintsStepProps {
  data: Constraint[];
  onChange: (data: Constraint[]) => void;
}

const presetConstraints: Omit<Constraint, 'id'>[] = [
  {
    type: 'weather',
    name: 'Wind Speed Restriction',
    description: 'Crane operations suspended above threshold',
    threshold: '25 knots',
    action: 'Suspend crane operations',
  },
  {
    type: 'tide',
    name: 'Low Tide Draft Restriction',
    description: 'Minimum depth requirement for vessel entry',
    threshold: '12.5m',
    action: 'Delay berthing until high tide',
  },
  {
    type: 'environmental',
    name: 'Night-time Noise Restriction',
    description: 'Noise level limits during night hours',
    threshold: '22:00-06:00',
    action: 'Reduce cargo operations',
  },
  {
    type: 'safety',
    name: 'Hazmat Segregation',
    description: 'Dangerous goods require minimum distance',
    threshold: 'IMDG Class 1: 50m separation',
    action: 'Allocate dedicated berth',
  },
];

export function ConstraintsStep({ data, onChange }: ConstraintsStepProps) {
  const [constraints, setConstraints] = useState<Constraint[]>(data);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState<Partial<Constraint>>({});

  const handleAddPreset = (preset: Omit<Constraint, 'id'>) => {
    const newConstraint: Constraint = { id: `C${Date.now()}`, ...preset };
    const updated = [...constraints, newConstraint];
    setConstraints(updated);
    onChange(updated);
  };

  const handleAddCustom = () => {
    setEditingId('new');
    setFormData({
      type: 'operational',
      name: '',
      description: '',
      threshold: '',
      action: '',
    });
  };

  const handleSave = () => {
    if (!formData.name || !formData.description) return;

    let updated: Constraint[];
    if (editingId === 'new') {
      updated = [...constraints, { id: `C${Date.now()}`, ...formData } as Constraint];
    } else {
      updated = constraints.map((c) => (c.id === editingId ? { ...c, ...formData } as Constraint : c));
    }

    setConstraints(updated);
    onChange(updated);
    setEditingId(null);
  };

  const handleDelete = (id: string) => {
    const updated = constraints.filter((c) => c.id !== id);
    setConstraints(updated);
    onChange(updated);
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'weather': return 'var(--status-at-risk)';
      case 'tide': return 'var(--kale-ocean)';
      case 'environmental': return 'var(--kale-teal)';
      case 'safety': return 'var(--status-critical)';
      default: return 'var(--kale-blue)';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'weather': return '🌪️';
      case 'tide': return '🌊';
      case 'environmental': return '🌍';
      case 'safety': return '⚠️';
      default: return '⚙️';
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="flex items-center gap-2 mb-1 text-lg" style={{ color: 'var(--kale-blue)' }}>
          <Shield className="w-5 h-5" />
          Safety & Constraints
        </h2>
        <p className="text-sm" style={{ color: 'var(--muted-foreground)' }}>
          Define operational constraints and safety requirements
        </p>
      </div>

      {/* Preset Constraints */}
      <div>
        <h3 className="text-xs mb-2" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
          Common Constraints (Quick Add)
        </h3>
        <div className="grid grid-cols-2 gap-2">
          {presetConstraints.filter(p => !constraints.some(c => c.name === p.name)).map((preset) => (
            <div key={preset.name} onClick={() => handleAddPreset(preset)}
              className="cursor-pointer p-2.5 rounded-lg border-2 border-dashed transition-all hover:border-solid"
              style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center gap-2">
                <span className="text-base">{getTypeIcon(preset.type)}</span>
                <div className="flex-1 min-w-0">
                  <div className="text-xs" style={{ fontWeight: 600 }}>{preset.name}</div>
                  <div className="text-[10px] truncate" style={{ color: 'var(--muted-foreground)' }}>
                    {preset.description}
                  </div>
                </div>
                <Plus className="w-3.5 h-3.5 flex-shrink-0" style={{ color: 'var(--kale-blue)' }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Custom Constraint Button */}
      {!editingId && (
        <button onClick={handleAddCustom}
          className="flex items-center gap-2 px-3 py-2 rounded-lg border-2 border-dashed w-full text-sm"
          style={{ borderColor: 'var(--kale-blue)', color: 'var(--kale-blue)', fontWeight: 600 }}>
          <Plus className="w-4 h-4" />
          Add Custom Constraint
        </button>
      )}

      {/* Edit Form */}
      {editingId && (
        <div className="bg-white rounded-lg shadow-sm border p-4" style={{ borderColor: 'var(--border)' }}>
          <h3 className="text-sm mb-3" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
            {editingId === 'new' ? 'New Constraint' : 'Edit Constraint'}
          </h3>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs mb-1" style={{ fontWeight: 600 }}>Name *</label>
                <input type="text" value={formData.name || ''}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Maximum vessel length"
                  className="w-full px-3 py-2 rounded-lg border text-sm"
                  style={{ borderColor: 'var(--border)', backgroundColor: 'var(--input-background)' }} />
              </div>
              <div>
                <label className="block text-xs mb-1" style={{ fontWeight: 600 }}>Type *</label>
                <select value={formData.type || 'operational'}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value as Constraint['type'] })}
                  className="w-full px-3 py-2 rounded-lg border text-sm"
                  style={{ borderColor: 'var(--border)', backgroundColor: 'var(--input-background)' }}>
                  <option value="weather">Weather</option>
                  <option value="tide">Tide</option>
                  <option value="environmental">Environmental</option>
                  <option value="safety">Safety</option>
                  <option value="operational">Operational</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-xs mb-1" style={{ fontWeight: 600 }}>Description *</label>
              <textarea value={formData.description || ''}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Describe the constraint"
                rows={2}
                className="w-full px-3 py-2 rounded-lg border resize-none text-sm"
                style={{ borderColor: 'var(--border)', backgroundColor: 'var(--input-background)' }} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs mb-1" style={{ fontWeight: 600 }}>Threshold</label>
                <input type="text" value={formData.threshold || ''}
                  onChange={(e) => setFormData({ ...formData, threshold: e.target.value })}
                  placeholder="e.g., >30 knots"
                  className="w-full px-3 py-2 rounded-lg border text-sm"
                  style={{ borderColor: 'var(--border)', backgroundColor: 'var(--input-background)' }} />
              </div>
              <div>
                <label className="block text-xs mb-1" style={{ fontWeight: 600 }}>Action *</label>
                <input type="text" value={formData.action || ''}
                  onChange={(e) => setFormData({ ...formData, action: e.target.value })}
                  placeholder="e.g., Delay operations"
                  className="w-full px-3 py-2 rounded-lg border text-sm"
                  style={{ borderColor: 'var(--border)', backgroundColor: 'var(--input-background)' }} />
              </div>
            </div>
            <div className="flex gap-2">
              <button onClick={() => setEditingId(null)} className="flex-1 px-3 py-2 rounded-lg border text-sm"
                style={{ borderColor: 'var(--border)', color: 'var(--kale-blue)', fontWeight: 600 }}>Cancel</button>
              <button onClick={handleSave} className="flex-1 px-3 py-2 rounded-lg text-sm"
                style={{ backgroundColor: 'var(--kale-blue)', color: 'white', fontWeight: 600 }}>
                {editingId === 'new' ? 'Add Constraint' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Active Constraints - Card Grid */}
      {constraints.length > 0 && (
        <div>
          <h3 className="text-xs mb-2" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
            Active Constraints ({constraints.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {constraints.map((constraint) => (
              <div key={constraint.id} className="bg-white rounded-lg border p-3" style={{ borderColor: 'var(--border)' }}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-1.5 min-w-0">
                    <span className="text-base flex-shrink-0">{getTypeIcon(constraint.type)}</span>
                    <span className="text-sm truncate" style={{ fontWeight: 600, color: 'var(--kale-blue)' }}>{constraint.name}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded capitalize flex-shrink-0"
                      style={{ backgroundColor: `${getTypeColor(constraint.type)}20`, color: getTypeColor(constraint.type), fontWeight: 600 }}>
                      {constraint.type}
                    </span>
                  </div>
                  {!editingId && (
                    <div className="flex gap-1 flex-shrink-0">
                      <button onClick={() => { setEditingId(constraint.id); setFormData(constraint); }} className="p-1 rounded hover:bg-gray-100">
                        <Edit2 className="w-3 h-3" style={{ color: 'var(--kale-blue)' }} />
                      </button>
                      <button onClick={() => handleDelete(constraint.id)} className="p-1 rounded hover:bg-gray-100">
                        <Trash2 className="w-3 h-3" style={{ color: 'var(--status-critical)' }} />
                      </button>
                    </div>
                  )}
                </div>
                <p className="text-[10px] mb-2" style={{ color: 'var(--muted-foreground)' }}>{constraint.description}</p>
                <div className="grid grid-cols-2 gap-1.5 text-[10px] px-2 py-1.5 rounded" style={{ backgroundColor: 'var(--kale-sky)' }}>
                  {constraint.threshold && (
                    <div>
                      <div style={{ color: 'var(--muted-foreground)' }}>Threshold</div>
                      <div style={{ fontWeight: 600, fontSize: '11px' }}>{constraint.threshold}</div>
                    </div>
                  )}
                  <div>
                    <div style={{ color: 'var(--muted-foreground)' }}>Action</div>
                    <div style={{ fontWeight: 600, fontSize: '11px' }}>{constraint.action}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
