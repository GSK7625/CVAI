namespace FutureCV.Domain.Entities;

/// <summary>
/// Domain entity representing a Refresh Token.
/// Tracks token hash (SHA-256), expiration, creation time, revocation, and rotation replacement token ID.
/// </summary>
public class RefreshToken
{
    public Guid Id { get; set; }
    public Guid UserId { get; set; }
    public string TokenHash { get; set; } = string.Empty;
    public DateTimeOffset ExpiresAt { get; set; }
    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;
    public DateTimeOffset? RevokedAt { get; set; }
    public Guid? ReplacedByTokenId { get; set; }

    public bool IsActive => RevokedAt is null && ExpiresAt > DateTimeOffset.UtcNow;
    public bool IsRevoked => RevokedAt is not null;
    public bool IsExpired => ExpiresAt <= DateTimeOffset.UtcNow;
}
