using FutureCV.Domain.Common;
using FutureCV.Domain.Enums;

namespace FutureCV.Domain.Entities;

public class JobApplication : BaseEntity
{
    public Guid CandidateId { get; set; }
    public Guid JobId { get; set; }
    public Guid CvId { get; set; }
    public string? CoverLetter { get; set; }
    public ApplicationStatus Status { get; set; } = ApplicationStatus.Applied;
    public DateTime AppliedAt { get; set; } = DateTime.UtcNow;

    // Recruiter internal evaluation (P4-UC05)
    public int? Rating { get; set; }
    public string? EvaluationLabel { get; set; }
    public string? PrivateNotes { get; set; }

    // Rule-based matching score & breakdown (P3-UC05, P4-UC03)
    public int? MatchScore { get; set; }
    public string? MatchExplanation { get; set; }
    public string? MatchedSkillsJson { get; set; }
    public string? MissingSkillsJson { get; set; }

    public bool IsDeleted { get; set; } = false;

    // Navigation properties
    public Candidate Candidate { get; set; } = null!;
    public Job Job { get; set; } = null!;
    public CandidateCv Cv { get; set; } = null!;
    public ICollection<ApplicationStatusHistory> StatusHistories { get; set; } = [];
}
