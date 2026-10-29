using FutureCV.Domain.Common;

namespace FutureCV.Domain.Entities;

public class JobCategory : BaseEntity
{
    public string Name { get; set; } = string.Empty;
    public Guid? ParentId { get; set; }

    // Navigation properties
    public JobCategory? Parent { get; set; }
    public ICollection<JobCategory> Children { get; set; } = [];
    public ICollection<Job> Jobs { get; set; } = [];
}
