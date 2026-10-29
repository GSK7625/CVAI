using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.Employer.DTOs;

namespace FutureCV.Application.Features.Employer.Interfaces;

public interface IEmployerService
{
    Task<ServiceResult<EmployerProfileResponse>> GetProfileAsync(
        Guid userId, CancellationToken cancellationToken = default);

    Task<ServiceResult<EmployerProfileResponse>> UpdatePersonalInfoAsync(
        Guid userId, UpdateEmployerInfoRequest request, CancellationToken cancellationToken = default);

    Task<ServiceResult<string>> UpdateAvatarAsync(
        Guid userId, FileUploadRequest file, CancellationToken cancellationToken = default);

    Task<ServiceResult<CompanyProfileResponse>> GetCompanyProfileAsync(
        Guid userId, CancellationToken cancellationToken = default);

    Task<ServiceResult<CompanyProfileResponse>> CreateCompanyAsync(
        Guid userId, CreateCompanyRequest request, CancellationToken cancellationToken = default);

    Task<ServiceResult<CompanyProfileResponse>> UpdateCompanyInfoAsync(
        Guid userId, UpdateCompanyInfoRequest request, CancellationToken cancellationToken = default);

    Task<ServiceResult<CompanyProfileResponse>> UpdateCompanyLogoAsync(
        Guid userId, FileUploadRequest file, CancellationToken cancellationToken = default);
}

