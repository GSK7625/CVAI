using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.Job.DTOs;
using FutureCV.Application.Features.Job.Interfaces;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace FutureCV.Api.Controllers;

[Route("api/jobs")]
public class JobsController : ApiControllerBase
{
    private readonly IJobService _jobService;

    public JobsController(IJobService jobService)
    {
        _jobService = jobService;
    }

    // -------------------------------------------------------------------------
    // Public Search & Detail
    // -------------------------------------------------------------------------

    [HttpGet]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(PagedResult<JobListResponse>))]
    public async Task<IActionResult> SearchJobs(
        [FromQuery] JobFilterRequest filter, CancellationToken cancellationToken)
    {
        var result = await _jobService.SearchJobsAsync(filter, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpGet("{id:guid}")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(JobDetailResponse))]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetJobDetail(
        Guid id, CancellationToken cancellationToken)
    {
        var result = await _jobService.GetJobDetailAsync(id, incrementView: true, cancellationToken);
        return ToHttpResult(result);
    }

    [Authorize]
    [HttpPost("{id:guid}/report")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(bool))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status409Conflict)]
    public async Task<IActionResult> ReportJob(
        Guid id, [FromBody] CreateJobReportRequest request, CancellationToken cancellationToken)
    {
        var result = await _jobService.ReportJobAsync(GetCurrentUserId(), id, request, cancellationToken);
        return ToHttpResult(result);
    }

    // -------------------------------------------------------------------------
    // Master Data Lookups for Filters / Form Selects
    // -------------------------------------------------------------------------

    [HttpGet("categories")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(IReadOnlyList<JobCategoryResponse>))]
    public async Task<IActionResult> GetCategories(CancellationToken cancellationToken)
    {
        var result = await _jobService.GetCategoriesAsync(cancellationToken);
        return ToHttpResult(result);
    }

    [HttpGet("levels")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(IReadOnlyList<JobLevelResponse>))]
    public async Task<IActionResult> GetLevels(CancellationToken cancellationToken)
    {
        var result = await _jobService.GetLevelsAsync(cancellationToken);
        return ToHttpResult(result);
    }

    [HttpGet("employment-types")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(IReadOnlyList<EmploymentTypeResponse>))]
    public async Task<IActionResult> GetEmploymentTypes(CancellationToken cancellationToken)
    {
        var result = await _jobService.GetEmploymentTypesAsync(cancellationToken);
        return ToHttpResult(result);
    }

    [HttpGet("locations")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(IReadOnlyList<LocationResponse>))]
    public async Task<IActionResult> GetLocations(CancellationToken cancellationToken)
    {
        var result = await _jobService.GetLocationsAsync(cancellationToken);
        return ToHttpResult(result);
    }
}
