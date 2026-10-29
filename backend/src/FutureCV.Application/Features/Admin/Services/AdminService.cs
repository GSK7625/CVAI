using System.Text.Json;
using Microsoft.EntityFrameworkCore;
using FutureCV.Application.Common.Interfaces;
using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.Admin.DTOs;
using FutureCV.Application.Features.Admin.Interfaces;
using FutureCV.Application.Features.Employer.DTOs;
using FutureCV.Domain.Entities;
using FutureCV.Domain.Enums;

namespace FutureCV.Application.Features.Admin.Services;

public class AdminService : IAdminService
{
    private readonly IApplicationDbContext _context;
    private readonly IIdentityService _identityService;

    public AdminService(
        IApplicationDbContext context,
        IIdentityService identityService)
    {
        _context         = context;
        _identityService = identityService;
    }

    // -------------------------------------------------------------------------
    // User Management
    // -------------------------------------------------------------------------

    public async Task<ServiceResult<PagedResult<AdminUserResponse>>> GetUsersAsync(
        UserQueryFilter filter, CancellationToken cancellationToken = default)
    {
        var usersPaged = await _identityService.GetUsersAsync(filter, cancellationToken);
        var userIds = usersPaged.Items.Select(u => u.Id).ToList();

        // Fetch candidate & employer full names for display
        var candidateNames = await _context.Candidates
            .Where(c => userIds.Contains(c.UserId))
            .ToDictionaryAsync(c => c.UserId, c => c.FullName, cancellationToken);

        var employerNames = await _context.Employers
            .Where(e => userIds.Contains(e.UserId))
            .ToDictionaryAsync(e => e.UserId, e => e.FullName, cancellationToken);

        var items = new List<AdminUserResponse>();

        foreach (var u in usersPaged.Items)
        {
            string? fullName = candidateNames.GetValueOrDefault(u.Id)
                ?? employerNames.GetValueOrDefault(u.Id);

            items.Add(new AdminUserResponse(
                u.Id,
                u.Email,
                u.Phone,
                fullName,
                u.Roles,
                u.IsLockedOut,
                u.LockoutEnd,
                u.CreatedAt));
        }

        var result = new PagedResult<AdminUserResponse>(items, usersPaged.TotalCount, usersPaged.PageIndex, usersPaged.PageSize);
        return ServiceResult.Success(result);
    }

    public async Task<ServiceResult<bool>> LockUserAsync(
        Guid adminUserId, Guid targetUserId, string reason, string? ipAddress, CancellationToken cancellationToken = default)
    {
        if (adminUserId == targetUserId)
            return ServiceResult.Failure<bool>("You cannot lock your own account.");

        var lockResult = await _identityService.LockUserAsync(targetUserId, cancellationToken);
        if (!lockResult.IsSuccess)
            return lockResult;

        // Revoke all active refresh tokens immediately
        var activeTokens = await _context.RefreshTokens
            .Where(r => r.UserId == targetUserId && r.RevokedAt == null)
            .ToListAsync(cancellationToken);

        foreach (var token in activeTokens)
        {
            token.RevokedAt = DateTimeOffset.UtcNow;
        }

        // Write Audit Log
        _context.AuditLogs.Add(new AuditLog
        {
            UserId      = adminUserId,
            Action      = "User.Locked",
            EntityType  = "User",
            EntityId    = targetUserId.ToString(),
            PayloadJson = JsonSerializer.Serialize(new { Reason = reason }),
            IpAddress   = ipAddress,
        });

        await _context.SaveChangesAsync(cancellationToken);
        return ServiceResult.Success(true);
    }

    public async Task<ServiceResult<bool>> UnlockUserAsync(
        Guid adminUserId, Guid targetUserId, string? ipAddress, CancellationToken cancellationToken = default)
    {
        var unlockResult = await _identityService.UnlockUserAsync(targetUserId, cancellationToken);
        if (!unlockResult.IsSuccess)
            return unlockResult;

        // Write Audit Log
        _context.AuditLogs.Add(new AuditLog
        {
            UserId     = adminUserId,
            Action     = "User.Unlocked",
            EntityType = "User",
            EntityId   = targetUserId.ToString(),
            IpAddress  = ipAddress,
        });

        await _context.SaveChangesAsync(cancellationToken);
        return ServiceResult.Success(true);
    }

    // -------------------------------------------------------------------------
    // Company Verification & Management
    // -------------------------------------------------------------------------

    public async Task<ServiceResult<PagedResult<AdminCompanyProfileResponse>>> GetCompaniesAsync(
        CompanyQueryFilter filter, CancellationToken cancellationToken = default)
    {
        var pageIndex = filter.PageIndex < 1 ? 1 : filter.PageIndex;
        var pageSize  = filter.PageSize is < 1 or > 100 ? 10 : filter.PageSize;

        var query = from company in _context.Companies
                    join employer in _context.Employers on company.Id equals employer.CompanyId
                    where !company.IsDeleted && !employer.IsDeleted
                    select new { company, employer };

        if (!string.IsNullOrWhiteSpace(filter.Search))
        {
            var search = filter.Search.Trim().ToLowerInvariant();
            query = query.Where(x =>
                x.company.Name.ToLower().Contains(search) ||
                x.company.TaxCode.ToLower().Contains(search));
        }

        if (!string.IsNullOrWhiteSpace(filter.Status) &&
            Enum.TryParse<CompanyVerificationStatus>(filter.Status, true, out var statusEnum))
        {
            query = query.Where(x => x.company.VerifiedStatus == statusEnum);
        }

        var totalCount = await query.CountAsync(cancellationToken);

        var results = await query
            .OrderByDescending(x => x.company.CreatedAt)
            .Skip((pageIndex - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync(cancellationToken);

        // Fetch user emails for each employer
        var userIds = results.Select(r => r.employer.UserId).Distinct().ToList();
        var userEmails = new Dictionary<Guid, string?>();
        foreach (var uid in userIds)
        {
            userEmails[uid] = await _identityService.GetUserEmailAsync(uid, cancellationToken);
        }

        var items = results.Select(r => new AdminCompanyProfileResponse(
            r.company.Id,
            r.employer.UserId,
            r.company.Name,
            userEmails.GetValueOrDefault(r.employer.UserId) ?? "",
            r.employer.Phone,
            r.company.WebsiteUrl,
            r.company.Address,
            r.company.Scale,
            r.company.Industry,
            r.company.Description,
            r.company.LogoUrl,
            r.company.VerifiedStatus.ToString(),
            r.company.CreatedAt,
            r.company.UpdatedAt
        )).ToList();

        var result = new PagedResult<AdminCompanyProfileResponse>(items, totalCount, pageIndex, pageSize);
        return ServiceResult.Success(result);
    }

    public async Task<ServiceResult<AdminCompanyProfileResponse>> UpdateCompanyStatusAsync(
        Guid adminUserId, Guid companyId, UpdateCompanyStatusRequest request, string? ipAddress, CancellationToken cancellationToken = default)
    {
        var company = await _context.Companies
            .FirstOrDefaultAsync(c => c.Id == companyId && !c.IsDeleted, cancellationToken);

        if (company is null)
            return ServiceResult.NotFound<AdminCompanyProfileResponse>("Company not found.");

        var employer = await _context.Employers
            .FirstOrDefaultAsync(e => e.CompanyId == companyId && !e.IsDeleted, cancellationToken);

        if (employer is null)
            return ServiceResult.NotFound<AdminCompanyProfileResponse>("Employer not found for this company.");

        if (!Enum.TryParse<CompanyVerificationStatus>(request.Status, true, out var newStatus))
            return ServiceResult.Failure<AdminCompanyProfileResponse>($"Invalid company verification status: '{request.Status}'.", ServiceErrorType.Validation);

        company.VerifiedStatus = newStatus;
        company.VerifiedAt     = newStatus == CompanyVerificationStatus.Verified
            ? DateTimeOffset.UtcNow
            : null;

        // Write Audit Log
        _context.AuditLogs.Add(new AuditLog
        {
            UserId      = adminUserId,
            Action      = "Company.StatusUpdated",
            EntityType  = "Company",
            EntityId    = companyId.ToString(),
            PayloadJson = JsonSerializer.Serialize(new { Status = request.Status, Note = request.Note }),
            IpAddress   = ipAddress,
        });

        await _context.SaveChangesAsync(cancellationToken);

        var userEmail = await _identityService.GetUserEmailAsync(employer.UserId, cancellationToken);

        var response = new AdminCompanyProfileResponse(
            company.Id,
            employer.UserId,
            company.Name,
            userEmail ?? "",
            employer.Phone,
            company.WebsiteUrl,
            company.Address,
            company.Scale,
            company.Industry,
            company.Description,
            company.LogoUrl,
            company.VerifiedStatus.ToString(),
            company.CreatedAt,
            company.UpdatedAt
        );

        return ServiceResult.Success(response);
    }

    public async Task<ServiceResult<bool>> ApproveCompanyAsync(
        Guid adminUserId, Guid companyId, string? ipAddress, CancellationToken cancellationToken = default)
    {
        var company = await _context.Companies
            .FirstOrDefaultAsync(c => c.Id == companyId && !c.IsDeleted, cancellationToken);

        if (company is null)
            return ServiceResult.NotFound<bool>("Company not found.");

        if (company.VerifiedStatus == CompanyVerificationStatus.Verified)
            return ServiceResult.Failure<bool>("Company is already verified.", ServiceErrorType.Conflict);

        company.VerifiedStatus = CompanyVerificationStatus.Verified;
        company.VerifiedAt     = DateTimeOffset.UtcNow;

        _context.AuditLogs.Add(new AuditLog
        {
            UserId      = adminUserId,
            Action      = "Company.Approved",
            EntityType  = "Company",
            EntityId    = companyId.ToString(),
            PayloadJson = JsonSerializer.Serialize(new { Status = "Verified" }),
            IpAddress   = ipAddress,
        });

        await _context.SaveChangesAsync(cancellationToken);

        return ServiceResult.Success(true);
    }

    public async Task<ServiceResult<bool>> RejectCompanyAsync(
        Guid adminUserId, Guid companyId, string reason, string? ipAddress, CancellationToken cancellationToken = default)
    {
        var company = await _context.Companies
            .FirstOrDefaultAsync(c => c.Id == companyId && !c.IsDeleted, cancellationToken);

        if (company is null)
            return ServiceResult.NotFound<bool>("Company not found.");

        if (company.VerifiedStatus == CompanyVerificationStatus.Rejected)
            return ServiceResult.Failure<bool>("Company is already rejected.", ServiceErrorType.Conflict);

        company.VerifiedStatus = CompanyVerificationStatus.Rejected;
        company.VerifiedAt     = null;

        _context.AuditLogs.Add(new AuditLog
        {
            UserId      = adminUserId,
            Action      = "Company.Rejected",
            EntityType  = "Company",
            EntityId    = companyId.ToString(),
            PayloadJson = JsonSerializer.Serialize(new { Status = "Rejected", Reason = reason }),
            IpAddress   = ipAddress,
        });

        await _context.SaveChangesAsync(cancellationToken);

        return ServiceResult.Success(true);
    }

    // -------------------------------------------------------------------------
    // Audit Log Management
    // -------------------------------------------------------------------------

    public async Task<ServiceResult<PagedResult<AuditLogResponse>>> GetAuditLogsAsync(
        AuditLogQueryFilter filter, CancellationToken cancellationToken = default)
    {
        var pageIndex = filter.PageIndex < 1 ? 1 : filter.PageIndex;
        var pageSize  = filter.PageSize is < 1 or > 100 ? 10 : filter.PageSize;

        var query = _context.AuditLogs.AsNoTracking();

        if (filter.UserId.HasValue)
            query = query.Where(a => a.UserId == filter.UserId.Value);

        if (!string.IsNullOrWhiteSpace(filter.Action))
        {
            var action = filter.Action.Trim().ToLower();
            query = query.Where(a => a.Action.ToLower().Contains(action));
        }

        var totalCount = await query.CountAsync(cancellationToken);

        var logs = await query
            .OrderByDescending(a => a.CreatedAt)
            .Skip((pageIndex - 1) * pageSize)
            .Take(pageSize)
            .Select(a => new AuditLogResponse(
                a.Id, a.UserId, a.Action, a.EntityType, a.EntityId,
                a.PayloadJson, a.IpAddress, a.CreatedAt))
            .ToListAsync(cancellationToken);

        var result = new PagedResult<AuditLogResponse>(logs, totalCount, pageIndex, pageSize);
        return ServiceResult.Success(result);
    }

    // -------------------------------------------------------------------------
    // Dashboard Statistics (P5-UC05)
    // -------------------------------------------------------------------------

    public async Task<ServiceResult<AdminDashboardStatsResponse>> GetDashboardStatsAsync(
        CancellationToken cancellationToken = default)
    {
        // 1. User stats via IIdentityService
        var userStats = await _identityService.GetUserStatsAsync(cancellationToken);

        // 2. Company stats
        var totalCompanies = await _context.Companies.CountAsync(c => !c.IsDeleted, cancellationToken);
        var verifiedCompanies = await _context.Companies
            .CountAsync(c => !c.IsDeleted && c.VerifiedStatus == CompanyVerificationStatus.Verified, cancellationToken);
        var pendingCompanies = await _context.Companies
            .CountAsync(c => !c.IsDeleted && c.VerifiedStatus == CompanyVerificationStatus.Pending, cancellationToken);
        var rejectedCompanies = await _context.Companies
            .CountAsync(c => !c.IsDeleted && c.VerifiedStatus == CompanyVerificationStatus.Rejected, cancellationToken);

        var companyStats = new AdminCompanyStatsDto(
            totalCompanies,
            verifiedCompanies,
            pendingCompanies,
            rejectedCompanies);

        // 3. Job stats
        var totalJobs = await _context.Jobs.CountAsync(j => !j.IsDeleted, cancellationToken);
        var activeJobs = await _context.Jobs
            .CountAsync(j => !j.IsDeleted && j.IsActive && !j.IsBanned && j.ApprovalStatus == JobApprovalStatus.Approved, cancellationToken);
        var pendingJobs = await _context.Jobs
            .CountAsync(j => !j.IsDeleted && j.ApprovalStatus == JobApprovalStatus.Pending, cancellationToken);
        var rejectedJobs = await _context.Jobs
            .CountAsync(j => !j.IsDeleted && j.ApprovalStatus == JobApprovalStatus.Rejected, cancellationToken);
        var bannedJobs = await _context.Jobs
            .CountAsync(j => !j.IsDeleted && j.IsBanned, cancellationToken);
        var now = DateTime.UtcNow;
        var expiredJobs = await _context.Jobs
            .CountAsync(j => !j.IsDeleted && j.Deadline.HasValue && j.Deadline.Value < now, cancellationToken);

        var jobStats = new AdminJobStatsDto(
            totalJobs,
            activeJobs,
            pendingJobs,
            rejectedJobs,
            bannedJobs,
            expiredJobs);

        // 4. Application stats
        var totalApplications = await _context.Applications.CountAsync(a => !a.IsDeleted, cancellationToken);
        var appliedCount = await _context.Applications.CountAsync(a => !a.IsDeleted && a.Status == ApplicationStatus.Applied, cancellationToken);
        var screeningCount = await _context.Applications.CountAsync(a => !a.IsDeleted && a.Status == ApplicationStatus.Screening, cancellationToken);
        var interviewCount = await _context.Applications.CountAsync(a => !a.IsDeleted && a.Status == ApplicationStatus.Interview, cancellationToken);
        var offerCount = await _context.Applications.CountAsync(a => !a.IsDeleted && a.Status == ApplicationStatus.Offer, cancellationToken);
        var hiredCount = await _context.Applications.CountAsync(a => !a.IsDeleted && a.Status == ApplicationStatus.Hired, cancellationToken);
        var rejectedAppsCount = await _context.Applications.CountAsync(a => !a.IsDeleted && a.Status == ApplicationStatus.Rejected, cancellationToken);
        var withdrawnCount = await _context.Applications.CountAsync(a => !a.IsDeleted && a.Status == ApplicationStatus.Withdrawn, cancellationToken);

        var appStats = new AdminApplicationStatsDto(
            totalApplications,
            appliedCount,
            screeningCount,
            interviewCount,
            offerCount,
            hiredCount,
            rejectedAppsCount,
            withdrawnCount);

        // 5. Pending reports count
        var pendingReportsCount = await _context.JobReports
            .CountAsync(r => !r.IsDeleted && r.Status == JobReportStatus.Pending, cancellationToken);

        // 6. Monthly trend (last 6 months)
        var monthlyTrends = new List<MonthlyTrendDto>();
        var nowUtc = DateTime.UtcNow;
        for (int i = 5; i >= 0; i--)
        {
            var monthStart = new DateTime(nowUtc.Year, nowUtc.Month, 1, 0, 0, 0, DateTimeKind.Utc).AddMonths(-i);
            var monthEnd = monthStart.AddMonths(1);
            var monthLabel = monthStart.ToString("yyyy-MM");

            var newJobs = await _context.Jobs
                .CountAsync(j => !j.IsDeleted && j.CreatedAt >= monthStart && j.CreatedAt < monthEnd, cancellationToken);
            var newApps = await _context.Applications
                .CountAsync(a => !a.IsDeleted && a.AppliedAt >= monthStart && a.AppliedAt < monthEnd, cancellationToken);
            var newCandidates = await _context.Candidates
                .CountAsync(c => !c.IsDeleted && c.CreatedAt >= monthStart && c.CreatedAt < monthEnd, cancellationToken);
            var newEmployers = await _context.Employers
                .CountAsync(e => !e.IsDeleted && e.CreatedAt >= monthStart && e.CreatedAt < monthEnd, cancellationToken);

            monthlyTrends.Add(new MonthlyTrendDto(monthLabel, newCandidates + newEmployers, newJobs, newApps));
        }

        var response = new AdminDashboardStatsResponse(
            userStats,
            companyStats,
            jobStats,
            appStats,
            pendingReportsCount,
            monthlyTrends);

        return ServiceResult.Success(response);
    }

    // -------------------------------------------------------------------------
    // Job Reports & Moderation (P5-UC07)
    // -------------------------------------------------------------------------

    public async Task<ServiceResult<PagedResult<JobReportResponse>>> GetJobReportsAsync(
        JobReportFilterRequest filter, CancellationToken cancellationToken = default)
    {
        var pageIndex = filter.PageIndex < 1 ? 1 : filter.PageIndex;
        var pageSize  = filter.PageSize is < 1 or > 100 ? 10 : filter.PageSize;

        var query = _context.JobReports
            .AsNoTracking()
            .Include(r => r.Job)
                .ThenInclude(j => j.Company)
            .Where(r => !r.IsDeleted);

        if (!string.IsNullOrWhiteSpace(filter.Status) &&
            Enum.TryParse<JobReportStatus>(filter.Status, true, out var reportStatusEnum))
        {
            query = query.Where(r => r.Status == reportStatusEnum);
        }

        if (filter.JobId.HasValue)
        {
            query = query.Where(r => r.JobId == filter.JobId.Value);
        }

        var totalCount = await query.CountAsync(cancellationToken);

        var reports = await query
            .OrderByDescending(r => r.CreatedAt)
            .Skip((pageIndex - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync(cancellationToken);

        // Fetch reporter emails
        var reporterUserIds = reports.Select(r => r.ReporterUserId).Distinct().ToList();
        var userEmails = new Dictionary<Guid, string?>();
        foreach (var uid in reporterUserIds)
        {
            userEmails[uid] = await _identityService.GetUserEmailAsync(uid, cancellationToken);
        }

        var items = reports.Select(r => new JobReportResponse(
            r.Id,
            r.JobId,
            r.Job.Title,
            r.Job.CompanyId,
            r.Job.Company.Name,
            r.ReporterUserId,
            userEmails.GetValueOrDefault(r.ReporterUserId),
            r.Reason,
            r.Details,
            r.Status.ToString(),
            r.ResolvedByAdminId,
            r.ResolvedAt,
            r.AdminNote,
            r.CreatedAt
        )).ToList();

        return ServiceResult.Success(new PagedResult<JobReportResponse>(items, totalCount, pageIndex, pageSize));
    }

    public async Task<ServiceResult<JobReportResponse>> GetJobReportByIdAsync(
        Guid reportId, CancellationToken cancellationToken = default)
    {
        var report = await _context.JobReports
            .AsNoTracking()
            .Include(r => r.Job)
                .ThenInclude(j => j.Company)
            .FirstOrDefaultAsync(r => r.Id == reportId && !r.IsDeleted, cancellationToken);

        if (report is null)
            return ServiceResult.NotFound<JobReportResponse>("Job report not found.");

        var reporterEmail = await _identityService.GetUserEmailAsync(report.ReporterUserId, cancellationToken);

        var response = new JobReportResponse(
            report.Id,
            report.JobId,
            report.Job.Title,
            report.Job.CompanyId,
            report.Job.Company.Name,
            report.ReporterUserId,
            reporterEmail,
            report.Reason,
            report.Details,
            report.Status.ToString(),
            report.ResolvedByAdminId,
            report.ResolvedAt,
            report.AdminNote,
            report.CreatedAt
        );

        return ServiceResult.Success(response);
    }

    public async Task<ServiceResult<bool>> ResolveJobReportAsync(
        Guid adminUserId, Guid reportId, ResolveJobReportRequest request, string? ipAddress, CancellationToken cancellationToken = default)
    {
        var report = await _context.JobReports
            .Include(r => r.Job)
            .FirstOrDefaultAsync(r => r.Id == reportId && !r.IsDeleted, cancellationToken);

        if (report is null)
            return ServiceResult.NotFound<bool>("Job report not found.");

        if (report.Status != JobReportStatus.Pending)
            return ServiceResult.Failure<bool>($"Report has already been processed with status '{report.Status}'.", ServiceErrorType.Validation);

        var now = DateTimeOffset.UtcNow;
        report.ResolvedByAdminId = adminUserId;
        report.ResolvedAt        = now;
        report.AdminNote         = request.AdminNote;

        if (request.Action.Equals("BanJob", StringComparison.OrdinalIgnoreCase))
        {
            report.Status = JobReportStatus.Resolved;

            // Ban the job
            report.Job.IsBanned = true;
            report.Job.IsActive = false;
            report.Job.BannedAt = now;
            report.Job.BannedByAdminId = adminUserId;
            report.Job.BannedReason = string.IsNullOrWhiteSpace(request.AdminNote) ? report.Reason : request.AdminNote;

            // Auto-resolve other pending reports for the same job
            var otherReports = await _context.JobReports
                .Where(r => r.JobId == report.JobId && r.Id != reportId && r.Status == JobReportStatus.Pending && !r.IsDeleted)
                .ToListAsync(cancellationToken);

            foreach (var other in otherReports)
            {
                other.Status = JobReportStatus.Resolved;
                other.ResolvedByAdminId = adminUserId;
                other.ResolvedAt = now;
                other.AdminNote = "Resolved along with report " + reportId;
            }

            // Audit Log
            _context.AuditLogs.Add(new AuditLog
            {
                UserId      = adminUserId,
                Action      = "Job.BannedViaReport",
                EntityType  = "Job",
                EntityId    = report.JobId.ToString(),
                PayloadJson = JsonSerializer.Serialize(new { ReportId = reportId, Reason = report.Job.BannedReason }),
                IpAddress   = ipAddress
            });
        }
        else
        {
            report.Status = JobReportStatus.Dismissed;

            // Audit Log
            _context.AuditLogs.Add(new AuditLog
            {
                UserId      = adminUserId,
                Action      = "JobReport.Dismissed",
                EntityType  = "JobReport",
                EntityId    = reportId.ToString(),
                PayloadJson = JsonSerializer.Serialize(new { Reason = request.AdminNote }),
                IpAddress   = ipAddress
            });
        }

        await _context.SaveChangesAsync(cancellationToken);
        return ServiceResult.Success(true);
    }

    public async Task<ServiceResult<bool>> BanJobAsync(
        Guid adminUserId, Guid jobId, string reason, string? ipAddress, CancellationToken cancellationToken = default)
    {
        var job = await _context.Jobs
            .FirstOrDefaultAsync(j => j.Id == jobId && !j.IsDeleted, cancellationToken);

        if (job is null)
            return ServiceResult.NotFound<bool>("Job not found.");

        if (job.IsBanned)
            return ServiceResult.Failure<bool>("This job is already banned.", ServiceErrorType.Validation);

        var now = DateTimeOffset.UtcNow;
        job.IsBanned          = true;
        job.IsActive          = false;
        job.BannedAt          = now;
        job.BannedByAdminId   = adminUserId;
        job.BannedReason      = reason;

        // Resolve any pending reports for this job
        var pendingReports = await _context.JobReports
            .Where(r => r.JobId == jobId && r.Status == JobReportStatus.Pending && !r.IsDeleted)
            .ToListAsync(cancellationToken);

        foreach (var r in pendingReports)
        {
            r.Status            = JobReportStatus.Resolved;
            r.ResolvedByAdminId = adminUserId;
            r.ResolvedAt        = now;
            r.AdminNote         = $"Job was banned directly by Admin: {reason}";
        }

        _context.AuditLogs.Add(new AuditLog
        {
            UserId      = adminUserId,
            Action      = "Job.Banned",
            EntityType  = "Job",
            EntityId    = jobId.ToString(),
            PayloadJson = JsonSerializer.Serialize(new { Reason = reason }),
            IpAddress   = ipAddress
        });

        await _context.SaveChangesAsync(cancellationToken);
        return ServiceResult.Success(true);
    }

    public async Task<ServiceResult<bool>> UnbanJobAsync(
        Guid adminUserId, Guid jobId, string? ipAddress, CancellationToken cancellationToken = default)
    {
        var job = await _context.Jobs
            .FirstOrDefaultAsync(j => j.Id == jobId && !j.IsDeleted, cancellationToken);

        if (job is null)
            return ServiceResult.NotFound<bool>("Job not found.");

        if (!job.IsBanned)
            return ServiceResult.Failure<bool>("This job is not currently banned.", ServiceErrorType.Validation);

        job.IsBanned        = false;
        job.BannedAt        = null;
        job.BannedByAdminId = null;
        job.BannedReason    = null;

        _context.AuditLogs.Add(new AuditLog
        {
            UserId      = adminUserId,
            Action      = "Job.Unbanned",
            EntityType  = "Job",
            EntityId    = jobId.ToString(),
            IpAddress   = ipAddress
        });

        await _context.SaveChangesAsync(cancellationToken);
        return ServiceResult.Success(true);
    }
}
