using FutureCV.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace FutureCV.Infrastructure.Persistence.Configurations;

public class ExperienceConfiguration : IEntityTypeConfiguration<Experience>
{
    public void Configure(EntityTypeBuilder<Experience> builder)
    {
        builder.ToTable("Experiences");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.CompanyName).IsRequired().HasMaxLength(300);
        builder.Property(e => e.Position).HasMaxLength(200);

        // DateOnly maps to SQL DATE — supported natively in Npgsql
        builder.Property(e => e.StartDate).IsRequired();

        builder.HasIndex(e => e.CandidateId);

        builder.HasOne(e => e.Candidate)
            .WithMany(c => c.Experiences)
            .HasForeignKey(e => e.CandidateId)
            .OnDelete(DeleteBehavior.Cascade);
    }
}
