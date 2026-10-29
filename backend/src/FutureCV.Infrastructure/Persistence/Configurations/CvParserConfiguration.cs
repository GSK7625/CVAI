using FutureCV.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace FutureCV.Infrastructure.Persistence.Configurations;

public class CvParserConfiguration : IEntityTypeConfiguration<CvParser>
{
    public void Configure(EntityTypeBuilder<CvParser> builder)
    {
        builder.ToTable("CVParsers");
        builder.HasKey(p => p.Id);

        builder.Property(p => p.ModelVersion).IsRequired().HasMaxLength(50);
        builder.Property(p => p.ParsedDataJson).HasColumnType("jsonb");

        builder.HasIndex(p => p.CvId).IsUnique();

        builder.HasOne(p => p.Cv)
            .WithOne(c => c.CvParser)
            .HasForeignKey<CvParser>(p => p.CvId)
            .OnDelete(DeleteBehavior.Cascade);
    }
}
