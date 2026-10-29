using FutureCV.Application.Common.Interfaces;
using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.Employer.DTOs;
using FutureCV.Application.Features.Employer.Interfaces;

using Microsoft.EntityFrameworkCore;

namespace FutureCV.Application.Features.Employer.Services;
using FutureCV.Domain.Entities;
using FutureCV.Domain.Enums;

public class EmployerService : IEmployerService
{
    private const string AvatarFolder = "avatars/employers";

    private readonly IApplicationDbContext _context;
    private readonly IFileStorage _fileStorage;

    public EmployerService(IApplicationDbContext context, IFileStorage fileStorage)
    {
        _context = context;
        _fileStorage = fileStorage;
    }

    // -------------------------------------------------------------------------
    // Employer personal profile
    // -------------------------------------------------------------------------

    public async Task<ServiceResult<EmployerProfileResponse>> GetProfileAsync(
        Guid userId, CancellationToken cancellationToken = default)
    {
        var employer = await FindByUserIdAsync(userId, cancellationToken);
        if (employer is null)
            return ServiceResult.NotFound<EmployerProfileResponse>("Employer profile not found.");

        return ServiceResult.Success(MapToProfileResponse(employer));
    }

    public async Task<ServiceResult<EmployerProfileResponse>> UpdatePersonalInfoAsync(
        Guid userId, UpdateEmployerInfoRequest request, CancellationToken cancellationToken = default)
    {
        var employer = await FindByUserIdAsync(userId, cancellationToken);
        if (employer is null)
            return ServiceResult.NotFound<EmployerProfileResponse>("Employer profile not found.");

        employer.FullName = request.FullName;
        employer.Position = request.Position;
        employer.Gender   = request.Gender;
        employer.Phone    = request.Phone;

        await _context.SaveChangesAsync(cancellationToken);
        return ServiceResult.Success(MapToProfileResponse(employer));
    }

    public async Task<ServiceResult<string>> UpdateAvatarAsync(
        Guid userId, FileUploadRequest file, CancellationToken cancellationToken = default)
    {
        // 1. Find Employer profile by UserId
        var employer = await FindByUserIdAsync(userId, cancellationToken);
        if (employer is null)
            return ServiceResult.NotFound<string>("Employer profile not found.");

        // 2. Store old AvatarPublicId for cleanup AFTER DB save succeeds
        var oldPublicId = employer.AvatarPublicId;

        // 3. Upload new avatar to Cloudinary
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

        // 4. Update entity with new Cloudinary URL and PublicId
        employer.AvatarUrl      = newPublicUrl;
        employer.AvatarPublicId = newPublicId;

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

        // 6. Only after upload AND DB update succeed: delete old avatar from Cloudinary using old AvatarPublicId
        if (!string.IsNullOrEmpty(oldPublicId))
        {
            try
            {
                await _fileStorage.DeleteAsync(oldPublicId, cancellationToken);
            }
            catch
            {
                // Non-critical: failure to delete old avatar from Cloudinary does not break successful DB update
            }
        }

        return ServiceResult.Success(newPublicUrl);
    }

    // -------------------------------------------------------------------------
    // Company profile
    // -------------------------------------------------------------------------

    public async Task<ServiceResult<CompanyProfileResponse>> GetCompanyProfileAsync(
        Guid userId, CancellationToken cancellationToken = default)
    {
        var employer = await FindByUserIdWithCompanyAsync(userId, cancellationToken);
        if (employer is null)
            return ServiceResult.NotFound<CompanyProfileResponse>("Employer profile not found.");

        return ServiceResult.Success(MapToCompanyResponse(employer.Company));
    }

    public async Task<ServiceResult<CompanyProfileResponse>> CreateCompanyAsync(
        Guid userId, CreateCompanyRequest request, CancellationToken cancellationToken = default)
    {
        var employer = await _context.Employers
            .Include(e => e.Company)
            .FirstOrDefaultAsync(e => e.UserId == userId, cancellationToken);

        if (employer is null)
            return ServiceResult.NotFound<CompanyProfileResponse>("Employer profile not found.");

        if (employer.CompanyId != Guid.Empty)
            return ServiceResult.Conflict<CompanyProfileResponse>("Employer is already linked to a company.");

        var taxCodeExists = await _context.Companies
            .AnyAsync(c => c.TaxCode == request.TaxCode, cancellationToken);
        if (taxCodeExists)
            return ServiceResult.Conflict<CompanyProfileResponse>("Tax code is already registered by another company.");

        var company = new Company
        {
            Name           = request.Name,
            TaxCode        = request.TaxCode,
            Scale          = request.Scale,
            Industry       = request.Industry,
            WebsiteUrl     = request.WebsiteUrl,
            Address        = request.Address,
            Description    = request.Description,
            VerifiedStatus = CompanyVerificationStatus.Pending,
        };

        _context.Companies.Add(company);
        employer.Company = company;

        await _context.SaveChangesAsync(cancellationToken);
        return ServiceResult.Success(MapToCompanyResponse(company));
    }

    public async Task<ServiceResult<CompanyProfileResponse>> UpdateCompanyInfoAsync(
        Guid userId, UpdateCompanyInfoRequest request, CancellationToken cancellationToken = default)
    {
        var employer = await FindByUserIdWithCompanyAsync(userId, cancellationToken);
        if (employer is null)
            return ServiceResult.NotFound<CompanyProfileResponse>("Employer profile not found.");

        var company = employer.Company;

        // TaxCode and VerifiedStatus are intentionally excluded — cannot be changed by employer
        company.Name        = request.Name;
        company.Scale       = request.Scale;
        company.Industry    = request.Industry;
        company.WebsiteUrl  = request.WebsiteUrl;
        company.Address     = request.Address;
        company.Description = request.Description;

        await _context.SaveChangesAsync(cancellationToken);
        return ServiceResult.Success(MapToCompanyResponse(company));
    }

    public async Task<ServiceResult<CompanyProfileResponse>> UpdateCompanyLogoAsync(
        Guid userId, FileUploadRequest file, CancellationToken cancellationToken = default)
    {
        var employer = await FindByUserIdWithCompanyAsync(userId, cancellationToken);
        if (employer is null)
            return ServiceResult.NotFound<CompanyProfileResponse>("Employer profile not found.");

        var company = employer.Company;
        if (employer.CompanyId == Guid.Empty)
            return ServiceResult.Failure<CompanyProfileResponse>("Employer has no linked company.");

        string newPublicUrl;
        try
        {
            (newPublicUrl, _) = await _fileStorage.UploadAsync(
                file.Stream, file.FileName, "logos/companies", cancellationToken);
        }
        catch (Exception ex)
        {
            return ServiceResult.Failure<CompanyProfileResponse>(
                $"Failed to upload company logo: {ex.Message}", ServiceErrorType.Infrastructure);
        }

        company.LogoUrl = newPublicUrl;
        await _context.SaveChangesAsync(cancellationToken);
        return ServiceResult.Success(MapToCompanyResponse(company));
    }

    // -------------------------------------------------------------------------
    // Private helpers
    // -------------------------------------------------------------------------

    private async Task<Employer?> FindByUserIdAsync(Guid userId, CancellationToken ct)
        => await _context.Employers
            .FirstOrDefaultAsync(e => e.UserId == userId, ct);

    // Loads Company navigation property — used when company data is needed
    private async Task<Employer?> FindByUserIdWithCompanyAsync(Guid userId, CancellationToken ct)
        => await _context.Employers
            .Include(e => e.Company)
            .FirstOrDefaultAsync(e => e.UserId == userId, ct);

    // -------------------------------------------------------------------------
    // Private static mappers
    // -------------------------------------------------------------------------

    private static EmployerProfileResponse MapToProfileResponse(Employer e) => new(
        e.Id, e.UserId, e.FullName, e.Position, e.Gender,
        e.Phone, e.AvatarUrl, e.CompanyId, e.CreatedAt);

    private static CompanyProfileResponse MapToCompanyResponse(Company c) => new(
        c.Id, c.Name, c.TaxCode, c.LogoUrl, c.Scale, c.Industry,
        c.WebsiteUrl, c.Address, c.Description,
        c.VerifiedStatus.ToString(), c.VerifiedAt, c.CreatedAt);
}
