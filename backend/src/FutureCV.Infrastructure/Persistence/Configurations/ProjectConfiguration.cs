using FutureCV.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace FutureCV.Infrastructure.Persistence.Configurations;

public class ProjectConfiguration : IEntityTypeConfiguration<Project>
{
    public void Configure(EntityTypeBuilder<Project> builder)
    {
        builder.ToTable("Projects");
        builder.HasKey(p => p.Id);

        builder.Property(p => p.Name).IsRequired().HasMaxLength(300);
        builder.Property(p => p.Role).HasMaxLength(200);

        builder.HasIndex(p => p.CandidateId);
        builder.HasIndex(p => p.CvId);

        builder.HasOne(p => p.Candidate)
            .WithMany(cand => cand.Projects)
            .HasForeignKey(p => p.CandidateId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(p => p.Cv)
            .WithMany()
            .HasForeignKey(p => p.CvId)
            .OnDelete(DeleteBehavior.SetNull);
    }
}
