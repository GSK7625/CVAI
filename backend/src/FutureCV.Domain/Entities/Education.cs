using FutureCV.Domain.Common;

namespace FutureCV.Domain.Entities;

public class Education : BaseEntity
{
    public Guid CandidateId { get; set; }
    public string School { get; set; } = string.Empty;
    public string? Degree { get; set; }
    public string? Major { get; set; }
    public int? StartYear { get; set; }
    public int? EndYear { get; set; }
    public string? Description { get; set; }
    public bool IsDeleted { get; set; }

    public Candidate Candidate { get; set; } = null!;
}
