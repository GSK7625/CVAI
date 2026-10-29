using FutureCV.Domain.Entities;
using FutureCV.Infrastructure.Identity;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace FutureCV.Infrastructure.Persistence.Configurations;

public class EmployerConfiguration : IEntityTypeConfiguration<Employer>
{
    public void Configure(EntityTypeBuilder<Employer> builder)
    {
        builder.HasKey(e => e.Id);

        builder.Property(e => e.FullName)
            .IsRequired()
            .HasMaxLength(200);

        builder.Property(e => e.Phone)
            .HasMaxLength(20);

        builder.Property(e => e.Position)
            .HasMaxLength(200);

        // Foreign Key to AspNetUsers (AppUser)
        builder.HasIndex(e => e.UserId)
            .IsUnique();

        builder.HasOne<AppUser>()
            .WithOne()
            .HasForeignKey<Employer>(e => e.UserId)
            .OnDelete(DeleteBehavior.Cascade);

        // Foreign Key to Companies
        builder.HasOne(e => e.Company)
            .WithMany()
            .HasForeignKey(e => e.CompanyId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.Property(e => e.IsDeleted)
            .HasDefaultValue(false);
    }
}
