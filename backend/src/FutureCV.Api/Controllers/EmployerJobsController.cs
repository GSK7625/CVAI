using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.Job.DTOs;
using FutureCV.Application.Features.Job.Interfaces;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace FutureCV.Api.Controllers;

[Authorize(Roles = "Employer")]
[Route("api/employer/jobs")]
public class EmployerJobsController : ApiControllerBase
{
    private readonly IJobService _jobService;

    public EmployerJobsController(IJobService jobService)
    {
        _jobService = jobService;
    }

    // -------------------------------------------------------------------------
    // Job Creation & Modification
    // -------------------------------------------------------------------------

    [HttpPost]
    [ProducesResponseType(StatusCodes.Status201Created, Type = typeof(JobDetailResponse))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> CreateJob(
        [FromBody] CreateJobRequest request, CancellationToken cancellationToken)
    {
        var result = await _jobService.CreateJobAsync(GetCurrentUserId(), request, cancellationToken);
        return ToHttpResult(result, created: true);
    }

    [HttpPut("{id:guid}")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(JobDetailResponse))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> UpdateJob(
        Guid id, [FromBody] UpdateJobRequest request, CancellationToken cancellationToken)
    {
        var result = await _jobService.UpdateJobAsync(GetCurrentUserId(), id, request, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpPatch("{id:guid}/status")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(bool))]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> ToggleJobStatus(
        Guid id, CancellationToken cancellationToken)
    {
        var result = await _jobService.ToggleJobStatusAsync(GetCurrentUserId(), id, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpDelete("{id:guid}")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(bool))]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> DeleteJob(
        Guid id, CancellationToken cancellationToken)
    {
        var result = await _jobService.DeleteJobAsync(GetCurrentUserId(), id, cancellationToken);
        return ToHttpResult(result);
    }

    // -------------------------------------------------------------------------
    // Job Queries
    // -------------------------------------------------------------------------

    [HttpGet]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(PagedResult<JobListResponse>))]
    public async Task<IActionResult> GetMyJobs(
        [FromQuery] EmployerJobFilterRequest filter, CancellationToken cancellationToken)
    {
        var result = await _jobService.GetEmployerJobsAsync(GetCurrentUserId(), filter, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpGet("{id:guid}")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(JobDetailResponse))]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetMyJobById(
        Guid id, CancellationToken cancellationToken)
    {
        var result = await _jobService.GetEmployerJobByIdAsync(GetCurrentUserId(), id, cancellationToken);
        return ToHttpResult(result);
    }
}
