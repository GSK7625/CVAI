using FutureCV.Domain.Common;

namespace FutureCV.Domain.Entities;

public class AuditLog : BaseEntity
{
    public Guid? UserId { get; set; }
    public string Action { get; set; } = string.Empty;
    public string? EntityType { get; set; }
    public string? EntityId { get; set; }
    public string? PayloadJson { get; set; }
    public string? IpAddress { get; set; }
}
