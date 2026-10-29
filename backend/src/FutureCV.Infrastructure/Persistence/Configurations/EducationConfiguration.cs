using FutureCV.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace FutureCV.Infrastructure.Persistence.Configurations;

public class EducationConfiguration : IEntityTypeConfiguration<Education>
{
    public void Configure(EntityTypeBuilder<Education> builder)
    {
        builder.ToTable("Educations");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.School).IsRequired().HasMaxLength(300);
        builder.Property(e => e.Degree).HasMaxLength(150);
        builder.Property(e => e.Major).HasMaxLength(150);

        builder.HasIndex(e => e.CandidateId);

        builder.HasOne(e => e.Candidate)
            .WithMany(c => c.Educations)
            .HasForeignKey(e => e.CandidateId)
            .OnDelete(DeleteBehavior.Cascade);
    }
}
