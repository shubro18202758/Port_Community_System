using BerthPlanning.Core.Interfaces;
using BerthPlanning.Core.Models;
using Microsoft.AspNetCore.Mvc;

namespace BerthPlanning.API.Controllers;

[ApiController]
[Route("[controller]")]
public class PortsController : ControllerBase
{
    private readonly IPortRepository _portRepository;
    private readonly ITerminalRepository _terminalRepository;
    private readonly ILogger<PortsController> _logger;

    public PortsController(
        IPortRepository portRepository,
        ITerminalRepository terminalRepository,
        ILogger<PortsController> logger)
    {
        _portRepository = portRepository;
        _terminalRepository = terminalRepository;
        _logger = logger;
    }

    [HttpGet]
    public async Task<ActionResult<IEnumerable<Port>>> GetAll()
    {
        try
        {
            IEnumerable<Port> ports = await _portRepository.GetAllAsync();
            return Ok(ports);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting ports");
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<Port>> GetById(int id)
    {
        try
        {
            Port? port = await _portRepository.GetByIdAsync(id);
            return port == null ? (ActionResult<Port>)NotFound($"Port with ID {id} not found") : (ActionResult<Port>)Ok(port);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting port {PortId}", id);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("code/{code}")]
    public async Task<ActionResult<Port>> GetByCode(string code)
    {
        try
        {
            Port? port = await _portRepository.GetByCodeAsync(code);
            return port == null ? (ActionResult<Port>)NotFound($"Port with code {code} not found") : (ActionResult<Port>)Ok(port);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting port by code {PortCode}", code);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("{id}/terminals")]
    public async Task<ActionResult<IEnumerable<Terminal>>> GetTerminals(int id)
    {
        try
        {
            Port? port = await _portRepository.GetByIdAsync(id);
            if (port == null)
            {
                return NotFound($"Port with ID {id} not found");
            }

            IEnumerable<Terminal> terminals = await _terminalRepository.GetByPortIdAsync(id);
            return Ok(terminals);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting terminals for port {PortId}", id);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpPost]
    public async Task<ActionResult<Port>> Create([FromBody] Port port)
    {
        try
        {
            if (string.IsNullOrWhiteSpace(port.PortName))
            {
                return BadRequest("Port name is required");
            }

            if (string.IsNullOrWhiteSpace(port.PortCode))
            {
                return BadRequest("Port code is required");
            }

            // Check if port code already exists
            Port? existing = await _portRepository.GetByCodeAsync(port.PortCode);
            if (existing != null)
            {
                return BadRequest($"Port with code {port.PortCode} already exists");
            }

            int id = await _portRepository.CreateAsync(port);
            port.PortId = id;

            return CreatedAtAction(nameof(GetById), new { id }, port);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating port");
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpPut("{id}")]
    public async Task<ActionResult> Update(int id, [FromBody] Port port)
    {
        try
        {
            if (id != port.PortId)
            {
                return BadRequest("ID mismatch");
            }

            Port? existing = await _portRepository.GetByIdAsync(id);
            if (existing == null)
            {
                return NotFound($"Port with ID {id} not found");
            }

            bool success = await _portRepository.UpdateAsync(port);
            return !success ? StatusCode(500, "Failed to update port") : NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating port {PortId}", id);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpDelete("{id}")]
    public async Task<ActionResult> Delete(int id)
    {
        try
        {
            Port? existing = await _portRepository.GetByIdAsync(id);
            if (existing == null)
            {
                return NotFound($"Port with ID {id} not found");
            }

            // Check if port has terminals
            IEnumerable<Terminal> terminals = await _terminalRepository.GetByPortIdAsync(id);
            if (terminals.Any())
            {
                return BadRequest("Cannot delete port with associated terminals");
            }

            bool success = await _portRepository.DeleteAsync(id);
            return !success ? StatusCode(500, "Failed to delete port") : NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting port {PortId}", id);
            return StatusCode(500, "Internal server error");
        }
    }
}
