export function ConstraintLegend() {
  const constraints = [
    { icon: '👨‍✈️', type: 'Pilot', description: 'Pilot availability and certification' },
    { icon: '🚢', type: 'Tug', description: 'Tugboat requirements and availability' },
    { icon: '🌊', type: 'Tide', description: 'Tidal windows for safe navigation' },
    { icon: '⚓', type: 'Berth', description: 'Berth availability and compatibility' },
    { icon: '📦', type: 'Cargo', description: 'Cargo handling requirements' },
    { icon: '🌤️', type: 'Weather', description: 'Weather conditions affecting operations' },
    { icon: '📏', type: 'Draft', description: 'Water depth requirements' },
  ];

  return (
    <div className="p-4 rounded-lg border" style={{ borderColor: 'var(--border)', backgroundColor: 'white' }}>
      <h4 className="mb-3" style={{ color: 'var(--kale-blue)' }}>Constraint Types</h4>
      <div className="grid grid-cols-2 gap-2 text-sm">
        {constraints.map((constraint) => (
          <div key={constraint.type} className="flex items-start gap-2">
            <span className="text-base flex-shrink-0">{constraint.icon}</span>
            <div className="flex-1">
              <div style={{ fontWeight: 600 }}>{constraint.type}</div>
              <div className="text-xs" style={{ color: 'var(--muted-foreground)' }}>
                {constraint.description}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
