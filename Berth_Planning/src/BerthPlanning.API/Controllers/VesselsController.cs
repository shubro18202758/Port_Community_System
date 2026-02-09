using BerthPlanning.Core.Interfaces;
using BerthPlanning.Core.Models;
using Microsoft.AspNetCore.Mvc;

namespace BerthPlanning.API.Controllers;

[ApiController]
[Route("[controller]")]
public class VesselsController : ControllerBase
{
    private readonly IVesselRepository _vesselRepository;
    private readonly ILogger<VesselsController> _logger;

    public VesselsController(IVesselRepository vesselRepository, ILogger<VesselsController> logger)
    {
        _vesselRepository = vesselRepository;
        _logger = logger;
    }

    [HttpGet]
    public async Task<ActionResult<IEnumerable<Vessel>>> GetAll()
    {
        try
        {
            IEnumerable<Vessel> vessels = await _vesselRepository.GetAllAsync();
            return Ok(vessels);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting vessels");
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<Vessel>> GetById(int id)
    {
        try
        {
            Vessel? vessel = await _vesselRepository.GetByIdAsync(id);
            return vessel == null ? (ActionResult<Vessel>)NotFound($"Vessel with ID {id} not found") : (ActionResult<Vessel>)Ok(vessel);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting vessel {VesselId}", id);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("imo/{imo}")]
    public async Task<ActionResult<Vessel>> GetByIMO(string imo)
    {
        try
        {
            Vessel? vessel = await _vesselRepository.GetByIMOAsync(imo);
            return vessel == null ? (ActionResult<Vessel>)NotFound($"Vessel with IMO {imo} not found") : (ActionResult<Vessel>)Ok(vessel);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting vessel by IMO {IMO}", imo);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("type/{vesselType}")]
    public async Task<ActionResult<IEnumerable<Vessel>>> GetByType(string vesselType)
    {
        try
        {
            IEnumerable<Vessel> vessels = await _vesselRepository.GetByTypeAsync(vesselType);
            return Ok(vessels);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting vessels by type {VesselType}", vesselType);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpPost]
    public async Task<ActionResult<Vessel>> Create([FromBody] Vessel vessel)
    {
        try
        {
            if (string.IsNullOrWhiteSpace(vessel.VesselName))
            {
                return BadRequest("Vessel name is required");
            }

            int id = await _vesselRepository.CreateAsync(vessel);
            vessel.VesselId = id;

            return CreatedAtAction(nameof(GetById), new { id }, vessel);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating vessel");
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpPut("{id}")]
    public async Task<ActionResult> Update(int id, [FromBody] Vessel vessel)
    {
        try
        {
            if (id != vessel.VesselId)
            {
                return BadRequest("ID mismatch");
            }

            Vessel? existing = await _vesselRepository.GetByIdAsync(id);
            if (existing == null)
            {
                return NotFound($"Vessel with ID {id} not found");
            }

            bool success = await _vesselRepository.UpdateAsync(vessel);
            return !success ? StatusCode(500, "Failed to update vessel") : NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating vessel {VesselId}", id);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpDelete("{id}")]
    public async Task<ActionResult> Delete(int id)
    {
        try
        {
            Vessel? existing = await _vesselRepository.GetByIdAsync(id);
            if (existing == null)
            {
                return NotFound($"Vessel with ID {id} not found");
            }

            bool success = await _vesselRepository.DeleteAsync(id);
            return !success ? StatusCode(500, "Failed to delete vessel") : NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting vessel {VesselId}", id);
            return StatusCode(500, "Internal server error");
        }
    }
}
