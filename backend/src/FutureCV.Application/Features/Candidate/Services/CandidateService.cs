using System.Text.Json;
using FutureCV.Application.Common.Interfaces;
using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.Candidate.DTOs;
using FutureCV.Application.Features.Candidate.Interfaces;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace FutureCV.Application.Features.Candidate.Services;

using FutureCV.Domain.Entities;

public class CandidateService : ICandidateService
{
    private const string AvatarFolder = "avatars/candidates";
    private const string CvFolder = "cvs/candidates";
    private const long CvMaxSizeBytes = 5 * 1024 * 1024; // 5 MB

    private readonly IApplicationDbContext _context;
    private readonly IFileStorage _fileStorage;
    private readonly IIdentityService _identityService;
    private readonly IAiCvClient? _aiCvClient;
    private readonly ILogger<CandidateService>? _logger;

    public CandidateService(
        IApplicationDbContext context,
        IFileStorage fileStorage,
        IIdentityService identityService,
        IAiCvClient? aiCvClient = null,
        ILogger<CandidateService>? logger = null)
    {
        _context = context;
        _fileStorage = fileStorage;
        _identityService = identityService;
        _aiCvClient = aiCvClient;
        _logger = logger;
    }

    // -------------------------------------------------------------------------
    // Profile
    // -------------------------------------------------------------------------

    public async Task<ServiceResult<CandidateProfileResponse>> GetProfileAsync(
        Guid userId, CancellationToken cancellationToken = default)
    {
        var candidate = await FindByUserIdAsync(userId, cancellationToken);
        if (candidate is null)
            return ServiceResult.NotFound<CandidateProfileResponse>("Candidate profile not found.");

        var email = await GetUserEmailAsync(userId);
        return ServiceResult.Success(MapToProfileResponse(candidate, email));
    }

    public async Task<ServiceResult<CandidateFullProfileResponse>> GetFullProfileAsync(
        Guid userId, CancellationToken cancellationToken = default)
    {
        var candidate = await _context.Candidates
            .Include(c => c.Educations.Where(e => !e.IsDeleted))
            .Include(c => c.Experiences.Where(e => !e.IsDeleted))
            .Include(c => c.Skills)
                .ThenInclude(cs => cs.Skill)
            .Include(c => c.Certificates.Where(cert => !cert.IsDeleted))
            .Include(c => c.Projects.Where(p => !p.IsDeleted))
            .Include(c => c.CVs.Where(cv => !cv.IsDeleted))
            .FirstOrDefaultAsync(c => c.UserId == userId && !c.IsDeleted, cancellationToken);

        if (candidate is null)
            return ServiceResult.NotFound<CandidateFullProfileResponse>("Candidate profile not found.");

        var email = await GetUserEmailAsync(userId);
        return ServiceResult.Success(MapToFullProfileResponse(candidate, email));
    }

    public async Task<ServiceResult<CandidateProfileResponse>> UpdatePersonalInfoAsync(
        Guid userId, UpdateCandidateInfoRequest request, CancellationToken cancellationToken = default)
    {
        var candidate = await FindByUserIdAsync(userId, cancellationToken);
        if (candidate is null)
            return ServiceResult.NotFound<CandidateProfileResponse>("Candidate profile not found.");

        candidate.FullName = request.FullName;
        candidate.Phone = request.Phone;
        candidate.Address = request.Address;
        candidate.DateOfBirth = request.DateOfBirth;
        candidate.Gender = request.Gender;
        candidate.Summary = request.Summary;
        candidate.DesiredPosition = request.DesiredPosition;
        candidate.DesiredSalaryMin = request.DesiredSalaryMin;
        candidate.DesiredSalaryMax = request.DesiredSalaryMax;
        candidate.ProfileUpdatedAt = DateTimeOffset.UtcNow;

        await _context.SaveChangesAsync(cancellationToken);
        var email = await GetUserEmailAsync(userId);
        return ServiceResult.Success(MapToProfileResponse(candidate, email));
    }

    public async Task<ServiceResult<string>> UpdateAvatarAsync(
        Guid userId, FileUploadRequest file, CancellationToken cancellationToken = default)
    {
        // 1. Find Candidate profile by UserId
        var candidate = await FindByUserIdAsync(userId, cancellationToken);
        if (candidate is null)
            return ServiceResult.NotFound<string>("Candidate profile not found.");

        // 2. Store old AvatarPublicId for cleanup AFTER DB save succeeds
        var oldPublicId = candidate.AvatarPublicId;

        // 3. Upload new avatar to Cloudinary via IFileStorage
        string newPublicUrl;
        string newPublicId;
        try
        {
            (newPublicUrl, newPublicId) = await _fileStorage.UploadAsync(
                file.Stream, file.FileName, AvatarFolder, cancellationToken);
        }
        catch (Exception ex)
        {
            return ServiceResult.Failure<string>($"Failed to upload avatar: {ex.Message}", ServiceErrorType.Infrastructure);
        }

        // 4. Update entity with new URL and PublicId
        candidate.AvatarUrl = newPublicUrl;
        candidate.AvatarPublicId = newPublicId;
        candidate.ProfileUpdatedAt = DateTimeOffset.UtcNow;

        // 5. Persist changes to database
        try
        {
            await _context.SaveChangesAsync(cancellationToken);
        }
        catch (Exception ex)
        {
            // If DB update fails, clean up the newly uploaded file to prevent orphan files
            try
            {
                await _fileStorage.DeleteAsync(newPublicId, cancellationToken);
            }
            catch
            {
                // Best effort cleanup — ignore deletion errors
            }

            return ServiceResult.Failure<string>($"Failed to save avatar to database: {ex.Message}", ServiceErrorType.Infrastructure);
        }

        // 6. Only after upload AND DB update succeed: delete old avatar using old AvatarPublicId
        if (!string.IsNullOrEmpty(oldPublicId))
        {
            try
            {
                await _fileStorage.DeleteAsync(oldPublicId, cancellationToken);
            }
            catch
            {
                // Non-critical: failure to delete old avatar does not break successful DB update
            }
        }

        return ServiceResult.Success(newPublicUrl);
    }

    // -------------------------------------------------------------------------
    // Education
    // -------------------------------------------------------------------------

    public async Task<ServiceResult<EducationResponse>> AddEducationAsync(
        Guid userId, EducationDto dto, CancellationToken cancellationToken = default)
    {
        var candidate = await FindByUserIdAsync(userId, cancellationToken);
        if (candidate is null)
            return ServiceResult.NotFound<EducationResponse>("Candidate profile not found.");

        var education = new Education
        {
            CandidateId = candidate.Id,
            School = dto.School,
            Degree = dto.Degree,
            Major = dto.Major,
            StartYear = dto.StartYear,
            EndYear = dto.EndYear,
            Description = dto.Description,
        };

        _context.Educations.Add(education);
        await _context.SaveChangesAsync(cancellationToken);
        return ServiceResult.Success(MapToEducationResponse(education));
    }

    public async Task<ServiceResult<EducationResponse>> UpdateEducationAsync(
        Guid userId, Guid educationId, EducationDto dto, CancellationToken cancellationToken = default)
    {
        var (education, error) = await FindEducationWithOwnershipAsync(userId, educationId, cancellationToken);
        if (error is not null) return error;

        education!.School = dto.School;
        education.Degree = dto.Degree;
        education.Major = dto.Major;
        education.StartYear = dto.StartYear;
        education.EndYear = dto.EndYear;
        education.Description = dto.Description;

        await _context.SaveChangesAsync(cancellationToken);
        return ServiceResult.Success(MapToEducationResponse(education));
    }

    public async Task<ServiceResult<bool>> DeleteEducationAsync(
        Guid userId, Guid educationId, CancellationToken cancellationToken = default)
    {
        var (education, error) = await FindEducationWithOwnershipAsync(userId, educationId, cancellationToken);
        if (error is not null) return ServiceResult.Failure<bool>(error.ErrorMessage!, error.ErrorType);

        education!.IsDeleted = true;
        await _context.SaveChangesAsync(cancellationToken);
        return ServiceResult.Success(true);
    }

    // -------------------------------------------------------------------------
    // Experience
    // -------------------------------------------------------------------------

    public async Task<ServiceResult<ExperienceResponse>> AddExperienceAsync(
        Guid userId, ExperienceDto dto, CancellationToken cancellationToken = default)
    {
        var candidate = await FindByUserIdAsync(userId, cancellationToken);
        if (candidate is null)
            return ServiceResult.NotFound<ExperienceResponse>("Candidate profile not found.");

        var experience = new Experience
        {
            CandidateId = candidate.Id,
            CompanyName = dto.CompanyName,
            Position = dto.Position,
            StartDate = dto.StartDate,
            EndDate = dto.IsCurrent ? null : dto.EndDate,
            IsCurrent = dto.IsCurrent,
            Description = dto.Description,
        };

        _context.Experiences.Add(experience);
        await _context.SaveChangesAsync(cancellationToken);
        return ServiceResult.Success(MapToExperienceResponse(experience));
    }

    public async Task<ServiceResult<ExperienceResponse>> UpdateExperienceAsync(
        Guid userId, Guid experienceId, ExperienceDto dto, CancellationToken cancellationToken = default)
    {
        var (experience, error) = await FindExperienceWithOwnershipAsync(userId, experienceId, cancellationToken);
        if (error is not null) return error;

        experience!.CompanyName = dto.CompanyName;
        experience.Position = dto.Position;
        experience.StartDate = dto.StartDate;
        experience.EndDate = dto.IsCurrent ? null : dto.EndDate;
        experience.IsCurrent = dto.IsCurrent;
        experience.Description = dto.Description;

        await _context.SaveChangesAsync(cancellationToken);
        return ServiceResult.Success(MapToExperienceResponse(experience));
    }

    public async Task<ServiceResult<bool>> DeleteExperienceAsync(
        Guid userId, Guid experienceId, CancellationToken cancellationToken = default)
    {
        var (experience, error) = await FindExperienceWithOwnershipAsync(userId, experienceId, cancellationToken);
        if (error is not null) return ServiceResult.Failure<bool>(error.ErrorMessage!, error.ErrorType);

        experience!.IsDeleted = true;
        await _context.SaveChangesAsync(cancellationToken);
        return ServiceResult.Success(true);
    }

    // -------------------------------------------------------------------------
    // Skills
    // -------------------------------------------------------------------------

    public async Task<ServiceResult<CandidateSkillResponse>> AddSkillAsync(
        Guid userId, CandidateSkillDto dto, CancellationToken cancellationToken = default)
    {
        var candidate = await FindByUserIdAsync(userId, cancellationToken);
        if (candidate is null)
            return ServiceResult.NotFound<CandidateSkillResponse>("Candidate profile not found.");

        var skill = await _context.Skills.FirstOrDefaultAsync(s => s.Id == dto.SkillId, cancellationToken);
        if (skill is null)
            return ServiceResult.NotFound<CandidateSkillResponse>("Skill not found.");

        var alreadyExists = await _context.CandidateSkills
            .AnyAsync(cs => cs.CandidateId == candidate.Id && cs.SkillId == dto.SkillId, cancellationToken);
        if (alreadyExists)
            return ServiceResult.Conflict<CandidateSkillResponse>("This skill has already been added to your profile.");

        var candidateSkill = new CandidateSkill
        {
            CandidateId = candidate.Id,
            SkillId = dto.SkillId,
            Level = dto.Level,
            Years = dto.Years,
        };

        _context.CandidateSkills.Add(candidateSkill);
        await _context.SaveChangesAsync(cancellationToken);
        return ServiceResult.Success(MapToSkillResponse(candidateSkill, skill));
    }

    public async Task<ServiceResult<bool>> RemoveSkillAsync(
        Guid userId, Guid skillId, CancellationToken cancellationToken = default)
    {
        var candidate = await FindByUserIdAsync(userId, cancellationToken);
        if (candidate is null)
            return ServiceResult.NotFound<bool>("Candidate profile not found.");

        var candidateSkill = await _context.CandidateSkills
            .FirstOrDefaultAsync(cs => cs.CandidateId == candidate.Id && cs.SkillId == skillId, cancellationToken);

        if (candidateSkill is null)
            return ServiceResult.NotFound<bool>("Skill not found in your profile.");

        _context.CandidateSkills.Remove(candidateSkill);
        await _context.SaveChangesAsync(cancellationToken);
        return ServiceResult.Success(true);
    }

    // -------------------------------------------------------------------------
    // CV PDF Management (P2-UC03, P2-UC07)
    // -------------------------------------------------------------------------

    public async Task<ServiceResult<CvResponse>> UploadCvAsync(
        Guid userId, FileUploadRequest file, string? title, CancellationToken cancellationToken = default)
    {
        var candidate = await FindByUserIdAsync(userId, cancellationToken);
        if (candidate is null)
            return ServiceResult.NotFound<CvResponse>("Candidate profile not found.");

        if (file.SizeInBytes > CvMaxSizeBytes)
            return ServiceResult.Failure<CvResponse>($"CV file size must not exceed 5 MB.");

        // Read stream to byte array to allow both uploading to Cloudinary and parsing via AI
        byte[] fileBytes;
        using (var ms = new MemoryStream())
        {
            await file.Stream.CopyToAsync(ms, cancellationToken);
            fileBytes = ms.ToArray();
        }

        string publicUrl, publicId;
        try
        {
            using var uploadStream = new MemoryStream(fileBytes);
            (publicUrl, publicId) = await _fileStorage.UploadDocumentAsync(
                uploadStream, file.FileName, CvFolder, cancellationToken);
        }
        catch (Exception ex)
        {
            return ServiceResult.Failure<CvResponse>(
                $"Failed to upload CV: {ex.Message}", ServiceErrorType.Infrastructure);
        }

        // If this is the first CV, auto-set as primary
        var hasPrimary = await _context.CandidateCvs
            .AnyAsync(cv => cv.CandidateId == candidate.Id && cv.IsPrimary && !cv.IsDeleted, cancellationToken);

        var cv = new CandidateCv
        {
            CandidateId = candidate.Id,
            Title = title ?? file.FileName,
            FileUrl = publicUrl,
            PublicId = publicId,
            FileType = "PDF",
            FileSizeBytes = file.SizeInBytes,
            Source = "Upload",
            ParseStatus = "Pending",
            IsPrimary = !hasPrimary,
        };

        try
        {
            _context.CandidateCvs.Add(cv);
            await _context.SaveChangesAsync(cancellationToken);
        }
        catch (Exception ex)
        {
            // Rollback cloud upload on DB failure
            try { await _fileStorage.DeleteDocumentAsync(publicId, cancellationToken); } catch { }
            return ServiceResult.Failure<CvResponse>(
                $"Failed to save CV record: {ex.Message}", ServiceErrorType.Infrastructure);
        }

        // Automatically trigger AI scanning & extraction if client is available
        if (_aiCvClient != null)
        {
            try
            {
                var aiResult = await _aiCvClient.AnalyzePdfAsync(
                    fileBytes, file.FileName, cancellationToken: cancellationToken);

                if (aiResult.IsSuccess && aiResult.Data != null)
                {
                    var analysis = aiResult.Data;
                    var structuredData = FastApiCvMapper.ToStructuredCvDataDto(analysis.StructuredCv);
                    var structuredJson = JsonSerializer.Serialize(structuredData);

                    var parser = new CvParser
                    {
                        CvId = cv.Id,
                        RawText = analysis.RawText ?? structuredJson,
                        ParsedDataJson = structuredJson,
                        ModelVersion = "AI-v1",
                        ParsedAt = DateTime.UtcNow,
                        IsVerifiedByUser = false
                    };
                    _context.CvParsers.Add(parser);

                    var evaluation = new CvEvaluation
                    {
                        CvId = cv.Id,
                        CvScore = analysis.CvScore,
                        StrengthsJson = JsonSerializer.Serialize(analysis.Strengths ?? []),
                        WeaknessesJson = JsonSerializer.Serialize(analysis.Weaknesses ?? []),
                        ImprovementsJson = JsonSerializer.Serialize(analysis.ImprovementSuggestions ?? []),
                        MissingSkillsJson = "[]",
                        ModelVersion = "AI-v1",
                        GeneratedAt = DateTime.UtcNow
                    };
                    _context.CvEvaluations.Add(evaluation);

                    cv.ParseStatus = "Parsed";
                    cv.ParsedAt = DateTime.UtcNow;

                    await _context.SaveChangesAsync(cancellationToken);

                    _logger?.LogInformation(
                        "Automatically scanned and parsed CV {CvId} for candidate {CandidateId}. Score: {Score}",
                        cv.Id, candidate.Id, analysis.CvScore);
                }
                else
                {
                    _logger?.LogWarning(
                        "AI CV analysis returned non-success for CV {CvId}: {Error}",
                        cv.Id, aiResult.ErrorMessage);
                }
            }
            catch (Exception ex)
            {
                _logger?.LogWarning(ex, "Background AI CV parsing failed for CV {CvId}. Leaving as Pending.", cv.Id);
            }
        }

        return ServiceResult.Success(MapToCvResponse(cv));
    }

    public async Task<ServiceResult<IReadOnlyList<CvResponse>>> GetCvsAsync(
        Guid userId, CancellationToken cancellationToken = default)
    {
        var candidate = await FindByUserIdAsync(userId, cancellationToken);
        if (candidate is null)
            return ServiceResult.NotFound<IReadOnlyList<CvResponse>>("Candidate profile not found.");

        var cvs = await _context.CandidateCvs
            .Where(cv => cv.CandidateId == candidate.Id && !cv.IsDeleted)
            .OrderByDescending(cv => cv.CreatedAt)
            .ToListAsync(cancellationToken);

        return ServiceResult.Success<IReadOnlyList<CvResponse>>(
            cvs.Select(MapToCvResponse).ToList());
    }

    public async Task<ServiceResult<CvResponse>> GetCvByIdAsync(
        Guid userId, Guid cvId, CancellationToken cancellationToken = default)
    {
        var (cv, error) = await FindCvWithOwnershipAsync(userId, cvId, cancellationToken);
        if (error is not null) return error;
        return ServiceResult.Success(MapToCvResponse(cv!));
    }

    public async Task<ServiceResult<CvResponse>> UpdateCvTitleAsync(
        Guid userId, Guid cvId, string title, CancellationToken cancellationToken = default)
    {
        var (cv, error) = await FindCvWithOwnershipAsync(userId, cvId, cancellationToken);
        if (error is not null) return error;

        cv!.Title = title;
        await _context.SaveChangesAsync(cancellationToken);
        return ServiceResult.Success(MapToCvResponse(cv));
    }

    public async Task<ServiceResult<bool>> DeleteCvAsync(
        Guid userId, Guid cvId, CancellationToken cancellationToken = default)
    {
        var (cv, error) = await FindCvWithOwnershipAsync(userId, cvId, cancellationToken);
        if (error is not null) return ServiceResult.Failure<bool>(error.ErrorMessage!, error.ErrorType);

        var oldPublicId = cv!.PublicId;
        cv.IsDeleted = true;

        // If deleted CV was primary, reassign to the next most recent CV atomically
        if (cv.IsPrimary)
        {
            var candidate = await FindByUserIdAsync(userId, cancellationToken);
            if (candidate is null)
                return ServiceResult.NotFound<bool>("Candidate profile not found.");

            // Use an explicit database transaction to ensure atomicity and avoid unique index collision
            await using var transaction = await _context.Database.BeginTransactionAsync(cancellationToken);
            try
            {
                // Step 1: Reset primary flag on deleted CV and persist to release unique filtered index
                cv.IsPrimary = false;
                await _context.SaveChangesAsync(cancellationToken);

                // Step 2: Promote next most recent non-deleted CV to primary if available
                var next = await _context.CandidateCvs
                    .Where(c => c.CandidateId == candidate.Id && c.Id != cvId && !c.IsDeleted)
                    .OrderByDescending(c => c.CreatedAt)
                    .FirstOrDefaultAsync(cancellationToken);

                if (next is not null)
                {
                    next.IsPrimary = true;
                    await _context.SaveChangesAsync(cancellationToken);
                }

                await transaction.CommitAsync(cancellationToken);
            }
            catch
            {
                await transaction.RollbackAsync(cancellationToken);
                throw;
            }
        }
        else
        {
            await _context.SaveChangesAsync(cancellationToken);
        }

        // Best-effort cleanup on Cloudinary after DB is committed
        if (!string.IsNullOrEmpty(oldPublicId))
            try { await _fileStorage.DeleteDocumentAsync(oldPublicId, cancellationToken); } catch { }

        return ServiceResult.Success(true);
    }

    public async Task<ServiceResult<CvResponse>> SelectPrimaryCvAsync(
        Guid userId, Guid cvId, CancellationToken cancellationToken = default)
    {
        var (cv, error) = await FindCvWithOwnershipAsync(userId, cvId, cancellationToken);
        if (error is not null) return error;

        // Fast-path: If the selected CV is already primary, return immediately (Idempotent)
        if (cv!.IsPrimary)
            return ServiceResult.Success(MapToCvResponse(cv));

        var candidate = await FindByUserIdAsync(userId, cancellationToken);
        if (candidate is null)
            return ServiceResult.NotFound<CvResponse>("Candidate profile not found.");

        // Wrap operations in an explicit database transaction to guarantee atomicity and
        // prevent Unique Filtered Index collision (IX_CandidateCvs_CandidateId_IsPrimary)
        await using var transaction = await _context.Database.BeginTransactionAsync(cancellationToken);
        try
        {
            // Step 1: Unset any existing primary CV(s) for the candidate and persist immediately
            // to release PostgreSQL unique filtered index constraint
            var currentPrimaries = await _context.CandidateCvs
                .Where(c => c.CandidateId == candidate.Id && c.Id != cvId && c.IsPrimary && !c.IsDeleted)
                .ToListAsync(cancellationToken);

            foreach (var p in currentPrimaries)
            {
                p.IsPrimary = false;
            }

            if (currentPrimaries.Count > 0)
            {
                await _context.SaveChangesAsync(cancellationToken);
            }

            // Step 2: Assign target CV as primary and persist
            cv.IsPrimary = true;
            await _context.SaveChangesAsync(cancellationToken);

            // Commit the entire atomic unit of work
            await transaction.CommitAsync(cancellationToken);
            return ServiceResult.Success(MapToCvResponse(cv));
        }
        catch
        {
            await transaction.RollbackAsync(cancellationToken);
            throw;
        }
    }

    // -------------------------------------------------------------------------
    // Certificates (P2-UC04)
    // -------------------------------------------------------------------------

    public async Task<ServiceResult<CertificateResponse>> AddCertificateAsync(
        Guid userId, CertificateDto dto, CancellationToken cancellationToken = default)
    {
        var candidate = await FindByUserIdAsync(userId, cancellationToken);
        if (candidate is null)
            return ServiceResult.NotFound<CertificateResponse>("Candidate profile not found.");

        var cert = new Certificate
        {
            CandidateId = candidate.Id,
            Name = dto.Name,
            Organization = dto.Organization,
            IssueDate = dto.IssueDate,
            ExpirationDate = dto.ExpirationDate,
            CredentialUrl = dto.CredentialUrl,
            Description = dto.Description,
        };

        _context.Certificates.Add(cert);
        await _context.SaveChangesAsync(cancellationToken);
        return ServiceResult.Success(MapToCertificateResponse(cert));
    }

    public async Task<ServiceResult<CertificateResponse>> UpdateCertificateAsync(
        Guid userId, Guid certificateId, CertificateDto dto, CancellationToken cancellationToken = default)
    {
        var (cert, error) = await FindCertificateWithOwnershipAsync(userId, certificateId, cancellationToken);
        if (error is not null) return error;

        cert!.Name = dto.Name;
        cert.Organization = dto.Organization;
        cert.IssueDate = dto.IssueDate;
        cert.ExpirationDate = dto.ExpirationDate;
        cert.CredentialUrl = dto.CredentialUrl;
        cert.Description = dto.Description;

        await _context.SaveChangesAsync(cancellationToken);
        return ServiceResult.Success(MapToCertificateResponse(cert));
    }

    public async Task<ServiceResult<bool>> DeleteCertificateAsync(
        Guid userId, Guid certificateId, CancellationToken cancellationToken = default)
    {
        var (cert, error) = await FindCertificateWithOwnershipAsync(userId, certificateId, cancellationToken);
        if (error is not null) return ServiceResult.Failure<bool>(error.ErrorMessage!, error.ErrorType);

        cert!.IsDeleted = true;
        await _context.SaveChangesAsync(cancellationToken);
        return ServiceResult.Success(true);
    }

    // -------------------------------------------------------------------------
    // Projects (P2-UC04)
    // -------------------------------------------------------------------------

    public async Task<ServiceResult<ProjectResponse>> AddProjectAsync(
        Guid userId, ProjectDto dto, CancellationToken cancellationToken = default)
    {
        var candidate = await FindByUserIdAsync(userId, cancellationToken);
        if (candidate is null)
            return ServiceResult.NotFound<ProjectResponse>("Candidate profile not found.");

        var project = new Project
        {
            CandidateId = candidate.Id,
            Name = dto.Name,
            Role = dto.Role,
            StartDate = dto.StartDate,
            EndDate = dto.IsCurrent ? null : dto.EndDate,
            IsCurrent = dto.IsCurrent,
            ProjectUrl = dto.ProjectUrl,
            Description = dto.Description,
        };

        _context.Projects.Add(project);
        await _context.SaveChangesAsync(cancellationToken);
        return ServiceResult.Success(MapToProjectResponse(project));
    }

    public async Task<ServiceResult<ProjectResponse>> UpdateProjectAsync(
        Guid userId, Guid projectId, ProjectDto dto, CancellationToken cancellationToken = default)
    {
        var (project, error) = await FindProjectWithOwnershipAsync(userId, projectId, cancellationToken);
        if (error is not null) return error;

        project!.Name = dto.Name;
        project.Role = dto.Role;
        project.StartDate = dto.StartDate;
        project.EndDate = dto.IsCurrent ? null : dto.EndDate;
        project.IsCurrent = dto.IsCurrent;
        project.ProjectUrl = dto.ProjectUrl;
        project.Description = dto.Description;

        await _context.SaveChangesAsync(cancellationToken);
        return ServiceResult.Success(MapToProjectResponse(project));
    }

    public async Task<ServiceResult<bool>> DeleteProjectAsync(
        Guid userId, Guid projectId, CancellationToken cancellationToken = default)
    {
        var (project, error) = await FindProjectWithOwnershipAsync(userId, projectId, cancellationToken);
        if (error is not null) return ServiceResult.Failure<bool>(error.ErrorMessage!, error.ErrorType);

        project!.IsDeleted = true;
        await _context.SaveChangesAsync(cancellationToken);
        return ServiceResult.Success(true);
    }

    // -------------------------------------------------------------------------
    // Structured CV Data & AI Analysis (P2-UC04, P2-UC05, P2-UC06)
    // -------------------------------------------------------------------------

    public async Task<ServiceResult<CvStructuredDataResponse>> GetStructuredCvDataAsync(
        Guid userId, Guid cvId, CancellationToken cancellationToken = default)
    {
        var (cv, error) = await FindCvWithOwnershipAsync(userId, cvId, cancellationToken);
        if (error is not null) return ServiceResult.Failure<CvStructuredDataResponse>(error.ErrorMessage ?? "CV not found.", error.ErrorType);

        var parser = await _context.CvParsers
            .FirstOrDefaultAsync(p => p.CvId == cvId, cancellationToken);

        StructuredCvDataDto data;

        if (parser is null || string.IsNullOrWhiteSpace(parser.ParsedDataJson))
        {
            // Auto-populate initial baseline structured data from candidate profile
            var candidate = await _context.Candidates
                .Include(c => c.Skills).ThenInclude(cs => cs.Skill)
                .Include(c => c.Experiences)
                .Include(c => c.Educations)
                .Include(c => c.Projects)
                .FirstOrDefaultAsync(c => c.UserId == userId, cancellationToken);

            var email = await GetUserEmailAsync(userId);

            data = new StructuredCvDataDto(
                candidate?.FullName ?? string.Empty,
                email,
                candidate?.Phone,
                candidate?.Summary,
                candidate?.Skills.Select(s => s.Skill?.Name ?? string.Empty).Where(s => !string.IsNullOrEmpty(s)).ToList() ?? [],
                candidate?.Experiences.Where(e => !e.IsDeleted).Select(e => new CvExperienceDto(e.CompanyName, e.Position, e.StartDate, e.EndDate, e.IsCurrent, e.Description)).ToList() ?? [],
                candidate?.Educations.Where(e => !e.IsDeleted).Select(e => new CvEducationDto(e.School, e.Degree, e.Major, e.StartYear, e.EndYear, e.Description)).ToList() ?? [],
                candidate?.Projects.Where(p => !p.IsDeleted).Select(p => new CvProjectDto(p.Name, p.Role, p.StartDate, p.EndDate, p.IsCurrent, p.Description, null)).ToList() ?? []
            );

            var json = JsonSerializer.Serialize(data);

            if (parser is null)
            {
                parser = new CvParser
                {
                    CvId = cv!.Id,
                    RawText = json,
                    ParsedDataJson = json,
                    ModelVersion = "1.0",
                    ParsedAt = DateTime.UtcNow,
                    IsVerifiedByUser = false
                };
                _context.CvParsers.Add(parser);
            }
            else
            {
                parser.ParsedDataJson = json;
                if (string.IsNullOrWhiteSpace(parser.RawText))
                {
                    parser.RawText = json;
                }
            }

            cv!.ParseStatus = "Parsed";
            cv.ParsedAt = DateTime.UtcNow;

            await _context.SaveChangesAsync(cancellationToken);
        }
        else
        {
            try
            {
                data = JsonSerializer.Deserialize<StructuredCvDataDto>(parser.ParsedDataJson) ?? FallbackEmptyStructuredData();
            }
            catch
            {
                data = FallbackEmptyStructuredData();
            }
        }

        var response = new CvStructuredDataResponse(
            cv!.Id,
            cv.Title,
            cv.FileUrl,
            cv.ParseStatus,
            parser.IsVerifiedByUser,
            parser.VerifiedAt,
            data,
            parser.RawText
        );

        return ServiceResult.Success(response);
    }

    public async Task<ServiceResult<CvStructuredDataResponse>> UpdateStructuredCvDataAsync(
        Guid userId, Guid cvId, UpdateStructuredCvDataRequest request, CancellationToken cancellationToken = default)
    {
        var (cv, error) = await FindCvWithOwnershipAsync(userId, cvId, cancellationToken);
        if (error is not null) return ServiceResult.Failure<CvStructuredDataResponse>(error.ErrorMessage ?? "CV not found.", error.ErrorType);

        var parser = await _context.CvParsers
            .FirstOrDefaultAsync(p => p.CvId == cvId, cancellationToken);

        var json = JsonSerializer.Serialize(request.Data);

        if (parser is null)
        {
            parser = new CvParser
            {
                CvId = cv!.Id,
                RawText = json,
                ParsedDataJson = json,
                ModelVersion = "1.0",
                ParsedAt = DateTime.UtcNow,
                IsVerifiedByUser = true,
                VerifiedAt = DateTime.UtcNow
            };
            _context.CvParsers.Add(parser);
        }
        else
        {
            if (string.IsNullOrWhiteSpace(parser.RawText))
            {
                parser.RawText = parser.ParsedDataJson ?? json;
            }
            parser.ParsedDataJson = json;
            parser.IsVerifiedByUser = true;
            parser.VerifiedAt = DateTime.UtcNow;
        }

        cv!.ParseStatus = "Parsed";
        await _context.SaveChangesAsync(cancellationToken);

        var response = new CvStructuredDataResponse(
            cv.Id,
            cv.Title,
            cv.FileUrl,
            cv.ParseStatus,
            parser.IsVerifiedByUser,
            parser.VerifiedAt,
            request.Data,
            parser.RawText
        );

        return ServiceResult.Success(response);
    }

    public async Task<ServiceResult<CvStructuredDataResponse>> RevertStructuredCvDataAsync(
        Guid userId, Guid cvId, CancellationToken cancellationToken = default)
    {
        var (cv, error) = await FindCvWithOwnershipAsync(userId, cvId, cancellationToken);
        if (error is not null) return ServiceResult.Failure<CvStructuredDataResponse>(error.ErrorMessage ?? "CV not found.", error.ErrorType);

        var parser = await _context.CvParsers
            .FirstOrDefaultAsync(p => p.CvId == cvId, cancellationToken);

        if (parser is null || string.IsNullOrWhiteSpace(parser.RawText))
            return ServiceResult.Failure<CvStructuredDataResponse>("No initial parsed data available to revert to.", ServiceErrorType.Validation);

        parser.ParsedDataJson = parser.RawText;
        parser.IsVerifiedByUser = false;
        parser.VerifiedAt = null;

        await _context.SaveChangesAsync(cancellationToken);

        StructuredCvDataDto data;
        try
        {
            data = JsonSerializer.Deserialize<StructuredCvDataDto>(parser.ParsedDataJson) ?? FallbackEmptyStructuredData();
        }
        catch
        {
            data = FallbackEmptyStructuredData();
        }

        var response = new CvStructuredDataResponse(
            cv!.Id,
            cv.Title,
            cv.FileUrl,
            cv.ParseStatus,
            parser.IsVerifiedByUser,
            parser.VerifiedAt,
            data,
            parser.RawText
        );

        return ServiceResult.Success(response);
    }

    public async Task<ServiceResult<CvAnalysisResponse>> GetCvAnalysisAsync(
        Guid userId, Guid cvId, CancellationToken cancellationToken = default)
    {
        var (cv, error) = await FindCvWithOwnershipAsync(userId, cvId, cancellationToken);
        if (error is not null) return ServiceResult.Failure<CvAnalysisResponse>(error.ErrorMessage ?? "CV not found.", error.ErrorType);

        var evaluation = await _context.CvEvaluations
            .FirstOrDefaultAsync(e => e.CvId == cvId, cancellationToken);

        if (evaluation is null)
        {
            // Auto-analyze CV if not yet evaluated
            return await AnalyzeCvAsync(userId, cvId, cancellationToken);
        }

        var strengths = DeserializeList(evaluation.StrengthsJson);
        var weaknesses = DeserializeList(evaluation.WeaknessesJson);
        var improvements = DeserializeList(evaluation.ImprovementsJson);
        var missingSkills = DeserializeList(evaluation.MissingSkillsJson);

        var response = new CvAnalysisResponse(
            cv!.Id,
            evaluation.CvScore ?? 0,
            strengths,
            weaknesses,
            improvements,
            missingSkills,
            evaluation.ModelVersion,
            evaluation.GeneratedAt
        );

        return ServiceResult.Success(response);
    }

    public async Task<ServiceResult<CvAnalysisResponse>> AnalyzeCvAsync(
        Guid userId, Guid cvId, CancellationToken cancellationToken = default)
    {
        var (cv, error) = await FindCvWithOwnershipAsync(userId, cvId, cancellationToken);
        if (error is not null) return ServiceResult.Failure<CvAnalysisResponse>(error.ErrorMessage ?? "CV not found.", error.ErrorType);

        // Load structured data
        var structuredDataResult = await GetStructuredCvDataAsync(userId, cvId, cancellationToken);
        if (!structuredDataResult.IsSuccess || structuredDataResult.Data is null)
            return ServiceResult.Failure<CvAnalysisResponse>("Could not load structured CV data for analysis.");

        var data = structuredDataResult.Data.Data;

        // Perform Quality Evaluation via AI Service with fallback to Rule-based Evaluation
        int score = 0;
        IReadOnlyList<string> strengths = [];
        IReadOnlyList<string> weaknesses = [];
        IReadOnlyList<string> improvements = [];
        IReadOnlyList<string> missingSkills = [];
        string modelVersion = "1.0";

        var parser = await _context.CvParsers.FirstOrDefaultAsync(p => p.CvId == cvId, cancellationToken);
        var rawTextToAnalyze = parser?.RawText ?? JsonSerializer.Serialize(data);

        bool aiSuccess = false;
        if (_aiCvClient != null && !string.IsNullOrWhiteSpace(rawTextToAnalyze))
        {
            try
            {
                var aiResult = await _aiCvClient.AnalyzeTextAsync(
                    rawTextToAnalyze, cv!.CandidateId.ToString(), cancellationToken: cancellationToken);

                if (aiResult.IsSuccess && aiResult.Data != null)
                {
                    score = aiResult.Data.CvScore;
                    strengths = aiResult.Data.Strengths ?? [];
                    weaknesses = aiResult.Data.Weaknesses ?? [];
                    improvements = aiResult.Data.ImprovementSuggestions ?? [];
                    missingSkills = [];
                    modelVersion = "AI-v1";
                    aiSuccess = true;
                }
            }
            catch (Exception ex)
            {
                _logger?.LogWarning(ex, "AI CV text re-analysis failed for CV {CvId}. Falling back to rule-based evaluation.", cvId);
            }
        }

        if (!aiSuccess)
        {
            var ruleEval = EvaluateCvQuality(data);
            score = ruleEval.Score;
            strengths = ruleEval.Strengths;
            weaknesses = ruleEval.Weaknesses;
            improvements = ruleEval.Improvements;
            missingSkills = ruleEval.MissingSkills;
        }

        var evaluation = await _context.CvEvaluations
            .FirstOrDefaultAsync(e => e.CvId == cvId, cancellationToken);

        if (evaluation is null)
        {
            evaluation = new CvEvaluation
            {
                CvId = cv!.Id,
                CvScore = score,
                StrengthsJson = JsonSerializer.Serialize(strengths),
                WeaknessesJson = JsonSerializer.Serialize(weaknesses),
                ImprovementsJson = JsonSerializer.Serialize(improvements),
                MissingSkillsJson = JsonSerializer.Serialize(missingSkills),
                ModelVersion = modelVersion,
                GeneratedAt = DateTime.UtcNow
            };
            _context.CvEvaluations.Add(evaluation);
        }
        else
        {
            evaluation.CvScore = score;
            evaluation.StrengthsJson = JsonSerializer.Serialize(strengths);
            evaluation.WeaknessesJson = JsonSerializer.Serialize(weaknesses);
            evaluation.ImprovementsJson = JsonSerializer.Serialize(improvements);
            evaluation.MissingSkillsJson = JsonSerializer.Serialize(missingSkills);
            evaluation.ModelVersion = modelVersion;
            evaluation.GeneratedAt = DateTime.UtcNow;
        }

        await _context.SaveChangesAsync(cancellationToken);

        var response = new CvAnalysisResponse(
            cv!.Id,
            score,
            strengths,
            weaknesses,
            improvements,
            missingSkills,
            evaluation.ModelVersion,
            evaluation.GeneratedAt
        );

        return ServiceResult.Success(response);
    }

    public async Task<ServiceResult<bool>> ProcessAiCvCallbackAsync(
        Guid cvId, AiCvCallbackRequest request, CancellationToken cancellationToken = default)
    {
        var cv = await _context.CandidateCvs
            .FirstOrDefaultAsync(c => c.Id == cvId && !c.IsDeleted, cancellationToken);

        if (cv is null)
            return ServiceResult.NotFound<bool>("CV not found.");

        cv.ParseStatus = request.ErrorMessage != null ? "Failed" : "Parsed";
        cv.ParsedAt = DateTime.UtcNow;

        if (request.StructuredData != null)
        {
            var json = JsonSerializer.Serialize(request.StructuredData);
            var parser = await _context.CvParsers.FirstOrDefaultAsync(p => p.CvId == cvId, cancellationToken);
            if (parser is null)
            {
                parser = new CvParser
                {
                    CvId = cv.Id,
                    RawText = request.RawText ?? json,
                    ParsedDataJson = json,
                    ModelVersion = "AI-v1",
                    ParsedAt = DateTime.UtcNow,
                    ErrorMessage = request.ErrorMessage
                };
                _context.CvParsers.Add(parser);
            }
            else
            {
                parser.RawText = request.RawText ?? parser.RawText ?? json;
                parser.ParsedDataJson = json;
                parser.ParsedAt = DateTime.UtcNow;
                parser.ErrorMessage = request.ErrorMessage;
            }
        }

        if (request.CvScore.HasValue)
        {
            var evaluation = await _context.CvEvaluations.FirstOrDefaultAsync(e => e.CvId == cvId, cancellationToken);
            if (evaluation is null)
            {
                evaluation = new CvEvaluation
                {
                    CvId = cv.Id,
                    CvScore = request.CvScore.Value,
                    StrengthsJson = JsonSerializer.Serialize(request.Strengths ?? []),
                    WeaknessesJson = JsonSerializer.Serialize(request.Weaknesses ?? []),
                    ImprovementsJson = JsonSerializer.Serialize(request.Improvements ?? []),
                    MissingSkillsJson = JsonSerializer.Serialize(request.MissingSkills ?? []),
                    ModelVersion = "AI-v1",
                    GeneratedAt = DateTime.UtcNow
                };
                _context.CvEvaluations.Add(evaluation);
            }
            else
            {
                evaluation.CvScore = request.CvScore.Value;
                evaluation.StrengthsJson = JsonSerializer.Serialize(request.Strengths ?? []);
                evaluation.WeaknessesJson = JsonSerializer.Serialize(request.Weaknesses ?? []);
                evaluation.ImprovementsJson = JsonSerializer.Serialize(request.Improvements ?? []);
                evaluation.MissingSkillsJson = JsonSerializer.Serialize(request.MissingSkills ?? []);
                evaluation.GeneratedAt = DateTime.UtcNow;
            }
        }

        await _context.SaveChangesAsync(cancellationToken);
        return ServiceResult.Success(true);
    }

    // -------------------------------------------------------------------------
    // Private helpers — reusable across all methods
    // -------------------------------------------------------------------------

    // Single point for candidate lookup — reused by every operation
    private async Task<Candidate?> FindByUserIdAsync(Guid userId, CancellationToken ct)
        => await _context.Candidates
            .FirstOrDefaultAsync(c => c.UserId == userId && !c.IsDeleted, ct);

    // IDOR guard for Education: verifies the record exists AND belongs to the current user
    private async Task<(Education? education, ServiceResult<EducationResponse>? error)>
        FindEducationWithOwnershipAsync(Guid userId, Guid educationId, CancellationToken ct)
    {
        var candidate = await FindByUserIdAsync(userId, ct);
        if (candidate is null)
            return (null, ServiceResult.NotFound<EducationResponse>("Candidate profile not found."));

        var education = await _context.Educations
            .FirstOrDefaultAsync(e => e.Id == educationId && !e.IsDeleted, ct);

        if (education is null)
            return (null, ServiceResult.NotFound<EducationResponse>("Education entry not found."));

        // IDOR check: ensure the record belongs to the authenticated user's candidate
        if (education.CandidateId != candidate.Id)
            return (null, ServiceResult.Forbidden<EducationResponse>("Access denied."));

        return (education, null);
    }

    // IDOR guard for Experience
    private async Task<(Experience? experience, ServiceResult<ExperienceResponse>? error)>
        FindExperienceWithOwnershipAsync(Guid userId, Guid experienceId, CancellationToken ct)
    {
        var candidate = await FindByUserIdAsync(userId, ct);
        if (candidate is null)
            return (null, ServiceResult.NotFound<ExperienceResponse>("Candidate profile not found."));

        var experience = await _context.Experiences
            .FirstOrDefaultAsync(e => e.Id == experienceId && !e.IsDeleted, ct);

        if (experience is null)
            return (null, ServiceResult.NotFound<ExperienceResponse>("Experience entry not found."));

        if (experience.CandidateId != candidate.Id)
            return (null, ServiceResult.Forbidden<ExperienceResponse>("Access denied."));

        return (experience, null);
    }

    private async Task<string> GetUserEmailAsync(Guid userId)
    {
        var email = await _identityService.GetUserEmailAsync(userId);
        return email ?? string.Empty;
    }

    private async Task<(CandidateCv? cv, ServiceResult<CvResponse>? error)>
        FindCvWithOwnershipAsync(Guid userId, Guid cvId, CancellationToken ct)
    {
        var candidate = await FindByUserIdAsync(userId, ct);
        if (candidate is null)
            return (null, ServiceResult.NotFound<CvResponse>("Candidate profile not found."));

        var cv = await _context.CandidateCvs
            .FirstOrDefaultAsync(c => c.Id == cvId && !c.IsDeleted, ct);
        if (cv is null)
            return (null, ServiceResult.NotFound<CvResponse>("CV not found."));

        if (cv.CandidateId != candidate.Id)
            return (null, ServiceResult.Forbidden<CvResponse>("Access denied."));

        return (cv, null);
    }

    private async Task<(Certificate? cert, ServiceResult<CertificateResponse>? error)>
        FindCertificateWithOwnershipAsync(Guid userId, Guid certId, CancellationToken ct)
    {
        var candidate = await FindByUserIdAsync(userId, ct);
        if (candidate is null)
            return (null, ServiceResult.NotFound<CertificateResponse>("Candidate profile not found."));

        var cert = await _context.Certificates
            .FirstOrDefaultAsync(c => c.Id == certId && !c.IsDeleted, ct);
        if (cert is null)
            return (null, ServiceResult.NotFound<CertificateResponse>("Certificate not found."));

        if (cert.CandidateId != candidate.Id)
            return (null, ServiceResult.Forbidden<CertificateResponse>("Access denied."));

        return (cert, null);
    }

    private async Task<(Project? project, ServiceResult<ProjectResponse>? error)>
        FindProjectWithOwnershipAsync(Guid userId, Guid projectId, CancellationToken ct)
    {
        var candidate = await FindByUserIdAsync(userId, ct);
        if (candidate is null)
            return (null, ServiceResult.NotFound<ProjectResponse>("Candidate profile not found."));

        var project = await _context.Projects
            .FirstOrDefaultAsync(p => p.Id == projectId && !p.IsDeleted, ct);
        if (project is null)
            return (null, ServiceResult.NotFound<ProjectResponse>("Project not found."));

        if (project.CandidateId != candidate.Id)
            return (null, ServiceResult.Forbidden<ProjectResponse>("Access denied."));

        return (project, null);
    }

    // -------------------------------------------------------------------------
    // Private static mappers
    // -------------------------------------------------------------------------

    private static CandidateProfileResponse MapToProfileResponse(Candidate c, string email) => new(
        c.Id, c.UserId, email, c.FullName, c.Phone, c.Address, c.AvatarUrl,
        c.DateOfBirth, c.Gender, c.Summary, c.DesiredPosition,
        c.DesiredSalaryMin, c.DesiredSalaryMax, c.ProfileUpdatedAt, c.CreatedAt);

    private static CandidateFullProfileResponse MapToFullProfileResponse(Candidate c, string email) => new()
    {
        Id = c.Id,
        UserId = c.UserId,
        Email = email,
        FullName = c.FullName,
        Phone = c.Phone,
        Address = c.Address,
        AvatarUrl = c.AvatarUrl,
        DateOfBirth = c.DateOfBirth,
        Gender = c.Gender,
        Summary = c.Summary,
        DesiredPosition = c.DesiredPosition,
        DesiredSalaryMin = c.DesiredSalaryMin,
        DesiredSalaryMax = c.DesiredSalaryMax,
        ProfileUpdatedAt = c.ProfileUpdatedAt,
        CreatedAt = c.CreatedAt,
        Educations = c.Educations.Select(MapToEducationResponse).ToList(),
        Experiences = c.Experiences.Select(MapToExperienceResponse).ToList(),
        Skills = c.Skills.Select(cs => MapToSkillResponse(cs, cs.Skill)).ToList(),
        Certificates = c.Certificates.Select(MapToCertificateResponse).ToList(),
        Projects = c.Projects.Select(MapToProjectResponse).ToList(),
        CVs = c.CVs.Select(MapToCvResponse).ToList(),
    };

    private static EducationResponse MapToEducationResponse(Education e) => new(
        e.Id, e.School, e.Degree, e.Major, e.StartYear, e.EndYear, e.Description);

    private static ExperienceResponse MapToExperienceResponse(Experience e) => new(
        e.Id, e.CompanyName, e.Position, e.StartDate, e.EndDate, e.IsCurrent, e.Description);

    private static CandidateSkillResponse MapToSkillResponse(CandidateSkill cs, Skill skill) => new(
        skill.Id, skill.Name, skill.Category, cs.Level.ToString(), cs.Years);

    private static CvResponse MapToCvResponse(CandidateCv cv) => new(
        cv.Id, cv.CandidateId, cv.Title, cv.FileUrl, cv.FileType,
        cv.FileSizeBytes, cv.IsPrimary, cv.CreatedAt);

    private static CertificateResponse MapToCertificateResponse(Certificate c) => new(
        c.Id, c.Name, c.Organization, c.IssueDate, c.ExpirationDate, c.CredentialUrl, c.Description);

    private static ProjectResponse MapToProjectResponse(Project p) => new(
        p.Id, p.Name, p.Role, p.StartDate, p.EndDate, p.IsCurrent, p.ProjectUrl, p.Description);

    private static (int Score, List<string> Strengths, List<string> Weaknesses, List<string> Improvements, List<string> MissingSkills)
        EvaluateCvQuality(StructuredCvDataDto data)
    {
        int score = 0;
        var strengths = new List<string>();
        var weaknesses = new List<string>();
        var improvements = new List<string>();
        var missingSkills = new List<string>();

        // 1. Career Summary (15 points)
        if (!string.IsNullOrWhiteSpace(data.Summary) && data.Summary.Trim().Length >= 50)
        {
            score += 15;
            strengths.Add("Phần tóm tắt sự nghiệp (Summary) rõ ràng, súc tích và có điểm nhấn.");
        }
        else if (!string.IsNullOrWhiteSpace(data.Summary))
        {
            score += 8;
            improvements.Add("Nên mở rộng phần giới thiệu bản thân chi tiết hơn (3-5 câu nêu rõ mục tiêu và thế mạnh nổi bật).");
        }
        else
        {
            weaknesses.Add("Hồ sơ chưa có đoạn tóm tắt mục tiêu và định hướng sự nghiệp.");
            improvements.Add("Bổ sung mục Career Summary để gây ấn tượng nhanh với nhà tuyển dụng trong 6 giây đầu tiên.");
        }

        // 2. Skills Portfolio (25 points)
        var validSkills = data.Skills.Where(s => !string.IsNullOrWhiteSpace(s)).Distinct().ToList();
        if (validSkills.Count >= 7)
        {
            score += 25;
            strengths.Add($"Danh mục kỹ năng đa dạng và phong phú ({validSkills.Count} kỹ năng chuyên môn).");
        }
        else if (validSkills.Count >= 4)
        {
            score += 18;
            strengths.Add($"Có bộ kỹ năng cơ bản tốt ({validSkills.Count} kỹ năng).");
            improvements.Add("Nên bổ sung thêm các công cụ hỗ trợ hoặc công nghệ liên quan để làm phong phú hồ sơ.");
        }
        else if (validSkills.Count >= 1)
        {
            score += 10;
            weaknesses.Add($"Số lượng kỹ năng còn khá ít ({validSkills.Count} kỹ năng).");
            improvements.Add("Liệt kê thêm các kỹ năng kỹ thuật, thư viện, hoặc kỹ năng mềm liên quan đến chuyên môn.");
        }
        else
        {
            weaknesses.Add("Hồ sơ chưa có kỹ năng chuyên môn nào.");
            improvements.Add("Bổ sung ngay danh sách các kỹ năng then chốt cho vị trí ứng tuyển.");
        }

        // 3. Work Experiences (35 points)
        var validExperiences = data.Experiences.Where(e => !string.IsNullOrWhiteSpace(e.CompanyName)).ToList();
        if (validExperiences.Count >= 2)
        {
            score += 25;
            var detailedCount = validExperiences.Count(e => !string.IsNullOrWhiteSpace(e.Description) && e.Description.Trim().Length >= 40);
            if (detailedCount >= 2)
            {
                score += 10;
                strengths.Add("Lịch sử kinh nghiệm công tác rõ ràng, có phần mô tả công việc và trách nhiệm chi tiết.");
            }
            else
            {
                improvements.Add("Bổ sung thêm mô tả cụ thể về trách nhiệm, công nghệ và kết quả đạt được tại các công ty.");
            }
        }
        else if (validExperiences.Count == 1)
        {
            score += 20;
            if (!string.IsNullOrWhiteSpace(validExperiences[0].Description) && validExperiences[0].Description.Trim().Length >= 40)
            {
                score += 8;
                strengths.Add("Kinh nghiệm làm việc có mô tả rõ ràng.");
            }
            else
            {
                improvements.Add("Bổ sung các gạch đầu dòng mô tả nhiệm vụ và thành tựu tại nơi làm việc.");
            }
        }
        else
        {
            score += 10; // Junior / Fresher baseline
            weaknesses.Add("Chưa có mục kinh nghiệm làm việc thực tế.");
            improvements.Add("Nếu bạn là sinh viên mới ra trường, hãy nhấn mạnh kinh nghiệm thực tập, dự án môn học hoặc hoạt động ngoại khóa.");
        }

        // 4. Education & Academic Background (15 points)
        var validEducations = data.Educations.Where(e => !string.IsNullOrWhiteSpace(e.School)).ToList();
        if (validEducations.Count > 0)
        {
            score += 15;
            strengths.Add("Thông tin trình độ học vấn và cơ sở đào tạo đầy đủ.");
        }
        else
        {
            weaknesses.Add("Chưa cung cấp thông tin học vấn/bằng cấp.");
            improvements.Add("Cập nhật thông tin trường Đại học / Cao đẳng / Trung tâm đào tạo đã theo học.");
        }

        // 5. Projects (10 points)
        var validProjects = data.Projects.Where(p => !string.IsNullOrWhiteSpace(p.Name)).ToList();
        if (validProjects.Count >= 2)
        {
            score += 10;
            strengths.Add($"Có {validProjects.Count} dự án thực tế minh chứng trực quan cho năng lực chuyên môn.");
        }
        else if (validProjects.Count == 1)
        {
            score += 7;
            strengths.Add("Có dự án thực tế minh họa kinh nghiệm.");
            improvements.Add("Bổ sung thêm 1 dự án tiêu biểu khác kèm link demo/Github (nếu có).");
        }
        else
        {
            improvements.Add("Nên bổ sung các dự án cá nhân hoặc dự án nhóm nổi bật để chứng minh kỹ năng áp dụng vào thực tế.");
        }

        score = Math.Clamp(score, 0, 100);

        return (score, strengths, weaknesses, improvements, missingSkills);
    }

    private static StructuredCvDataDto FallbackEmptyStructuredData() =>
        new(string.Empty, null, null, null, [], [], [], []);

    private static List<string> DeserializeList(string? json)
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
