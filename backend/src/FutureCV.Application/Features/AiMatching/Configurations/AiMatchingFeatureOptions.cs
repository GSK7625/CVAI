namespace FutureCV.Application.Features.AiMatching.Configurations;

/// <summary>
/// Strongly-typed feature options for AI Candidate-Job Matching within the Application layer.
/// Bound from configuration section "AiMatching".
/// </summary>
public sealed class AiMatchingFeatureOptions
{
    public const string SectionName = "AiMatching";

    /// <summary>
    /// When true, candidate preview requests evaluate AI matching in shadow mode (diagnostic logging only).
    /// Defaults to false.
    /// </summary>
    public bool PreviewShadowEnabled { get; set; } = false;

    /// <summary>
    /// When true, candidate preview requests use AI matching as the authoritative result (with legacy fallback).
    /// Defaults to false.
    /// </summary>
    public bool PreviewAiEnabled { get; set; } = false;
}
