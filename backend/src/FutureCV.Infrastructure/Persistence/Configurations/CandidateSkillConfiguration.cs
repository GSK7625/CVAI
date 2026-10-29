using FutureCV.Domain.Entities;
using FutureCV.Domain.Enums;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace FutureCV.Infrastructure.Persistence.Configurations;

public class CandidateSkillConfiguration : IEntityTypeConfiguration<CandidateSkill>
{
    public void Configure(EntityTypeBuilder<CandidateSkill> builder)
    {
        builder.ToTable("CandidateSkills");

        // Composite PK matching the DB schema
        builder.HasKey(cs => new { cs.CandidateId, cs.SkillId });

        // Store enum as string to match DB CHECK ('Beginner','Intermediate','Advanced')
        builder.Property(cs => cs.Level)
            .HasConversion<string>()
            .HasMaxLength(20)
            .IsRequired();

        builder.HasIndex(cs => cs.SkillId);

        builder.HasOne(cs => cs.Candidate)
            .WithMany(c => c.Skills)
            .HasForeignKey(cs => cs.CandidateId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(cs => cs.Skill)
            .WithMany()
            .HasForeignKey(cs => cs.SkillId)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
