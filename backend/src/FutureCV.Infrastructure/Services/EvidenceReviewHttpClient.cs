using CloudinaryDotNet;
using HttpMethod = System.Net.Http.HttpMethod;
using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using FutureCV.Application.Common.Interfaces;
using FutureCV.Application.Common.Models;
using Microsoft.Extensions.Configuration;

namespace FutureCV.Infrastructure.Services;

public sealed class EvidenceReviewHttpClient(HttpClient http, IConfiguration configuration) : IEvidenceReviewClient
{
    public async Task<ServiceResult<string>> ExtractPdfFromUrlAsync(string fileUrl, CancellationToken cancellationToken, string? publicId = null)
    {
        const int maxBytes = 5 * 1024 * 1024;
        var key = configuration["EvidenceAi:ApiKey"];
        if (string.IsNullOrWhiteSpace(key) || key.Length < 32)
            return ServiceResult.InfrastructureError<string>("Dịch vụ đánh giá chưa được cấu hình.");
        if (!Uri.TryCreate(fileUrl, UriKind.Absolute, out var uri) || uri.Scheme != "https" ||
            uri.Host != "res.cloudinary.com" || !string.IsNullOrEmpty(uri.UserInfo) || uri.Port != 443)
            return ServiceResult.Failure<string>("PDF phải là tệp đã tải lên kho CV của hệ thống.");
        try
        {
            // Authenticated download avoids enabling public PDF delivery on the account.
            var cloud = configuration["Cloudinary:CloudName"];
            var cloudKey = configuration["Cloudinary:ApiKey"];
            var cloudSecret = configuration["Cloudinary:ApiSecret"];
            if (!string.IsNullOrWhiteSpace(publicId) && !string.IsNullOrWhiteSpace(cloud) &&
                !string.IsNullOrWhiteSpace(cloudKey) && !string.IsNullOrWhiteSpace(cloudSecret))
            {
                if (!uri.AbsolutePath.StartsWith("/" + cloud + "/", StringComparison.Ordinal) ||
                    !publicId.StartsWith("cvs/candidates/", StringComparison.Ordinal))
                    return ServiceResult.Failure<string>("PDF không thuộc kho CV đã cấu hình.");
                var storage = new Cloudinary(new Account(cloud, cloudKey, cloudSecret));
                storage.Api.Secure = true;
                uri = new Uri(storage.DownloadPrivate(publicId, type: "upload", resourceType: "raw",
                    expiresAt: DateTimeOffset.UtcNow.AddMinutes(1).ToUnixTimeSeconds()));
            }
            using var download = await http.GetAsync(uri, HttpCompletionOption.ResponseHeadersRead, cancellationToken);
            if (!download.IsSuccessStatusCode)
                return ServiceResult.InfrastructureError<string>("Không tải được PDF từ kho CV. Kiểm tra quyền truy cập tệp Cloudinary.");
            if (download.Content.Headers.ContentLength > maxBytes)
                return ServiceResult.Failure<string>("PDF vượt quá 5 MB.");
            using var bytes = new MemoryStream();
            await using var stream = await download.Content.ReadAsStreamAsync(cancellationToken);
            var buffer = new byte[8192];
            int count;
            while ((count = await stream.ReadAsync(buffer, cancellationToken)) > 0)
            {
                if (bytes.Length + count > maxBytes) return ServiceResult.Failure<string>("PDF vượt quá 5 MB.");
                await bytes.WriteAsync(buffer.AsMemory(0, count), cancellationToken);
            }
            using var request = new HttpRequestMessage(HttpMethod.Post, "extract-pdf");
            request.Headers.Add("X-Internal-API-Key", key);
            request.Content = JsonContent.Create(new { pdf_base64 = Convert.ToBase64String(bytes.ToArray()) });
            using var response = await http.SendAsync(request, cancellationToken);
            if (response.StatusCode == HttpStatusCode.NotFound)
                return ServiceResult.InfrastructureError<string>("Hãy khởi động lại dịch vụ model sau khi cập nhật code để đọc PDF.");
            if (response.StatusCode == HttpStatusCode.UnprocessableEntity)
                return ServiceResult.Failure<string>("PDF không đọc được văn bản, có thể là ảnh quét hoặc bị khóa. Hãy dùng PDF có thể bôi chọn chữ.");
            if (!response.IsSuccessStatusCode)
                return ServiceResult.InfrastructureError<string>("Dịch vụ đọc PDF đang bận hoặc chưa sẵn sàng. Vui lòng thử lại.");
            using var document = await JsonDocument.ParseAsync(await response.Content.ReadAsStreamAsync(cancellationToken), cancellationToken: cancellationToken);
            var text = document.RootElement.GetProperty("text").GetString();
            if (string.IsNullOrWhiteSpace(text) || text.Length > 30000)
                return ServiceResult.Failure<string>("Văn bản CV rỗng hoặc vượt giới hạn 30.000 ký tự.");
            return ServiceResult.Success(text);
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested) { throw; }
        catch (Exception error) when (error is HttpRequestException or OperationCanceledException or JsonException or InvalidOperationException or KeyNotFoundException)
        {
            return ServiceResult.InfrastructureError<string>("Không thể trích văn bản PDF. Vui lòng thử lại.");
        }
    }

    public bool Enabled => configuration.GetValue<bool>("EvidenceAi:Enabled");

    public async Task<ServiceResult<JsonElement>> ReviewAsync(string cvText, string jdText, string jobTitle, CancellationToken cancellationToken)
    {
        var key = configuration["EvidenceAi:ApiKey"];
        if (string.IsNullOrWhiteSpace(key) || key.Length < 32)
            return ServiceResult.InfrastructureError<JsonElement>("Dịch vụ đánh giá chưa được cấu hình.");
        try
        {
            using var request = new HttpRequestMessage(HttpMethod.Post, "review");
            request.Headers.Add("X-Internal-API-Key", key);
            request.Content = JsonContent.Create(new { cv_text = cvText, jd_text = jdText, job_title = jobTitle });
            using var response = await http.SendAsync(request, cancellationToken);
            if (response.StatusCode == HttpStatusCode.UnprocessableEntity)
            {
                using var errorDocument = await JsonDocument.ParseAsync(
                    await response.Content.ReadAsStreamAsync(cancellationToken), cancellationToken: cancellationToken);
                // Older model servers return parser diagnostics in a 422; other 422s are input errors.
                if (errorDocument.RootElement.TryGetProperty("detail", out var detail) && detail.ValueKind == JsonValueKind.Object &&
                    detail.TryGetProperty("jd_profile", out var profile) && profile.ValueKind == JsonValueKind.Object &&
                    profile.TryGetProperty("unresolved", out var unresolved) && unresolved.ValueKind == JsonValueKind.Array)
                    return ServiceResult.Success(JsonSerializer.SerializeToElement(new { status = "needs_review", score = (decimal?)null,
                        summary = "Bộ đọc JD chưa xử lý được một số yêu cầu bên dưới. Đây chưa phải kết luận về độ phù hợp của CV.",
                        jd_profile = profile.Clone(), assessments = Array.Empty<object>() }));
                return ServiceResult.Failure<JsonElement>("Dữ liệu CV/JD không hợp lệ hoặc vượt giới hạn xử lý. Vui lòng kiểm tra nội dung và thử lại.");
            }
            if (!response.IsSuccessStatusCode)
                return ServiceResult.InfrastructureError<JsonElement>("Dịch vụ đánh giá đang bận hoặc chưa sẵn sàng. Vui lòng thử lại.");
            using var document = await JsonDocument.ParseAsync(await response.Content.ReadAsStreamAsync(cancellationToken), cancellationToken: cancellationToken);
            var data = document.RootElement;
            var status = data.GetProperty("status").GetString();
            var score = data.GetProperty("score");
            if (status is not ("ready" or "needs_review") ||
                (status == "ready" && (!score.TryGetDecimal(out var value) || value < 0 || value > 100)) ||
                (status == "needs_review" && score.ValueKind != JsonValueKind.Null) ||
                data.GetProperty("assessments").ValueKind != JsonValueKind.Array)
                return ServiceResult.InfrastructureError<JsonElement>("Kết quả AI không hợp lệ.");
            return ServiceResult.Success(data.Clone());
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested) { throw; }
        catch (Exception error) when (error is HttpRequestException or OperationCanceledException or JsonException or InvalidOperationException or KeyNotFoundException)
        {
            // Never log CV text, provider bodies or internal credentials.
            return ServiceResult.InfrastructureError<JsonElement>("Không thể lấy kết quả AI. Vui lòng thử lại.");
        }
    }
}
