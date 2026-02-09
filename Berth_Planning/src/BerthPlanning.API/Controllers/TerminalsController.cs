using BerthPlanning.Core.Interfaces;
using BerthPlanning.Core.Models;
using Microsoft.AspNetCore.Mvc;

namespace BerthPlanning.API.Controllers;

[ApiController]
[Route("[controller]")]
public class TerminalsController : ControllerBase
{
    private readonly ITerminalRepository _terminalRepository;
    private readonly IPortRepository _portRepository;
    private readonly IBerthRepository _berthRepository;
    private readonly ILogger<TerminalsController> _logger;

    public TerminalsController(
        ITerminalRepository terminalRepository,
        IPortRepository portRepository,
        IBerthRepository berthRepository,
        ILogger<TerminalsController> logger)
    {
        _terminalRepository = terminalRepository;
        _portRepository = portRepository;
        _berthRepository = berthRepository;
        _logger = logger;
    }

    [HttpGet]
    public async Task<ActionResult<IEnumerable<Terminal>>> GetAll()
    {
        try
        {
            IEnumerable<Terminal> terminals = await _terminalRepository.GetAllAsync();
            return Ok(terminals);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting terminals");
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<Terminal>> GetById(int id)
    {
        try
        {
            Terminal? terminal = await _terminalRepository.GetByIdAsync(id);
            return terminal == null ? (ActionResult<Terminal>)NotFound($"Terminal with ID {id} not found") : (ActionResult<Terminal>)Ok(terminal);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting terminal {TerminalId}", id);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("port/{portId}")]
    public async Task<ActionResult<IEnumerable<Terminal>>> GetByPortId(int portId)
    {
        try
        {
            Port? port = await _portRepository.GetByIdAsync(portId);
            if (port == null)
            {
                return NotFound($"Port with ID {portId} not found");
            }

            IEnumerable<Terminal> terminals = await _terminalRepository.GetByPortIdAsync(portId);
            return Ok(terminals);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting terminals for port {PortId}", portId);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("{id}/berths")]
    public async Task<ActionResult<IEnumerable<Berth>>> GetBerths(int id)
    {
        try
        {
            Terminal? terminal = await _terminalRepository.GetByIdAsync(id);
            if (terminal == null)
            {
                return NotFound($"Terminal with ID {id} not found");
            }

            IEnumerable<Berth> berths = await _berthRepository.GetByTerminalIdAsync(id);
            return Ok(berths);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting berths for terminal {TerminalId}", id);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpPost]
    public async Task<ActionResult<Terminal>> Create([FromBody] Terminal terminal)
    {
        try
        {
            if (string.IsNullOrWhiteSpace(terminal.TerminalName))
            {
                return BadRequest("Terminal name is required");
            }

            if (string.IsNullOrWhiteSpace(terminal.TerminalCode))
            {
                return BadRequest("Terminal code is required");
            }

            // Validate port exists
            Port? port = await _portRepository.GetByIdAsync(terminal.PortId);
            if (port == null)
            {
                return BadRequest($"Port with ID {terminal.PortId} not found");
            }

            // Check if terminal code already exists
            Terminal? existing = await _terminalRepository.GetByCodeAsync(terminal.TerminalCode);
            if (existing != null)
            {
                return BadRequest($"Terminal with code {terminal.TerminalCode} already exists");
            }

            int id = await _terminalRepository.CreateAsync(terminal);
            terminal.TerminalId = id;

            return CreatedAtAction(nameof(GetById), new { id }, terminal);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating terminal");
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpPut("{id}")]
    public async Task<ActionResult> Update(int id, [FromBody] Terminal terminal)
    {
        try
        {
            if (id != terminal.TerminalId)
            {
                return BadRequest("ID mismatch");
            }

            Terminal? existing = await _terminalRepository.GetByIdAsync(id);
            if (existing == null)
            {
                return NotFound($"Terminal with ID {id} not found");
            }

            // Validate port exists
            Port? port = await _portRepository.GetByIdAsync(terminal.PortId);
            if (port == null)
            {
                return BadRequest($"Port with ID {terminal.PortId} not found");
            }

            bool success = await _terminalRepository.UpdateAsync(terminal);
            return !success ? StatusCode(500, "Failed to update terminal") : NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating terminal {TerminalId}", id);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpDelete("{id}")]
    public async Task<ActionResult> Delete(int id)
    {
        try
        {
            Terminal? existing = await _terminalRepository.GetByIdAsync(id);
            if (existing == null)
            {
                return NotFound($"Terminal with ID {id} not found");
            }

            // Check if terminal has berths
            IEnumerable<Berth> berths = await _berthRepository.GetByTerminalIdAsync(id);
            if (berths.Any())
            {
                return BadRequest("Cannot delete terminal with associated berths");
            }

            bool success = await _terminalRepository.DeleteAsync(id);
            return !success ? StatusCode(500, "Failed to delete terminal") : NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting terminal {TerminalId}", id);
            return StatusCode(500, "Internal server error");
        }
    }
}
