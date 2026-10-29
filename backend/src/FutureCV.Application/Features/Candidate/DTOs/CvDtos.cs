namespace FutureCV.Application.Features.Candidate.DTOs;

public sealed record CvUploadRequest(
    string? Title);

public sealed record UpdateCvTitleRequest(
    string Title);

public sealed record CvResponse(
    Guid Id,
    Guid CandidateId,
    string? Title,
    string? FileUrl,
    string? FileType,
    long? FileSizeBytes,
    bool IsPrimary,
    DateTime UploadedAt);
