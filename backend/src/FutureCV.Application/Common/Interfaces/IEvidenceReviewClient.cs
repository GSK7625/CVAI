using System.Text.Json;
using FutureCV.Application.Common.Models;
namespace FutureCV.Application.Common.Interfaces;

public interface IEvidenceReviewClient
{
    bool Enabled { get; }
    Task<ServiceResult<string>> ExtractPdfFromUrlAsync(string fileUrl, CancellationToken cancellationToken, string? publicId = null)
        => Task.FromResult(ServiceResult.InfrastructureError<string>("Dịch vụ chưa hỗ trợ trích văn bản PDF."));
    Task<ServiceResult<JsonElement>> ReviewAsync(string cvText, string jdText, string jobTitle, CancellationToken cancellationToken);
}
