# Berth Assignment Checklist - Operational Guidelines

**Category**: Best Practices

## Pre-Assignment Validation Checklist

### Physical Constraints (HARD)
- [ ] vessel.LOA ≤ berth.Length (check VESSELS.LOA vs BERTHS.Length)
- [ ] vessel.Draft ≤ berth.MaxDraft + tide_height (check VESSELS.Draft vs BERTHS.MaxDraft + TIDAL_DATA.TideHeight)
- [ ] vessel.Beam ≤ berth.MaxBeam (check VESSELS.Beam vs BERTHS.MaxBeam)
- [ ] vessel.AirDraft ≤ berth.HeightClearance (if applicable)

### Cargo Compatibility (HARD)
- [ ] vessel.VesselType matches berth.BerthType (Container→Container, Bulk→Bulk, etc.)
- [ ] Dangerous goods segregation rules met (check VESSELS.DangerousGoods)
- [ ] Reefer plug availability (if needed for refrigerated cargo)

### Operational Constraints (SOFT)
- [ ] Berth not under maintenance (check BERTH_MAINTENANCE.Status != 'InProgress')
- [ ] Adequate crane capacity (check BERTHS.NumberOfCranes vs vessel requirements)
- [ ] Pilot certification available (check RESOURCES where ResourceType='Pilot')
- [ ] Tugboat bollard pull sufficient (check RESOURCES where ResourceType='Tugboat')

### Temporal Constraints
- [ ] No schedule overlap (check VESSEL_SCHEDULE for existing assignments)
- [ ] Tidal window adequate for deep draft (check TIDAL_DATA if vessel.Draft > 12m)
- [ ] Weather acceptable (check WEATHER_DATA.WindSpeed < 35 knots)

### Priority & Commercial
- [ ] Priority level respected (check VESSEL_SCHEDULE.Priority)
- [ ] Window vessel requirements met (if applicable)
- [ ] Resource allocation conflicts resolved (check RESOURCE_ALLOCATION)

**AI Agent Integration**: Run through this checklist sequentially. Hard constraints MUST pass before evaluating soft constraints.

**Keywords**: berth assignment, validation checklist, hard constraints, soft constraints, operational guidelines
