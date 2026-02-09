using BerthPlanning.Core.DTOs;

namespace BerthPlanning.Core.Services.Contracts;

public interface IWhatIfService
{
    // What-If Scenario Simulation
    Task<WhatIfScenarioResultDto> SimulateVesselDelayAsync(int scheduleId, int delayMinutes);
    Task<WhatIfScenarioResultDto> SimulateBerthClosureAsync(int berthId, DateTime closureStart, DateTime closureEnd);
    Task<WhatIfScenarioResultDto> SimulateWeatherAlertAsync(string weatherCondition, DateTime duration);
    Task<WhatIfScenarioResultDto> SimulateNewVesselAsync(int vesselId, DateTime proposedETA);
    Task<WhatIfScenarioResultDto> RunCustomScenarioAsync(WhatIfScenarioRequestDto request);
}
