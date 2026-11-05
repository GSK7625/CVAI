using System.Text.Json;
using FutureCV.Application.Common.Models;
namespace FutureCV.Application.Common.Interfaces;

public interface IEvidenceReviewClient
{
    bool Enabled { get; }
    Task<ServiceResult<JsonElement>> ReviewAsync(string cvText, string jdText, string jobTitle, CancellationToken cancellationToken);
}
