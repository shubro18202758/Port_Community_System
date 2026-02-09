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
}
