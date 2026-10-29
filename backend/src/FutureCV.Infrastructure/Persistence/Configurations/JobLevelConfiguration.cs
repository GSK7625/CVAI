using FutureCV.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace FutureCV.Infrastructure.Persistence.Configurations;

public class JobLevelConfiguration : IEntityTypeConfiguration<JobLevel>
{
    public void Configure(EntityTypeBuilder<JobLevel> builder)
    {
        builder.ToTable("JobLevels");

        builder.HasKey(l => l.Id);

        builder.Property(l => l.Name)
            .IsRequired()
            .HasMaxLength(100);

        builder.HasIndex(l => l.Name)
            .IsUnique();
    }
}
