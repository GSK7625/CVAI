using FutureCV.Domain.Entities;
using FutureCV.Domain.Enums;
using FutureCV.Infrastructure.Identity;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace FutureCV.Infrastructure.Persistence.Configurations;

public class JobReportConfiguration : IEntityTypeConfiguration<JobReport>
{
    public void Configure(EntityTypeBuilder<JobReport> builder)
    {
        builder.ToTable("JobReports");

        builder.HasKey(r => r.Id);

        builder.Property(r => r.Reason)
            .IsRequired()
            .HasMaxLength(100);

        builder.Property(r => r.Details)
            .HasMaxLength(2000);

        builder.Property(r => r.Status)
            .HasConversion<string>()
            .IsRequired()
            .HasMaxLength(20)
            .HasDefaultValue(JobReportStatus.Pending);

        builder.Property(r => r.AdminNote)
            .HasMaxLength(2000);

        builder.Property(r => r.IsDeleted)
            .HasDefaultValue(false);

        // Foreign Keys
        builder.HasOne(r => r.Job)
            .WithMany(j => j.Reports)
            .HasForeignKey(r => r.JobId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne<AppUser>()
            .WithMany()
            .HasForeignKey(r => r.ReporterUserId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<AppUser>()
            .WithMany()
            .HasForeignKey(r => r.ResolvedByAdminId)
            .OnDelete(DeleteBehavior.SetNull);

        // Indexes
        builder.HasIndex(r => r.JobId);
        builder.HasIndex(r => r.ReporterUserId);
        builder.HasIndex(r => r.Status);
    }
}
