namespace FutureCV.Infrastructure.Configurations;

/// <summary>
/// Strongly-typed settings for Cloudinary SDK.
/// Bound from appsettings section "Cloudinary".
/// </summary>
public class CloudinarySettings
{
    public string CloudName { get; set; } = string.Empty;
    public string ApiKey { get; set; } = string.Empty;
    public string ApiSecret { get; set; } = string.Empty;
}
