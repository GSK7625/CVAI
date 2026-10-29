using System.Text;
using System.Text.Json;
using FutureCV.Application.Common.Interfaces;
using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.JobApplication.DTOs;
using FutureCV.Application.Features.JobApplication.Interfaces;
using Microsoft.EntityFrameworkCore;

namespace FutureCV.Application.Features.JobApplication.Services;

using FutureCV.Domain.Entities;
using FutureCV.Domain.Enums;

using FutureCV.Application.Features.AiMatching.Configurations;
using FutureCV.Application.Features.AiMatching.Mappers;
using FutureCV.Application.Features.Candidate.DTOs;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

public class ApplicationService : IApplicationService
{
    private readonly IApplicationDbContext _context;
    private readonly IIdentityService _identityService;
    private readonly IAiMatchingClient _aiMatchingClient;
    private readonly AiMatchingFeatureOptions _aiOptions;
    private readonly ILogger<ApplicationService> _logger;

    public ApplicationService(
        IApplicationDbContext context,
        IIdentityService identityService,
        IAiMatchingClient aiMatchingClient,
        IOptions<AiMatchingFeatureOptions>? aiOptions = null,
        ILogger<ApplicationService>? logger = null)
    {
        _context = context;
        _identityService = identityService;
        _aiMatchingClient = aiMatchingClient;
        _aiOptions = aiOptions?.Value ?? new AiMatchingFeatureOptions();
        _logger = logger ?? Microsoft.Extensions.Logging.Abstractions.NullLogger<ApplicationService>.Instance;
    }

    // -------------------------------------------------------------------------
    // Candidate Operations
    // -------------------------------------------------------------------------

    public async Task<ServiceResult<ApplyJobResponse>> ApplyJobAsync(
        Guid userId, Guid jobId, ApplyJobRequest request, CancellationToken cancellationToken = default)
    {
        // 1. Verify candidate profile
        var candidate = await _context.Candidates
            .Include(c => c.Skills)
            .FirstOrDefaultAsync(c => c.UserId == userId, cancellationToken);

        if (candidate is null)
            return ServiceResult.NotFound<ApplyJobResponse>("Candidate profile not found.");

        // 2. Verify selected CV belongs to candidate and exists
        var cv = await _context.CandidateCvs
            .FirstOrDefaultAsync(c => c.Id == request.CvId && c.CandidateId == candidate.Id && !c.IsDeleted, cancellationToken);

        if (cv is null)
            return ServiceResult.NotFound<ApplyJobResponse>("Selected CV not found or does not belong to candidate.");

        // 3. Verify job validity
        var job = await _context.Jobs
            .Include(j => j.JobSkills)
                .ThenInclude(js => js.Skill)
            .FirstOrDefaultAsync(j => j.Id == jobId && !j.IsDeleted, cancellationToken);

        if (job is null)
            return ServiceResult.NotFound<ApplyJobResponse>("Job not found.");

        if (!job.IsActive || job.ApprovalStatus != JobApprovalStatus.Approved || (job.Deadline.HasValue && job.Deadline.Value < DateTime.UtcNow))
            return ServiceResult.Failure<ApplyJobResponse>("Job is closed, expired, or not approved for applications.");

        // Check self-application (dual-role user cannot apply to own job or own company)
        if (job.PostedById == userId)
            return ServiceResult.Failure<ApplyJobResponse>("You cannot apply to your own job posting.");

        var employerProfile = await _context.Employers
            .AsNoTracking()
            .FirstOrDefaultAsync(e => e.UserId == userId, cancellationToken);
        if (employerProfile is not null && employerProfile.CompanyId == job.CompanyId)
            return ServiceResult.Failure<ApplyJobResponse>("You cannot apply to a job posted by your own company.");

        // 4. Check for duplicate active application (P3-UC05 E2)
        var alreadyApplied = await _context.Applications
            .AnyAsync(a => a.CandidateId == candidate.Id && a.JobId == jobId && !a.IsDeleted && a.Status != ApplicationStatus.Withdrawn, cancellationToken);

        if (alreadyApplied)
            return ServiceResult.Conflict<ApplyJobResponse>("You have already applied for this position.");

        // 5. Calculate Rule-based Match Score (Pure LINQ - No AI dependency)
        var (matchScore, explanation, matchedSkills, missingSkills) = CalculateMatchScore(candidate, job);

        // 6. Create JobApplication record
        var application = new JobApplication
        {
            CandidateId = candidate.Id,
            JobId = jobId,
            CvId = request.CvId,
            CoverLetter = request.CoverLetter,
            Status = ApplicationStatus.Applied,
            AppliedAt = DateTime.UtcNow,
            MatchScore = matchScore,
            MatchExplanation = explanation,
            MatchedSkillsJson = JsonSerializer.Serialize(matchedSkills),
            MissingSkillsJson = JsonSerializer.Serialize(missingSkills),
            IsDeleted = false
        };

        // 7. Add initial status history record (P3-UC05 Step 7)
        application.StatusHistories.Add(new ApplicationStatusHistory
        {
            Application = application,
            FromStatus = null,
            ToStatus = ApplicationStatus.Applied.ToString(),
            ChangedById = userId,
            Reason = "Initial application submission",
            ChangedAt = DateTime.UtcNow
        });

        _context.Applications.Add(application);
        await _context.SaveChangesAsync(cancellationToken);

        return ServiceResult.Success(new ApplyJobResponse(
            application.Id,
            job.Id,
            job.Title,
            application.Status.ToString(),
            application.MatchScore,
            application.AppliedAt
        ));
    }

    public async Task<ServiceResult<PagedResult<CandidateApplicationListResponse>>> GetCandidateApplicationsAsync(
        Guid userId, CandidateApplicationFilterRequest filter, CancellationToken cancellationToken = default)
    {
        var candidate = await _context.Candidates
            .FirstOrDefaultAsync(c => c.UserId == userId, cancellationToken);

        if (candidate is null)
            return ServiceResult.NotFound<PagedResult<CandidateApplicationListResponse>>("Candidate profile not found.");

        var query = _context.Applications
            .AsNoTracking()
            .Where(a => a.CandidateId == candidate.Id && !a.IsDeleted);

        if (!string.IsNullOrWhiteSpace(filter.Status) &&
            Enum.TryParse<ApplicationStatus>(filter.Status, true, out var appStatusEnum))
        {
            query = query.Where(a => a.Status == appStatusEnum);
        }

        var totalCount = await query.CountAsync(cancellationToken);

        var pageIndex = filter.PageIndex < 1 ? 1 : filter.PageIndex;
        var pageSize = filter.PageSize is < 1 or > 100 ? 10 : filter.PageSize;

        var items = await query
            .OrderByDescending(a => a.AppliedAt)
            .Skip((pageIndex - 1) * pageSize)
            .Take(pageSize)
            .Select(a => new CandidateApplicationListResponse(
                a.Id,
                a.JobId,
                a.Job.Title,
                a.Job.CompanyId,
                a.Job.Company.Name,
                a.Job.Company.LogoUrl,
                a.Job.Location != null ? a.Job.Location.Name : null,
                a.Job.SalaryMin,
                a.Job.SalaryMax,
                a.Job.SalaryCurrency,
                a.Status.ToString(),
                a.MatchScore,
                a.AppliedAt,
                a.UpdatedAt
            ))
            .ToListAsync(cancellationToken);

        return ServiceResult.Success(new PagedResult<CandidateApplicationListResponse>(items, totalCount, pageIndex, pageSize));
    }

    public async Task<ServiceResult<CandidateApplicationDetailResponse>> GetCandidateApplicationDetailAsync(
        Guid userId, Guid applicationId, CancellationToken cancellationToken = default)
    {
        var candidate = await _context.Candidates
            .FirstOrDefaultAsync(c => c.UserId == userId, cancellationToken);

        if (candidate is null)
            return ServiceResult.NotFound<CandidateApplicationDetailResponse>("Candidate profile not found.");

        var application = await _context.Applications
            .AsNoTracking()
            .Include(a => a.Job)
                .ThenInclude(j => j.Company)
            .Include(a => a.Cv)
            .Include(a => a.StatusHistories)
            .FirstOrDefaultAsync(a => a.Id == applicationId && a.CandidateId == candidate.Id && !a.IsDeleted, cancellationToken);

        if (application is null)
            return ServiceResult.NotFound<CandidateApplicationDetailResponse>("Application not found.");

        var matchedSkills = DeserializeSkillList(application.MatchedSkillsJson);
        var missingSkills = DeserializeSkillList(application.MissingSkillsJson);

        var timeline = application.StatusHistories
            .OrderBy(h => h.ChangedAt)
            .Select(h => new ApplicationStatusTimelineItem(h.FromStatus, h.ToStatus, h.Reason, h.ChangedAt))
            .ToList();

        var response = new CandidateApplicationDetailResponse(
            application.Id,
            application.JobId,
            application.Job.Title,
            application.Job.CompanyId,
            application.Job.Company.Name,
            application.Job.Company.LogoUrl,
            application.CvId,
            application.Cv.Title,
            application.Cv.FileUrl,
            application.CoverLetter,
            application.Status.ToString(),
            application.MatchScore,
            application.MatchExplanation,
            matchedSkills,
            missingSkills,
            application.AppliedAt,
            timeline
        );

        return ServiceResult.Success(response);
    }

    public async Task<ServiceResult<bool>> WithdrawApplicationAsync(
        Guid userId, Guid applicationId, WithdrawApplicationRequest request, CancellationToken cancellationToken = default)
    {
        var candidate = await _context.Candidates
            .FirstOrDefaultAsync(c => c.UserId == userId, cancellationToken);

        if (candidate is null)
            return ServiceResult.NotFound<bool>("Candidate profile not found.");

        var application = await _context.Applications
            .Include(a => a.StatusHistories)
            .FirstOrDefaultAsync(a => a.Id == applicationId && a.CandidateId == candidate.Id && !a.IsDeleted, cancellationToken);

        if (application is null)
            return ServiceResult.NotFound<bool>("Application not found.");

        // P3-UC07 E1: Cannot withdraw if already finalized (Offer, Hired, Rejected) or past Interview
        if (application.Status is ApplicationStatus.Offer or ApplicationStatus.Hired or ApplicationStatus.Rejected or ApplicationStatus.Interview)
            return ServiceResult.Failure<bool>($"Cannot withdraw an application currently in '{application.Status}' status.");

        if (application.Status == ApplicationStatus.Withdrawn)
            return ServiceResult.Failure<bool>("Application has already been withdrawn.");

        var oldStatus = application.Status;
        application.Status = ApplicationStatus.Withdrawn;

        // Explicitly add via DbSet to ensure EF Core marks the entity as EntityState.Added.
        // Adding via navigation collection (application.StatusHistories.Add) causes EF Core
        // to infer EntityState.Modified because BaseEntity pre-assigns Id with Guid.NewGuid().
        _context.ApplicationStatusHistories.Add(new ApplicationStatusHistory
        {
            ApplicationId = application.Id,
            FromStatus = oldStatus.ToString(),
            ToStatus = ApplicationStatus.Withdrawn.ToString(),
            ChangedById = userId,
            Reason = string.IsNullOrWhiteSpace(request.Reason) ? "Candidate withdrew application" : request.Reason.Trim(),
            ChangedAt = DateTime.UtcNow
        });

        await _context.SaveChangesAsync(cancellationToken);
        return ServiceResult.Success(true);
    }

    public async Task<ServiceResult<bool>> ToggleSaveJobAsync(
        Guid userId, Guid jobId, CancellationToken cancellationToken = default)
    {
        var candidate = await _context.Candidates
            .FirstOrDefaultAsync(c => c.UserId == userId, cancellationToken);

        if (candidate is null)
            return ServiceResult.NotFound<bool>("Candidate profile not found.");

        var jobExists = await _context.Jobs.AnyAsync(j => j.Id == jobId && !j.IsDeleted, cancellationToken);
        if (!jobExists)
            return ServiceResult.NotFound<bool>("Job not found.");

        var existingSavedJob = await _context.SavedJobs
            .FirstOrDefaultAsync(sj => sj.CandidateId == candidate.Id && sj.JobId == jobId, cancellationToken);

        if (existingSavedJob != null)
        {
            // Unsave
            _context.SavedJobs.Remove(existingSavedJob);
            await _context.SaveChangesAsync(cancellationToken);
            return ServiceResult.Success(false); // false = not saved anymore
        }
        else
        {
            // Save
            _context.SavedJobs.Add(new SavedJob
            {
                CandidateId = candidate.Id,
                JobId = jobId,
                SavedAt = DateTime.UtcNow
            });
            await _context.SaveChangesAsync(cancellationToken);
            return ServiceResult.Success(true); // true = saved
        }
    }

    public async Task<ServiceResult<PagedResult<SavedJobResponse>>> GetSavedJobsAsync(
        Guid userId, SavedJobFilterRequest filter, CancellationToken cancellationToken = default)
    {
        var candidate = await _context.Candidates
            .FirstOrDefaultAsync(c => c.UserId == userId, cancellationToken);

        if (candidate is null)
            return ServiceResult.NotFound<PagedResult<SavedJobResponse>>("Candidate profile not found.");

        var query = _context.SavedJobs
            .AsNoTracking()
            .Where(sj => sj.CandidateId == candidate.Id && !sj.Job.IsDeleted);

        var totalCount = await query.CountAsync(cancellationToken);

        var pageIndex = filter.PageIndex < 1 ? 1 : filter.PageIndex;
        var pageSize = filter.PageSize is < 1 or > 100 ? 10 : filter.PageSize;

        var items = await query
            .OrderByDescending(sj => sj.SavedAt)
            .Skip((pageIndex - 1) * pageSize)
            .Take(pageSize)
            .Select(sj => new SavedJobResponse(
                sj.JobId,
                sj.Job.Title,
                sj.Job.CompanyId,
                sj.Job.Company.Name,
                sj.Job.Company.LogoUrl,
                sj.Job.Location != null ? sj.Job.Location.Name : null,
                sj.Job.SalaryMin,
                sj.Job.SalaryMax,
                sj.Job.SalaryCurrency,
                sj.Job.Deadline,
                sj.Job.IsActive,
                sj.Job.Deadline.HasValue && sj.Job.Deadline.Value < DateTime.UtcNow,
                sj.SavedAt
            ))
            .ToListAsync(cancellationToken);

        return ServiceResult.Success(new PagedResult<SavedJobResponse>(items, totalCount, pageIndex, pageSize));
    }

    public async Task<ServiceResult<PagedResult<JobSuggestionResponse>>> GetJobSuggestionsAsync(
        Guid userId, JobSuggestionFilterRequest filter, CancellationToken cancellationToken = default)
    {
        var candidate = await _context.Candidates
            .Include(c => c.Skills)
            .FirstOrDefaultAsync(c => c.UserId == userId, cancellationToken);

        if (candidate is null)
            return ServiceResult.NotFound<PagedResult<JobSuggestionResponse>>("Candidate profile not found.");

        var now = DateTime.UtcNow;

        // Fetch active, approved, non-expired jobs
        var activeJobs = await _context.Jobs
            .AsNoTracking()
            .Include(j => j.Company)
            .Include(j => j.Category)
            .Include(j => j.Level)
            .Include(j => j.Location)
            .Include(j => j.JobSkills)
                .ThenInclude(js => js.Skill)
            .Where(j => !j.IsDeleted && j.IsActive && j.ApprovalStatus == JobApprovalStatus.Approved && (!j.Deadline.HasValue || j.Deadline.Value >= now))
            .ToListAsync(cancellationToken);

        // Score each job using Rule-Based matching engine
        var scoredJobs = activeJobs
            .Select(j =>
            {
                var (score, explanation, matchedSkills, missingSkills) = CalculateMatchScore(candidate, j);
                return new
                {
                    Job = j,
                    Score = score,
                    Explanation = explanation,
                    MatchedSkills = matchedSkills,
                    MissingSkills = missingSkills
                };
            })
            .OrderByDescending(x => x.Score)
            .ThenByDescending(x => x.Job.CreatedAt)
            .ToList();

        var totalCount = scoredJobs.Count;
        var pageIndex = filter.PageIndex < 1 ? 1 : filter.PageIndex;
        var pageSize = filter.PageSize is < 1 or > 100 ? 10 : filter.PageSize;

        var pagedItems = scoredJobs
            .Skip((pageIndex - 1) * pageSize)
            .Take(pageSize)
            .Select(x => new JobSuggestionResponse(
                x.Job.Id,
                x.Job.CompanyId,
                x.Job.Company.Name,
                x.Job.Company.LogoUrl,
                x.Job.Title,
                x.Job.Category?.Name,
                x.Job.Level?.Name,
                x.Job.Location?.Name,
                x.Job.SalaryMin,
                x.Job.SalaryMax,
                x.Job.SalaryCurrency,
                x.Job.Deadline,
                x.Score,
                x.Explanation,
                x.MatchedSkills,
                x.MissingSkills
            ))
            .ToList();

        return ServiceResult.Success(new PagedResult<JobSuggestionResponse>(pagedItems, totalCount, pageIndex, pageSize));
    }

    public async Task<ServiceResult<JobMatchPreviewResponse>> PreviewJobMatchAsync(
        Guid userId, Guid jobId, PreviewJobMatchRequest request, CancellationToken cancellationToken = default)
    {
        var candidate = await _context.Candidates
            .Include(c => c.Skills)
                .ThenInclude(cs => cs.Skill)
            .Include(c => c.CVs)
            .FirstOrDefaultAsync(c => c.UserId == userId && !c.IsDeleted, cancellationToken);

        if (candidate is null)
            return ServiceResult.NotFound<JobMatchPreviewResponse>("Candidate profile not found.");

        var job = await _context.Jobs
            .AsNoTracking()
            .Include(j => j.JobSkills)
                .ThenInclude(js => js.Skill)
            .Include(j => j.Location)
            .Include(j => j.EmploymentType)
            .FirstOrDefaultAsync(j => j.Id == jobId && !j.IsDeleted, cancellationToken);

        if (job is null)
            return ServiceResult.NotFound<JobMatchPreviewResponse>("Job not found.");

        if (job.IsBanned || !job.IsActive || job.ApprovalStatus != JobApprovalStatus.Approved)
            return ServiceResult.Failure<JobMatchPreviewResponse>("Job is closed, expired, or not approved for applications.", ServiceErrorType.Validation);

        CandidateCv? selectedCv = null;
        if (request.CvId.HasValue)
        {
            selectedCv = candidate.CVs.FirstOrDefault(c => c.Id == request.CvId.Value && !c.IsDeleted);
            if (selectedCv is null)
                return ServiceResult.NotFound<JobMatchPreviewResponse>("The specified CV was not found in your profile.");
        }
        else
        {
            selectedCv = candidate.CVs
                .Where(c => !c.IsDeleted)
                .OrderByDescending(c => c.CreatedAt)
                .FirstOrDefault();

            if (selectedCv is null)
                return ServiceResult.Failure<JobMatchPreviewResponse>("No active CV found. Please upload a CV first.", ServiceErrorType.Validation);
        }

        var (score, explanation, matchedSkills, missingSkills) = CalculateMatchScore(candidate, job);

        var locationMatched = !job.LocationId.HasValue ||
            (!string.IsNullOrWhiteSpace(candidate.DesiredLocationId) &&
             string.Equals(candidate.DesiredLocationId, job.LocationId.Value.ToString(), StringComparison.OrdinalIgnoreCase));

        var salaryMatched = !job.SalaryMin.HasValue || !candidate.DesiredSalaryMax.HasValue ||
            (candidate.DesiredSalaryMin.GetValueOrDefault(0) <= (job.SalaryMax ?? int.MaxValue) &&
             candidate.DesiredSalaryMax.Value >= job.SalaryMin.Value);

        var legacyResponse = new JobMatchPreviewResponse(
            job.Id,
            job.Title,
            selectedCv.Id,
            selectedCv.Title,
            score,
            matchedSkills,
            missingSkills,
            explanation,
            locationMatched,
            salaryMatched,
            ExperienceComparison: null,
            EducationComparison: null,
            ProjectDomainRelevance: null,
            IsAiPreview: false,
            MatchSource: "legacy"
        );

        // ---------------------------------------------------------------------
        // AI Matching Preview Evaluation (AI-MATCH-DEMO-001)
        // Priority:
        // 1. PreviewAiEnabled == true: AI is authoritative with legacy fallback.
        // 2. PreviewShadowEnabled == true: Legacy authoritative + AI shadow log.
        // 3. Both false: Legacy only.
        // If both are true, PreviewAiEnabled takes precedence.
        // ---------------------------------------------------------------------
        if (_aiOptions.PreviewAiEnabled)
        {
            var authoritativeResponse = await ExecuteAuthoritativeAiMatchingAsync(selectedCv.Id, job, legacyResponse, cancellationToken);
            return ServiceResult.Success(authoritativeResponse);
        }

        if (_aiOptions.PreviewShadowEnabled)
        {
            await ExecuteShadowMatchingAsync(selectedCv.Id, job, legacyResponse.MatchScore, cancellationToken);
        }

        return ServiceResult.Success(legacyResponse);
    }

    private async Task<JobMatchPreviewResponse> ExecuteAuthoritativeAiMatchingAsync(
        Guid cvId,
        Job job,
        JobMatchPreviewResponse legacyResponse,
        CancellationToken cancellationToken)
    {
        try
        {
            cancellationToken.ThrowIfCancellationRequested();

            var parser = await _context.CvParsers
                .AsNoTracking()
                .FirstOrDefaultAsync(p => p.CvId == cvId, cancellationToken);

            if (parser is null || string.IsNullOrWhiteSpace(parser.ParsedDataJson))
            {
                _logger.LogWarning(
                    "AI preview unavailable; legacy fallback used. JobId={JobId}, CvId={CvId}, Reason={Reason}",
                    job.Id,
                    cvId,
                    "Structured CV not ready");
                return legacyResponse;
            }

            StructuredCvDataDto? structuredCvData;
            try
            {
                structuredCvData = JsonSerializer.Deserialize<StructuredCvDataDto>(parser.ParsedDataJson);
            }
            catch (JsonException ex)
            {
                _logger.LogWarning(
                    ex,
                    "AI preview unavailable; legacy fallback used. JobId={JobId}, CvId={CvId}, Reason={Reason}",
                    job.Id,
                    cvId,
                    "Malformed parsed CV JSON");
                return legacyResponse;
            }

            if (structuredCvData is null)
            {
                _logger.LogWarning(
                    "AI preview unavailable; legacy fallback used. JobId={JobId}, CvId={CvId}, Reason={Reason}",
                    job.Id,
                    cvId,
                    "Structured CV data is null");
                return legacyResponse;
            }

            var aiRequest = AiMatchingMapper.ToAiMatchRequest(structuredCvData, job);
            var aiResult = await _aiMatchingClient.MatchAsync(aiRequest, cancellationToken: cancellationToken);

            if (!aiResult.IsSuccess || aiResult.Data is null)
            {
                _logger.LogWarning(
                    "AI preview unavailable; legacy fallback used. JobId={JobId}, CvId={CvId}, Reason={Reason}",
                    job.Id,
                    cvId,
                    aiResult.ErrorMessage ?? "AI service returned failure or null data");
                return legacyResponse;
            }

            var matchResult = aiResult.Data;

            string aiExplanation;
            if (!string.IsNullOrWhiteSpace(matchResult.MatchExplanation))
            {
                aiExplanation = matchResult.MatchExplanation;
            }
            else
            {
                var parts = new List<string>();
                if (!string.IsNullOrWhiteSpace(matchResult.ExperienceComparison))
                    parts.Add(matchResult.ExperienceComparison);
                if (!string.IsNullOrWhiteSpace(matchResult.EducationComparison))
                    parts.Add(matchResult.EducationComparison);
                if (!string.IsNullOrWhiteSpace(matchResult.ProjectDomainRelevance))
                    parts.Add(matchResult.ProjectDomainRelevance);

                aiExplanation = parts.Count > 0 ? string.Join(" ", parts) : legacyResponse.Explanation;
            }

            _logger.LogInformation(
                "AI preview completed. JobId={JobId}, CvId={CvId}, AiScore={AiScore}, AlgorithmVersion={AlgorithmVersion}, ContractVersion={ContractVersion}, CorrelationId={CorrelationId}",
                job.Id,
                cvId,
                matchResult.MatchScore,
                matchResult.Meta.AlgorithmVersion,
                matchResult.Meta.ContractVersion,
                matchResult.Meta.CorrelationId);

            return new JobMatchPreviewResponse(
                legacyResponse.JobId,
                legacyResponse.JobTitle,
                legacyResponse.CvId,
                legacyResponse.CvTitle,
                matchResult.MatchScore,
                matchResult.MatchedSkills,
                matchResult.MissingSkills,
                aiExplanation,
                legacyResponse.LocationMatched,
                legacyResponse.SalaryMatched,
                matchResult.ExperienceComparison,
                matchResult.EducationComparison,
                matchResult.ProjectDomainRelevance,
                IsAiPreview: true,
                MatchSource: "ai",
                ExplanationDetails: matchResult.ExplanationDetails
            );

        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
        {
            throw;
        }
        catch (Exception ex)
        {
            _logger.LogWarning(
                ex,
                "AI preview unavailable; legacy fallback used. JobId={JobId}, CvId={CvId}, Reason={Reason}",
                job.Id,
                cvId,
                "Unexpected exception");
            return legacyResponse;
        }
    }

    private async Task ExecuteShadowMatchingAsync(
        Guid cvId,
        Job job,
        int legacyScore,
        CancellationToken cancellationToken)
    {
        try
        {
            cancellationToken.ThrowIfCancellationRequested();

            var parser = await _context.CvParsers
                .AsNoTracking()
                .FirstOrDefaultAsync(p => p.CvId == cvId, cancellationToken);

            if (parser is null || string.IsNullOrWhiteSpace(parser.ParsedDataJson))
            {
                _logger.LogInformation(
                    "AI preview shadow skipped: structured CV not ready. JobId={JobId}, CvId={CvId}",
                    job.Id,
                    cvId);
                return;
            }

            StructuredCvDataDto? structuredCvData;
            try
            {
                structuredCvData = JsonSerializer.Deserialize<StructuredCvDataDto>(parser.ParsedDataJson);
            }
            catch (JsonException ex)
            {
                _logger.LogWarning(
                    ex,
                    "AI preview shadow skipped: malformed parsed CV JSON. JobId={JobId}, CvId={CvId}",
                    job.Id,
                    cvId);
                return;
            }

            if (structuredCvData is null)
            {
                _logger.LogInformation(
                    "AI preview shadow skipped: structured CV data is null. JobId={JobId}, CvId={CvId}",
                    job.Id,
                    cvId);
                return;
            }

            var aiRequest = AiMatchingMapper.ToAiMatchRequest(structuredCvData, job);
            var aiResult = await _aiMatchingClient.MatchAsync(aiRequest, cancellationToken: cancellationToken);

            if (aiResult.IsSuccess && aiResult.Data is not null)
            {
                var matchResult = aiResult.Data;
                var aiScore = matchResult.MatchScore;
                var delta = aiScore - legacyScore;

                _logger.LogInformation(
                    "AI preview shadow completed. JobId={JobId}, CvId={CvId}, LegacyScore={LegacyScore}, AiScore={AiScore}, Delta={Delta}, Algorithm={AlgorithmVersion}, Contract={ContractVersion}, LlmInvoked={LlmInvoked}, ExplanationMode={ExplanationMode}, ProcessingTimeMs={ProcessingTimeMs}, CorrelationId={CorrelationId}",
                    job.Id,
                    cvId,
                    legacyScore,
                    aiScore,
                    delta,
                    matchResult.Meta.AlgorithmVersion,
                    matchResult.Meta.ContractVersion,
                    matchResult.Meta.LlmInvoked,
                    matchResult.Meta.ExplanationMode,
                    matchResult.Meta.ProcessingTimeMs,
                    matchResult.Meta.CorrelationId);
            }
            else
            {
                _logger.LogWarning(
                    "AI preview shadow failed: {ErrorMessage}. JobId={JobId}, CvId={CvId}",
                    aiResult.ErrorMessage ?? "Unknown error",
                    job.Id,
                    cvId);
            }
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
        {
            throw;
        }
        catch (Exception ex)
        {
            _logger.LogWarning(
                ex,
                "AI preview shadow encountered an unexpected error. JobId={JobId}, CvId={CvId}",
                job.Id,
                cvId);
        }
    }

    // -------------------------------------------------------------------------
    // Recruiter Operations
    // -------------------------------------------------------------------------

    public async Task<ServiceResult<PagedResult<RecruiterApplicationListResponse>>> GetJobApplicationsAsync(
        Guid userId, Guid jobId, RecruiterApplicationFilterRequest filter, CancellationToken cancellationToken = default)
    {
        // Check recruiter ownership of the job
        var employer = await _context.Employers
            .FirstOrDefaultAsync(e => e.UserId == userId, cancellationToken);

        if (employer is null)
            return ServiceResult.NotFound<PagedResult<RecruiterApplicationListResponse>>("Employer profile not found.");

        var job = await _context.Jobs
            .FirstOrDefaultAsync(j => j.Id == jobId && !j.IsDeleted, cancellationToken);

        if (job is null)
            return ServiceResult.NotFound<PagedResult<RecruiterApplicationListResponse>>("Job not found.");

        if (job.CompanyId != employer.CompanyId)
            return ServiceResult.Forbidden<PagedResult<RecruiterApplicationListResponse>>("Access denied. You do not own this job.");

        var query = _context.Applications
            .AsNoTracking()
            .Include(a => a.Candidate)
            .Include(a => a.Cv)
            .Where(a => a.JobId == jobId && !a.IsDeleted);

        if (!string.IsNullOrWhiteSpace(filter.Status) &&
            Enum.TryParse<ApplicationStatus>(filter.Status, true, out var appStatusEnum))
        {
            query = query.Where(a => a.Status == appStatusEnum);
        }

        if (filter.MinRating.HasValue)
        {
            query = query.Where(a => a.Rating.HasValue && a.Rating >= filter.MinRating.Value);
        }

        if (!string.IsNullOrWhiteSpace(filter.Keyword))
        {
            var kw = filter.Keyword.Trim().ToLower();
            query = query.Where(a => a.Candidate.FullName.ToLower().Contains(kw));
        }

        var totalCount = await query.CountAsync(cancellationToken);

        var pageIndex = filter.PageIndex < 1 ? 1 : filter.PageIndex;
        var pageSize = filter.PageSize is < 1 or > 100 ? 10 : filter.PageSize;

        var items = await query
            .OrderByDescending(a => a.AppliedAt)
            .Skip((pageIndex - 1) * pageSize)
            .Take(pageSize)
            .Select(a => new RecruiterApplicationListResponse(
                a.Id,
                a.CandidateId,
                a.Candidate.FullName,
                a.Candidate.AvatarUrl,
                a.Candidate.Phone,
                null, // email omitted here or populated if joined with AppUser
                a.CvId,
                a.Cv.Title,
                a.Cv.FileUrl,
                a.Status.ToString(),
                a.Rating,
                a.EvaluationLabel,
                a.MatchScore,
                a.AppliedAt
            ))
            .ToListAsync(cancellationToken);

        return ServiceResult.Success(new PagedResult<RecruiterApplicationListResponse>(items, totalCount, pageIndex, pageSize));
    }

    public async Task<ServiceResult<RecruiterApplicationDetailResponse>> GetApplicationDetailAsync(
        Guid userId, Guid applicationId, CancellationToken cancellationToken = default)
    {
        var (application, error) = await FindApplicationWithRecruiterOwnershipAsync(userId, applicationId, cancellationToken);
        if (error is not null) return error;

        var matchedSkills = DeserializeSkillList(application!.MatchedSkillsJson);
        var missingSkills = DeserializeSkillList(application.MissingSkillsJson);

        var timeline = application.StatusHistories
            .OrderBy(h => h.ChangedAt)
            .Select(h => new ApplicationStatusTimelineItem(h.FromStatus, h.ToStatus, h.Reason, h.ChangedAt))
            .ToList();

        var response = new RecruiterApplicationDetailResponse(
            application.Id,
            application.JobId,
            application.Job.Title,
            application.CandidateId,
            application.Candidate.FullName,
            application.Candidate.AvatarUrl,
            application.Candidate.Phone,
            null,
            application.Candidate.Address,
            application.CvId,
            application.Cv.Title,
            application.Cv.FileUrl,
            application.CoverLetter,
            application.Status.ToString(),
            application.Rating,
            application.EvaluationLabel,
            application.PrivateNotes,
            application.MatchScore,
            application.MatchExplanation,
            matchedSkills,
            missingSkills,
            application.AppliedAt,
            timeline
        );

        return ServiceResult.Success(response);
    }

    public async Task<ServiceResult<bool>> EvaluateApplicationAsync(
        Guid userId, Guid applicationId, EvaluateApplicationRequest request, CancellationToken cancellationToken = default)
    {
        var (application, error) = await FindApplicationWithRecruiterOwnershipAsync(userId, applicationId, cancellationToken);
        if (error is not null) return ServiceResult.Failure<bool>(error.ErrorMessage ?? "Access denied.", error.ErrorType);

        application!.Rating = request.Rating;
        application.EvaluationLabel = request.EvaluationLabel;
        application.PrivateNotes = request.PrivateNotes;

        await _context.SaveChangesAsync(cancellationToken);
        return ServiceResult.Success(true);
    }

    public async Task<ServiceResult<bool>> UpdateApplicationStatusAsync(
        Guid userId, Guid applicationId, UpdateApplicationStatusRequest request, CancellationToken cancellationToken = default)
    {
        var (application, error) = await FindApplicationWithRecruiterOwnershipAsync(userId, applicationId, cancellationToken);
        if (error is not null) return ServiceResult.Failure<bool>(error.ErrorMessage ?? "Access denied.", error.ErrorType);

        if (!Enum.TryParse<ApplicationStatus>(request.NewStatus, true, out var newStatusEnum))
            return ServiceResult.Failure<bool>($"Invalid application status: '{request.NewStatus}'.", ServiceErrorType.Validation);

        if (application!.Status == ApplicationStatus.Withdrawn)
            return ServiceResult.Failure<bool>("Cannot update status of a withdrawn application.");

        var oldStatus = application.Status;
        application.Status = newStatusEnum;

        // Explicitly add via DbSet to ensure EF Core marks the entity as EntityState.Added.
        // Adding via navigation collection causes EF Core to infer EntityState.Modified on pre-keyed entities.
        _context.ApplicationStatusHistories.Add(new ApplicationStatusHistory
        {
            ApplicationId = application.Id,
            FromStatus = oldStatus.ToString(),
            ToStatus = newStatusEnum.ToString(),
            ChangedById = userId,
            Reason = request.Reason,
            ChangedAt = DateTime.UtcNow
        });

        await _context.SaveChangesAsync(cancellationToken);
        return ServiceResult.Success(true);
    }

    public async Task<ServiceResult<RecruitmentPipelineResponse>> GetRecruitmentPipelineAsync(
        Guid userId, Guid jobId, CancellationToken cancellationToken = default)
    {
        var employer = await _context.Employers
            .FirstOrDefaultAsync(e => e.UserId == userId, cancellationToken);

        if (employer is null)
            return ServiceResult.NotFound<RecruitmentPipelineResponse>("Employer profile not found.");

        var job = await _context.Jobs
            .FirstOrDefaultAsync(j => j.Id == jobId && !j.IsDeleted, cancellationToken);

        if (job is null)
            return ServiceResult.NotFound<RecruitmentPipelineResponse>("Job not found.");

        if (job.CompanyId != employer.CompanyId)
            return ServiceResult.Forbidden<RecruitmentPipelineResponse>("Access denied. You do not own this job.");

        // Fetch applications excluding withdrawn ones
        var applications = await _context.Applications
            .AsNoTracking()
            .Include(a => a.Candidate)
            .Include(a => a.Cv)
            .Include(a => a.StatusHistories)
            .Where(a => a.JobId == jobId && !a.IsDeleted && a.Status != ApplicationStatus.Withdrawn)
            .ToListAsync(cancellationToken);

        var pipelineStages = new[] { "Applied", "Screening", "Interview", "Offer", "Hired", "Rejected" };
        var now = DateTime.UtcNow;

        var stageResponses = pipelineStages.Select(stage =>
        {
            var appsInStage = applications.Where(a => a.Status.ToString().Equals(stage, StringComparison.OrdinalIgnoreCase)).ToList();
            var cards = appsInStage.Select(a =>
            {
                var lastHistory = a.StatusHistories
                    .OrderByDescending(h => h.ChangedAt)
                    .FirstOrDefault();
                var lastStatusChangedAt = lastHistory?.ChangedAt ?? a.AppliedAt;
                var daysInStage = (int)Math.Max(0, (now - lastStatusChangedAt).TotalDays);

                var stageAlert = "Normal";
                if (a.Status is not (ApplicationStatus.Hired or ApplicationStatus.Rejected))
                {
                    stageAlert = daysInStage switch
                    {
                        > 14 => "Critical",
                        > 7 => "Warning",
                        _ => "Normal"
                    };
                }

                return new PipelineCandidateCardResponse(
                    a.Id,
                    a.CandidateId,
                    a.Candidate.FullName,
                    a.Candidate.AvatarUrl,
                    a.Rating,
                    a.EvaluationLabel,
                    a.MatchScore,
                    a.AppliedAt,
                    a.Cv.FileUrl,
                    daysInStage,
                    stageAlert,
                    lastStatusChangedAt
                );
            }).ToList();

            return new PipelineStageResponse(stage, cards.Count, cards);
        }).ToList();

        var response = new RecruitmentPipelineResponse(
            job.Id,
            job.Title,
            applications.Count,
            stageResponses
        );

        return ServiceResult.Success(response);
    }

    public async Task<ServiceResult<PipelineAnalyticsResponse>> GetPipelineAnalyticsAsync(
        Guid userId, Guid jobId, CancellationToken cancellationToken = default)
    {
        var employer = await _context.Employers
            .FirstOrDefaultAsync(e => e.UserId == userId, cancellationToken);

        if (employer is null)
            return ServiceResult.NotFound<PipelineAnalyticsResponse>("Employer profile not found.");

        var job = await _context.Jobs
            .FirstOrDefaultAsync(j => j.Id == jobId && !j.IsDeleted, cancellationToken);

        if (job is null)
            return ServiceResult.NotFound<PipelineAnalyticsResponse>("Job not found.");

        if (job.CompanyId != employer.CompanyId)
            return ServiceResult.Forbidden<PipelineAnalyticsResponse>("Access denied. You do not own this job.");

        var applications = await _context.Applications
            .AsNoTracking()
            .Include(a => a.StatusHistories)
            .Where(a => a.JobId == jobId && !a.IsDeleted)
            .ToListAsync(cancellationToken);

        var totalApplications = applications.Count;
        var hiredCount = applications.Count(a => a.Status == ApplicationStatus.Hired);
        var rejectedCount = applications.Count(a => a.Status == ApplicationStatus.Rejected);
        var withdrawnCount = applications.Count(a => a.Status == ApplicationStatus.Withdrawn);
        var activeApplications = totalApplications - hiredCount - rejectedCount - withdrawnCount;

        // Overall conversion rate: Hired / Total
        var overallConversionRate = totalApplications > 0
            ? Math.Round((double)hiredCount / totalApplications * 100, 1)
            : 0.0;

        // Average Time-to-Hire in days
        var hiredApps = applications.Where(a => a.Status == ApplicationStatus.Hired).ToList();
        double? averageTimeToHireDays = null;
        if (hiredApps.Count > 0)
        {
            var daysList = hiredApps.Select(a =>
            {
                var hiredHistory = a.StatusHistories
                    .OrderByDescending(h => h.ChangedAt)
                    .FirstOrDefault(h => h.ToStatus == "Hired");
                var hiredAt = hiredHistory?.ChangedAt ?? a.UpdatedAt ?? a.AppliedAt;
                return Math.Max(0, (hiredAt - a.AppliedAt).TotalDays);
            }).ToList();

            averageTimeToHireDays = Math.Round(daysList.Average(), 1);
        }

        // Funnel stages: Applied -> Screening -> Interview -> Offer -> Hired
        int CountReached(ApplicationStatus targetStatus)
        {
            var targetStr = targetStatus.ToString();
            return applications.Count(a =>
                a.Status == targetStatus ||
                a.StatusHistories.Any(h => h.ToStatus.Equals(targetStr, StringComparison.OrdinalIgnoreCase)));
        }

        var countApplied = totalApplications;
        var countScreening = CountReached(ApplicationStatus.Screening);
        var countInterview = CountReached(ApplicationStatus.Interview);
        var countOffer = CountReached(ApplicationStatus.Offer);
        var countHired = hiredCount;

        static double CalcRate(int from, int to) => from > 0 ? Math.Round((double)to / from * 100, 1) : 0.0;

        var stageConversionRates = new List<StageConversionDto>
        {
            new("Applied", "Screening", countApplied, countScreening, CalcRate(countApplied, countScreening)),
            new("Screening", "Interview", countScreening, countInterview, CalcRate(countScreening, countInterview)),
            new("Interview", "Offer", countInterview, countOffer, CalcRate(countInterview, countOffer)),
            new("Offer", "Hired", countOffer, countHired, CalcRate(countOffer, countHired))
        };

        // Active stages duration & bottleneck detection
        var activeStages = new[] { "Applied", "Screening", "Interview", "Offer" };
        var stageDurations = new List<StageDurationDto>();
        var now = DateTime.UtcNow;
        int overdueCandidatesCount = 0;

        string? bottleneckStage = null;
        double maxAvgDays = -1;

        foreach (var stage in activeStages)
        {
            var appsInStage = applications.Where(a => a.Status.ToString().Equals(stage, StringComparison.OrdinalIgnoreCase)).ToList();
            if (appsInStage.Count == 0)
            {
                stageDurations.Add(new StageDurationDto(stage, 0.0, 0, 0));
                continue;
            }

            var daysInStageList = appsInStage.Select(a =>
            {
                var lastH = a.StatusHistories.OrderByDescending(h => h.ChangedAt).FirstOrDefault();
                var changedAt = lastH?.ChangedAt ?? a.AppliedAt;
                return Math.Max(0, (now - changedAt).TotalDays);
            }).ToList();

            var avgDays = Math.Round(daysInStageList.Average(), 1);
            var overdueInStage = daysInStageList.Count(d => d > 7);
            overdueCandidatesCount += overdueInStage;

            stageDurations.Add(new StageDurationDto(stage, avgDays, appsInStage.Count, overdueInStage));

            if (avgDays > maxAvgDays && appsInStage.Count > 0)
            {
                maxAvgDays = avgDays;
                bottleneckStage = stage;
            }
        }

        var response = new PipelineAnalyticsResponse(
            job.Id,
            job.Title,
            totalApplications,
            activeApplications,
            hiredCount,
            rejectedCount,
            withdrawnCount,
            averageTimeToHireDays,
            overallConversionRate,
            stageConversionRates,
            stageDurations,
            bottleneckStage,
            overdueCandidatesCount
        );

        return ServiceResult.Success(response);
    }

    public async Task<ServiceResult<byte[]>> ExportPipelineCsvAsync(
        Guid userId, Guid jobId, CancellationToken cancellationToken = default)
    {
        var employer = await _context.Employers
            .FirstOrDefaultAsync(e => e.UserId == userId, cancellationToken);

        if (employer is null)
            return ServiceResult.NotFound<byte[]>("Employer profile not found.");

        var job = await _context.Jobs
            .FirstOrDefaultAsync(j => j.Id == jobId && !j.IsDeleted, cancellationToken);

        if (job is null)
            return ServiceResult.NotFound<byte[]>("Job not found.");

        if (job.CompanyId != employer.CompanyId)
            return ServiceResult.Forbidden<byte[]>("Access denied. You do not own this job.");

        var applications = await _context.Applications
            .AsNoTracking()
            .Include(a => a.Candidate)
            .Include(a => a.Cv)
            .Include(a => a.StatusHistories)
            .Where(a => a.JobId == jobId && !a.IsDeleted)
            .OrderByDescending(a => a.AppliedAt)
            .ToListAsync(cancellationToken);

        // Fetch candidate emails
        var candidateUserIds = applications.Select(a => a.Candidate.UserId).Distinct().ToList();
        var userEmails = new Dictionary<Guid, string?>();
        foreach (var uid in candidateUserIds)
        {
            userEmails[uid] = await _identityService.GetUserEmailAsync(uid, cancellationToken);
        }

        var sb = new StringBuilder();

        // CSV Header
        sb.AppendLine("\"Mã ứng tuyển\",\"Họ tên ứng viên\",\"Email\",\"Số điện thoại\",\"Tiêu đề CV\",\"Trạng thái\",\"Số ngày ở stage\",\"Mức cảnh báo\",\"Đánh giá (Sao)\",\"Nhãn đánh giá\",\"Độ tương thích (%)\",\"Ngày nộp đơn\",\"Ghi chú nội bộ\"");

        var now = DateTime.UtcNow;

        foreach (var a in applications)
        {
            var lastHistory = a.StatusHistories
                .OrderByDescending(h => h.ChangedAt)
                .FirstOrDefault();
            var lastStatusChangedAt = lastHistory?.ChangedAt ?? a.AppliedAt;
            var daysInStage = (int)Math.Max(0, (now - lastStatusChangedAt).TotalDays);

            var stageAlert = "Normal";
            if (a.Status is not (ApplicationStatus.Hired or ApplicationStatus.Rejected or ApplicationStatus.Withdrawn))
            {
                stageAlert = daysInStage switch
                {
                    > 14 => "Critical",
                    > 7 => "Warning",
                    _ => "Normal"
                };
            }

            var email = userEmails.GetValueOrDefault(a.Candidate.UserId) ?? string.Empty;
            var ratingStr = a.Rating.HasValue ? a.Rating.Value.ToString() : string.Empty;
            var matchScoreStr = a.MatchScore.HasValue ? a.MatchScore.Value.ToString() : string.Empty;

            static string Escape(string? val) => $"\"{(val ?? string.Empty).Replace("\"", "\"\"")}\"";

            sb.AppendLine(string.Join(",",
                Escape(a.Id.ToString()),
                Escape(a.Candidate.FullName),
                Escape(email),
                Escape(a.Candidate.Phone),
                Escape(a.Cv.Title),
                Escape(a.Status.ToString()),
                daysInStage,
                Escape(stageAlert),
                ratingStr,
                Escape(a.EvaluationLabel),
                matchScoreStr,
                Escape(a.AppliedAt.ToString("yyyy-MM-dd HH:mm:ss")),
                Escape(a.PrivateNotes)
            ));
        }

        // Include UTF-8 BOM so Excel opens with proper accents
        var preamble = Encoding.UTF8.GetPreamble();
        var dataBytes = Encoding.UTF8.GetBytes(sb.ToString());
        var fullBytes = new byte[preamble.Length + dataBytes.Length];
        Buffer.BlockCopy(preamble, 0, fullBytes, 0, preamble.Length);
        Buffer.BlockCopy(dataBytes, 0, fullBytes, preamble.Length, dataBytes.Length);

        return ServiceResult.Success(fullBytes);
    }

    // -------------------------------------------------------------------------
    // Private Helpers & Rule-based Matching Engine
    // -------------------------------------------------------------------------

    private async Task<(JobApplication? App, ServiceResult<RecruiterApplicationDetailResponse>? Error)>
        FindApplicationWithRecruiterOwnershipAsync(Guid userId, Guid applicationId, CancellationToken ct)
    {
        var employer = await _context.Employers
            .FirstOrDefaultAsync(e => e.UserId == userId, ct);

        if (employer is null)
            return (null, ServiceResult.NotFound<RecruiterApplicationDetailResponse>("Employer profile not found."));

        var application = await _context.Applications
            .Include(a => a.Job)
            .Include(a => a.Candidate)
            .Include(a => a.Cv)
            .Include(a => a.StatusHistories)
            .FirstOrDefaultAsync(a => a.Id == applicationId && !a.IsDeleted, ct);

        if (application is null)
            return (null, ServiceResult.NotFound<RecruiterApplicationDetailResponse>("Application not found."));

        if (application.Job.CompanyId != employer.CompanyId)
            return (null, ServiceResult.Forbidden<RecruiterApplicationDetailResponse>("Access denied. You do not own this application."));

        return (application, null);
    }

    /// <summary>
    /// Pure Rule-based matching algorithm (SQL / LINQ).
    /// Calculates compatibility score (0 - 100%) based on:
    /// 1. Skills overlap (up to 70% weight)
    /// 2. Location match (15% weight)
    /// 3. Salary expectation overlap (15% weight)
    /// </summary>
    private static (int Score, string Explanation, List<string> MatchedSkills, List<string> MissingSkills)
        CalculateMatchScore(Candidate candidate, Job job)
    {
        var candidateSkillIds = candidate.Skills.Select(s => s.SkillId).ToHashSet();
        var requiredJobSkills = job.JobSkills.Where(js => js.IsRequired).ToList();
        var optionalJobSkills = job.JobSkills.Where(js => !js.IsRequired).ToList();

        var matchedSkillNames = new List<string>();
        var missingSkillNames = new List<string>();

        double skillScore = 0;
        string skillExplanation;

        if (job.JobSkills.Count == 0)
        {
            // Case 1: Employer did not specify any skills for the job
            // Candidate is not blocked by skill requirements -> gets full 70% skill weight
            skillScore = 70.0;
            skillExplanation = "Tin tuyển dụng không yêu cầu kỹ năng cụ thể (hưởng trọn 70% điểm kỹ năng)";
        }
        else if (requiredJobSkills.Count == 0 && optionalJobSkills.Count > 0)
        {
            // Case 2: Employer specified only optional/preferred skills, no mandatory ones
            int matchedOptCount = 0;
            foreach (var js in optionalJobSkills)
            {
                if (candidateSkillIds.Contains(js.SkillId))
                {
                    matchedOptCount++;
                    if (js.Skill != null) matchedSkillNames.Add(js.Skill.Name);
                }
            }

            // 60% baseline (no mandatory barriers) + up to 10% bonus for optional skills
            var optBonus = ((double)matchedOptCount / optionalJobSkills.Count) * 10.0;
            skillScore = 60.0 + optBonus;
            skillExplanation = $"Tin tuyển dụng không có kỹ năng bắt buộc (phù hợp {matchedOptCount}/{optionalJobSkills.Count} kỹ năng ưu tiên: +{Math.Round(optBonus, 1)}%)";
        }
        else
        {
            // Case 3: Employer specified mandatory required skills
            int matchedReqCount = 0;
            foreach (var js in requiredJobSkills)
            {
                if (candidateSkillIds.Contains(js.SkillId))
                {
                    matchedReqCount++;
                    if (js.Skill != null) matchedSkillNames.Add(js.Skill.Name);
                }
                else
                {
                    if (js.Skill != null) missingSkillNames.Add(js.Skill.Name);
                }
            }

            // Up to 60% for required skills
            skillScore = ((double)matchedReqCount / requiredJobSkills.Count) * 60.0;

            // Up to 10% bonus for optional/nice-to-have skills
            if (optionalJobSkills.Count > 0)
            {
                int matchedOptCount = 0;
                foreach (var js in optionalJobSkills)
                {
                    if (candidateSkillIds.Contains(js.SkillId))
                    {
                        matchedOptCount++;
                        if (js.Skill != null) matchedSkillNames.Add(js.Skill.Name);
                    }
                }
                skillScore += ((double)matchedOptCount / optionalJobSkills.Count) * 10.0;
            }

            if (missingSkillNames.Count == 0)
            {
                skillExplanation = $"Trùng khớp toàn bộ {matchedReqCount}/{requiredJobSkills.Count} kỹ năng yêu cầu";
            }
            else
            {
                skillExplanation = $"Trùng khớp {matchedReqCount}/{requiredJobSkills.Count} kỹ năng yêu cầu (còn thiếu: {string.Join(", ", missingSkillNames)})";
            }
        }

        // 2. Location matching (15%)
        double locationScore = 0;
        if (job.LocationId.HasValue && !string.IsNullOrEmpty(candidate.DesiredLocationId))
        {
            if (job.LocationId.Value.ToString().Equals(candidate.DesiredLocationId, StringComparison.OrdinalIgnoreCase))
            {
                locationScore = 15.0;
            }
        }
        else
        {
            // Neutral
            locationScore = 10.0;
        }

        // 3. Salary overlap matching (15%)
        double salaryScore = 0;
        if (job.SalaryMin.HasValue && candidate.DesiredSalaryMax.HasValue)
        {
            bool overlaps = (!candidate.DesiredSalaryMin.HasValue || candidate.DesiredSalaryMin <= job.SalaryMax) &&
                            (!job.SalaryMin.HasValue || candidate.DesiredSalaryMax >= job.SalaryMin);
            if (overlaps) salaryScore = 15.0;
        }
        else
        {
            salaryScore = 10.0;
        }

        int totalScore = (int)Math.Clamp(Math.Round(skillScore + locationScore + salaryScore), 0, 100);

        string explanation = $"{skillExplanation}. " +
                             $"Điểm kỹ năng: {Math.Round(skillScore, 1)}%, Địa điểm: {(int)locationScore}%, Mức lương: {(int)salaryScore}%.";

        return (totalScore, explanation, matchedSkillNames, missingSkillNames);
    }

    private static List<string> DeserializeSkillList(string? json)
    {
        if (string.IsNullOrWhiteSpace(json)) return [];
        try
        {
            return JsonSerializer.Deserialize<List<string>>(json) ?? [];
        }
        catch
        {
            return [];
        }
    }
}
