using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.Employer.DTOs;
using FutureCV.Application.Features.Employer.Interfaces;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace FutureCV.Api.Controllers;

[Authorize(Roles = "Employer")]
[Route("api/employer")]
public class EmployerProfileController : ApiControllerBase
{
    private readonly IEmployerService _employerService;

    public EmployerProfileController(IEmployerService employerService)
    {
        _employerService = employerService;
    }

    // -------------------------------------------------------------------------
    // Employer personal profile
    // -------------------------------------------------------------------------

    [HttpGet("profile")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(EmployerProfileResponse))]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetProfile(CancellationToken cancellationToken)
    {
        var result = await _employerService.GetProfileAsync(GetCurrentUserId(), cancellationToken);
        return ToHttpResult(result);
    }

    [HttpPut("profile")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(EmployerProfileResponse))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> UpdateProfile(
        [FromBody] UpdateEmployerInfoRequest request, CancellationToken cancellationToken)
    {
        var result = await _employerService.UpdatePersonalInfoAsync(GetCurrentUserId(), request, cancellationToken);
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

        var result = await _employerService.UpdateAvatarAsync(GetCurrentUserId(), fileUpload, cancellationToken);
        return ToHttpResult(result);
    }

    // -------------------------------------------------------------------------
    // Company profile
    // -------------------------------------------------------------------------

    [HttpGet("company")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(CompanyProfileResponse))]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetCompany(CancellationToken cancellationToken)
    {
        var result = await _employerService.GetCompanyProfileAsync(GetCurrentUserId(), cancellationToken);
        return ToHttpResult(result);
    }

    [HttpPost("company")]
    [ProducesResponseType(StatusCodes.Status201Created, Type = typeof(CompanyProfileResponse))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status409Conflict)]
    public async Task<IActionResult> CreateCompany(
        [FromBody] CreateCompanyRequest request, CancellationToken cancellationToken)
    {
        var result = await _employerService.CreateCompanyAsync(GetCurrentUserId(), request, cancellationToken);
        return ToHttpResult(result, created: true);
    }

    [HttpPut("company")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(CompanyProfileResponse))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> UpdateCompany(
        [FromBody] UpdateCompanyInfoRequest request, CancellationToken cancellationToken)
    {
        var result = await _employerService.UpdateCompanyInfoAsync(GetCurrentUserId(), request, cancellationToken);
        return ToHttpResult(result);
    }

    [HttpPost("company/logo")]
    [ProducesResponseType(StatusCodes.Status200OK, Type = typeof(CompanyProfileResponse))]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> UpdateCompanyLogo(IFormFile logo, CancellationToken cancellationToken)
    {
        var validationError = ValidateAvatarFile(logo);
        if (validationError is not null) return validationError;

        await using var stream = logo.OpenReadStream();
        var fileUpload = new FileUploadRequest(stream, logo.FileName, logo.ContentType, logo.Length);

        var result = await _employerService.UpdateCompanyLogoAsync(GetCurrentUserId(), fileUpload, cancellationToken);
        return ToHttpResult(result);
    }
}

