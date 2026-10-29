/**
 * @file useSavedJobIds.ts
 * @description Hook lấy tập hợp (Set) các ID việc làm đã lưu của ứng viên phục vụ hiển thị trạng thái nút tim.
 * @architecture Trả về Set<jobId> với O(1) lookup, cache 5 phút, chỉ kích hoạt khi đã đăng nhập vai trò candidate.
 */

import { useQuery } from "@tanstack/react-query";
import { savedJobsService } from "../services/savedJobsService";
import { candidateQueryKeys } from "../queries/candidateQueryKeys";
import { useAuthStore } from "~/stores/useAuthStore";

/**
 * Hook truy vấn và chuyển đổi danh sách việc làm đã lưu thành Set các jobId.
 * Giúp các component hiển thị thẻ công việc (JobCard, JobListItemRow) kiểm tra nhanh `has(jobId)` để fill màu tim đỏ.
 */
export function useSavedJobIds() {
  const user = useAuthStore((s) => s.user);

  return useQuery({
    queryKey: candidateQueryKeys.savedJobs.all,
    queryFn: async ({ signal }) => {
      const res = await savedJobsService.list(1, 200, signal);
      return new Set<string>(res.items.map((j) => j.jobId));
    },
    enabled: !!user && user.role === "candidate",
    staleTime: 5 * 60 * 1000,
  });
}
