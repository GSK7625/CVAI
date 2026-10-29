using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.Candidate.DTOs;

namespace FutureCV.Application.Common.Interfaces;

/// <summary>
/// Client port communicating with the Python FastAPI CV analysis and extraction microservice.
/// </summary>
public interface IAiCvClient
{
    Task<ServiceResult<FastApiCvAnalysisResponseDto>> AnalyzePdfAsync(
        byte[] fileBytes,
        string fileName,
        string? correlationId = null,
        CancellationToken cancellationToken = default);

    Task<ServiceResult<FastApiCvAnalysisResponseDto>> AnalyzeTextAsync(
        string rawText,
        string? candidateId = null,
        string? correlationId = null,
        CancellationToken cancellationToken = default);
}

