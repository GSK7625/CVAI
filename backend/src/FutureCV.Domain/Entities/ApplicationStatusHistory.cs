using FutureCV.Domain.Common;

namespace FutureCV.Domain.Entities;

public class ApplicationStatusHistory : BaseEntity
{
    public Guid ApplicationId { get; set; }
    public string? FromStatus { get; set; }
    public string ToStatus { get; set; } = string.Empty;
    public Guid? ChangedById { get; set; }
    public string? Reason { get; set; }
    public DateTime ChangedAt { get; set; } = DateTime.UtcNow;

    // Navigation property
    public JobApplication Application { get; set; } = null!;
}
