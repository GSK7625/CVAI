using FutureCV.Domain.Entities;
using FutureCV.Domain.Enums;
using FutureCV.Infrastructure.Identity;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace FutureCV.Infrastructure.Persistence.Configurations;

public class JobConfiguration : IEntityTypeConfiguration<Job>
{
    public void Configure(EntityTypeBuilder<Job> builder)
    {
        builder.ToTable("Jobs");

        builder.HasKey(j => j.Id);

        builder.Property(j => j.Title)
            .IsRequired()
            .HasMaxLength(300);

        builder.Property(j => j.Description)
            .IsRequired();

        builder.Property(j => j.SalaryCurrency)
            .IsRequired()
            .HasMaxLength(10)
            .HasDefaultValue("VND");

        builder.Property(j => j.ApprovalStatus)
            .HasConversion<string>()
            .IsRequired()
            .HasMaxLength(20)
            .HasDefaultValue(JobApprovalStatus.Draft);

        builder.Property(j => j.PositionsCount)
            .HasDefaultValue(1);

        builder.Property(j => j.IsActive)
            .HasDefaultValue(true);

        builder.Property(j => j.IsExpired)
            .HasDefaultValue(false);

        builder.Property(j => j.ViewCount)
            .HasDefaultValue(0);

        builder.Property(j => j.IsDeleted)
            .HasDefaultValue(false);

        builder.Property(j => j.IsBanned)
            .HasDefaultValue(false);

        // Foreign Keys
        builder.HasOne(j => j.Company)
            .WithMany()
            .HasForeignKey(j => j.CompanyId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<AppUser>()
            .WithMany()
            .HasForeignKey(j => j.PostedById)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<AppUser>()
            .WithMany()
            .HasForeignKey(j => j.ApprovedByAdminId)
            .OnDelete(DeleteBehavior.SetNull);

        builder.HasOne<AppUser>()
            .WithMany()
            .HasForeignKey(j => j.BannedByAdminId)
            .OnDelete(DeleteBehavior.SetNull);

        builder.HasOne(j => j.Category)
            .WithMany(c => c.Jobs)
            .HasForeignKey(j => j.CategoryId)
            .OnDelete(DeleteBehavior.SetNull);

        builder.HasOne(j => j.Level)
            .WithMany(l => l.Jobs)
            .HasForeignKey(j => j.LevelId)
            .OnDelete(DeleteBehavior.SetNull);

        builder.HasOne(j => j.EmploymentType)
            .WithMany(t => t.Jobs)
            .HasForeignKey(j => j.EmploymentTypeId)
            .OnDelete(DeleteBehavior.SetNull);

        builder.HasOne(j => j.Location)
            .WithMany(l => l.Jobs)
            .HasForeignKey(j => j.LocationId)
            .OnDelete(DeleteBehavior.SetNull);

        // Indexes matching dbschema.sql
        builder.HasIndex(j => j.CompanyId);
        builder.HasIndex(j => j.CategoryId);
        builder.HasIndex(j => j.LocationId);
        builder.HasIndex(j => new { j.ApprovalStatus, j.IsActive });
    }
}
