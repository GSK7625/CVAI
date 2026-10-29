/** Read successful API responses, including file downloads and text uploads. */
export async function readApiResponse(response: Response, responseType: "json" | "blob" = "json"): Promise<unknown> {
  if (response.status === 204) return undefined;
  if (responseType === "blob") return response.blob();
  const text = await response.text();
  if (!text) return undefined;
  if (response.headers.get("content-type")?.includes("application/json")) return JSON.parse(text);
  try { return JSON.parse(text); }
  catch { return text; }
}

/** Support both controller errors and ASP.NET ProblemDetails. */
export async function readApiError(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data?.message === "string" && data.message) return data.message;
    if (data?.errors) {
      const first = Object.values(data.errors).flat()[0];
      if (typeof first === "string") return first;
    }
    if (typeof data?.detail === "string" && data.detail) return data.detail;
    if (typeof data?.title === "string" && data.title) return data.title;
  } catch {
    // Non-JSON error responses use the HTTP status as a fallback.
  }
  return `Yêu cầu thất bại (${response.status})`;
}
