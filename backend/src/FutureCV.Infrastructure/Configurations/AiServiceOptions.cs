namespace FutureCV.Infrastructure.Configurations;

/// <summary>
/// Strongly-typed HTTP transport and connection options for the external AI Service.
/// Bound from configuration section "AiService".
/// Owned exclusively by the Infrastructure layer.
/// </summary>
public sealed class AiServiceOptions
{
    public const string SectionName = "AiService";

    public string BaseUrl { get; set; } = "http://localhost:8000";
    public string ApiKey { get; set; } = string.Empty;
    public double TimeoutSeconds { get; set; } = 90.0;
}
