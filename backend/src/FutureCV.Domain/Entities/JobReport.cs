using FutureCV.Domain.Common;
using FutureCV.Domain.Enums;

namespace FutureCV.Domain.Entities;

public class JobReport : BaseEntity
{
    public Guid JobId { get; set; }
    public Guid ReporterUserId { get; set; }
    public string Reason { get; set; } = string.Empty;
    public string? Details { get; set; }
    public JobReportStatus Status { get; set; } = JobReportStatus.Pending;
    public Guid? ResolvedByAdminId { get; set; }
    public DateTimeOffset? ResolvedAt { get; set; }
    public string? AdminNote { get; set; }
    public bool IsDeleted { get; set; } = false;

    // Navigation properties
    public Job Job { get; set; } = null!;
}
