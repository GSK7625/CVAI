using FutureCV.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace FutureCV.Infrastructure.Persistence.Configurations;

public class CvEvaluationConfiguration : IEntityTypeConfiguration<CvEvaluation>
{
    public void Configure(EntityTypeBuilder<CvEvaluation> builder)
    {
        builder.ToTable("CVEvaluations");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.ModelVersion).IsRequired().HasMaxLength(50);
        builder.Property(e => e.StrengthsJson).HasColumnType("jsonb");
        builder.Property(e => e.WeaknessesJson).HasColumnType("jsonb");
        builder.Property(e => e.ImprovementsJson).HasColumnType("jsonb");
        builder.Property(e => e.MissingSkillsJson).HasColumnType("jsonb");

        builder.HasIndex(e => e.CvId).IsUnique();

        builder.HasOne(e => e.Cv)
            .WithOne(c => c.Evaluation)
            .HasForeignKey<CvEvaluation>(e => e.CvId)
            .OnDelete(DeleteBehavior.Cascade);
    }
}
