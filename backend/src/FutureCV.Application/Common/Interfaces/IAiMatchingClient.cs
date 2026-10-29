using FutureCV.Application.Common.Models;
using FutureCV.Application.Features.AiMatching.DTOs;

namespace FutureCV.Application.Common.Interfaces;

/// <summary>
/// Application port for invoking the Python AI Matching Engine.
/// Provides stateless, inspectable Candidate–Job compatibility evaluation.
/// </summary>
public interface IAiMatchingClient
{
    Task<ServiceResult<AiMatchResultDto>> MatchAsync(
        AiMatchRequest request,
        string? correlationId = null,
        CancellationToken cancellationToken = default);
}

