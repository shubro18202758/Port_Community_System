using BerthPlanning.Core.DTOs;
using BerthPlanning.Core.Services.Contracts;
using Microsoft.AspNetCore.Mvc;

namespace BerthPlanning.API.Controllers;

[ApiController]
[Route("[controller]")]
public class PredictionsController : ControllerBase
{
    private readonly IPredictionService _predictionService;
    private readonly ILogger<PredictionsController> _logger;

    public PredictionsController(IPredictionService predictionService, ILogger<PredictionsController> logger)
    {
        _predictionService = predictionService;
        _logger = logger;
    }

    [HttpGet("eta/active")]
    public async Task<ActionResult<IEnumerable<ETAPredictionDto>>> GetAllActiveETAPredictions()
    {
        try
        {
            IEnumerable<ETAPredictionDto> predictions = await _predictionService.PredictAllActiveETAsAsync();
            return Ok(predictions);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error predicting ETAs for active vessels");
            return StatusCode(500, "Internal server error");
        }
    }
}
