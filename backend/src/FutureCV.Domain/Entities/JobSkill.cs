namespace FutureCV.Domain.Entities;

public class JobSkill
{
    public Guid JobId { get; set; }
    public Guid SkillId { get; set; }
    public bool IsRequired { get; set; } = true;

    // Navigation properties
    public Job Job { get; set; } = null!;
    public Skill Skill { get; set; } = null!;
}
