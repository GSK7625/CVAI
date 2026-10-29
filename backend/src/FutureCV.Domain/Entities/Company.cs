using FutureCV.Domain.Common;
using FutureCV.Domain.Enums;

namespace FutureCV.Domain.Entities;

public class Company : BaseEntity
{
    public string Name { get; set; } = string.Empty;
    public string TaxCode { get; set; } = string.Empty;
    public string? LogoUrl { get; set; }
    public string? Scale { get; set; }
    public string? Industry { get; set; }
    public string? WebsiteUrl { get; set; }
    public string? Address { get; set; }
    public string? Description { get; set; }
    public CompanyVerificationStatus VerifiedStatus { get; set; } = CompanyVerificationStatus.Pending;
    public DateTimeOffset? VerifiedAt { get; set; }
    public bool IsDeleted { get; set; } = false;
}
