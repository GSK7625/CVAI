using FutureCV.Domain.Common;

namespace FutureCV.Domain.Entities;

public class CandidateCv : BaseEntity
{
    public Guid CandidateId { get; set; }
    public string? Title { get; set; }
    public string? FileUrl { get; set; }
    public string? PublicId { get; set; }
    public string? FileType { get; set; } = "PDF";
    public long? FileSizeBytes { get; set; }
    public string Source { get; set; } = "Upload";
    public string ParseStatus { get; set; } = "Pending";
    public DateTime? ParsedAt { get; set; }
    public bool IsPrimary { get; set; }
    public bool IsDeleted { get; set; }

    public Candidate Candidate { get; set; } = null!;
    public CvParser? CvParser { get; set; }
    public CvEvaluation? Evaluation { get; set; }
}
