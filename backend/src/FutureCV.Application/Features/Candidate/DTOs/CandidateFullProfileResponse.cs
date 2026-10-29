namespace FutureCV.Application.Features.Candidate.DTOs;

/// <summary>
/// Full candidate profile including nested collections and computed completion score.
/// Used for GET /profile/full endpoint.
/// </summary>
public sealed class CandidateFullProfileResponse
{
    public Guid Id { get; init; }
    public Guid UserId { get; init; }
    public string Email { get; init; } = string.Empty;
    public string FullName { get; init; } = string.Empty;
    public string? Phone { get; init; }
    public string? Address { get; init; }
    public string? AvatarUrl { get; init; }
    public DateTime? DateOfBirth { get; init; }
    public string? Gender { get; init; }
    public string? Summary { get; init; }
    public string? DesiredPosition { get; init; }
    public int? DesiredSalaryMin { get; init; }
    public int? DesiredSalaryMax { get; init; }
    public DateTimeOffset? ProfileUpdatedAt { get; init; }
    public DateTime CreatedAt { get; init; }

    public IReadOnlyList<EducationResponse> Educations { get; init; } = [];
    public IReadOnlyList<ExperienceResponse> Experiences { get; init; } = [];
    public IReadOnlyList<CandidateSkillResponse> Skills { get; init; } = [];
    public IReadOnlyList<CertificateResponse> Certificates { get; init; } = [];
    public IReadOnlyList<ProjectResponse> Projects { get; init; } = [];
    public IReadOnlyList<CvResponse> CVs { get; init; } = [];

    // Computed — calculated in service, not persisted in DB
    public int ProfileCompletionPercent => CalculateCompletion();

    // Eligible for job recommendation suggestions when completion >= 70% (UC-004, FR-15)
    public bool IsEligibleForRecommendation => ProfileCompletionPercent >= 70;

    // Completion algorithm (approved 2026-08-30):
    // Basic info (30%): FullName=8, Phone=5, DOB=5, Gender=4, Avatar=8
    // Sections (70%): Education=20, Experience=20, Skills=15, Job desires=15
    private int CalculateCompletion()
    {
        int score = 0;

        // Basic info — 30%
        if (!string.IsNullOrWhiteSpace(FullName))  score += 8;
        if (!string.IsNullOrWhiteSpace(Phone))     score += 5;
        if (DateOfBirth.HasValue)                  score += 5;
        if (!string.IsNullOrWhiteSpace(Gender))    score += 4;
        if (!string.IsNullOrWhiteSpace(AvatarUrl)) score += 8;

        // Profile sections — 70%
        if (Educations.Count > 0)  score += 20;
        if (Experiences.Count > 0) score += 20;
        if (Skills.Count > 0)      score += 15;

        // Job desires: both DesiredPosition and at least one salary value filled
        if (!string.IsNullOrWhiteSpace(DesiredPosition)
            && (DesiredSalaryMin.HasValue || DesiredSalaryMax.HasValue))
            score += 15;

        return Math.Min(score, 100);
    }
}
