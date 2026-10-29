using FutureCV.Domain.Common;

namespace FutureCV.Domain.Entities;

public class CvParser : BaseEntity
{
    public Guid CvId { get; set; }
    public string? RawText { get; set; }
    public string? ParsedDataJson { get; set; }
    public string ModelVersion { get; set; } = "1.0";
    public DateTime ParsedAt { get; set; } = DateTime.UtcNow;
    public string? ErrorMessage { get; set; }
    public bool IsVerifiedByUser { get; set; }
    public DateTime? VerifiedAt { get; set; }

    public CandidateCv Cv { get; set; } = null!;
}
