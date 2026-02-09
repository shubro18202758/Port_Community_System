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
    private readonly ILogger<TerminalsController> _logger;

    public TerminalsController(
        ITerminalRepository terminalRepository,
        IPortRepository portRepository,
        ILogger<TerminalsController> logger)
    {
        _terminalRepository = terminalRepository;
        _portRepository = portRepository;
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

            Port? port = await _portRepository.GetByIdAsync(terminal.PortId);
            if (port == null)
            {
                return BadRequest($"Port with ID {terminal.PortId} not found");
            }

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
}
