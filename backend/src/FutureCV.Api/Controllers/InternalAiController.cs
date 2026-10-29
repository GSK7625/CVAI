using FutureCV.Application.Features.Candidate.DTOs;
using FutureCV.Application.Features.Candidate.Interfaces;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace FutureCV.Api.Controllers;

/// <summary>
/// Internal endpoints for AI microservice webhooks and asynchronous callbacks.
/// Does not require candidate JWT auth, but can be protected via internal network or API secret.
/// </summary>
[ApiController]
[Route("api/internal/cvs")]
[AllowAnonymous]
public class InternalAiController : ApiControllerBase
{
    private readonly ICandidateService _candidateService;
    private readonly IConfiguration _configuration;

    public InternalAiController(ICandidateService candidateService, IConfiguration configuration)
    {
        _candidateService = candidateService;
        _configuration = configuration;
    }

    /// <summary>
    /// Webhook called by the Python AI microservice when CV parsing and evaluation are complete.
    /// Updates CVParsers and CVEvaluations in PostgreSQL.
    /// </summary>
    [HttpPost("{cvId:guid}/ai-callback")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> ProcessAiCallback(
        Guid cvId,
        [FromBody] AiCvCallbackRequest request,
        CancellationToken cancellationToken)
    {
        // Optional API key validation if configured in appsettings: "InternalAi:ApiKey"
        var configuredApiKey = _configuration["InternalAi:ApiKey"];
        if (!string.IsNullOrEmpty(configuredApiKey))
        {
            if (!Request.Headers.TryGetValue("X-Internal-Api-Key", out var providedKey) ||
                providedKey != configuredApiKey)
            {
                return Unauthorized(new { message = "Invalid or missing internal API key." });
            }
        }

        var result = await _candidateService.ProcessAiCvCallbackAsync(cvId, request, cancellationToken);
        return ToHttpResult(result);
    }
}
