import { useState } from 'react';
import { Building2, Plus, Edit2, Trash2 } from 'lucide-react';
import type { Terminal } from '../port-onboarding-wizard';

interface TerminalSetupStepProps {
  data: Terminal[];
  onChange: (data: Terminal[]) => void;
}

export function TerminalSetupStep({ data, onChange }: TerminalSetupStepProps) {
  const [terminals, setTerminals] = useState<Terminal[]>(data);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState<Partial<Terminal>>({});

  const handleAdd = () => {
    setEditingId('new');
    setFormData({
      name: '',
      code: '',
      terminalType: 'container',
      operatingCompany: '',
      operationalHours: '24/7',
    });
  };

  const handleEdit = (terminal: Terminal) => {
    setEditingId(terminal.id);
    setFormData(terminal);
  };

  const handleSave = () => {
    if (!formData.name || !formData.code) return;

    let updated: Terminal[];
    if (editingId === 'new') {
      const newTerminal: Terminal = {
        id: `T${Date.now()}`,
        name: formData.name!,
        code: formData.code!,
        terminalType: formData.terminalType as Terminal['terminalType'],
        operatingCompany: formData.operatingCompany || '',
        operationalHours: formData.operationalHours || '24/7',
      };
      updated = [...terminals, newTerminal];
    } else {
      updated = terminals.map((t) =>
        t.id === editingId ? { ...t, ...formData } as Terminal : t
      );
    }

    setTerminals(updated);
    onChange(updated);
    setEditingId(null);
    setFormData({});
  };

  const handleDelete = (id: string) => {
    const updated = terminals.filter((t) => t.id !== id);
    setTerminals(updated);
    onChange(updated);
  };

  const handleCancel = () => {
    setEditingId(null);
    setFormData({});
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="flex items-center gap-2 mb-1 text-lg" style={{ color: 'var(--kale-blue)' }}>
          <Building2 className="w-5 h-5" />
          Terminal Setup
        </h2>
        <p className="text-sm" style={{ color: 'var(--muted-foreground)' }}>
          Configure the terminals within your port facility
        </p>
      </div>

      {/* Add Terminal Button */}
      {!editingId && (
        <button
          onClick={handleAdd}
          className="flex items-center gap-2 px-3 py-2 rounded-lg transition-colors border-2 border-dashed w-full text-sm"
          style={{ borderColor: 'var(--kale-blue)', color: 'var(--kale-blue)', fontWeight: 600 }}
        >
          <Plus className="w-4 h-4" />
          Add Terminal
        </button>
      )}

      {/* Edit Form */}
      {editingId && (
        <div className="bg-white rounded-lg shadow-sm border p-4" style={{ borderColor: 'var(--border)' }}>
          <h3 className="text-sm mb-3" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
            {editingId === 'new' ? 'New Terminal' : 'Edit Terminal'}
          </h3>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs mb-1" style={{ fontWeight: 600 }}>Terminal Name *</label>
                <input
                  type="text"
                  value={formData.name || ''}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Terminal 1"
                  className="w-full px-3 py-2 rounded-lg border text-sm"
                  style={{ borderColor: 'var(--border)', backgroundColor: 'var(--input-background)' }}
                />
              </div>
              <div>
                <label className="block text-xs mb-1" style={{ fontWeight: 600 }}>Terminal Code *</label>
                <input
                  type="text"
                  value={formData.code || ''}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                  placeholder="e.g., T1"
                  className="w-full px-3 py-2 rounded-lg border text-sm"
                  style={{ borderColor: 'var(--border)', backgroundColor: 'var(--input-background)' }}
                />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs mb-1" style={{ fontWeight: 600 }}>Type *</label>
                <select
                  value={formData.terminalType || 'container'}
                  onChange={(e) => setFormData({ ...formData, terminalType: e.target.value as Terminal['terminalType'] })}
                  className="w-full px-3 py-2 rounded-lg border text-sm"
                  style={{ borderColor: 'var(--border)', backgroundColor: 'var(--input-background)' }}
                >
                  <option value="container">Container</option>
                  <option value="bulk">Bulk Cargo</option>
                  <option value="ro-ro">Ro-Ro</option>
                  <option value="multi-purpose">Multi-Purpose</option>
                </select>
              </div>
              <div>
                <label className="block text-xs mb-1" style={{ fontWeight: 600 }}>Operating Company</label>
                <input
                  type="text"
                  value={formData.operatingCompany || ''}
                  onChange={(e) => setFormData({ ...formData, operatingCompany: e.target.value })}
                  placeholder="e.g., PSA International"
                  className="w-full px-3 py-2 rounded-lg border text-sm"
                  style={{ borderColor: 'var(--border)', backgroundColor: 'var(--input-background)' }}
                />
              </div>
              <div>
                <label className="block text-xs mb-1" style={{ fontWeight: 600 }}>Hours</label>
                <input
                  type="text"
                  value={formData.operationalHours || ''}
                  onChange={(e) => setFormData({ ...formData, operationalHours: e.target.value })}
                  placeholder="e.g., 24/7"
                  className="w-full px-3 py-2 rounded-lg border text-sm"
                  style={{ borderColor: 'var(--border)', backgroundColor: 'var(--input-background)' }}
                />
              </div>
            </div>
            <div className="flex gap-2 pt-2">
              <button onClick={handleCancel} className="flex-1 px-3 py-2 rounded-lg border text-sm"
                style={{ borderColor: 'var(--border)', color: 'var(--kale-blue)', fontWeight: 600 }}>
                Cancel
              </button>
              <button onClick={handleSave} disabled={!formData.name || !formData.code}
                className="flex-1 px-3 py-2 rounded-lg text-sm disabled:opacity-50"
                style={{ backgroundColor: 'var(--kale-blue)', color: 'white', fontWeight: 600 }}>
                {editingId === 'new' ? 'Add Terminal' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Terminals Grid */}
      {terminals.length > 0 && (
        <div>
          <h3 className="text-xs mb-2" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
            Configured Terminals ({terminals.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {terminals.map((terminal) => (
              <div key={terminal.id} className="bg-white rounded-lg shadow-sm border p-3"
                style={{ borderColor: 'var(--border)' }}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-1.5 min-w-0">
                    <Building2 className="w-3.5 h-3.5 flex-shrink-0" style={{ color: 'var(--kale-blue)' }} />
                    <span className="text-sm truncate" style={{ fontWeight: 600, color: 'var(--kale-blue)' }}>
                      {terminal.name}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded flex-shrink-0"
                      style={{ backgroundColor: 'var(--muted)', fontWeight: 600 }}>
                      {terminal.code}
                    </span>
                  </div>
                  {!editingId && (
                    <div className="flex gap-1 flex-shrink-0">
                      <button onClick={() => handleEdit(terminal)} className="p-1 rounded hover:bg-gray-100">
                        <Edit2 className="w-3 h-3" style={{ color: 'var(--kale-blue)' }} />
                      </button>
                      <button onClick={() => handleDelete(terminal.id)} className="p-1 rounded hover:bg-gray-100">
                        <Trash2 className="w-3 h-3" style={{ color: 'var(--status-critical)' }} />
                      </button>
                    </div>
                  )}
                </div>
                <div className="grid grid-cols-3 gap-2 text-[11px]">
                  <div>
                    <div style={{ color: 'var(--muted-foreground)' }}>Type</div>
                    <div style={{ fontWeight: 500 }} className="capitalize">{terminal.terminalType.replace('-', ' ')}</div>
                  </div>
                  <div>
                    <div style={{ color: 'var(--muted-foreground)' }}>Company</div>
                    <div style={{ fontWeight: 500 }} className="truncate">{terminal.operatingCompany || 'N/A'}</div>
                  </div>
                  <div>
                    <div style={{ color: 'var(--muted-foreground)' }}>Hours</div>
                    <div style={{ fontWeight: 500 }}>{terminal.operationalHours}</div>
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
