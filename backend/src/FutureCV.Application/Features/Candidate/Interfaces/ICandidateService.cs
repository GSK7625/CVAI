using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.Candidate.DTOs;

namespace FutureCV.Application.Features.Candidate.Interfaces;

public interface ICandidateService
{
    Task<ServiceResult<CandidateProfileResponse>> GetProfileAsync(
        Guid userId, CancellationToken cancellationToken = default);

    Task<ServiceResult<CandidateFullProfileResponse>> GetFullProfileAsync(
        Guid userId, CancellationToken cancellationToken = default);

    Task<ServiceResult<CandidateProfileResponse>> UpdatePersonalInfoAsync(
        Guid userId, UpdateCandidateInfoRequest request, CancellationToken cancellationToken = default);

    Task<ServiceResult<string>> UpdateAvatarAsync(
        Guid userId, FileUploadRequest file, CancellationToken cancellationToken = default);

    // --- Education ---
    Task<ServiceResult<EducationResponse>> AddEducationAsync(
        Guid userId, EducationDto dto, CancellationToken cancellationToken = default);

    Task<ServiceResult<EducationResponse>> UpdateEducationAsync(
        Guid userId, Guid educationId, EducationDto dto, CancellationToken cancellationToken = default);

    Task<ServiceResult<bool>> DeleteEducationAsync(
        Guid userId, Guid educationId, CancellationToken cancellationToken = default);

    // --- Experience ---
    Task<ServiceResult<ExperienceResponse>> AddExperienceAsync(
        Guid userId, ExperienceDto dto, CancellationToken cancellationToken = default);

    Task<ServiceResult<ExperienceResponse>> UpdateExperienceAsync(
        Guid userId, Guid experienceId, ExperienceDto dto, CancellationToken cancellationToken = default);

    Task<ServiceResult<bool>> DeleteExperienceAsync(
        Guid userId, Guid experienceId, CancellationToken cancellationToken = default);

    // --- Skills ---
    Task<ServiceResult<CandidateSkillResponse>> AddSkillAsync(
        Guid userId, CandidateSkillDto dto, CancellationToken cancellationToken = default);

    Task<ServiceResult<bool>> RemoveSkillAsync(
        Guid userId, Guid skillId, CancellationToken cancellationToken = default);

    // --- CV PDF ---
    Task<ServiceResult<CvResponse>> UploadCvAsync(
        Guid userId, FileUploadRequest file, string? title, CancellationToken cancellationToken = default);

    Task<ServiceResult<IReadOnlyList<CvResponse>>> GetCvsAsync(
        Guid userId, CancellationToken cancellationToken = default);

    Task<ServiceResult<CvResponse>> GetCvByIdAsync(
        Guid userId, Guid cvId, CancellationToken cancellationToken = default);

    Task<ServiceResult<CvResponse>> UpdateCvTitleAsync(
        Guid userId, Guid cvId, string title, CancellationToken cancellationToken = default);

    Task<ServiceResult<bool>> DeleteCvAsync(
        Guid userId, Guid cvId, CancellationToken cancellationToken = default);

    Task<ServiceResult<CvResponse>> SelectPrimaryCvAsync(
        Guid userId, Guid cvId, CancellationToken cancellationToken = default);

    // --- Certificates ---
    Task<ServiceResult<CertificateResponse>> AddCertificateAsync(
        Guid userId, CertificateDto dto, CancellationToken cancellationToken = default);

    Task<ServiceResult<CertificateResponse>> UpdateCertificateAsync(
        Guid userId, Guid certificateId, CertificateDto dto, CancellationToken cancellationToken = default);

    Task<ServiceResult<bool>> DeleteCertificateAsync(
        Guid userId, Guid certificateId, CancellationToken cancellationToken = default);

    // --- Projects ---
    Task<ServiceResult<ProjectResponse>> AddProjectAsync(
        Guid userId, ProjectDto dto, CancellationToken cancellationToken = default);

    Task<ServiceResult<ProjectResponse>> UpdateProjectAsync(
        Guid userId, Guid projectId, ProjectDto dto, CancellationToken cancellationToken = default);

    Task<ServiceResult<bool>> DeleteProjectAsync(
        Guid userId, Guid projectId, CancellationToken cancellationToken = default);

    // --- Structured CV Data & AI Analysis (P2-UC04, P2-UC05, P2-UC06) ---
    Task<ServiceResult<CvStructuredDataResponse>> GetStructuredCvDataAsync(
        Guid userId, Guid cvId, CancellationToken cancellationToken = default);

    Task<ServiceResult<CvStructuredDataResponse>> UpdateStructuredCvDataAsync(
        Guid userId, Guid cvId, UpdateStructuredCvDataRequest request, CancellationToken cancellationToken = default);

    Task<ServiceResult<CvStructuredDataResponse>> RevertStructuredCvDataAsync(
        Guid userId, Guid cvId, CancellationToken cancellationToken = default);

    Task<ServiceResult<CvAnalysisResponse>> GetCvAnalysisAsync(
        Guid userId, Guid cvId, CancellationToken cancellationToken = default);

    Task<ServiceResult<CvAnalysisResponse>> AnalyzeCvAsync(
        Guid userId, Guid cvId, CancellationToken cancellationToken = default);

    Task<ServiceResult<bool>> ProcessAiCvCallbackAsync(
        Guid cvId, AiCvCallbackRequest request, CancellationToken cancellationToken = default);
}

