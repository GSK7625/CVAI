using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using FutureCV.Application.Common.Interfaces;
using FutureCV.Application.Common.Models;
using Microsoft.Extensions.Configuration;

namespace FutureCV.Infrastructure.Services;

public sealed class EvidenceReviewHttpClient(HttpClient http, IConfiguration configuration) : IEvidenceReviewClient
{
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
                return ServiceResult.Success(JsonSerializer.SerializeToElement(new { status = "needs_review", score = (decimal?)null,
                    summary = "Yêu cầu tuyển dụng có điều kiện chưa được hỗ trợ. Cần kiểm tra thủ công.", assessments = Array.Empty<object>() }));
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
