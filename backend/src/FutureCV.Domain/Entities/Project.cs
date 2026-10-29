using FutureCV.Domain.Common;

namespace FutureCV.Domain.Entities;

public class Project : BaseEntity
{
    public Guid CandidateId { get; set; }
    public Guid? CvId { get; set; }
    public string Name { get; set; } = string.Empty;
    public string? Role { get; set; }
    public DateTime? StartDate { get; set; }
    public DateTime? EndDate { get; set; }
    public bool IsCurrent { get; set; }
    public string? ProjectUrl { get; set; }
    public string? Description { get; set; }
    public bool IsDeleted { get; set; }

    public Candidate Candidate { get; set; } = null!;
    public CandidateCv? Cv { get; set; }
}
