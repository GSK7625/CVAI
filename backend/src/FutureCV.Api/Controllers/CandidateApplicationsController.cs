using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.JobApplication.DTOs;
using FutureCV.Application.Features.JobApplication.Interfaces;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace FutureCV.Api.Controllers;

[Authorize(Roles = "Candidate")]
[Route("api/candidate")]
public class CandidateApplicationsController : ApiControllerBase
{
    private readonly IApplicationService _applicationService;

    public CandidateApplicationsController(IApplicationService applicationService)
    {
        _applicationService = applicationService;
    }

    // -------------------------------------------------------------------------
    // Job Application (P3-UC05, P3-UC06, P3-UC07)
    // -------------------------------------------------------------------------

    [HttpPost("jobs/{jobId:guid}/apply")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(ApplyJobResponse))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status409Conflict)]
    public async Task<IActionResult> ApplyJob(
        Guid jobId, [FromBody] ApplyJobRequest request, CancellationToken cancellationToken)
    {
        var result = await _applicationService.ApplyJobAsync(GetCurrentUserId(), jobId, request, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpGet("applications")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(PagedResult<CandidateApplicationListResponse>))]
    public async Task<IActionResult> GetMyApplications(
        [FromQuery] CandidateApplicationFilterRequest filter, CancellationToken cancellationToken)
    {
        var result = await _applicationService.GetCandidateApplicationsAsync(GetCurrentUserId(), filter, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpGet("applications/{id:guid}")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(CandidateApplicationDetailResponse))]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetApplicationDetail(
        Guid id, CancellationToken cancellationToken)
    {
        var result = await _applicationService.GetCandidateApplicationDetailAsync(GetCurrentUserId(), id, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpPatch("applications/{id:guid}/withdraw")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(bool))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> WithdrawApplication(
        Guid id, [FromBody] WithdrawApplicationRequest request, CancellationToken cancellationToken)
    {
        var result = await _applicationService.WithdrawApplicationAsync(GetCurrentUserId(), id, request, cancellationToken);
        return ToHttpResult(result);
    }

    // -------------------------------------------------------------------------
    // Saved Jobs (P3-UC04)
    // -------------------------------------------------------------------------

    [HttpPost("jobs/{jobId:guid}/save")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(bool))]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> ToggleSaveJob(
        Guid jobId, CancellationToken cancellationToken)
    {
        var result = await _applicationService.ToggleSaveJobAsync(GetCurrentUserId(), jobId, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpGet("saved-jobs")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(PagedResult<SavedJobResponse>))]
    public async Task<IActionResult> GetSavedJobs(
        [FromQuery] SavedJobFilterRequest filter, CancellationToken cancellationToken)
    {
        var result = await _applicationService.GetSavedJobsAsync(GetCurrentUserId(), filter, cancellationToken);
        return ToHttpResult(result);
    }

    // -------------------------------------------------------------------------
    // Job Suggestions & Match Preview (P4-UC01, P4-UC02, P4-UC03)
    // -------------------------------------------------------------------------

    [HttpGet("jobs/suggestions")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(PagedResult<JobSuggestionResponse>))]
    public async Task<IActionResult> GetJobSuggestions(
        [FromQuery] JobSuggestionFilterRequest filter, CancellationToken cancellationToken)
    {
        var result = await _applicationService.GetJobSuggestionsAsync(GetCurrentUserId(), filter, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpPost("jobs/{jobId:guid}/preview-match")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(JobMatchPreviewResponse))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> PreviewJobMatch(
        Guid jobId, [FromBody] PreviewJobMatchRequest request, CancellationToken cancellationToken)
    {
        var result = await _applicationService.PreviewJobMatchAsync(GetCurrentUserId(), jobId, request, cancellationToken);
        return ToHttpResult(result);
    }
}
