namespace FutureCV.Application.Common.Models;

/// <summary>
/// Represents a file to be uploaded, decoupled from ASP.NET Core's IFormFile.
/// Controllers extract stream/metadata from IFormFile before passing to the service.
/// </summary>
public sealed record FileUploadRequest(
    Stream Stream,
    string FileName,
    string ContentType,
    long SizeInBytes);
