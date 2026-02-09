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
    public async Task<ActionResult<IEnumerable<Berth>>> GetAll([FromQuery] int? terminalId = null)
    {
        try
        {
            IEnumerable<Berth> berths;
            if (terminalId.HasValue)
            {
                berths = await _berthRepository.GetByTerminalIdAsync(terminalId.Value);
            }
            else
            {
                berths = await _berthRepository.GetAllAsync();
            }
            return Ok(berths);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting berths");
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
}
