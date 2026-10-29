import { useAuthStore } from "~/stores/useAuthStore";
import { prepareRequestBody } from "./requestBody";
import { translateErrorMessage } from "./errorMapper";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:5000";
const DEFAULT_TIMEOUT_MS = 15_000;

export class ApiError extends Error {
  status: number;
  /** true = lỗi hạ tầng (mất mạng, timeout), không phải lỗi từ server response. */
  readonly isNetworkError: boolean;

  constructor(message: string, status: number, isNetworkError = false) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.isNetworkError = isNetworkError;
  }
}

export interface FetchOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  auth?: boolean;
  /** Mặc định 15s. Truyền Infinity để tắt. */
  timeoutMs?: number;
  /** Kiểu response mong muốn: "json" (mặc định), "blob", "text" */
  responseType?: "json" | "blob" | "text";
}

async function parseErrorMessage(response: Response): Promise<string> {
  let rawMessage: string | null = null;
  try {
    const data = await response.json();
    if (data?.message && typeof data.message === "string") {
      rawMessage = data.message;
    } else if (data?.detail && typeof data.detail === "string") {
      rawMessage = data.detail;
    } else if (data?.errors && typeof data.errors === "object") {
      const first = Object.values(data.errors).flat()[0];
      if (typeof first === "string") rawMessage = first;
    } else if (data?.title && typeof data.title === "string") {
      rawMessage = data.title;
    }
  } catch {
    // Body không phải JSON -> dùng message mặc định
  }
  return translateErrorMessage(rawMessage, response.status);
}

async function readApiError(response: Response): Promise<string> {
  return await parseErrorMessage(response);
}

async function readApiResponse(response: Response, responseType: string = "json"): Promise<unknown> {
  if (responseType === "blob") {
    return await response.blob();
  }
  if (responseType === "text") {
    return await response.text();
  }
  // Default: json
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

async function requestOnce<T>(
  path: string,
  options: FetchOptions,
  externalSignal?: AbortSignal,
): Promise<T> {
  const { body, auth = false, headers, timeoutMs = DEFAULT_TIMEOUT_MS, signal, responseType = "json", ...rest } = options;
  const preparedBody = prepareRequestBody(body);

  const targetSignal: AbortSignal | undefined = externalSignal ?? (signal ?? undefined);

  const requestHeaders: Record<string, string> = {
    ...(preparedBody.hasJsonBody ? { "Content-Type": "application/json" } : {}),
    ...((headers as Record<string, string>) ?? {}),
  };
  if (auth) {
    const token = useAuthStore.getState().accessToken;
    if (token) requestHeaders.Authorization = `Bearer ${token}`;
  }

  // Kết hợp external signal + timeout signal
  const timeoutSignal =
    Number.isFinite(timeoutMs) && timeoutMs > 0 ? AbortSignal.timeout(timeoutMs) : undefined;

  let compositeSignal: AbortSignal | undefined = targetSignal;
  if (timeoutSignal) {
    compositeSignal = targetSignal ? AbortSignal.any([targetSignal, timeoutSignal]) : timeoutSignal;
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...rest,
      signal: compositeSignal,
      headers: requestHeaders,
      body: preparedBody.body,
    });
  } catch (err: unknown) {
    if (targetSignal?.aborted) throw err;
    if (err instanceof DOMException && err.name === "TimeoutError") {
      throw new ApiError("Hết thời gian chờ phản hồi từ máy chủ.", 408, true);
    }
    if (err instanceof ApiError) throw err;
    throw new ApiError("Không thể kết nối đến máy chủ. Kiểm tra mạng của bạn.", 0, true);
  }

  if (!response.ok) {
    throw new ApiError(await parseErrorMessage(response), response.status);
  }
  if (response.status === 204) return undefined as T;
  if (responseType === "blob") {
    return (await response.blob()) as T;
  }
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return (await response.json()) as T;
  }
  const text = await response.text();
  try {
    return JSON.parse(text) as T;
  } catch {
    return text as unknown as T;
  }
}

export async function fetcher<T>(path: string, options: FetchOptions = {}): Promise<T> {
  try {
    return await requestOnce<T>(path, options);
  } catch (error) {
    // 401 + có auth flag + còn refreshToken -> tự động refresh token 1 lần
    const canRefresh =
      options.auth &&
      error instanceof ApiError &&
      error.status === 401 &&
      useAuthStore.getState().refreshToken !== null;

    if (!canRefresh) throw error;

    const { refreshToken, updateTokens, logout } = useAuthStore.getState();
    try {
      const tokens = await requestOnce<{ accessToken: string; refreshToken: string }>(
        "/api/auth/refresh",
        { method: "POST", body: { refreshToken } },
      );
      updateTokens(tokens);
      return await requestOnce<T>(path, options);
    } catch (refreshError) {
      logout();
      throw refreshError instanceof ApiError ? refreshError : error;
    }
  }
}

export { API_BASE };
