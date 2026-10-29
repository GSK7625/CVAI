/**
 * @file usePreviewJobMatch.ts
 * @description Hook truy vấn điểm khớp (match preview) AI giữa công việc và CV của ứng viên (FC-81a).
 * @architecture Gọi POST /api/candidate/jobs/{jobId}/preview-match, tự động refetch khi thay đổi cvId được chọn.
 */

import { useQuery } from "@tanstack/react-query";
import { jobService } from "../services/jobService";
import { candidateQueryKeys } from "../queries/candidateQueryKeys";
import { useAuthStore } from "~/stores/useAuthStore";

/**
 * Hook xem trước độ phù hợp của hồ sơ với vị trí tuyển dụng.
 * @param jobId ID của công việc đang ứng tuyển
 * @param cvId ID của CV ứng viên chọn (tùy chọn; nếu không truyền backend sẽ dùng CV chính/mới nhất)
 */
export function usePreviewJobMatch(jobId: string, cvId?: string, enabled = true) {
  const user = useAuthStore((s) => s.user);

  return useQuery({
    queryKey: candidateQueryKeys.previewMatch(jobId, cvId),
    queryFn: ({ signal }) => jobService().previewMatch(jobId, cvId, signal),
    enabled: enabled && !!user && user.role === "candidate" && !!jobId,
    staleTime: 60 * 1000,
    retry: 1,
  });
}
