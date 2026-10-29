/**
 * @file useSavedJobs.ts
 * @description Hook truy vấn danh sách việc làm đã lưu có phân trang cho ứng viên.
 * @architecture Sử dụng TanStack Query với placeholderData giữ dữ liệu trang trước để tránh giật giao diện.
 */

import { useQuery } from "@tanstack/react-query";
import { savedJobsService } from "../services/savedJobsService";
import { candidateQueryKeys } from "../queries/candidateQueryKeys";

/**
 * Hook lấy danh sách các việc làm mà ứng viên hiện tại đã lưu.
 * @param page Trang hiện tại (1-based index, mặc định: 1)
 * @param pageSize Kích thước trang (mặc định: 10)
 */
export function useSavedJobs(page = 1, pageSize = 10) {
  return useQuery({
    queryKey: candidateQueryKeys.savedJobs.list(page),
    queryFn: ({ signal }) => savedJobsService.list(page, pageSize, signal),
    placeholderData: (prev) => prev,
  });
}
