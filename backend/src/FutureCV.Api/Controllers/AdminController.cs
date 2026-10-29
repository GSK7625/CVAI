using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.Admin.DTOs;
using FutureCV.Application.Features.Admin.Interfaces;
using FutureCV.Application.Features.Employer.DTOs;
using FutureCV.Application.Features.Job.DTOs;
using FutureCV.Application.Features.Job.Interfaces;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace FutureCV.Api.Controllers;

[Authorize(Roles = "Admin")]
[Route("api/admin")]
public class AdminController : ApiControllerBase
{
    private readonly IAdminService _adminService;
    private readonly IJobService _jobService;

    public AdminController(IAdminService adminService, IJobService jobService)
    {
        _adminService = adminService;
        _jobService = jobService;
    }

    // -------------------------------------------------------------------------
    // User Management
    // -------------------------------------------------------------------------

    [HttpGet("users")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(PagedResult<AdminUserResponse>))]
    public async Task<IActionResult> GetUsers(
        [FromQuery] UserQueryFilter filter, CancellationToken cancellationToken)
    {
        var result = await _adminService.GetUsersAsync(filter, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpPost("users/{id:guid}/lock")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> LockUser(
        Guid id, [FromBody] LockUserRequest request, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.Reason))
            return BadRequest(new { message = "Lock reason is required." });

        var result = await _adminService.LockUserAsync(
            GetCurrentUserId(), id, request.Reason, GetClientIpAddress(), cancellationToken);
        return ToHttpResult(result);
    }

    [HttpPost("users/{id:guid}/unlock")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> UnlockUser(Guid id, CancellationToken cancellationToken)
    {
        var result = await _adminService.UnlockUserAsync(
            GetCurrentUserId(), id, GetClientIpAddress(), cancellationToken);
        return ToHttpResult(result);
    }

    // -------------------------------------------------------------------------
    // Company Verification & Management
    // -------------------------------------------------------------------------

    [HttpGet("companies")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(PagedResult<AdminCompanyProfileResponse>))]
    public async Task<IActionResult> GetCompanies(
        [FromQuery] CompanyQueryFilter filter, CancellationToken cancellationToken)
    {
        var result = await _adminService.GetCompaniesAsync(filter, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpPut("companies/{id:guid}/status")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(AdminCompanyProfileResponse))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> UpdateCompanyStatus(
        Guid id, [FromBody] UpdateCompanyStatusRequest request, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.Status))
            return BadRequest(new { message = "Status is required." });

        var result = await _adminService.UpdateCompanyStatusAsync(
            GetCurrentUserId(), id, request, GetClientIpAddress(), cancellationToken);
        return ToHttpResult(result);
    }

    [HttpPost("companies/{id:guid}/approve")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(bool))]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status409Conflict)]
    public async Task<IActionResult> ApproveCompany(Guid id, CancellationToken cancellationToken)
    {
        var result = await _adminService.ApproveCompanyAsync(
            GetCurrentUserId(), id, GetClientIpAddress(), cancellationToken);
        return ToHttpResult(result);
    }

    [HttpPost("companies/{id:guid}/reject")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(bool))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status409Conflict)]
    public async Task<IActionResult> RejectCompany(
        Guid id, [FromBody] RejectCompanyRequest request, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.Reason))
            return BadRequest(new { message = "Reject reason is required." });

        var result = await _adminService.RejectCompanyAsync(
            GetCurrentUserId(), id, request.Reason, GetClientIpAddress(), cancellationToken);
        return ToHttpResult(result);
    }

    // -------------------------------------------------------------------------
    // Audit Log Management
    // -------------------------------------------------------------------------

    [HttpGet("audit-logs")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(PagedResult<AuditLogResponse>))]
    public async Task<IActionResult> GetAuditLogs(
        [FromQuery] AuditLogQueryFilter filter, CancellationToken cancellationToken)
    {
        var result = await _adminService.GetAuditLogsAsync(filter, cancellationToken);
        return ToHttpResult(result);
    }

    // -------------------------------------------------------------------------
    // Job Moderation
    // -------------------------------------------------------------------------

    [HttpGet("jobs")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(PagedResult<JobListResponse>))]
    public async Task<IActionResult> GetJobs(
        [FromQuery] AdminJobFilterRequest filter, CancellationToken cancellationToken)
    {
        var result = await _jobService.GetAdminJobsAsync(filter, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpPatch("jobs/{id:guid}/approval")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(bool))]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> ModerateJob(
        Guid id, [FromBody] ApproveJobRequest request, CancellationToken cancellationToken)
    {
        var result = await _jobService.ModerateJobAsync(GetCurrentUserId(), id, request, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpPost("jobs/{id:guid}/ban")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(bool))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> BanJob(
        Guid id, [FromBody] BanJobRequest request, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.Reason))
            return BadRequest(new { message = "Ban reason is required." });

        var result = await _adminService.BanJobAsync(
            GetCurrentUserId(), id, request.Reason, GetClientIpAddress(), cancellationToken);
        return ToHttpResult(result);
    }

    [HttpPost("jobs/{id:guid}/unban")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(bool))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> UnbanJob(Guid id, CancellationToken cancellationToken)
    {
        var result = await _adminService.UnbanJobAsync(
            GetCurrentUserId(), id, GetClientIpAddress(), cancellationToken);
        return ToHttpResult(result);
    }

    // -------------------------------------------------------------------------
    // Job Reports (P3-UC03, P5-UC07)
    // -------------------------------------------------------------------------

    [HttpGet("job-reports")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(PagedResult<JobReportResponse>))]
    public async Task<IActionResult> GetJobReports(
        [FromQuery] JobReportFilterRequest filter, CancellationToken cancellationToken)
    {
        var result = await _adminService.GetJobReportsAsync(filter, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpGet("job-reports/{id:guid}")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(JobReportResponse))]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetJobReportById(
        Guid id, CancellationToken cancellationToken)
    {
        var result = await _adminService.GetJobReportByIdAsync(id, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpPatch("job-reports/{id:guid}/resolve")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(bool))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> ResolveJobReport(
        Guid id, [FromBody] ResolveJobReportRequest request, CancellationToken cancellationToken)
    {
        var result = await _adminService.ResolveJobReportAsync(
            GetCurrentUserId(), id, request, GetClientIpAddress(), cancellationToken);
        return ToHttpResult(result);
    }

    // -------------------------------------------------------------------------
    // Admin Dashboard (P5-UC05)
    // -------------------------------------------------------------------------

    [HttpGet("dashboard")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(AdminDashboardStatsResponse))]
    public async Task<IActionResult> GetDashboardStats(CancellationToken cancellationToken)
    {
        var result = await _adminService.GetDashboardStatsAsync(cancellationToken);
        return ToHttpResult(result);
    }
}
