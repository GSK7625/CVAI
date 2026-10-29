using Microsoft.AspNetCore.Identity;

namespace FutureCV.Infrastructure.Identity;

public class AppUser : IdentityUser<Guid>
{

    public DateTimeOffset? LastLoginAt { get; set; }

    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;

    public DateTimeOffset UpdatedAt { get; set; } = DateTimeOffset.UtcNow;


    public bool IsDeleted { get; set; }
}
