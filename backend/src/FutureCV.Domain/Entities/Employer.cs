using FutureCV.Domain.Common;

namespace FutureCV.Domain.Entities;

public class Employer : BaseEntity
{
    public Guid UserId { get; set; }
    public string FullName { get; set; } = string.Empty;
    public string? Position { get; set; }
    public string? Gender { get; set; }
    public string? Phone { get; set; }
    public string? AvatarUrl { get; set; }
    public string? AvatarPublicId { get; set; }
    
    public Guid CompanyId { get; set; }
    public Company Company { get; set; } = null!;
    public bool IsDeleted { get; set; } = false;
}
