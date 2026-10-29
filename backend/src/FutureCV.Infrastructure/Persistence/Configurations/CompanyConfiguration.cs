using FutureCV.Domain.Entities;
using FutureCV.Domain.Enums;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace FutureCV.Infrastructure.Persistence.Configurations;

public class CompanyConfiguration : IEntityTypeConfiguration<Company>
{
    public void Configure(EntityTypeBuilder<Company> builder)
    {
        builder.HasKey(c => c.Id);

        builder.Property(c => c.Name)
            .IsRequired()
            .HasMaxLength(300);

        builder.Property(c => c.TaxCode)
            .IsRequired()
            .HasMaxLength(50);

        builder.HasIndex(c => c.TaxCode)
            .IsUnique();

        builder.Property(c => c.VerifiedStatus)
            .HasConversion<string>()
            .IsRequired()
            .HasMaxLength(20)
            .HasDefaultValue(CompanyVerificationStatus.Pending);

        builder.Property(c => c.IsDeleted)
            .HasDefaultValue(false);
    }
}
