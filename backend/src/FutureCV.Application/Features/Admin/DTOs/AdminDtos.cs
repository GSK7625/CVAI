namespace FutureCV.Application.Features.Admin.DTOs;

public sealed record AdminUserResponse(
    Guid Id,
    string Email,
    string? Phone,
    string? FullName,
    IReadOnlyList<string> Roles,
    bool IsLockedOut,
    DateTimeOffset? LockoutEnd,
    DateTimeOffset CreatedAt);

public sealed record LockUserRequest(
    string Reason);

public sealed record UpdateCompanyStatusRequest(
    string Status,
    string? Note);

public sealed record RejectCompanyRequest(
    string Reason);

public sealed record AuditLogResponse(
    Guid Id,
    Guid? UserId,
    string Action,
    string? EntityType,
    string? EntityId,
    string? PayloadJson,
    string? IpAddress,
    DateTime CreatedAt);

public sealed record UserQueryFilter(
    string? Search = null,
    string? Role = null,
    bool? IsLocked = null,
    int PageIndex = 1,
    int PageSize = 10);

public sealed record CompanyQueryFilter(
    string? Search = null,
    string? Status = null,
    int PageIndex = 1,
    int PageSize = 10);

public sealed record AuditLogQueryFilter(
    Guid? UserId = null,
    string? Action = null,
    int PageIndex = 1,
    int PageSize = 10);

// -----------------------------------------------------------------------------
// Admin Dashboard DTOs (P5-UC05)
// -----------------------------------------------------------------------------

public sealed record AdminUserStatsDto(
    int TotalUsers,
    int TotalCandidates,
    int TotalEmployers,
    int LockedUsersCount,
    int NewUsersLast30Days);

public sealed record AdminCompanyStatsDto(
    int TotalCompanies,
    int VerifiedCompaniesCount,
    int PendingVerificationCount,
    int RejectedCompaniesCount);

public sealed record AdminJobStatsDto(
    int TotalJobs,
    int ActiveJobsCount,
    int PendingApprovalCount,
    int RejectedJobsCount,
    int BannedJobsCount,
    int ExpiredJobsCount);

public sealed record AdminApplicationStatsDto(
    int TotalApplications,
    int AppliedCount,
    int ScreeningCount,
    int InterviewCount,
    int OfferCount,
    int HiredCount,
    int RejectedCount,
    int WithdrawnCount);

public sealed record MonthlyTrendDto(
    string Month,
    int NewUsers,
    int NewJobs,
    int NewApplications);

public sealed record AdminDashboardStatsResponse(
    AdminUserStatsDto Users,
    AdminCompanyStatsDto Companies,
    AdminJobStatsDto Jobs,
    AdminApplicationStatsDto Applications,
    int PendingReportsCount,
    IReadOnlyList<MonthlyTrendDto> MonthlyTrends);

// -----------------------------------------------------------------------------
// Job Report & Moderation DTOs (P3-UC03, P5-UC07)
// -----------------------------------------------------------------------------

public sealed record JobReportResponse(
    Guid Id,
    Guid JobId,
    string JobTitle,
    Guid CompanyId,
    string CompanyName,
    Guid ReporterUserId,
    string? ReporterEmail,
    string Reason,
    string? Details,
    string Status,
    Guid? ResolvedByAdminId,
    DateTimeOffset? ResolvedAt,
    string? AdminNote,
    DateTime CreatedAt);

public sealed record JobReportFilterRequest(
    string? Status = null,
    Guid? JobId = null,
    int PageIndex = 1,
    int PageSize = 10);

public sealed record ResolveJobReportRequest(
    string Action,
    string? AdminNote = null);

public sealed record BanJobRequest(
    string Reason);

// -----------------------------------------------------------------------------
// Admin Company Management DTO
// -----------------------------------------------------------------------------

public sealed record AdminCompanyProfileResponse(
    Guid Id,
    Guid UserId,
    string CompanyName,
    string Email,
    string? PhoneNumber,
    string? Website,
    string? Address,
    string? CompanySize,
    string? Industry,
    string? Description,
    string? LogoUrl,
    string Status,
    DateTime CreatedAt,
    DateTime? UpdatedAt);
