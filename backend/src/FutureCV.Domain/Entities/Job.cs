using FutureCV.Domain.Common;
using FutureCV.Domain.Enums;

namespace FutureCV.Domain.Entities;

public class Job : BaseEntity
{
    public Guid CompanyId { get; set; }
    public Guid PostedById { get; set; }
    public string Title { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string? Requirements { get; set; }
    public string? Benefits { get; set; }
    public Guid? CategoryId { get; set; }
    public Guid? LevelId { get; set; }
    public Guid? EmploymentTypeId { get; set; }
    public Guid? LocationId { get; set; }
    public int? SalaryMin { get; set; }
    public int? SalaryMax { get; set; }
    public string SalaryCurrency { get; set; } = "VND";
    public int? ExperienceYearsMin { get; set; }
    public int? ExperienceYearsMax { get; set; }
    public DateTime? Deadline { get; set; }
    public int PositionsCount { get; set; } = 1;
    public JobApprovalStatus ApprovalStatus { get; set; } = JobApprovalStatus.Draft;
    public Guid? ApprovedByAdminId { get; set; }
    public DateTimeOffset? ApprovedAt { get; set; }
    public string? RejectionReason { get; set; }
    public bool IsActive { get; set; } = true;
    public bool IsExpired { get; set; } = false;
    public bool IsBanned { get; set; } = false;
    public DateTimeOffset? BannedAt { get; set; }
    public Guid? BannedByAdminId { get; set; }
    public string? BannedReason { get; set; }
    public int ViewCount { get; set; } = 0;
    public bool IsDeleted { get; set; } = false;

    // Navigation properties
    public Company Company { get; set; } = null!;
    public JobCategory? Category { get; set; }
    public JobLevel? Level { get; set; }
    public EmploymentType? EmploymentType { get; set; }
    public Location? Location { get; set; }
    public ICollection<JobSkill> JobSkills { get; set; } = [];
    public ICollection<SavedJob> SavedJobs { get; set; } = [];
    public ICollection<JobApplication> Applications { get; set; } = [];
    public ICollection<JobReport> Reports { get; set; } = [];
}
