using FutureCV.Domain.Common;

namespace FutureCV.Domain.Entities;

public class JobLevel : BaseEntity
{
    public string Name { get; set; } = string.Empty;

    // Navigation properties
    public ICollection<Job> Jobs { get; set; } = [];
}
