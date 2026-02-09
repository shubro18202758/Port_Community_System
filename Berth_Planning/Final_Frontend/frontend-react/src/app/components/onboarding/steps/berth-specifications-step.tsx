import { useState } from 'react';
import { Anchor, Plus, Edit2, Trash2 } from 'lucide-react';
import type { Terminal, BerthSpec } from '../port-onboarding-wizard';

interface BerthSpecificationsStepProps {
  terminals: Terminal[];
  data: BerthSpec[];
  onChange: (data: BerthSpec[]) => void;
}

export function BerthSpecificationsStep({ terminals, data, onChange }: BerthSpecificationsStepProps) {
  const [berths, setBerths] = useState<BerthSpec[]>(data);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState<Partial<BerthSpec>>({});

  const handleAdd = () => {
    setEditingId('new');
    setFormData({
      terminalId: terminals[0]?.id || '',
      name: '',
      length: 0,
      maxDraft: 0,
      maxLOA: 0,
      maxBeam: 0,
      maxDWT: 0,
      bollards: 0,
      fenders: 0,
      reeferPoints: 0,
      freshWater: true,
      bunkering: false,
    });
  };

  const handleSave = () => {
    if (!formData.name || !formData.terminalId) return;

    let updated: BerthSpec[];
    if (editingId === 'new') {
      const newBerth: BerthSpec = {
        id: `B${Date.now()}`,
        ...formData as Omit<BerthSpec, 'id'>,
      };
      updated = [...berths, newBerth];
    } else {
      updated = berths.map((b) =>
        b.id === editingId ? { ...b, ...formData } as BerthSpec : b
      );
    }

    setBerths(updated);
    onChange(updated);
    setEditingId(null);
  };

  const handleDelete = (id: string) => {
    const updated = berths.filter((b) => b.id !== id);
    setBerths(updated);
    onChange(updated);
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="flex items-center gap-2 mb-1 text-lg" style={{ color: 'var(--kale-blue)' }}>
          <Anchor className="w-5 h-5" />
          Berth Specifications
        </h2>
        <p className="text-sm" style={{ color: 'var(--muted-foreground)' }}>
          Define technical specifications for each berth
        </p>
      </div>

      {!editingId && (
        <button onClick={handleAdd}
          className="flex items-center gap-2 px-3 py-2 rounded-lg border-2 border-dashed w-full text-sm"
          style={{ borderColor: 'var(--kale-blue)', color: 'var(--kale-blue)', fontWeight: 600 }}>
          <Plus className="w-4 h-4" />
          Add Berth
        </button>
      )}

      {editingId && (
        <div className="bg-white rounded-lg shadow-sm border p-4" style={{ borderColor: 'var(--border)' }}>
          <h3 className="text-sm mb-3" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
            {editingId === 'new' ? 'New Berth' : 'Edit Berth'}
          </h3>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs mb-1" style={{ fontWeight: 600 }}>Terminal *</label>
                <select value={formData.terminalId || ''}
                  onChange={(e) => setFormData({ ...formData, terminalId: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border text-sm"
                  style={{ borderColor: 'var(--border)', backgroundColor: 'var(--input-background)' }}>
                  {terminals.map((t) => (<option key={t.id} value={t.id}>{t.name}</option>))}
                </select>
              </div>
              <div>
                <label className="block text-xs mb-1" style={{ fontWeight: 600 }}>Berth Name *</label>
                <input type="text" value={formData.name || ''}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Berth 1"
                  className="w-full px-3 py-2 rounded-lg border text-sm"
                  style={{ borderColor: 'var(--border)', backgroundColor: 'var(--input-background)' }} />
              </div>
            </div>

            <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--kale-sky)' }}>
              <h4 className="text-xs mb-2" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>Physical Dimensions</h4>
              <div className="grid grid-cols-4 gap-2">
                {[
                  { key: 'length', label: 'Length (m)', placeholder: '300' },
                  { key: 'maxLOA', label: 'Max LOA (m)', placeholder: '310' },
                  { key: 'maxBeam', label: 'Max Beam (m)', placeholder: '48' },
                  { key: 'maxDraft', label: 'Max Draft (m)', placeholder: '14.5' },
                  { key: 'maxDWT', label: 'Max DWT (t)', placeholder: '50000' },
                  { key: 'bollards', label: 'Bollards', placeholder: '12' },
                  { key: 'fenders', label: 'Fenders', placeholder: '20' },
                  { key: 'reeferPoints', label: 'Reefer Pts', placeholder: '80' },
                ].map((field) => (
                  <div key={field.key}>
                    <label className="block text-[10px] mb-0.5" style={{ color: 'var(--foreground)' }}>{field.label}</label>
                    <input type="number" step="0.1"
                      value={String(formData[field.key as keyof BerthSpec] ?? '')}
                      onChange={(e) => setFormData({ ...formData, [field.key]: parseFloat(e.target.value) || 0 })}
                      placeholder={field.placeholder}
                      className="w-full px-2 py-1.5 rounded border text-xs"
                      style={{ borderColor: 'var(--border)', backgroundColor: 'white' }} />
                  </div>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-4 px-3 py-2 rounded-lg text-sm" style={{ backgroundColor: 'var(--muted)' }}>
              <label className="flex items-center gap-1.5 text-xs">
                <input type="checkbox" checked={formData.freshWater || false}
                  onChange={(e) => setFormData({ ...formData, freshWater: e.target.checked })} />
                Fresh Water
              </label>
              <label className="flex items-center gap-1.5 text-xs">
                <input type="checkbox" checked={formData.bunkering || false}
                  onChange={(e) => setFormData({ ...formData, bunkering: e.target.checked })} />
                Bunkering
              </label>
            </div>

            <div className="flex gap-2">
              <button onClick={() => setEditingId(null)} className="flex-1 px-3 py-2 rounded-lg border text-sm"
                style={{ borderColor: 'var(--border)', color: 'var(--kale-blue)', fontWeight: 600 }}>Cancel</button>
              <button onClick={handleSave} className="flex-1 px-3 py-2 rounded-lg text-sm"
                style={{ backgroundColor: 'var(--kale-blue)', color: 'white', fontWeight: 600 }}>
                {editingId === 'new' ? 'Add Berth' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}

      {berths.length > 0 && (
        <div>
          <h3 className="text-xs mb-2" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
            Configured Berths ({berths.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {berths.map((berth) => {
              const terminal = terminals.find(t => t.id === berth.terminalId);
              return (
                <div key={berth.id} className="bg-white rounded-lg border p-3" style={{ borderColor: 'var(--border)' }}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-1.5 min-w-0">
                      <Anchor className="w-3.5 h-3.5 flex-shrink-0" style={{ color: 'var(--kale-blue)' }} />
                      <span className="text-sm truncate" style={{ fontWeight: 600, color: 'var(--kale-blue)' }}>{berth.name}</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded flex-shrink-0 truncate max-w-[100px]"
                        style={{ backgroundColor: 'var(--muted)' }}>
                        {terminal?.name}
                      </span>
                    </div>
                    {!editingId && (
                      <div className="flex gap-1 flex-shrink-0">
                        <button onClick={() => { setEditingId(berth.id); setFormData(berth); }} className="p-1 rounded hover:bg-gray-100">
                          <Edit2 className="w-3 h-3" style={{ color: 'var(--kale-blue)' }} />
                        </button>
                        <button onClick={() => handleDelete(berth.id)} className="p-1 rounded hover:bg-gray-100">
                          <Trash2 className="w-3 h-3" style={{ color: 'var(--status-critical)' }} />
                        </button>
                      </div>
                    )}
                  </div>
                  <div className="grid grid-cols-4 gap-1.5 text-[10px] px-2 py-1.5 rounded" style={{ backgroundColor: 'var(--kale-sky)' }}>
                    <div className="text-center">
                      <div style={{ color: 'var(--muted-foreground)' }}>Length</div>
                      <div style={{ fontWeight: 700, fontSize: '11px' }}>{berth.length}m</div>
                    </div>
                    <div className="text-center">
                      <div style={{ color: 'var(--muted-foreground)' }}>LOA</div>
                      <div style={{ fontWeight: 700, fontSize: '11px' }}>{berth.maxLOA}m</div>
                    </div>
                    <div className="text-center">
                      <div style={{ color: 'var(--muted-foreground)' }}>Draft</div>
                      <div style={{ fontWeight: 700, fontSize: '11px' }}>{berth.maxDraft}m</div>
                    </div>
                    <div className="text-center">
                      <div style={{ color: 'var(--muted-foreground)' }}>Reefer</div>
                      <div style={{ fontWeight: 700, fontSize: '11px' }}>{berth.reeferPoints}</div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
