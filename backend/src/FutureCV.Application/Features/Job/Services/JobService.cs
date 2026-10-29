using FutureCV.Application.Common.Interfaces;
using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.Job.DTOs;
using FutureCV.Application.Features.Job.Interfaces;
using FutureCV.Domain.Entities;
using Microsoft.EntityFrameworkCore;

namespace FutureCV.Application.Features.Job.Services;

using FutureCV.Domain.Entities;
using FutureCV.Domain.Enums;

public class JobService : IJobService
{
    private readonly IApplicationDbContext _context;

    public JobService(IApplicationDbContext context)
    {
        _context = context;
    }

    // -------------------------------------------------------------------------
    // Employer Operations
    // -------------------------------------------------------------------------

    public async Task<ServiceResult<JobDetailResponse>> CreateJobAsync(
        Guid userId, CreateJobRequest request, CancellationToken cancellationToken = default)
    {
        // 1. Verify Employer profile and associated company
        var employer = await _context.Employers
            .Include(e => e.Company)
            .FirstOrDefaultAsync(e => e.UserId == userId, cancellationToken);

        if (employer is null)
            return ServiceResult.NotFound<JobDetailResponse>("Employer profile not found.");

        if (employer.CompanyId == Guid.Empty || employer.Company is null)
            return ServiceResult.Failure<JobDetailResponse>("Employer is not linked to any company. Please register company first.");

        // 2. Determine approval status: Verified companies post Approved jobs, others are Pending
        var initialApprovalStatus = employer.Company.VerifiedStatus == CompanyVerificationStatus.Verified
            ? JobApprovalStatus.Approved
            : JobApprovalStatus.Pending;

        // 3. Initialize Job entity
        var job = new Job
        {
            CompanyId          = employer.CompanyId,
            PostedById         = userId,
            Title              = request.Title.Trim(),
            Description        = request.Description,
            Requirements       = request.Requirements,
            Benefits           = request.Benefits,
            CategoryId         = request.CategoryId,
            LevelId            = request.LevelId,
            EmploymentTypeId   = request.EmploymentTypeId,
            LocationId         = request.LocationId,
            SalaryMin          = request.SalaryMin,
            SalaryMax          = request.SalaryMax,
            SalaryCurrency     = string.IsNullOrWhiteSpace(request.SalaryCurrency) ? "VND" : request.SalaryCurrency.ToUpperInvariant(),
            ExperienceYearsMin = request.ExperienceYearsMin,
            ExperienceYearsMax = request.ExperienceYearsMax,
            Deadline           = request.Deadline,
            PositionsCount     = request.PositionsCount <= 0 ? 1 : request.PositionsCount,
            ApprovalStatus     = initialApprovalStatus,
            IsActive           = true,
            IsExpired          = false,
            ViewCount          = 0,
            IsDeleted          = false
        };

        // 4. Attach valid skills if requested
        if (request.Skills != null && request.Skills.Count > 0)
        {
            var requestedSkillIds = request.Skills.Select(s => s.SkillId).Distinct().ToList();
            var validSkillIds = await _context.Skills
                .Where(s => requestedSkillIds.Contains(s.Id))
                .Select(s => s.Id)
                .ToListAsync(cancellationToken);

            foreach (var skillDto in request.Skills.Where(s => validSkillIds.Contains(s.SkillId)))
            {
                job.JobSkills.Add(new JobSkill
                {
                    Job        = job,
                    SkillId    = skillDto.SkillId,
                    IsRequired = skillDto.IsRequired
                });
            }
        }

        // 5. Persist to database
        _context.Jobs.Add(job);
        await _context.SaveChangesAsync(cancellationToken);

        return await GetJobDetailInternalAsync(job.Id, cancellationToken);
    }

    public async Task<ServiceResult<JobDetailResponse>> UpdateJobAsync(
        Guid userId, Guid jobId, UpdateJobRequest request, CancellationToken cancellationToken = default)
    {
        // 1. Check ownership
        var (job, error) = await FindJobWithOwnershipAsync(userId, jobId, cancellationToken);
        if (error is not null) return error;

        // 2. Update job properties
        job!.Title              = request.Title.Trim();
        job.Description         = request.Description;
        job.Requirements        = request.Requirements;
        job.Benefits            = request.Benefits;
        job.CategoryId          = request.CategoryId;
        job.LevelId             = request.LevelId;
        job.EmploymentTypeId    = request.EmploymentTypeId;
        job.LocationId          = request.LocationId;
        job.SalaryMin           = request.SalaryMin;
        job.SalaryMax           = request.SalaryMax;
        job.SalaryCurrency      = string.IsNullOrWhiteSpace(request.SalaryCurrency) ? "VND" : request.SalaryCurrency.ToUpperInvariant();
        job.ExperienceYearsMin  = request.ExperienceYearsMin;
        job.ExperienceYearsMax  = request.ExperienceYearsMax;
        job.Deadline            = request.Deadline;
        job.PositionsCount      = request.PositionsCount <= 0 ? 1 : request.PositionsCount;

        // 3. Refresh job skills
        var existingSkills = await _context.JobSkills
            .Where(js => js.JobId == jobId)
            .ToListAsync(cancellationToken);

        _context.JobSkills.RemoveRange(existingSkills);

        if (request.Skills != null && request.Skills.Count > 0)
        {
            var requestedSkillIds = request.Skills.Select(s => s.SkillId).Distinct().ToList();
            var validSkillIds = await _context.Skills
                .Where(s => requestedSkillIds.Contains(s.Id))
                .Select(s => s.Id)
                .ToListAsync(cancellationToken);

            foreach (var skillDto in request.Skills.Where(s => validSkillIds.Contains(s.SkillId)))
            {
                _context.JobSkills.Add(new JobSkill
                {
                    JobId      = jobId,
                    SkillId    = skillDto.SkillId,
                    IsRequired = skillDto.IsRequired
                });
            }
        }

        // 4. Save changes
        await _context.SaveChangesAsync(cancellationToken);

        return await GetJobDetailInternalAsync(jobId, cancellationToken);
    }

    public async Task<ServiceResult<bool>> ToggleJobStatusAsync(
        Guid userId, Guid jobId, CancellationToken cancellationToken = default)
    {
        var (job, error) = await FindJobWithOwnershipAsync(userId, jobId, cancellationToken);
        if (error is not null) return ServiceResult.Failure<bool>(error.ErrorMessage ?? "Job not found.", error.ErrorType);

        if (job!.IsBanned)
        {
            return ServiceResult.Failure<bool>(
                "This job has been banned by an administrator due to policy violations and cannot be activated.",
                ServiceErrorType.Forbidden);
        }

        job.IsActive = !job.IsActive;
        await _context.SaveChangesAsync(cancellationToken);

        return ServiceResult.Success(job.IsActive);
    }

    public async Task<ServiceResult<bool>> DeleteJobAsync(
        Guid userId, Guid jobId, CancellationToken cancellationToken = default)
    {
        var (job, error) = await FindJobWithOwnershipAsync(userId, jobId, cancellationToken);
        if (error is not null) return ServiceResult.Failure<bool>(error.ErrorMessage ?? "Job not found.", error.ErrorType);

        job!.IsDeleted = true;
        await _context.SaveChangesAsync(cancellationToken);

        return ServiceResult.Success(true);
    }

    public async Task<ServiceResult<PagedResult<JobListResponse>>> GetEmployerJobsAsync(
        Guid userId, EmployerJobFilterRequest filter, CancellationToken cancellationToken = default)
    {
        var employer = await _context.Employers
            .FirstOrDefaultAsync(e => e.UserId == userId, cancellationToken);

        if (employer is null)
            return ServiceResult.NotFound<PagedResult<JobListResponse>>("Employer profile not found.");

        var query = _context.Jobs
            .AsNoTracking()
            .Where(j => j.CompanyId == employer.CompanyId && !j.IsDeleted);

        if (!string.IsNullOrWhiteSpace(filter.Keyword))
        {
            var kw = filter.Keyword.Trim().ToLower();
            query = query.Where(j => j.Title.ToLower().Contains(kw));
        }

        if (!string.IsNullOrWhiteSpace(filter.ApprovalStatus) &&
            Enum.TryParse<JobApprovalStatus>(filter.ApprovalStatus, true, out var approvalStatusEnum))
        {
            query = query.Where(j => j.ApprovalStatus == approvalStatusEnum);
        }

        if (filter.IsActive.HasValue)
        {
            query = query.Where(j => j.IsActive == filter.IsActive.Value);
        }

        var totalCount = await query.CountAsync(cancellationToken);

        var pageIndex = filter.PageIndex < 1 ? 1 : filter.PageIndex;
        var pageSize  = filter.PageSize is < 1 or > 100 ? 10 : filter.PageSize;

        var items = await query
            .OrderByDescending(j => j.CreatedAt)
            .Skip((pageIndex - 1) * pageSize)
            .Take(pageSize)
            .Select(j => new JobListResponse(
                j.Id,
                j.CompanyId,
                j.Company.Name,
                j.Company.LogoUrl,
                j.Title,
                j.Category != null ? j.Category.Name : null,
                j.Level != null ? j.Level.Name : null,
                j.EmploymentType != null ? j.EmploymentType.Name : null,
                j.Location != null ? j.Location.Name : null,
                j.SalaryMin,
                j.SalaryMax,
                j.SalaryCurrency,
                j.ExperienceYearsMin,
                j.ExperienceYearsMax,
                j.Deadline,
                j.PositionsCount,
                j.ApprovalStatus.ToString(),
                j.IsActive,
                j.IsExpired,
                j.ViewCount,
                j.CreatedAt,
                j.JobSkills.Where(js => js.IsRequired).Select(js => js.Skill.Name).ToList()
            ))
            .ToListAsync(cancellationToken);

        return ServiceResult.Success(new PagedResult<JobListResponse>(items, totalCount, pageIndex, pageSize));
    }

    public async Task<ServiceResult<JobDetailResponse>> GetEmployerJobByIdAsync(
        Guid userId, Guid jobId, CancellationToken cancellationToken = default)
    {
        var (job, error) = await FindJobWithOwnershipAsync(userId, jobId, cancellationToken);
        if (error is not null) return error;

        return await GetJobDetailInternalAsync(jobId, cancellationToken);
    }

    // -------------------------------------------------------------------------
    // Public / Candidate Search & Details
    // -------------------------------------------------------------------------

    public async Task<ServiceResult<PagedResult<JobListResponse>>> SearchJobsAsync(
        JobFilterRequest filter, CancellationToken cancellationToken = default)
    {
        var now = DateTime.UtcNow;

        var query = _context.Jobs
            .AsNoTracking()
            .Where(j => !j.IsDeleted && !j.IsBanned && j.IsActive && j.ApprovalStatus == JobApprovalStatus.Approved);

        // Exclude expired jobs
        query = query.Where(j => !j.Deadline.HasValue || j.Deadline.Value >= now);

        // 1. Keyword search (Title or Description)
        if (!string.IsNullOrWhiteSpace(filter.Keyword))
        {
            var kw = filter.Keyword.Trim().ToLower();
            query = query.Where(j => j.Title.ToLower().Contains(kw) || j.Description.ToLower().Contains(kw));
        }

        // 2. Taxonomy filters
        if (filter.CategoryId.HasValue)
            query = query.Where(j => j.CategoryId == filter.CategoryId.Value);

        if (filter.LevelId.HasValue)
            query = query.Where(j => j.LevelId == filter.LevelId.Value);

        if (filter.EmploymentTypeId.HasValue)
            query = query.Where(j => j.EmploymentTypeId == filter.EmploymentTypeId.Value);

        if (filter.LocationId.HasValue)
            query = query.Where(j => j.LocationId == filter.LocationId.Value);

        // 3. Salary range filter
        if (filter.SalaryMin.HasValue)
            query = query.Where(j => j.SalaryMax == null || j.SalaryMax >= filter.SalaryMin.Value);

        if (filter.SalaryMax.HasValue)
            query = query.Where(j => j.SalaryMin == null || j.SalaryMin <= filter.SalaryMax.Value);

        // 4. Skills filter
        if (filter.SkillIds != null && filter.SkillIds.Count > 0)
        {
            query = query.Where(j => j.JobSkills.Any(js => filter.SkillIds.Contains(js.SkillId)));
        }

        var totalCount = await query.CountAsync(cancellationToken);

        // 5. Sorting
        query = (filter.SortBy?.ToLowerInvariant()) switch
        {
            "salary_desc" => query.OrderByDescending(j => j.SalaryMax ?? j.SalaryMin ?? 0),
            "deadline"    => query.OrderBy(j => j.Deadline ?? DateTime.MaxValue),
            _             => query.OrderByDescending(j => j.CreatedAt)
        };

        var pageIndex = filter.PageIndex < 1 ? 1 : filter.PageIndex;
        var pageSize  = filter.PageSize is < 1 or > 100 ? 10 : filter.PageSize;

        var items = await query
            .Skip((pageIndex - 1) * pageSize)
            .Take(pageSize)
            .Select(j => new JobListResponse(
                j.Id,
                j.CompanyId,
                j.Company.Name,
                j.Company.LogoUrl,
                j.Title,
                j.Category != null ? j.Category.Name : null,
                j.Level != null ? j.Level.Name : null,
                j.EmploymentType != null ? j.EmploymentType.Name : null,
                j.Location != null ? j.Location.Name : null,
                j.SalaryMin,
                j.SalaryMax,
                j.SalaryCurrency,
                j.ExperienceYearsMin,
                j.ExperienceYearsMax,
                j.Deadline,
                j.PositionsCount,
                j.ApprovalStatus.ToString(),
                j.IsActive,
                j.IsExpired,
                j.ViewCount,
                j.CreatedAt,
                j.JobSkills.Where(js => js.IsRequired).Select(js => js.Skill.Name).ToList()
            ))
            .ToListAsync(cancellationToken);

        return ServiceResult.Success(new PagedResult<JobListResponse>(items, totalCount, pageIndex, pageSize));
    }

    public async Task<ServiceResult<JobDetailResponse>> GetJobDetailAsync(
        Guid jobId, bool incrementView = true, CancellationToken cancellationToken = default)
    {
        var job = await _context.Jobs
            .FirstOrDefaultAsync(j => j.Id == jobId && !j.IsDeleted, cancellationToken);

        if (job is null || job.IsBanned)
            return ServiceResult.NotFound<JobDetailResponse>("Job not found.");

        // Automatically increment view count
        if (incrementView)
        {
            job.ViewCount++;
            await _context.SaveChangesAsync(cancellationToken);
        }

        return await GetJobDetailInternalAsync(jobId, cancellationToken);
    }

    public async Task<ServiceResult<bool>> ReportJobAsync(
        Guid userId, Guid jobId, CreateJobReportRequest request, CancellationToken cancellationToken = default)
    {
        var job = await _context.Jobs
            .FirstOrDefaultAsync(j => j.Id == jobId && !j.IsDeleted, cancellationToken);

        if (job is null || job.IsBanned)
            return ServiceResult.NotFound<bool>("Job not found.");

        // Prevent reporting own job
        if (job.PostedById == userId)
            return ServiceResult.Failure<bool>("You cannot report your own job posting.", ServiceErrorType.Validation);

        // Check if user has already submitted a pending report for this job
        var alreadyReported = await _context.JobReports
            .AnyAsync(r => r.JobId == jobId && r.ReporterUserId == userId && r.Status == JobReportStatus.Pending && !r.IsDeleted, cancellationToken);

        if (alreadyReported)
            return ServiceResult.Conflict<bool>("You have already submitted a pending report for this job.");

        var report = new JobReport
        {
            JobId          = jobId,
            ReporterUserId = userId,
            Reason         = request.Reason.Trim(),
            Details        = request.Details?.Trim(),
            Status         = JobReportStatus.Pending
        };

        _context.JobReports.Add(report);
        await _context.SaveChangesAsync(cancellationToken);

        return ServiceResult.Success(true);
    }

    // -------------------------------------------------------------------------
    // Master Data Lookups
    // -------------------------------------------------------------------------

    public async Task<ServiceResult<IReadOnlyList<JobCategoryResponse>>> GetCategoriesAsync(
        CancellationToken cancellationToken = default)
    {
        var items = await _context.JobCategories
            .AsNoTracking()
            .OrderBy(c => c.Name)
            .Select(c => new JobCategoryResponse(c.Id, c.Name, c.ParentId))
            .ToListAsync(cancellationToken);

        return ServiceResult.Success<IReadOnlyList<JobCategoryResponse>>(items);
    }

    public async Task<ServiceResult<IReadOnlyList<JobLevelResponse>>> GetLevelsAsync(
        CancellationToken cancellationToken = default)
    {
        var items = await _context.JobLevels
            .AsNoTracking()
            .OrderBy(l => l.Name)
            .Select(l => new JobLevelResponse(l.Id, l.Name))
            .ToListAsync(cancellationToken);

        return ServiceResult.Success<IReadOnlyList<JobLevelResponse>>(items);
    }

    public async Task<ServiceResult<IReadOnlyList<EmploymentTypeResponse>>> GetEmploymentTypesAsync(
        CancellationToken cancellationToken = default)
    {
        var items = await _context.EmploymentTypes
            .AsNoTracking()
            .OrderBy(t => t.Name)
            .Select(t => new EmploymentTypeResponse(t.Id, t.Name))
            .ToListAsync(cancellationToken);

        return ServiceResult.Success<IReadOnlyList<EmploymentTypeResponse>>(items);
    }

    public async Task<ServiceResult<IReadOnlyList<LocationResponse>>> GetLocationsAsync(
        CancellationToken cancellationToken = default)
    {
        var items = await _context.Locations
            .AsNoTracking()
            .OrderBy(l => l.Name)
            .Select(l => new LocationResponse(l.Id, l.Name, l.ParentId))
            .ToListAsync(cancellationToken);

        return ServiceResult.Success<IReadOnlyList<LocationResponse>>(items);
    }

    // -------------------------------------------------------------------------
    // Admin Operations
    // -------------------------------------------------------------------------

    public async Task<ServiceResult<PagedResult<JobListResponse>>> GetAdminJobsAsync(
        AdminJobFilterRequest filter, CancellationToken cancellationToken = default)
    {
        var query = _context.Jobs
            .AsNoTracking()
            .Where(j => !j.IsDeleted);

        if (!string.IsNullOrWhiteSpace(filter.Keyword))
        {
            var kw = filter.Keyword.Trim().ToLower();
            query = query.Where(j => j.Title.ToLower().Contains(kw) || j.Company.Name.ToLower().Contains(kw));
        }

        if (!string.IsNullOrWhiteSpace(filter.ApprovalStatus) &&
            Enum.TryParse<JobApprovalStatus>(filter.ApprovalStatus, true, out var approvalStatusEnum))
        {
            query = query.Where(j => j.ApprovalStatus == approvalStatusEnum);
            
            // Tab "Đang tuyển": chỉ hiện jobs đã duyệt, active và chưa hết hạn
            if (approvalStatusEnum == JobApprovalStatus.Approved)
            {
                query = query.Where(j => j.IsActive && !j.IsExpired);
            }
        }

        var totalCount = await query.CountAsync(cancellationToken);

        var pageIndex = filter.PageIndex < 1 ? 1 : filter.PageIndex;
        var pageSize  = filter.PageSize is < 1 or > 100 ? 10 : filter.PageSize;

        var items = await query
            .OrderByDescending(j => j.CreatedAt)
            .Skip((pageIndex - 1) * pageSize)
            .Take(pageSize)
            .Select(j => new JobListResponse(
                j.Id,
                j.CompanyId,
                j.Company.Name,
                j.Company.LogoUrl,
                j.Title,
                j.Category != null ? j.Category.Name : null,
                j.Level != null ? j.Level.Name : null,
                j.EmploymentType != null ? j.EmploymentType.Name : null,
                j.Location != null ? j.Location.Name : null,
                j.SalaryMin,
                j.SalaryMax,
                j.SalaryCurrency,
                j.ExperienceYearsMin,
                j.ExperienceYearsMax,
                j.Deadline,
                j.PositionsCount,
                j.ApprovalStatus.ToString(),
                j.IsActive,
                j.IsExpired,
                j.ViewCount,
                j.CreatedAt,
                j.JobSkills.Where(js => js.IsRequired).Select(js => js.Skill.Name).ToList()
            ))
            .ToListAsync(cancellationToken);

        return ServiceResult.Success(new PagedResult<JobListResponse>(items, totalCount, pageIndex, pageSize));
    }

    public async Task<ServiceResult<bool>> ModerateJobAsync(
        Guid adminUserId, Guid jobId, ApproveJobRequest request, CancellationToken cancellationToken = default)
    {
        var job = await _context.Jobs
            .FirstOrDefaultAsync(j => j.Id == jobId && !j.IsDeleted, cancellationToken);

        if (job is null)
            return ServiceResult.NotFound<bool>("Job not found.");

        job.ApprovalStatus    = request.IsApproved ? JobApprovalStatus.Approved : JobApprovalStatus.Rejected;
        job.ApprovedByAdminId = adminUserId;
        job.ApprovedAt        = DateTimeOffset.UtcNow;
        job.RejectionReason   = request.IsApproved ? null : (request.RejectionReason ?? request.Note);

        await _context.SaveChangesAsync(cancellationToken);

        return ServiceResult.Success(true);
    }

    // -------------------------------------------------------------------------
    // Private Helpers & Ownership Verification
    // -------------------------------------------------------------------------

    private async Task<(Job? Job, ServiceResult<JobDetailResponse>? Error)> FindJobWithOwnershipAsync(
        Guid userId, Guid jobId, CancellationToken cancellationToken)
    {
        var employer = await _context.Employers
            .FirstOrDefaultAsync(e => e.UserId == userId, cancellationToken);

        if (employer is null)
            return (null, ServiceResult.NotFound<JobDetailResponse>("Employer profile not found."));

        var job = await _context.Jobs
            .FirstOrDefaultAsync(j => j.Id == jobId && !j.IsDeleted, cancellationToken);

        if (job is null)
            return (null, ServiceResult.NotFound<JobDetailResponse>("Job not found."));

        if (job.CompanyId != employer.CompanyId)
            return (null, ServiceResult.Forbidden<JobDetailResponse>("Access denied. You do not have permission to manage this job."));

        return (job, null);
    }

    private async Task<ServiceResult<JobDetailResponse>> GetJobDetailInternalAsync(
        Guid jobId, CancellationToken cancellationToken)
    {
        var job = await _context.Jobs
            .AsNoTracking()
            .Include(j => j.Company)
            .Include(j => j.Category)
            .Include(j => j.Level)
            .Include(j => j.EmploymentType)
            .Include(j => j.Location)
            .Include(j => j.JobSkills)
                .ThenInclude(js => js.Skill)
            .FirstOrDefaultAsync(j => j.Id == jobId && !j.IsDeleted, cancellationToken);

        if (job is null)
            return ServiceResult.NotFound<JobDetailResponse>("Job not found.");

        return ServiceResult.Success(MapToJobDetailResponse(job));
    }

    // -------------------------------------------------------------------------
    // Private static mappers — pure functions, easy to extend/test
    // -------------------------------------------------------------------------

    private static JobDetailResponse MapToJobDetailResponse(Job j) => new(
        j.Id,
        j.CompanyId,
        new JobCompanyResponse(
            j.Company.Id,
            j.Company.Name,
            j.Company.LogoUrl,
            j.Company.Address,
            j.Company.Industry,
            j.Company.Scale,
            j.Company.VerifiedStatus.ToString()
        ),
        j.PostedById,
        j.Title,
        j.Description,
        j.Requirements,
        j.Benefits,
        j.CategoryId,
        j.Category?.Name,
        j.LevelId,
        j.Level?.Name,
        j.EmploymentTypeId,
        j.EmploymentType?.Name,
        j.LocationId,
        j.Location?.Name,
        j.SalaryMin,
        j.SalaryMax,
        j.SalaryCurrency,
        j.ExperienceYearsMin,
        j.ExperienceYearsMax,
        j.Deadline,
        j.PositionsCount,
        j.ApprovalStatus.ToString(),
        j.IsActive,
        j.IsExpired,
        j.ViewCount,
        j.CreatedAt,
        j.UpdatedAt,
        j.JobSkills.Select(MapToJobSkillResponse).ToList()
    );

    private static JobSkillResponse MapToJobSkillResponse(JobSkill js) => new(
        js.SkillId,
        js.Skill?.Name ?? string.Empty,
        js.Skill?.Category,
        js.IsRequired
    );
}
