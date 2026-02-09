using BerthPlanning.Core.Interfaces;
using BerthPlanning.Core.Models;
using Microsoft.AspNetCore.Mvc;

namespace BerthPlanning.API.Controllers;

[ApiController]
[Route("[controller]")]
public class ResourcesController : ControllerBase
{
    private readonly IResourceRepository _resourceRepository;
    private readonly ILogger<ResourcesController> _logger;

    public ResourcesController(
        IResourceRepository resourceRepository,
        ILogger<ResourcesController> logger)
    {
        _resourceRepository = resourceRepository;
        _logger = logger;
    }

    [HttpGet]
    public async Task<ActionResult<IEnumerable<Resource>>> GetAll()
    {
        try
        {
            var resources = await _resourceRepository.GetAllAsync();
            return Ok(resources);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting all resources");
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<Resource>> GetById(int id)
    {
        try
        {
            var resource = await _resourceRepository.GetByIdAsync(id);
            if (resource == null)
            {
                return NotFound(new { Message = $"Resource {id} not found" });
            }
            return Ok(resource);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting resource {ResourceId}", id);
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpPost]
    public async Task<ActionResult<Resource>> Create([FromBody] Resource resource)
    {
        try
        {
            if (string.IsNullOrWhiteSpace(resource.ResourceName))
            {
                return BadRequest("Resource name is required");
            }
            if (string.IsNullOrWhiteSpace(resource.ResourceType))
            {
                return BadRequest("Resource type is required");
            }

            int id = await _resourceRepository.CreateAsync(resource);
            resource.ResourceId = id;
            return CreatedAtAction(nameof(GetById), new { id }, resource);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating resource");
            return StatusCode(500, "Internal server error");
        }
    }
}
