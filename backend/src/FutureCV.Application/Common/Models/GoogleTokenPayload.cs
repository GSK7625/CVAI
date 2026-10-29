namespace FutureCV.Application.Common.Models;

public class GoogleTokenPayload
{
    public string Email { get; set; } = string.Empty;
    public string Subject { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public bool EmailVerified { get; set; }
}
