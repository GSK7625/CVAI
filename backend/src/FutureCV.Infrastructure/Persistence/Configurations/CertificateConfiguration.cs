using FutureCV.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace FutureCV.Infrastructure.Persistence.Configurations;

public class CertificateConfiguration : IEntityTypeConfiguration<Certificate>
{
    public void Configure(EntityTypeBuilder<Certificate> builder)
    {
        builder.ToTable("Certificates");
        builder.HasKey(c => c.Id);

        builder.Property(c => c.Name).IsRequired().HasMaxLength(300);
        builder.Property(c => c.Organization).HasMaxLength(300);

        builder.HasIndex(c => c.CandidateId);
        builder.HasIndex(c => c.CvId);

        builder.HasOne(c => c.Candidate)
            .WithMany(cand => cand.Certificates)
            .HasForeignKey(c => c.CandidateId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(c => c.Cv)
            .WithMany()
            .HasForeignKey(c => c.CvId)
            .OnDelete(DeleteBehavior.SetNull);
    }
}
