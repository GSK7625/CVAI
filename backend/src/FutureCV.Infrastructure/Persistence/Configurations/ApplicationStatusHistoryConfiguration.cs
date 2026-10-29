using FutureCV.Domain.Entities;
using FutureCV.Infrastructure.Identity;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace FutureCV.Infrastructure.Persistence.Configurations;

public class ApplicationStatusHistoryConfiguration : IEntityTypeConfiguration<ApplicationStatusHistory>
{
    public void Configure(EntityTypeBuilder<ApplicationStatusHistory> builder)
    {
        builder.ToTable("ApplicationStatusHistories");

        builder.HasKey(h => h.Id);

        builder.Property(h => h.FromStatus)
            .HasMaxLength(20);

        builder.Property(h => h.ToStatus)
            .IsRequired()
            .HasMaxLength(20);

        builder.Property(h => h.Reason)
            .HasMaxLength(500);

        builder.HasOne(h => h.Application)
            .WithMany(a => a.StatusHistories)
            .HasForeignKey(h => h.ApplicationId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne<AppUser>()
            .WithMany()
            .HasForeignKey(h => h.ChangedById)
            .OnDelete(DeleteBehavior.SetNull);

        builder.HasIndex(h => h.ApplicationId);
    }
}
