using FutureCV.Domain.Common;

namespace FutureCV.Domain.Entities;

public class CvEvaluation : BaseEntity
{
    public Guid CvId { get; set; }
    public int? CvScore { get; set; }
    public string? StrengthsJson { get; set; }
    public string? WeaknessesJson { get; set; }
    public string? ImprovementsJson { get; set; }
    public string? MissingSkillsJson { get; set; }
    public string ModelVersion { get; set; } = "1.0";
    public DateTime GeneratedAt { get; set; } = DateTime.UtcNow;

    // Navigation property
    public CandidateCv Cv { get; set; } = null!;
}
