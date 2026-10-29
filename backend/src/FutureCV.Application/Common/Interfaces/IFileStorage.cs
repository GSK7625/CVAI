using System.IO;
using System.Threading;
using System.Threading.Tasks;

namespace FutureCV.Application.Common.Interfaces;

/// <summary>
/// Abstraction for cloud file storage (avatar, CV, etc.).
/// Application layer depends on this interface; Infrastructure provides the concrete implementation.
/// </summary>
public interface IFileStorage
{
    /// <summary>
    /// Uploads a file stream and returns the public URL and the provider-specific public ID.
    /// The public ID is required to update or delete the file later.
    /// </summary>
    /// <param name="stream">File content stream.</param>
    /// <param name="fileName">Original file name (used for format detection).</param>
    /// <param name="folder">Logical folder/path on the storage provider (e.g. "avatars/candidates").</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Tuple of (PublicUrl, PublicId).</returns>
    Task<(string PublicUrl, string PublicId)> UploadAsync(
        Stream stream,
        string fileName,
        string folder,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Deletes a previously uploaded file by its provider-specific public ID.
    /// Does NOT throw if the file does not exist on the provider (idempotent).
    /// </summary>
    /// <param name="publicId">The public ID returned by <see cref="UploadAsync"/>.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    Task DeleteAsync(string publicId, CancellationToken cancellationToken = default);

    /// <summary>
    /// Uploads a raw document file (e.g. PDF CV) to cloud storage.
    /// Returns the public URL and provider-specific public ID.
    /// </summary>
    Task<(string PublicUrl, string PublicId)> UploadDocumentAsync(
        Stream stream,
        string fileName,
        string folder,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Deletes a raw document file by its provider-specific public ID.
    /// </summary>
    Task DeleteDocumentAsync(string publicId, CancellationToken cancellationToken = default);
}
