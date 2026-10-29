using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.JobApplication.DTOs;

namespace FutureCV.Application.Features.JobApplication.Interfaces;

public interface IApplicationService
{
    // -------------------------------------------------------------------------
    // Candidate Operations
    // -------------------------------------------------------------------------

    Task<ServiceResult<ApplyJobResponse>> ApplyJobAsync(
        Guid userId, Guid jobId, ApplyJobRequest request, CancellationToken cancellationToken = default);

    Task<ServiceResult<PagedResult<CandidateApplicationListResponse>>> GetCandidateApplicationsAsync(
        Guid userId, CandidateApplicationFilterRequest filter, CancellationToken cancellationToken = default);

    Task<ServiceResult<CandidateApplicationDetailResponse>> GetCandidateApplicationDetailAsync(
        Guid userId, Guid applicationId, CancellationToken cancellationToken = default);

    Task<ServiceResult<bool>> WithdrawApplicationAsync(
        Guid userId, Guid applicationId, WithdrawApplicationRequest request, CancellationToken cancellationToken = default);

    Task<ServiceResult<bool>> ToggleSaveJobAsync(
        Guid userId, Guid jobId, CancellationToken cancellationToken = default);

    Task<ServiceResult<PagedResult<SavedJobResponse>>> GetSavedJobsAsync(
        Guid userId, SavedJobFilterRequest filter, CancellationToken cancellationToken = default);

    Task<ServiceResult<PagedResult<JobSuggestionResponse>>> GetJobSuggestionsAsync(
        Guid userId, JobSuggestionFilterRequest filter, CancellationToken cancellationToken = default);

    Task<ServiceResult<JobMatchPreviewResponse>> PreviewJobMatchAsync(
        Guid userId, Guid jobId, PreviewJobMatchRequest request, CancellationToken cancellationToken = default);

    // -------------------------------------------------------------------------
    // Recruiter Operations
    // -------------------------------------------------------------------------

    Task<ServiceResult<PagedResult<RecruiterApplicationListResponse>>> GetJobApplicationsAsync(
        Guid userId, Guid jobId, RecruiterApplicationFilterRequest filter, CancellationToken cancellationToken = default);

    Task<ServiceResult<RecruiterApplicationDetailResponse>> GetApplicationDetailAsync(
        Guid userId, Guid applicationId, CancellationToken cancellationToken = default);

    Task<ServiceResult<bool>> EvaluateApplicationAsync(
        Guid userId, Guid applicationId, EvaluateApplicationRequest request, CancellationToken cancellationToken = default);

    Task<ServiceResult<bool>> UpdateApplicationStatusAsync(
        Guid userId, Guid applicationId, UpdateApplicationStatusRequest request, CancellationToken cancellationToken = default);

    Task<ServiceResult<RecruitmentPipelineResponse>> GetRecruitmentPipelineAsync(
        Guid userId, Guid jobId, CancellationToken cancellationToken = default);

    Task<ServiceResult<PipelineAnalyticsResponse>> GetPipelineAnalyticsAsync(
        Guid userId, Guid jobId, CancellationToken cancellationToken = default);

    Task<ServiceResult<byte[]>> ExportPipelineCsvAsync(
        Guid userId, Guid jobId, CancellationToken cancellationToken = default);
}
