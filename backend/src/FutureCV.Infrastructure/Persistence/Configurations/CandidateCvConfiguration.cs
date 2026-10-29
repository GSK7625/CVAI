using FutureCV.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace FutureCV.Infrastructure.Persistence.Configurations;

public class CandidateCvConfiguration : IEntityTypeConfiguration<CandidateCv>
{
    public void Configure(EntityTypeBuilder<CandidateCv> builder)
    {
        builder.ToTable("CVs");
        builder.HasKey(c => c.Id);

        builder.Property(c => c.Title).HasMaxLength(200);
        builder.Property(c => c.FileType).HasMaxLength(10);
        builder.Property(c => c.Source).IsRequired().HasMaxLength(10);
        builder.Property(c => c.ParseStatus).IsRequired().HasMaxLength(20);

        builder.HasIndex(c => c.CandidateId);

        // Unique filter index: Each candidate can have at most one IsPrimary = true (when not deleted)
        builder.HasIndex(c => new { c.CandidateId, c.IsPrimary })
            .HasFilter("\"IsPrimary\" = TRUE AND \"IsDeleted\" = FALSE")
            .IsUnique();

        builder.HasOne(c => c.Candidate)
            .WithMany(cand => cand.CVs)
            .HasForeignKey(c => c.CandidateId)
            .OnDelete(DeleteBehavior.Cascade);
    }
}
