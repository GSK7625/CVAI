using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.Admin.DTOs;
using FutureCV.Application.Features.Employer.DTOs;

namespace FutureCV.Application.Features.Admin.Interfaces;

public interface IAdminService
{
    Task<ServiceResult<PagedResult<AdminUserResponse>>> GetUsersAsync(
        UserQueryFilter filter, CancellationToken cancellationToken = default);

    Task<ServiceResult<bool>> LockUserAsync(
        Guid adminUserId, Guid targetUserId, string reason, string? ipAddress, CancellationToken cancellationToken = default);

    Task<ServiceResult<bool>> UnlockUserAsync(
        Guid adminUserId, Guid targetUserId, string? ipAddress, CancellationToken cancellationToken = default);

    Task<ServiceResult<PagedResult<AdminCompanyProfileResponse>>> GetCompaniesAsync(
        CompanyQueryFilter filter, CancellationToken cancellationToken = default);

    Task<ServiceResult<AdminCompanyProfileResponse>> UpdateCompanyStatusAsync(
        Guid adminUserId, Guid companyId, UpdateCompanyStatusRequest request, string? ipAddress, CancellationToken cancellationToken = default);

    Task<ServiceResult<bool>> ApproveCompanyAsync(
        Guid adminUserId, Guid companyId, string? ipAddress, CancellationToken cancellationToken = default);

    Task<ServiceResult<bool>> RejectCompanyAsync(
        Guid adminUserId, Guid companyId, string reason, string? ipAddress, CancellationToken cancellationToken = default);

    Task<ServiceResult<PagedResult<AuditLogResponse>>> GetAuditLogsAsync(
        AuditLogQueryFilter filter, CancellationToken cancellationToken = default);

    // Dashboard Statistics (P5-UC05)
    Task<ServiceResult<AdminDashboardStatsResponse>> GetDashboardStatsAsync(
        CancellationToken cancellationToken = default);

    // Job Reports & Moderation (P5-UC07)
    Task<ServiceResult<PagedResult<JobReportResponse>>> GetJobReportsAsync(
        JobReportFilterRequest filter, CancellationToken cancellationToken = default);

    Task<ServiceResult<JobReportResponse>> GetJobReportByIdAsync(
        Guid reportId, CancellationToken cancellationToken = default);

    Task<ServiceResult<bool>> ResolveJobReportAsync(
        Guid adminUserId, Guid reportId, ResolveJobReportRequest request, string? ipAddress, CancellationToken cancellationToken = default);

    Task<ServiceResult<bool>> BanJobAsync(
        Guid adminUserId, Guid jobId, string reason, string? ipAddress, CancellationToken cancellationToken = default);

    Task<ServiceResult<bool>> UnbanJobAsync(
        Guid adminUserId, Guid jobId, string? ipAddress, CancellationToken cancellationToken = default);
}
