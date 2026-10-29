using CloudinaryDotNet;
using CloudinaryDotNet.Actions;
using FutureCV.Application.Common.Interfaces;
using FutureCV.Infrastructure.Configurations;
using Microsoft.Extensions.Options;

namespace FutureCV.Infrastructure.Services;

/// <summary>
/// Cloudinary implementation of <see cref="IFileStorage"/>.
/// Handles image/file upload and deletion via the Cloudinary SDK.
/// </summary>
public class CloudinaryFileStorage : IFileStorage
{
    private readonly Cloudinary _cloudinary;

    public CloudinaryFileStorage(IOptions<CloudinarySettings> options)
    {
        var settings = options.Value;
        var account = new Account(settings.CloudName, settings.ApiKey, settings.ApiSecret);
        _cloudinary = new Cloudinary(account) { Api = { Secure = true } };
    }

    /// <inheritdoc />
    public async Task<(string PublicUrl, string PublicId)> UploadAsync(
        Stream stream,
        string fileName,
        string folder,
        CancellationToken cancellationToken = default)
    {
        var uploadParams = new ImageUploadParams
        {
            File = new FileDescription(fileName, stream),
            Folder = folder,
            // Overwrite = false by default — each upload gets a unique public_id
            UseFilename = false,
            UniqueFilename = true,
            // Auto-optimize format and quality for web delivery
            Transformation = new Transformation().Quality("auto").FetchFormat("auto"),
        };

        Task<ImageUploadResult> uploadTask = _cloudinary.UploadAsync(uploadParams);
        var result = await uploadTask;

        if (result.Error != null)
        {
            throw new InvalidOperationException(
                $"Cloudinary upload failed: {result.Error.Message}");
        }

        return (result.SecureUrl.ToString(), result.PublicId);
    }

    /// <summary>
    /// Uploads a raw document file (PDF) to Cloudinary using ResourceType.Raw.
    /// Returns the secure URL and the public ID for deletion.
    /// </summary>
    public async Task<(string PublicUrl, string PublicId)> UploadDocumentAsync(
        Stream stream,
        string fileName,
        string folder,
        CancellationToken cancellationToken = default)
    {
        var uploadParams = new RawUploadParams
        {
            File = new FileDescription(fileName, stream),
            Folder = folder,
            UseFilename = true,
            UniqueFilename = true,
        };

        Task<RawUploadResult> uploadTask = _cloudinary.UploadAsync(uploadParams);
        var result = await uploadTask;

        if (result.Error != null)
        {
            throw new InvalidOperationException(
                $"Cloudinary document upload failed: {result.Error.Message}");
        }

        return (result.SecureUrl.ToString(), result.PublicId);
    }

    /// <inheritdoc />
    public async Task DeleteAsync(string publicId, CancellationToken cancellationToken = default)
    {
        var deleteParams = new DeletionParams(publicId);
        // Ignore "not found" — treat as idempotent
        await _cloudinary.DestroyAsync(deleteParams);
    }

    /// <summary>
    /// Deletes a raw document (PDF) from Cloudinary using ResourceType.Raw.
    /// </summary>
    public async Task DeleteDocumentAsync(string publicId, CancellationToken cancellationToken = default)
    {
        var deleteParams = new DeletionParams(publicId) { ResourceType = ResourceType.Raw };
        await _cloudinary.DestroyAsync(deleteParams);
    }
}

