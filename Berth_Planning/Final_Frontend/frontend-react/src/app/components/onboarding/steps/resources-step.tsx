import { useState } from 'react';
import { Cpu, Users, Plus, Edit2, Trash2 } from 'lucide-react';
import type { Terminal, Equipment, HumanResource } from '../port-onboarding-wizard';

interface ResourcesStepProps {
  terminals: Terminal[];
  equipment: Equipment[];
  humanResources: HumanResource[];
  onEquipmentChange: (data: Equipment[]) => void;
  onHumanResourcesChange: (data: HumanResource[]) => void;
}

export function ResourcesStep({
  terminals,
  equipment,
  humanResources,
  onEquipmentChange,
  onHumanResourcesChange,
}: ResourcesStepProps) {
  const [equipmentList, setEquipmentList] = useState<Equipment[]>(equipment);
  const [resourcesList, setResourcesList] = useState<HumanResource[]>(
    humanResources.length > 0 ? humanResources : [
      { role: 'Pilots', count: 0, shifts: 3, availability: '24/7' },
      { role: 'Tug Operators', count: 0, shifts: 3, availability: '24/7' },
      { role: 'Crane Operators', count: 0, shifts: 3, availability: '24/7' },
      { role: 'Ground Workers', count: 0, shifts: 3, availability: '24/7' },
      { role: 'Security Personnel', count: 0, shifts: 3, availability: '24/7' },
    ]
  );
  const [editingEq, setEditingEq] = useState<string | null>(null);
  const [eqForm, setEqForm] = useState<Partial<Equipment>>({});

  const handleAddEquipment = () => {
    setEditingEq('new');
    setEqForm({
      terminalId: terminals[0]?.id || '',
      type: 'STS',
      name: '',
      capacity: 0,
      status: 'operational',
    });
  };

  const handleSaveEquipment = () => {
    if (!eqForm.name) return;
    let updated: Equipment[];
    if (editingEq === 'new') {
      updated = [...equipmentList, { id: `EQ${Date.now()}`, ...eqForm } as Equipment];
    } else {
      updated = equipmentList.map((e) => (e.id === editingEq ? { ...e, ...eqForm } as Equipment : e));
    }
    setEquipmentList(updated);
    onEquipmentChange(updated);
    setEditingEq(null);
  };

  const handleDeleteEquipment = (id: string) => {
    const updated = equipmentList.filter((e) => e.id !== id);
    setEquipmentList(updated);
    onEquipmentChange(updated);
  };

  const handleResourceChange = (index: number, field: keyof HumanResource, value: any) => {
    const updated = [...resourcesList];
    updated[index] = { ...updated[index], [field]: value };
    setResourcesList(updated);
    onHumanResourcesChange(updated);
  };

  const getTypeEmoji = (type: string) => {
    switch (type) {
      case 'STS': return '🏗️';
      case 'RTG': return '🚧';
      default: return '⚙️';
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="flex items-center gap-2 mb-1 text-lg" style={{ color: 'var(--kale-blue)' }}>
          <Cpu className="w-5 h-5" />
          Resources & Equipment
        </h2>
        <p className="text-sm" style={{ color: 'var(--muted-foreground)' }}>
          Configure equipment and human resources
        </p>
      </div>

      {/* Equipment Section */}
      <div>
        <h3 className="flex items-center gap-1.5 text-xs mb-2" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
          <Cpu className="w-3.5 h-3.5" />
          Terminal Equipment
        </h3>

        {!editingEq && (
          <button onClick={handleAddEquipment}
            className="flex items-center gap-2 px-3 py-2 rounded-lg border-2 border-dashed w-full text-sm mb-3"
            style={{ borderColor: 'var(--kale-blue)', color: 'var(--kale-blue)', fontWeight: 600 }}>
            <Plus className="w-4 h-4" />
            Add Equipment
          </button>
        )}

        {editingEq && (
          <div className="bg-white rounded-lg shadow-sm border p-4 mb-3" style={{ borderColor: 'var(--border)' }}>
            <h4 className="text-sm mb-3" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
              {editingEq === 'new' ? 'New Equipment' : 'Edit Equipment'}
            </h4>
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs mb-1" style={{ fontWeight: 600 }}>Terminal</label>
                  <select value={eqForm.terminalId || ''}
                    onChange={(e) => setEqForm({ ...eqForm, terminalId: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border text-sm"
                    style={{ borderColor: 'var(--border)', backgroundColor: 'var(--input-background)' }}>
                    {terminals.map((t) => (<option key={t.id} value={t.id}>{t.name}</option>))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs mb-1" style={{ fontWeight: 600 }}>Type</label>
                  <select value={eqForm.type || 'STS'}
                    onChange={(e) => setEqForm({ ...eqForm, type: e.target.value as Equipment['type'] })}
                    className="w-full px-3 py-2 rounded-lg border text-sm"
                    style={{ borderColor: 'var(--border)', backgroundColor: 'var(--input-background)' }}>
                    <option value="STS">STS Crane</option>
                    <option value="RTG">RTG Crane</option>
                    <option value="MHC">MHC Crane</option>
                    <option value="RMG">RMG Crane</option>
                    <option value="Reach Stacker">Reach Stacker</option>
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs mb-1" style={{ fontWeight: 600 }}>Name/ID *</label>
                  <input type="text" value={eqForm.name || ''}
                    onChange={(e) => setEqForm({ ...eqForm, name: e.target.value })}
                    placeholder="e.g., STS-1"
                    className="w-full px-3 py-2 rounded-lg border text-sm"
                    style={{ borderColor: 'var(--border)', backgroundColor: 'var(--input-background)' }} />
                </div>
                <div>
                  <label className="block text-xs mb-1" style={{ fontWeight: 600 }}>Capacity (tons)</label>
                  <input type="number" value={eqForm.capacity || ''}
                    onChange={(e) => setEqForm({ ...eqForm, capacity: parseFloat(e.target.value) || 0 })}
                    placeholder="65"
                    className="w-full px-3 py-2 rounded-lg border text-sm"
                    style={{ borderColor: 'var(--border)', backgroundColor: 'var(--input-background)' }} />
                </div>
              </div>
              <div className="flex gap-2">
                <button onClick={() => setEditingEq(null)} className="flex-1 px-3 py-2 rounded-lg border text-sm"
                  style={{ borderColor: 'var(--border)', color: 'var(--kale-blue)', fontWeight: 600 }}>Cancel</button>
                <button onClick={handleSaveEquipment} className="flex-1 px-3 py-2 rounded-lg text-sm"
                  style={{ backgroundColor: 'var(--kale-blue)', color: 'white', fontWeight: 600 }}>
                  {editingEq === 'new' ? 'Add' : 'Save'}
                </button>
              </div>
            </div>
          </div>
        )}

        {equipmentList.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {equipmentList.map((eq) => {
              const terminal = terminals.find(t => t.id === eq.terminalId);
              return (
                <div key={eq.id} className="bg-white rounded-lg border p-3" style={{ borderColor: 'var(--border)' }}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-1.5 min-w-0">
                      <span className="text-base flex-shrink-0">{getTypeEmoji(eq.type)}</span>
                      <span className="text-sm truncate" style={{ fontWeight: 600, color: 'var(--kale-blue)' }}>{eq.name}</span>
                    </div>
                    {!editingEq && (
                      <div className="flex gap-1 flex-shrink-0">
                        <button onClick={() => { setEditingEq(eq.id); setEqForm(eq); }} className="p-1 rounded hover:bg-gray-100">
                          <Edit2 className="w-3 h-3" style={{ color: 'var(--kale-blue)' }} />
                        </button>
                        <button onClick={() => handleDeleteEquipment(eq.id)} className="p-1 rounded hover:bg-gray-100">
                          <Trash2 className="w-3 h-3" style={{ color: 'var(--status-critical)' }} />
                        </button>
                      </div>
                    )}
                  </div>
                  <div className="grid grid-cols-3 gap-1.5 text-[11px]">
                    <div>
                      <div style={{ color: 'var(--muted-foreground)' }}>Type</div>
                      <div style={{ fontWeight: 500 }}>{eq.type}</div>
                    </div>
                    <div>
                      <div style={{ color: 'var(--muted-foreground)' }}>Capacity</div>
                      <div style={{ fontWeight: 500 }}>{eq.capacity}t</div>
                    </div>
                    <div>
                      <div style={{ color: 'var(--muted-foreground)' }}>Terminal</div>
                      <div style={{ fontWeight: 500 }} className="truncate">{terminal?.name || 'N/A'}</div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Human Resources */}
      <div>
        <h3 className="flex items-center gap-1.5 text-xs mb-2" style={{ color: 'var(--kale-blue)', fontWeight: 600 }}>
          <Users className="w-3.5 h-3.5" />
          Human Resources
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {resourcesList.map((resource, index) => (
            <div key={resource.role} className="bg-white rounded-lg border p-3" style={{ borderColor: 'var(--border)' }}>
              <div className="text-sm mb-2" style={{ fontWeight: 600, color: 'var(--kale-blue)' }}>{resource.role}</div>
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="block text-[10px] mb-0.5" style={{ color: 'var(--muted-foreground)' }}>Count</label>
                  <input type="number" value={resource.count}
                    onChange={(e) => handleResourceChange(index, 'count', parseInt(e.target.value) || 0)}
                    className="w-full px-2 py-1.5 rounded border text-xs"
                    style={{ borderColor: 'var(--border)', backgroundColor: 'var(--input-background)' }} />
                </div>
                <div>
                  <label className="block text-[10px] mb-0.5" style={{ color: 'var(--muted-foreground)' }}>Shifts</label>
                  <input type="number" value={resource.shifts}
                    onChange={(e) => handleResourceChange(index, 'shifts', parseInt(e.target.value) || 1)}
                    className="w-full px-2 py-1.5 rounded border text-xs"
                    style={{ borderColor: 'var(--border)', backgroundColor: 'var(--input-background)' }} />
                </div>
                <div>
                  <label className="block text-[10px] mb-0.5" style={{ color: 'var(--muted-foreground)' }}>Avail.</label>
                  <input type="text" value={resource.availability}
                    onChange={(e) => handleResourceChange(index, 'availability', e.target.value)}
                    className="w-full px-2 py-1.5 rounded border text-xs"
                    style={{ borderColor: 'var(--border)', backgroundColor: 'var(--input-background)' }} />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
