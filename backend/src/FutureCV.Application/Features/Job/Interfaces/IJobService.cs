using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.Job.DTOs;

namespace FutureCV.Application.Features.Job.Interfaces;

public interface IJobService
{
    // Employer endpoints
    Task<ServiceResult<JobDetailResponse>> CreateJobAsync(
        Guid userId, CreateJobRequest request, CancellationToken cancellationToken = default);

    Task<ServiceResult<JobDetailResponse>> UpdateJobAsync(
        Guid userId, Guid jobId, UpdateJobRequest request, CancellationToken cancellationToken = default);

    Task<ServiceResult<bool>> ToggleJobStatusAsync(
        Guid userId, Guid jobId, CancellationToken cancellationToken = default);

    Task<ServiceResult<bool>> DeleteJobAsync(
        Guid userId, Guid jobId, CancellationToken cancellationToken = default);

    Task<ServiceResult<PagedResult<JobListResponse>>> GetEmployerJobsAsync(
        Guid userId, EmployerJobFilterRequest filter, CancellationToken cancellationToken = default);

    Task<ServiceResult<JobDetailResponse>> GetEmployerJobByIdAsync(
        Guid userId, Guid jobId, CancellationToken cancellationToken = default);

    // Public / Candidate endpoints
    Task<ServiceResult<PagedResult<JobListResponse>>> SearchJobsAsync(
        JobFilterRequest filter, CancellationToken cancellationToken = default);

    Task<ServiceResult<JobDetailResponse>> GetJobDetailAsync(
        Guid jobId, bool incrementView = true, CancellationToken cancellationToken = default);

    Task<ServiceResult<bool>> ReportJobAsync(
        Guid userId, Guid jobId, CreateJobReportRequest request, CancellationToken cancellationToken = default);

    // Master data lookups
    Task<ServiceResult<IReadOnlyList<JobCategoryResponse>>> GetCategoriesAsync(
        CancellationToken cancellationToken = default);

    Task<ServiceResult<IReadOnlyList<JobLevelResponse>>> GetLevelsAsync(
        CancellationToken cancellationToken = default);

    Task<ServiceResult<IReadOnlyList<EmploymentTypeResponse>>> GetEmploymentTypesAsync(
        CancellationToken cancellationToken = default);

    Task<ServiceResult<IReadOnlyList<LocationResponse>>> GetLocationsAsync(
        CancellationToken cancellationToken = default);

    // Admin endpoints
    Task<ServiceResult<PagedResult<JobListResponse>>> GetAdminJobsAsync(
        AdminJobFilterRequest filter, CancellationToken cancellationToken = default);

    Task<ServiceResult<bool>> ModerateJobAsync(
        Guid adminUserId, Guid jobId, ApproveJobRequest request, CancellationToken cancellationToken = default);
}
