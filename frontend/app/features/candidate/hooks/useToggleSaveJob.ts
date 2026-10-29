/**
 * @file useToggleSaveJob.ts
 * @description Hook thực hiện thao tác lưu / bỏ lưu một việc làm cho ứng viên (P3-UC04).
 * @architecture
 * - Nếu chưa đăng nhập (khách / vai trò khác): chặn mutation, hiển thị toast và điều hướng sang trang login kèm returnTo.
 * - Nếu là ứng viên hợp lệ: gọi mutation POST /api/candidate/jobs/{jobId}/save, invalidate savedJobs.all, và hiển thị thông báo.
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useLocation, useNavigate } from "react-router";
import { savedJobsService } from "../services/savedJobsService";
import { candidateQueryKeys } from "../queries/candidateQueryKeys";
import { useAuthStore } from "~/stores/useAuthStore";
import { useUIStore } from "~/stores/useUIStore";

/**
 * Hook mutation chuyển đổi trạng thái lưu / bỏ lưu công việc.
 * Cung cấp hàm `toggleSave(jobId, opts)` an toàn với khách vãng lai và tự động cập nhật cache query.
 */
export function useToggleSaveJob() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const location = useLocation();
  const user = useAuthStore((s) => s.user);
  const showToast = useUIStore((s) => s.showToast);

  const mutation = useMutation({
    mutationFn: (jobId: string) => savedJobsService.toggleSave(jobId),
    onSuccess: async (isSaved) => {
      showToast(
        isSaved ? "Đã lưu việc làm" : "Đã bỏ lưu việc làm",
        "success",
      );
      await queryClient.invalidateQueries({
        queryKey: candidateQueryKeys.savedJobs.all,
      });
    },
    onError: (error: unknown) => {
      const message =
        error instanceof Error ? error.message : "Không thể thực hiện thao tác. Vui lòng thử lại.";
      showToast(message, "error");
    },
  });

  /**
   * Kích hoạt lưu hoặc bỏ lưu công việc.
   * @param jobId ID của công việc cần thao tác
   * @param opts Tùy chọn callback bổ sung khi thành công (ví dụ: đóng modal)
   */
  const toggleSave = (
    jobId: string,
    opts?: { onSuccess?: (saved: boolean) => void },
  ) => {
    // Chặn người dùng chưa đăng nhập hoặc không phải ứng viên
    if (!user || user.role !== "candidate") {
      const returnTo = encodeURIComponent(`${location.pathname}${location.search}`);
      showToast("Vui lòng đăng nhập để lưu việc làm", "info");
      navigate(`/login?returnTo=${returnTo}`);
      return;
    }
    mutation.mutate(jobId, opts);
  };

  return {
    ...mutation,
    mutate: toggleSave,
    toggleSave,
  };
}
