import { QueryClient } from "@tanstack/react-query";
import { ApiError } from "./fetcher";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      refetchOnWindowFocus: false,
      retry: (failureCount, error) => {
        // Lỗi 4xx là vĩnh viễn — không retry (ngoại trừ 408 timeout hoặc 429 rate limit)
        if (error instanceof ApiError) {
          if (error.status >= 400 && error.status < 500) {
            return error.status === 408 || error.status === 429 ? failureCount < 1 : false;
          }
          return failureCount < 1; // 5xx và network error: retry 1 lần
        }
        return failureCount < 1;
      },
    },
    mutations: {
      retry: 0, // Mutation ghi dữ liệu không tự động retry
    },
  },
});
