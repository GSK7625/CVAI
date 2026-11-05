import type { JobMatchPreviewResponse } from "../types";

type RequestPreview = (jobId: string, cvId: string) => Promise<JobMatchPreviewResponse>;

export function previewMatchMutationOptions(jobId: string, request: RequestPreview) {
  return {
    mutationKey: ["candidate", "preview-match", jobId],
    retry: false as const,
    mutationFn: async (cvId: string) => {
      if (typeof cvId !== "string" || !cvId.trim()) throw new Error("Vui lòng chọn CV cần phân tích.");
      const result = await request(jobId, cvId);
      if (result.cvId.toLowerCase() !== cvId.toLowerCase() || result.jobId.toLowerCase() !== jobId.toLowerCase()) {
        throw new Error("Kết quả không thuộc CV hoặc việc làm đang phân tích. Vui lòng thử lại.");
      }
      return result;
    },
  };
}
