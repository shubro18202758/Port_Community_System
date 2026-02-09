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
            IEnumerable<VesselSchedule> schedules = await _scheduleRepository.GetAllAsync();
            return Ok(schedules);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting schedules");
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("active")]
    public async Task<ActionResult<IEnumerable<VesselSchedule>>> GetActive()
    {
        try
        {
            IEnumerable<VesselSchedule> schedules = await _scheduleRepository.GetActiveAsync();
            return Ok(schedules);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting active schedules");
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("status/{status}")]
    public async Task<ActionResult<IEnumerable<VesselSchedule>>> GetByStatus(string status)
    {
        try
        {
            IEnumerable<VesselSchedule> schedules = await _scheduleRepository.GetByStatusAsync(status);
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
            IEnumerable<VesselSchedule> schedules = await _scheduleRepository.GetByBerthAsync(berthId);
            return Ok(schedules);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting schedules for berth {BerthId}", berthId);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("range")]
    public async Task<ActionResult<IEnumerable<VesselSchedule>>> GetByDateRange([FromQuery] DateTime startDate, [FromQuery] DateTime endDate)
    {
        try
        {
            IEnumerable<VesselSchedule> schedules = await _scheduleRepository.GetByDateRangeAsync(startDate, endDate);
            return Ok(schedules);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting schedules for date range");
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<VesselSchedule>> GetById(int id)
    {
        try
        {
            VesselSchedule? schedule = await _scheduleRepository.GetByIdAsync(id);
            return schedule == null ? (ActionResult<VesselSchedule>)NotFound($"Schedule with ID {id} not found") : (ActionResult<VesselSchedule>)Ok(schedule);
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
            VesselSchedule? schedule = await _scheduleRepository.GetByVesselIdAsync(vesselId);
            return schedule == null ? (ActionResult<VesselSchedule>)NotFound($"No active schedule found for vessel {vesselId}") : (ActionResult<VesselSchedule>)Ok(schedule);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting schedule for vessel {VesselId}", vesselId);
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

    [HttpPut("{id}/eta")]
    public async Task<ActionResult> UpdateETA(int id, [FromBody] UpdateScheduleDto request)
    {
        try
        {
            if (!request.ETA.HasValue)
            {
                return BadRequest("ETA is required");
            }

            bool success = await _scheduleRepository.UpdateVesselETAAsync(id, request.ETA.Value, null);
            return !success ? NotFound($"Schedule with ID {id} not found") : NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating ETA for schedule {ScheduleId}", id);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpPost("{id}/arrival")]
    public async Task<ActionResult> RecordArrival(int id, [FromBody] DateTime ata)
    {
        try
        {
            bool success = await _scheduleRepository.RecordVesselArrivalAsync(id, ata);
            return !success ? NotFound($"Schedule with ID {id} not found") : NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error recording arrival for schedule {ScheduleId}", id);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpPost("{id}/berthing")]
    public async Task<ActionResult> RecordBerthing(int id, [FromBody] DateTime atb)
    {
        try
        {
            bool success = await _scheduleRepository.RecordVesselBerthingAsync(id, atb);
            return !success ? NotFound($"Schedule with ID {id} not found") : NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error recording berthing for schedule {ScheduleId}", id);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpPost("{id}/departure")]
    public async Task<ActionResult> RecordDeparture(int id, [FromBody] DateTime atd)
    {
        try
        {
            bool success = await _scheduleRepository.RecordVesselDepartureAsync(id, atd);
            return !success ? NotFound($"Schedule with ID {id} not found") : NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error recording departure for schedule {ScheduleId}", id);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpPost]
    public async Task<ActionResult<VesselSchedule>> Create([FromBody] CreateScheduleDto request)
    {
        try
        {
            var schedule = new VesselSchedule
            {
                VesselId = request.VesselId,
                BerthId = request.BerthId,
                ETA = request.ETA,
                ETD = request.ETD,
                DwellTime = request.DwellTime,
                Status = "Scheduled"
            };

            int id = await _scheduleRepository.CreateAsync(schedule);
            schedule.ScheduleId = id;

            return CreatedAtAction(nameof(GetById), new { id }, schedule);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating schedule");
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpPut("{id}")]
    public async Task<ActionResult> Update(int id, [FromBody] UpdateScheduleDto request)
    {
        try
        {
            VesselSchedule? existing = await _scheduleRepository.GetByIdAsync(id);
            if (existing == null)
            {
                return NotFound($"Schedule with ID {id} not found");
            }

            // Update fields
            if (request.VesselId.HasValue)
            {
                existing.VesselId = request.VesselId.Value;
            }

            if (request.BerthId.HasValue)
            {
                existing.BerthId = request.BerthId;
            }

            if (request.ETA.HasValue)
            {
                existing.ETA = request.ETA;
            }

            if (request.ETD.HasValue)
            {
                existing.ETD = request.ETD;
            }

            if (!string.IsNullOrEmpty(request.Status))
            {
                existing.Status = request.Status;
            }

            if (request.DwellTime.HasValue)
            {
                existing.DwellTime = request.DwellTime;
            }

            bool success = await _scheduleRepository.UpdateAsync(existing);
            return !success ? StatusCode(500, "Failed to update schedule") : NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating schedule {ScheduleId}", id);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpPost("{id}/cancel")]
    public async Task<ActionResult> Cancel(int id)
    {
        try
        {
            VesselSchedule? existing = await _scheduleRepository.GetByIdAsync(id);
            if (existing == null)
            {
                return NotFound($"Schedule with ID {id} not found");
            }

            existing.Status = "Cancelled";
            bool success = await _scheduleRepository.UpdateAsync(existing);
            return !success ? StatusCode(500, "Failed to cancel schedule") : NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error cancelling schedule {ScheduleId}", id);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpDelete("{id}")]
    public async Task<ActionResult> Delete(int id)
    {
        try
        {
            VesselSchedule? existing = await _scheduleRepository.GetByIdAsync(id);
            if (existing == null)
            {
                return NotFound($"Schedule with ID {id} not found");
            }

            bool success = await _scheduleRepository.DeleteAsync(id);
            return !success ? StatusCode(500, "Failed to delete schedule") : NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting schedule {ScheduleId}", id);
            return StatusCode(500, "Internal server error");
        }
    }
}
