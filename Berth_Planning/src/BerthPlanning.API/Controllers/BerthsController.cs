using BerthPlanning.Core.Interfaces;
using BerthPlanning.Core.Models;
using Microsoft.AspNetCore.Mvc;

namespace BerthPlanning.API.Controllers;

[ApiController]
[Route("[controller]")]
public class BerthsController : ControllerBase
{
    private readonly IBerthRepository _berthRepository;
    private readonly ILogger<BerthsController> _logger;

    public BerthsController(IBerthRepository berthRepository, ILogger<BerthsController> logger)
    {
        _berthRepository = berthRepository;
        _logger = logger;
    }

    [HttpGet]
    public async Task<ActionResult<IEnumerable<Berth>>> GetAll()
    {
        try
        {
            IEnumerable<Berth> berths = await _berthRepository.GetAllAsync();
            return Ok(berths);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting berths");
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("active")]
    public async Task<ActionResult<IEnumerable<Berth>>> GetActive()
    {
        try
        {
            IEnumerable<Berth> berths = await _berthRepository.GetActiveAsync();
            return Ok(berths);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting active berths");
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<Berth>> GetById(int id)
    {
        try
        {
            Berth? berth = await _berthRepository.GetByIdAsync(id);
            return berth == null ? (ActionResult<Berth>)NotFound($"Berth with ID {id} not found") : (ActionResult<Berth>)Ok(berth);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting berth {BerthId}", id);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("code/{code}")]
    public async Task<ActionResult<Berth>> GetByCode(string code)
    {
        try
        {
            Berth? berth = await _berthRepository.GetByCodeAsync(code);
            return berth == null ? (ActionResult<Berth>)NotFound($"Berth with code {code} not found") : (ActionResult<Berth>)Ok(berth);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting berth by code {BerthCode}", code);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("compatible")]
    public async Task<ActionResult<IEnumerable<Berth>>> GetCompatible([FromQuery] decimal vesselLOA, [FromQuery] decimal vesselDraft)
    {
        try
        {
            IEnumerable<Berth> berths = await _berthRepository.GetCompatibleBerthsAsync(vesselLOA, vesselDraft);
            return Ok(berths);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting compatible berths for LOA={LOA}, Draft={Draft}", vesselLOA, vesselDraft);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("{id}/availability")]
    public async Task<ActionResult<object>> CheckAvailability(int id, [FromQuery] DateTime startTime, [FromQuery] DateTime endTime)
    {
        try
        {
            Berth? berth = await _berthRepository.GetByIdAsync(id);
            if (berth == null)
            {
                return NotFound($"Berth with ID {id} not found");
            }

            bool isAvailable = await _berthRepository.CheckAvailabilityAsync(id, startTime, endTime);

            return Ok(new
            {
                BerthId = id,
                berth.BerthName,
                StartTime = startTime,
                EndTime = endTime,
                IsAvailable = isAvailable
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error checking availability for berth {BerthId}", id);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpPost]
    public async Task<ActionResult<Berth>> Create([FromBody] Berth berth)
    {
        try
        {
            if (string.IsNullOrWhiteSpace(berth.BerthName) || string.IsNullOrWhiteSpace(berth.BerthCode))
            {
                return BadRequest("Berth name and code are required");
            }

            int id = await _berthRepository.CreateAsync(berth);
            berth.BerthId = id;

            return CreatedAtAction(nameof(GetById), new { id }, berth);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating berth");
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpPut("{id}")]
    public async Task<ActionResult> Update(int id, [FromBody] Berth berth)
    {
        try
        {
            if (id != berth.BerthId)
            {
                return BadRequest("ID mismatch");
            }

            Berth? existing = await _berthRepository.GetByIdAsync(id);
            if (existing == null)
            {
                return NotFound($"Berth with ID {id} not found");
            }

            bool success = await _berthRepository.UpdateAsync(berth);
            return !success ? StatusCode(500, "Failed to update berth") : NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating berth {BerthId}", id);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpDelete("{id}")]
    public async Task<ActionResult> Delete(int id)
    {
        try
        {
            Berth? existing = await _berthRepository.GetByIdAsync(id);
            if (existing == null)
            {
                return NotFound($"Berth with ID {id} not found");
            }

            bool success = await _berthRepository.DeleteAsync(id);
            return !success ? StatusCode(500, "Failed to delete berth") : NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting berth {BerthId}", id);
            return StatusCode(500, "Internal server error");
        }
    }
}
