using FutureCV.Domain.Common;

namespace FutureCV.Domain.Entities;

public class Certificate : BaseEntity
{
    public Guid CandidateId { get; set; }
    public Guid? CvId { get; set; }
    public string Name { get; set; } = string.Empty;
    public string? Organization { get; set; }
    public DateTime? IssueDate { get; set; }
    public DateTime? ExpirationDate { get; set; }
    public string? CredentialUrl { get; set; }
    public string? Description { get; set; }
    public bool IsDeleted { get; set; }

    public Candidate Candidate { get; set; } = null!;
    public CandidateCv? Cv { get; set; }
}
