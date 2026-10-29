using FutureCV.Domain.Entities;
using FutureCV.Infrastructure.Identity;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace FutureCV.Infrastructure.Persistence.Configurations;

public class CandidateConfiguration : IEntityTypeConfiguration<Candidate>
{
    public void Configure(EntityTypeBuilder<Candidate> builder)
    {
        builder.HasKey(c => c.Id);

        builder.Property(c => c.FullName)
            .IsRequired()
            .HasMaxLength(200);

        builder.Property(c => c.Phone)
            .HasMaxLength(20);

        builder.Property(c => c.Gender)
            .HasMaxLength(20);

        builder.Property(c => c.DesiredPosition)
            .HasMaxLength(200);

        // Foreign Key to AspNetUsers (AppUser)
        builder.HasIndex(c => c.UserId)
            .IsUnique();

        builder.HasOne<AppUser>()
            .WithOne()
            .HasForeignKey<Candidate>(c => c.UserId)
            .OnDelete(DeleteBehavior.Cascade);
    }
}
