using FutureCV.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace FutureCV.Infrastructure.Persistence.Configurations;

public class SavedJobConfiguration : IEntityTypeConfiguration<SavedJob>
{
    public void Configure(EntityTypeBuilder<SavedJob> builder)
    {
        builder.ToTable("SavedJobs");

        builder.HasKey(sj => new { sj.CandidateId, sj.JobId });

        builder.HasOne(sj => sj.Candidate)
            .WithMany(c => c.SavedJobs)
            .HasForeignKey(sj => sj.CandidateId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(sj => sj.Job)
            .WithMany(j => j.SavedJobs)
            .HasForeignKey(sj => sj.JobId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasIndex(sj => sj.JobId);
    }
}
