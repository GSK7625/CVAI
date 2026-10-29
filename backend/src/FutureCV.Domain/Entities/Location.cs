using FutureCV.Domain.Common;

namespace FutureCV.Domain.Entities;

public class Location : BaseEntity
{
    public string Name { get; set; } = string.Empty;
    public Guid? ParentId { get; set; }

    // Navigation properties
    public Location? Parent { get; set; }
    public ICollection<Location> Children { get; set; } = [];
    public ICollection<Job> Jobs { get; set; } = [];
}
