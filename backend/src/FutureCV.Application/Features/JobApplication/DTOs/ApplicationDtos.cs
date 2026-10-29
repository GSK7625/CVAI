using FutureCV.Application.Features.AiMatching.DTOs;

namespace FutureCV.Application.Features.JobApplication.DTOs;

// -----------------------------------------------------------------------------
// Candidate DTOs (P3-UC04, P3-UC05, P3-UC06, P3-UC07, P4-UC03)
// -----------------------------------------------------------------------------

public sealed record ApplyJobRequest(
    Guid CvId,
    string? CoverLetter = null);

public sealed record ApplyJobResponse(
    Guid ApplicationId,
    Guid JobId,
    string JobTitle,
    string Status,
    int? MatchScore,
    DateTime AppliedAt);

public sealed record ApplicationStatusTimelineItem(
    string? FromStatus,
    string ToStatus,
    string? Reason,
    DateTime ChangedAt);

public sealed record CandidateApplicationListResponse(
    Guid Id,
    Guid JobId,
    string JobTitle,
    Guid CompanyId,
    string CompanyName,
    string? CompanyLogoUrl,
    string? LocationName,
    int? SalaryMin,
    int? SalaryMax,
    string SalaryCurrency,
    string Status,
    int? MatchScore,
    DateTime AppliedAt,
    DateTime? UpdatedAt);

public sealed record CandidateApplicationDetailResponse(
    Guid Id,
    Guid JobId,
    string JobTitle,
    Guid CompanyId,
    string CompanyName,
    string? CompanyLogoUrl,
    Guid CvId,
    string? CvTitle,
    string? CvFileUrl,
    string? CoverLetter,
    string Status,
    int? MatchScore,
    string? MatchExplanation,
    IReadOnlyList<string> MatchedSkills,
    IReadOnlyList<string> MissingSkills,
    DateTime AppliedAt,
    IReadOnlyList<ApplicationStatusTimelineItem> Timeline);

public sealed record CandidateApplicationFilterRequest(
    string? Status = null,
    int PageIndex = 1,
    int PageSize = 10);

public sealed record WithdrawApplicationRequest(
    string? Reason = null);

public sealed record SavedJobResponse(
    Guid JobId,
    string Title,
    Guid CompanyId,
    string CompanyName,
    string? CompanyLogoUrl,
    string? LocationName,
    int? SalaryMin,
    int? SalaryMax,
    string SalaryCurrency,
    DateTime? Deadline,
    bool IsActive,
    bool IsExpired,
    DateTime SavedAt);

public sealed record SavedJobFilterRequest(
    int PageIndex = 1,
    int PageSize = 10);

public sealed record JobSuggestionResponse(
    Guid Id,
    Guid CompanyId,
    string CompanyName,
    string? CompanyLogoUrl,
    string Title,
    string? CategoryName,
    string? LevelName,
    string? LocationName,
    int? SalaryMin,
    int? SalaryMax,
    string SalaryCurrency,
    DateTime? Deadline,
    int MatchScore,
    string MatchExplanation,
    IReadOnlyList<string> MatchedSkills,
    IReadOnlyList<string> MissingSkills);

public sealed record JobSuggestionFilterRequest(
    int PageIndex = 1,
    int PageSize = 10);

// -----------------------------------------------------------------------------
// Recruiter DTOs (P4-UC04, P4-UC05, P4-UC06, P4-UC07)
// -----------------------------------------------------------------------------

public sealed record RecruiterApplicationFilterRequest(
    string? Status = null,
    int? MinRating = null,
    string? Keyword = null,
    int PageIndex = 1,
    int PageSize = 10);

public sealed record RecruiterApplicationListResponse(
    Guid Id,
    Guid CandidateId,
    string CandidateFullName,
    string? CandidateAvatarUrl,
    string? CandidatePhone,
    string? CandidateEmail,
    Guid CvId,
    string? CvTitle,
    string? CvFileUrl,
    string Status,
    int? Rating,
    string? EvaluationLabel,
    int? MatchScore,
    DateTime AppliedAt);

public sealed record RecruiterApplicationDetailResponse(
    Guid Id,
    Guid JobId,
    string JobTitle,
    Guid CandidateId,
    string CandidateFullName,
    string? CandidateAvatarUrl,
    string? CandidatePhone,
    string? CandidateEmail,
    string? CandidateAddress,
    Guid CvId,
    string? CvTitle,
    string? CvFileUrl,
    string? CoverLetter,
    string Status,
    int? Rating,
    string? EvaluationLabel,
    string? PrivateNotes,
    int? MatchScore,
    string? MatchExplanation,
    IReadOnlyList<string> MatchedSkills,
    IReadOnlyList<string> MissingSkills,
    DateTime AppliedAt,
    IReadOnlyList<ApplicationStatusTimelineItem> Timeline);

public sealed record EvaluateApplicationRequest(
    int Rating,
    string? EvaluationLabel = null,
    string? PrivateNotes = null);

public sealed record UpdateApplicationStatusRequest(
    string NewStatus,
    string? Reason = null);

public sealed record PipelineCandidateCardResponse(
    Guid ApplicationId,
    Guid CandidateId,
    string CandidateFullName,
    string? CandidateAvatarUrl,
    int? Rating,
    string? EvaluationLabel,
    int? MatchScore,
    DateTime AppliedAt,
    string? CvFileUrl,
    int DaysInStage = 0,
    string StageAlert = "Normal",
    DateTime? LastStatusChangedAt = null);

public sealed record PipelineStageResponse(
    string Stage,
    int Count,
    IReadOnlyList<PipelineCandidateCardResponse> Candidates);

public sealed record RecruitmentPipelineResponse(
    Guid JobId,
    string JobTitle,
    int TotalCandidates,
    IReadOnlyList<PipelineStageResponse> Stages);

// -----------------------------------------------------------------------------
// Recruitment Pipeline Analytics & Export DTOs (P4-UC07)
// -----------------------------------------------------------------------------

public sealed record StageConversionDto(
    string FromStage,
    string ToStage,
    int FromCount,
    int ToCount,
    double ConversionRate);

public sealed record StageDurationDto(
    string Stage,
    double AverageDays,
    int CandidateCount,
    int OverdueCount);

public sealed record PipelineAnalyticsResponse(
    Guid JobId,
    string JobTitle,
    int TotalApplications,
    int ActiveApplications,
    int HiredCount,
    int RejectedCount,
    int WithdrawnCount,
    double? AverageTimeToHireDays,
    double OverallConversionRate,
    IReadOnlyList<StageConversionDto> StageConversionRates,
    IReadOnlyList<StageDurationDto> StageAverageDurations,
    string? BottleneckStage,
    int OverdueCandidatesCount);

// -----------------------------------------------------------------------------
// Preview Match & Skill Gap DTOs (P4-UC01, P4-UC02)
// -----------------------------------------------------------------------------

public sealed record PreviewJobMatchRequest(
    Guid? CvId = null);

public sealed record JobMatchPreviewResponse(
    Guid JobId,
    string JobTitle,
    Guid CvId,
    string CvTitle,
    int MatchScore,
    IReadOnlyList<string> MatchedSkills,
    IReadOnlyList<string> MissingSkills,
    string Explanation,
    bool LocationMatched,
    bool SalaryMatched,
    string? ExperienceComparison = null,
    string? EducationComparison = null,
    string? ProjectDomainRelevance = null,
    bool IsAiPreview = false,
    string? MatchSource = null,
    AiMatchExplanationDto? ExplanationDetails = null);

