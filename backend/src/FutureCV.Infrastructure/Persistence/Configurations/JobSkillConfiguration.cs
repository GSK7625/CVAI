using FutureCV.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace FutureCV.Infrastructure.Persistence.Configurations;

public class JobSkillConfiguration : IEntityTypeConfiguration<JobSkill>
{
    public void Configure(EntityTypeBuilder<JobSkill> builder)
    {
        builder.ToTable("JobSkills");

        builder.HasKey(js => new { js.JobId, js.SkillId });

        builder.Property(js => js.IsRequired)
            .HasDefaultValue(true);

        builder.HasOne(js => js.Job)
            .WithMany(j => j.JobSkills)
            .HasForeignKey(js => js.JobId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(js => js.Skill)
            .WithMany()
            .HasForeignKey(js => js.SkillId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasIndex(js => js.SkillId);
    }
}
