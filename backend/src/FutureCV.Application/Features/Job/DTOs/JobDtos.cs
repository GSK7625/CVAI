namespace FutureCV.Application.Features.Job.DTOs;

public sealed record CreateJobRequest(
    string Title,
    string Description,
    string? Requirements,
    string? Benefits,
    Guid? CategoryId,
    Guid? LevelId,
    Guid? EmploymentTypeId,
    Guid? LocationId,
    int? SalaryMin,
    int? SalaryMax,
    string SalaryCurrency = "VND",
    int? ExperienceYearsMin = null,
    int? ExperienceYearsMax = null,
    DateTime? Deadline = null,
    int PositionsCount = 1,
    List<JobSkillDto>? Skills = null);

public sealed record UpdateJobRequest(
    string Title,
    string Description,
    string? Requirements,
    string? Benefits,
    Guid? CategoryId,
    Guid? LevelId,
    Guid? EmploymentTypeId,
    Guid? LocationId,
    int? SalaryMin,
    int? SalaryMax,
    string SalaryCurrency = "VND",
    int? ExperienceYearsMin = null,
    int? ExperienceYearsMax = null,
    DateTime? Deadline = null,
    int PositionsCount = 1,
    List<JobSkillDto>? Skills = null);

public sealed record JobCompanyResponse(
    Guid Id,
    string Name,
    string? LogoUrl,
    string? Address,
    string? Industry,
    string? Scale,
    string VerifiedStatus);

public sealed record JobDetailResponse(
    Guid Id,
    Guid CompanyId,
    JobCompanyResponse Company,
    Guid PostedById,
    string Title,
    string Description,
    string? Requirements,
    string? Benefits,
    Guid? CategoryId,
    string? CategoryName,
    Guid? LevelId,
    string? LevelName,
    Guid? EmploymentTypeId,
    string? EmploymentTypeName,
    Guid? LocationId,
    string? LocationName,
    int? SalaryMin,
    int? SalaryMax,
    string SalaryCurrency,
    int? ExperienceYearsMin,
    int? ExperienceYearsMax,
    DateTime? Deadline,
    int PositionsCount,
    string ApprovalStatus,
    bool IsActive,
    bool IsExpired,
    int ViewCount,
    DateTime CreatedAt,
    DateTime? UpdatedAt,
    IReadOnlyList<JobSkillResponse> Skills);

public sealed record JobListResponse(
    Guid Id,
    Guid CompanyId,
    string CompanyName,
    string? CompanyLogoUrl,
    string Title,
    string? CategoryName,
    string? LevelName,
    string? EmploymentTypeName,
    string? LocationName,
    int? SalaryMin,
    int? SalaryMax,
    string SalaryCurrency,
    int? ExperienceYearsMin,
    int? ExperienceYearsMax,
    DateTime? Deadline,
    int PositionsCount,
    string ApprovalStatus,
    bool IsActive,
    bool IsExpired,
    int ViewCount,
    DateTime CreatedAt,
    IReadOnlyList<string> RequiredSkills);

public sealed record JobFilterRequest(
    string? Keyword = null,
    Guid? CategoryId = null,
    Guid? LevelId = null,
    Guid? EmploymentTypeId = null,
    Guid? LocationId = null,
    int? SalaryMin = null,
    int? SalaryMax = null,
    List<Guid>? SkillIds = null,
    string? SortBy = "newest",
    int PageIndex = 1,
    int PageSize = 10);

public sealed record EmployerJobFilterRequest(
    string? Keyword = null,
    string? ApprovalStatus = null,
    bool? IsActive = null,
    int PageIndex = 1,
    int PageSize = 10);

public sealed record AdminJobFilterRequest(
    string? Keyword = null,
    string? ApprovalStatus = null,
    int PageIndex = 1,
    int PageSize = 10);

public sealed record ApproveJobRequest(
    bool IsApproved,
    string? RejectionReason = null,
    string? Note = null);

public sealed record CreateJobReportRequest(
    string Reason,
    string? Details = null);
