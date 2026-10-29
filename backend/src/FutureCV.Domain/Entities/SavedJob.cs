namespace FutureCV.Domain.Entities;

public class SavedJob
{
    public Guid CandidateId { get; set; }
    public Guid JobId { get; set; }
    public DateTime SavedAt { get; set; } = DateTime.UtcNow;

    // Navigation properties
    public Candidate Candidate { get; set; } = null!;
    public Job Job { get; set; } = null!;
}
