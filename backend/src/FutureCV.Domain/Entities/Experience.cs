using FutureCV.Domain.Common;

namespace FutureCV.Domain.Entities;

public class Experience : BaseEntity
{
    public Guid CandidateId { get; set; }
    public string CompanyName { get; set; } = string.Empty;
    public string? Position { get; set; }
    public DateOnly StartDate { get; set; }
    public DateOnly? EndDate { get; set; }
    public bool IsCurrent { get; set; }
    public string? Description { get; set; }
    public bool IsDeleted { get; set; }

    public Candidate Candidate { get; set; } = null!;
}
