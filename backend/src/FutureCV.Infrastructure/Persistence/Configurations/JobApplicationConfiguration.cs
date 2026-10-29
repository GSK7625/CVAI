using FutureCV.Domain.Entities;
using FutureCV.Domain.Enums;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace FutureCV.Infrastructure.Persistence.Configurations;

public class JobApplicationConfiguration : IEntityTypeConfiguration<JobApplication>
{
    public void Configure(EntityTypeBuilder<JobApplication> builder)
    {
        builder.ToTable("Applications");

        builder.HasKey(a => a.Id);

        builder.Property(a => a.Status)
            .HasConversion<string>()
            .IsRequired()
            .HasMaxLength(20)
            .HasDefaultValue(ApplicationStatus.Applied);

        builder.Property(a => a.CoverLetter)
            .HasMaxLength(2000);

        builder.Property(a => a.EvaluationLabel)
            .HasMaxLength(100);

        builder.Property(a => a.IsDeleted)
            .HasDefaultValue(false);

        // Unique constraint: 1 candidate can only apply once per job
        builder.HasIndex(a => new { a.CandidateId, a.JobId })
            .IsUnique();

        // Foreign Keys
        builder.HasOne(a => a.Candidate)
            .WithMany(c => c.Applications)
            .HasForeignKey(a => a.CandidateId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(a => a.Job)
            .WithMany(j => j.Applications)
            .HasForeignKey(a => a.JobId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(a => a.Cv)
            .WithMany()
            .HasForeignKey(a => a.CvId)
            .OnDelete(DeleteBehavior.Restrict);

        // Indexes
        builder.HasIndex(a => a.JobId);
        builder.HasIndex(a => a.CandidateId);
        builder.HasIndex(a => a.Status);
    }
}
