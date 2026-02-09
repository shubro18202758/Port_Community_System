using BerthPlanning.Core.DTOs;
using BerthPlanning.Core.Interfaces;
using BerthPlanning.Core.Models;
using Microsoft.AspNetCore.Mvc;

namespace BerthPlanning.API.Controllers;

[ApiController]
[Route("[controller]")]
public class SchedulesController : ControllerBase
{
    private readonly IScheduleRepository _scheduleRepository;
    private readonly ILogger<SchedulesController> _logger;

    public SchedulesController(IScheduleRepository scheduleRepository, ILogger<SchedulesController> logger)
    {
        _scheduleRepository = scheduleRepository;
        _logger = logger;
    }

    [HttpGet]
    public async Task<ActionResult<IEnumerable<VesselSchedule>>> GetAll()
    {
        try
        {
            var schedules = await _scheduleRepository.GetAllAsync();
            return Ok(schedules);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting all schedules");
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("active")]
    public async Task<ActionResult<IEnumerable<VesselSchedule>>> GetActive([FromQuery] int? terminalId = null)
    {
        try
        {
            IEnumerable<VesselSchedule> schedules;
            if (terminalId.HasValue)
            {
                schedules = await _scheduleRepository.GetActiveByTerminalIdAsync(terminalId.Value);
            }
            else
            {
                schedules = await _scheduleRepository.GetActiveAsync();
            }
            return Ok(schedules);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting active schedules");
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<VesselSchedule>> GetById(int id)
    {
        try
        {
            var schedule = await _scheduleRepository.GetByIdAsync(id);
            return schedule == null ? NotFound() : Ok(schedule);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting schedule {ScheduleId}", id);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("vessel/{vesselId}")]
    public async Task<ActionResult<VesselSchedule>> GetByVesselId(int vesselId)
    {
        try
        {
            var schedule = await _scheduleRepository.GetByVesselIdAsync(vesselId);
            return schedule == null ? NotFound() : Ok(schedule);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting schedule for vessel {VesselId}", vesselId);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("status/{status}")]
    public async Task<ActionResult<IEnumerable<VesselSchedule>>> GetByStatus(string status)
    {
        try
        {
            var schedules = await _scheduleRepository.GetByStatusAsync(status);
            return Ok(schedules);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting schedules by status {Status}", status);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("berth/{berthId}")]
    public async Task<ActionResult<IEnumerable<VesselSchedule>>> GetByBerth(int berthId)
    {
        try
        {
            var schedules = await _scheduleRepository.GetByBerthAsync(berthId);
            return Ok(schedules);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting schedules for berth {BerthId}", berthId);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpPost("allocate")]
    public async Task<ActionResult<AllocationResultDto>> AllocateVesselToBerth([FromBody] AllocateBerthDto request)
    {
        try
        {
            AllocationResultDto result = await _scheduleRepository.AllocateVesselToBerthAsync(
                request.VesselId,
                request.BerthId,
                request.ETA,
                request.ETD,
                request.DwellTime);

            return !result.Success ? (ActionResult<AllocationResultDto>)BadRequest(result) : (ActionResult<AllocationResultDto>)Ok(result);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error allocating vessel to berth");
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpPut("{id}")]
    public async Task<ActionResult> Update(int id, [FromBody] UpdateScheduleDto request)
    {
        try
        {
            var existing = await _scheduleRepository.GetByIdAsync(id);
            if (existing == null) return NotFound();

            if (request.VesselId.HasValue) existing.VesselId = request.VesselId.Value;
            if (request.BerthId.HasValue) existing.BerthId = request.BerthId.Value;
            if (request.ETA.HasValue) existing.ETA = request.ETA.Value;
            if (request.PredictedETA.HasValue) existing.PredictedETA = request.PredictedETA.Value;
            if (request.ETD.HasValue) existing.ETD = request.ETD.Value;
            if (request.ATA.HasValue) existing.ATA = request.ATA.Value;
            if (request.ATB.HasValue) existing.ATB = request.ATB.Value;
            if (request.ATD.HasValue) existing.ATD = request.ATD.Value;
            if (!string.IsNullOrEmpty(request.Status)) existing.Status = request.Status;
            if (request.DwellTime.HasValue) existing.DwellTime = request.DwellTime.Value;
            if (request.WaitingTime.HasValue) existing.WaitingTime = request.WaitingTime.Value;

            var success = await _scheduleRepository.UpdateAsync(existing);
            return success ? Ok(existing) : StatusCode(500, "Failed to update schedule");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating schedule {ScheduleId}", id);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpPut("{id}/eta")]
    public async Task<ActionResult> UpdateETA(int id, [FromBody] UpdateETADto request)
    {
        try
        {
            var success = await _scheduleRepository.UpdateVesselETAAsync(id, request.NewETA, request.NewPredictedETA);
            return success ? Ok(new { message = "ETA updated" }) : NotFound();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating ETA for schedule {ScheduleId}", id);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpPut("{id}/arrival")]
    public async Task<ActionResult> RecordArrival(int id, [FromBody] RecordArrivalDto request)
    {
        try
        {
            var success = await _scheduleRepository.RecordVesselArrivalAsync(id, request.ATA);
            return success ? Ok(new { message = "Arrival recorded", ata = request.ATA }) : NotFound();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error recording arrival for schedule {ScheduleId}", id);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpPut("{id}/berthing")]
    public async Task<ActionResult> RecordBerthing(int id, [FromBody] RecordBerthingDto request)
    {
        try
        {
            var success = await _scheduleRepository.RecordVesselBerthingAsync(id, request.ATB);
            return success ? Ok(new { message = "Berth-in recorded", atb = request.ATB }) : NotFound();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error recording berthing for schedule {ScheduleId}", id);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpPut("{id}/departure")]
    public async Task<ActionResult> RecordDeparture(int id, [FromBody] RecordDepartureDto request)
    {
        try
        {
            var success = await _scheduleRepository.RecordVesselDepartureAsync(id, request.ATD);
            return success ? Ok(new { message = "Berth-out recorded", atd = request.ATD }) : NotFound();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error recording departure for schedule {ScheduleId}", id);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpDelete("{id}")]
    public async Task<ActionResult> Delete(int id)
    {
        try
        {
            var success = await _scheduleRepository.DeleteAsync(id);
            return success ? Ok(new { message = "Schedule deleted" }) : NotFound();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting schedule {ScheduleId}", id);
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Forcefully clear ALL vessel schedules from the queue.
    /// Also clears related resource allocations, conflicts, and alerts.
    /// </summary>
    [HttpDelete("clear-all")]
    public async Task<ActionResult> ClearAll()
    {
        try
        {
            _logger.LogWarning("Clearing ALL vessel schedules from queue");
            var deletedCount = await _scheduleRepository.ClearAllAsync();
            return Ok(new {
                message = "All vessel schedules cleared successfully",
                deletedSchedules = deletedCount,
                clearedTables = new[] { "VESSEL_SCHEDULE", "RESOURCE_ALLOCATION", "CONFLICTS", "ALERTS_NOTIFICATIONS" }
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error clearing all schedules");
            return StatusCode(500, "Internal server error");
        }
    }
}
