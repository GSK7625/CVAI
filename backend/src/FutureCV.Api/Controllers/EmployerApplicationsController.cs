using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.JobApplication.DTOs;
using FutureCV.Application.Features.JobApplication.Interfaces;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace FutureCV.Api.Controllers;

[Authorize(Roles = "Employer")]
[Route("api/employer")]
public class EmployerApplicationsController : ApiControllerBase
{
    private readonly IApplicationService _applicationService;

    public EmployerApplicationsController(IApplicationService applicationService)
    {
        _applicationService = applicationService;
    }

    // -------------------------------------------------------------------------
    // Candidate Screening & CV Review (P4-UC04)
    // -------------------------------------------------------------------------

    [HttpGet("jobs/{jobId:guid}/applications")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(PagedResult<RecruiterApplicationListResponse>))]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetJobApplications(
        Guid jobId, [FromQuery] RecruiterApplicationFilterRequest filter, CancellationToken cancellationToken)
    {
        var result = await _applicationService.GetJobApplicationsAsync(GetCurrentUserId(), jobId, filter, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpGet("applications/{id:guid}")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(RecruiterApplicationDetailResponse))]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetApplicationDetail(
        Guid id, CancellationToken cancellationToken)
    {
        var result = await _applicationService.GetApplicationDetailAsync(GetCurrentUserId(), id, cancellationToken);
        return ToHttpResult(result);
    }

    // -------------------------------------------------------------------------
    // Candidate Internal Evaluation (P4-UC05)
    // -------------------------------------------------------------------------

    [HttpPut("applications/{id:guid}/evaluation")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(bool))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> EvaluateApplication(
        Guid id, [FromBody] EvaluateApplicationRequest request, CancellationToken cancellationToken)
    {
        var result = await _applicationService.EvaluateApplicationAsync(GetCurrentUserId(), id, request, cancellationToken);
        return ToHttpResult(result);
    }

    // -------------------------------------------------------------------------
    // Status Progression (P4-UC06)
    // -------------------------------------------------------------------------

    [HttpPatch("applications/{id:guid}/status")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(bool))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> UpdateApplicationStatus(
        Guid id, [FromBody] UpdateApplicationStatusRequest request, CancellationToken cancellationToken)
    {
        var result = await _applicationService.UpdateApplicationStatusAsync(GetCurrentUserId(), id, request, cancellationToken);
        return ToHttpResult(result);
    }

    // -------------------------------------------------------------------------
    // Recruitment Pipeline Kanban (P4-UC07)
    // -------------------------------------------------------------------------

    [HttpGet("jobs/{jobId:guid}/pipeline")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(RecruitmentPipelineResponse))]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetRecruitmentPipeline(
        Guid jobId, CancellationToken cancellationToken)
    {
        var result = await _applicationService.GetRecruitmentPipelineAsync(GetCurrentUserId(), jobId, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpGet("jobs/{jobId:guid}/pipeline/analytics")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(PipelineAnalyticsResponse))]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetPipelineAnalytics(
        Guid jobId, CancellationToken cancellationToken)
    {
        var result = await _applicationService.GetPipelineAnalyticsAsync(GetCurrentUserId(), jobId, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpGet("jobs/{jobId:guid}/pipeline/export")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> ExportPipelineCsv(
        Guid jobId, CancellationToken cancellationToken)
    {
        var result = await _applicationService.ExportPipelineCsvAsync(GetCurrentUserId(), jobId, cancellationToken);
        if (!result.IsSuccess)
        {
            return ToHttpResult(result);
        }

        return File(result.Data!, "text/csv; charset=utf-8", $"pipeline_{jobId}_{DateTime.UtcNow:yyyyMMddHHmmss}.csv");
    }
}
