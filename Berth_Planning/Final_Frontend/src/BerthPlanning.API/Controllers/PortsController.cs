using BerthPlanning.Core.Interfaces;
using BerthPlanning.Core.Models;
using Microsoft.AspNetCore.Mvc;

namespace BerthPlanning.API.Controllers;

[ApiController]
[Route("[controller]")]
public class PortsController : ControllerBase
{
    private readonly IPortRepository _portRepository;
    private readonly ILogger<PortsController> _logger;

    public PortsController(IPortRepository portRepository, ILogger<PortsController> logger)
    {
        _portRepository = portRepository;
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
}
