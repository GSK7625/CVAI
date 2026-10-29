using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.Candidate.DTOs;
using FutureCV.Application.Features.Candidate.Interfaces;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace FutureCV.Api.Controllers;

[Authorize(Roles = "Candidate")]
[Route("api/candidate")]
public class CandidateProfileController : ApiControllerBase
{
    private static readonly string[] CvAllowedMimeTypes  = ["application/pdf"];
    private static readonly string[] CvAllowedExtensions = [".pdf"];
    private const long CvMaxSizeBytes = 5 * 1024 * 1024; // 5 MB

    private readonly ICandidateService _candidateService;

    public CandidateProfileController(ICandidateService candidateService)
    {
        _candidateService = candidateService;
    }

    // -------------------------------------------------------------------------
    // Profile
    // -------------------------------------------------------------------------

    [HttpGet("profile")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(CandidateProfileResponse))]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetProfile(CancellationToken cancellationToken)
    {
        var result = await _candidateService.GetProfileAsync(GetCurrentUserId(), cancellationToken);
        return ToHttpResult(result);
    }

    [HttpGet("profile/full")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(CandidateFullProfileResponse))]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetFullProfile(CancellationToken cancellationToken)
    {
        var result = await _candidateService.GetFullProfileAsync(GetCurrentUserId(), cancellationToken);
        return ToHttpResult(result);
    }

    [HttpPut("profile")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(CandidateProfileResponse))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> UpdateProfile(
        [FromBody] UpdateCandidateInfoRequest request, CancellationToken cancellationToken)
    {
        var result = await _candidateService.UpdatePersonalInfoAsync(GetCurrentUserId(), request, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpPost("profile/avatar")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> UpdateAvatar(IFormFile avatar, CancellationToken cancellationToken)
    {
        var validationError = ValidateAvatarFile(avatar);
        if (validationError is not null) return validationError;

        await using var stream = avatar.OpenReadStream();
        var fileUpload = new FileUploadRequest(stream, avatar.FileName, avatar.ContentType, avatar.Length);

        var result = await _candidateService.UpdateAvatarAsync(GetCurrentUserId(), fileUpload, cancellationToken);
        return ToHttpResult(result);
    }

    // -------------------------------------------------------------------------
    // CV Management (P2-UC03, P2-UC07)
    // -------------------------------------------------------------------------

    [HttpPost("cvs")]
    [ProducesResponseType(StatusCodes.Status201Created, Type = typeof(CvResponse))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> UploadCv(
        IFormFile cv, [FromQuery] string? title, CancellationToken cancellationToken)
    {
        var validationError = ValidateCvFile(cv);
        if (validationError is not null) return validationError;

        await using var stream = cv.OpenReadStream();
        var fileUpload = new FileUploadRequest(stream, cv.FileName, cv.ContentType, cv.Length);

        var result = await _candidateService.UploadCvAsync(GetCurrentUserId(), fileUpload, title, cancellationToken);
        return ToHttpResult(result, created: true);
    }

    [HttpGet("cvs")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetCvs(CancellationToken cancellationToken)
    {
        var result = await _candidateService.GetCvsAsync(GetCurrentUserId(), cancellationToken);
        return ToHttpResult(result);
    }

    [HttpGet("cvs/{id:guid}")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(CvResponse))]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetCvById(Guid id, CancellationToken cancellationToken)
    {
        var result = await _candidateService.GetCvByIdAsync(GetCurrentUserId(), id, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpPatch("cvs/{id:guid}/title")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(CvResponse))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> UpdateCvTitle(
        Guid id, [FromBody] UpdateCvTitleRequest request, CancellationToken cancellationToken)
    {
        var result = await _candidateService.UpdateCvTitleAsync(GetCurrentUserId(), id, request.Title, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpDelete("cvs/{id:guid}")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> DeleteCv(Guid id, CancellationToken cancellationToken)
    {
        var result = await _candidateService.DeleteCvAsync(GetCurrentUserId(), id, cancellationToken);
        return result.IsSuccess ? NoContent() : ToHttpResult(result);
    }

    [HttpPut("cvs/{id:guid}/select")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(CvResponse))]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> SelectPrimaryCv(Guid id, CancellationToken cancellationToken)
    {
        var result = await _candidateService.SelectPrimaryCvAsync(GetCurrentUserId(), id, cancellationToken);
        return ToHttpResult(result);
    }

    // -------------------------------------------------------------------------
    // Structured CV Data & AI Analysis (P2-UC04, P2-UC05, P2-UC06)
    // -------------------------------------------------------------------------

    [HttpGet("cvs/{id:guid}/structured-data")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(CvStructuredDataResponse))]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetStructuredCvData(Guid id, CancellationToken cancellationToken)
    {
        var result = await _candidateService.GetStructuredCvDataAsync(GetCurrentUserId(), id, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpPut("cvs/{id:guid}/structured-data")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(CvStructuredDataResponse))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> UpdateStructuredCvData(
        Guid id, [FromBody] UpdateStructuredCvDataRequest request, CancellationToken cancellationToken)
    {
        var result = await _candidateService.UpdateStructuredCvDataAsync(GetCurrentUserId(), id, request, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpPost("cvs/{id:guid}/structured-data/revert")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(CvStructuredDataResponse))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> RevertStructuredCvData(Guid id, CancellationToken cancellationToken)
    {
        var result = await _candidateService.RevertStructuredCvDataAsync(GetCurrentUserId(), id, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpGet("cvs/{id:guid}/analysis")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(CvAnalysisResponse))]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetCvAnalysis(Guid id, CancellationToken cancellationToken)
    {
        var result = await _candidateService.GetCvAnalysisAsync(GetCurrentUserId(), id, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpPost("cvs/{id:guid}/analyze")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(CvAnalysisResponse))]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> AnalyzeCv(Guid id, CancellationToken cancellationToken)
    {
        var result = await _candidateService.AnalyzeCvAsync(GetCurrentUserId(), id, cancellationToken);
        return ToHttpResult(result);
    }

    // -------------------------------------------------------------------------
    // Education
    // -------------------------------------------------------------------------

    [HttpPost("educations")]
    [ProducesResponseType(StatusCodes.Status201Created, Type = typeof(EducationResponse))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> AddEducation(
        [FromBody] EducationDto dto, CancellationToken cancellationToken)
    {
        var result = await _candidateService.AddEducationAsync(GetCurrentUserId(), dto, cancellationToken);
        return ToHttpResult(result, created: true);
    }

    [HttpPut("educations/{id:guid}")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(EducationResponse))]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> UpdateEducation(
        Guid id, [FromBody] EducationDto dto, CancellationToken cancellationToken)
    {
        var result = await _candidateService.UpdateEducationAsync(GetCurrentUserId(), id, dto, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpDelete("educations/{id:guid}")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> DeleteEducation(Guid id, CancellationToken cancellationToken)
    {
        var result = await _candidateService.DeleteEducationAsync(GetCurrentUserId(), id, cancellationToken);
        return result.IsSuccess ? NoContent() : ToHttpResult(result);
    }

    // -------------------------------------------------------------------------
    // Experience
    // -------------------------------------------------------------------------

    [HttpPost("experiences")]
    [ProducesResponseType(StatusCodes.Status201Created, Type = typeof(ExperienceResponse))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> AddExperience(
        [FromBody] ExperienceDto dto, CancellationToken cancellationToken)
    {
        var result = await _candidateService.AddExperienceAsync(GetCurrentUserId(), dto, cancellationToken);
        return ToHttpResult(result, created: true);
    }

    [HttpPut("experiences/{id:guid}")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(ExperienceResponse))]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> UpdateExperience(
        Guid id, [FromBody] ExperienceDto dto, CancellationToken cancellationToken)
    {
        var result = await _candidateService.UpdateExperienceAsync(GetCurrentUserId(), id, dto, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpDelete("experiences/{id:guid}")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> DeleteExperience(Guid id, CancellationToken cancellationToken)
    {
        var result = await _candidateService.DeleteExperienceAsync(GetCurrentUserId(), id, cancellationToken);
        return result.IsSuccess ? NoContent() : ToHttpResult(result);
    }

    // -------------------------------------------------------------------------
    // Skills
    // -------------------------------------------------------------------------

    [HttpPost("skills")]
    [ProducesResponseType(StatusCodes.Status201Created, Type = typeof(CandidateSkillResponse))]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status409Conflict)]
    public async Task<IActionResult> AddSkill(
        [FromBody] CandidateSkillDto dto, CancellationToken cancellationToken)
    {
        var result = await _candidateService.AddSkillAsync(GetCurrentUserId(), dto, cancellationToken);
        return ToHttpResult(result, created: true);
    }

    [HttpDelete("skills/{skillId:guid}")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> RemoveSkill(Guid skillId, CancellationToken cancellationToken)
    {
        var result = await _candidateService.RemoveSkillAsync(GetCurrentUserId(), skillId, cancellationToken);
        return result.IsSuccess ? NoContent() : ToHttpResult(result);
    }

    // -------------------------------------------------------------------------
    // Certificates (P2-UC04)
    // -------------------------------------------------------------------------

    [HttpPost("certificates")]
    [ProducesResponseType(StatusCodes.Status201Created, Type = typeof(CertificateResponse))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> AddCertificate(
        [FromBody] CertificateDto dto, CancellationToken cancellationToken)
    {
        var result = await _candidateService.AddCertificateAsync(GetCurrentUserId(), dto, cancellationToken);
        return ToHttpResult(result, created: true);
    }

    [HttpPut("certificates/{id:guid}")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(CertificateResponse))]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> UpdateCertificate(
        Guid id, [FromBody] CertificateDto dto, CancellationToken cancellationToken)
    {
        var result = await _candidateService.UpdateCertificateAsync(GetCurrentUserId(), id, dto, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpDelete("certificates/{id:guid}")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> DeleteCertificate(Guid id, CancellationToken cancellationToken)
    {
        var result = await _candidateService.DeleteCertificateAsync(GetCurrentUserId(), id, cancellationToken);
        return result.IsSuccess ? NoContent() : ToHttpResult(result);
    }

    // -------------------------------------------------------------------------
    // Projects (P2-UC04)
    // -------------------------------------------------------------------------

    [HttpPost("projects")]
    [ProducesResponseType(StatusCodes.Status201Created, Type = typeof(ProjectResponse))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> AddProject(
        [FromBody] ProjectDto dto, CancellationToken cancellationToken)
    {
        var result = await _candidateService.AddProjectAsync(GetCurrentUserId(), dto, cancellationToken);
        return ToHttpResult(result, created: true);
    }

    [HttpPut("projects/{id:guid}")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(ProjectResponse))]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> UpdateProject(
        Guid id, [FromBody] ProjectDto dto, CancellationToken cancellationToken)
    {
        var result = await _candidateService.UpdateProjectAsync(GetCurrentUserId(), id, dto, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpDelete("projects/{id:guid}")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> DeleteProject(Guid id, CancellationToken cancellationToken)
    {
        var result = await _candidateService.DeleteProjectAsync(GetCurrentUserId(), id, cancellationToken);
        return result.IsSuccess ? NoContent() : ToHttpResult(result);
    }

    // -------------------------------------------------------------------------
    // Private helpers
    // -------------------------------------------------------------------------

    private IActionResult? ValidateCvFile(IFormFile file)
    {
        if (file is null || file.Length == 0)
            return BadRequest(new { message = "Please select a PDF file to upload." });

        var extension = Path.GetExtension(file.FileName).ToLowerInvariant();
        if (!CvAllowedExtensions.Contains(extension))
            return BadRequest(new { message = "Only PDF files are accepted." });

        if (!CvAllowedMimeTypes.Contains(file.ContentType.ToLowerInvariant()))
            return BadRequest(new { message = "Only PDF files are accepted." });

        if (file.Length > CvMaxSizeBytes)
            return BadRequest(new { message = "CV file size must not exceed 5 MB." });

        return null;
    }
}

