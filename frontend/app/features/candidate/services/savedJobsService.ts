/**
 * @file savedJobsService.ts
 * @description Candidate Saved Jobs Service: Giao tiếp API việc làm đã lưu của ứng viên (P3-UC04).
 * @architecture Gọi API thật qua fetcher (auth: true), dữ liệu người dùng cá nhân (KHÔNG dùng mock).
 */

import { fetcher } from "~/lib/fetcher";
import type {
  ApiPaged,
  ApiSavedJob,
  SavedJob,
  SavedJobsResult,
} from "../types";

/**
 * Quy đổi mức lương VND về đơn vị Triệu để tái sử dụng formatSalary trên UI.
 * @param vnd Số tiền VND (ví dụ: 15000000 -> 15)
 * @returns Mức lương đơn vị Triệu hoặc null
 */
const toMillions = (vnd: number | null | undefined): number | null => {
  if (vnd == null) return null;
  return Math.round((vnd / 1_000_000) * 10) / 10;
};

/**
 * Chuyển đổi định dạng ISO string sang định dạng ngày dd/MM/yyyy.
 * @param iso Chuỗi ngày tháng chuẩn ISO từ backend
 * @returns Chuỗi ngày dd/MM/yyyy hoặc undefined
 */
const formatDeadline = (iso?: string | null): string | undefined => {
  if (!iso) return undefined;
  const d = new Date(iso);
  if (isNaN(d.getTime())) return undefined;
  const day = String(d.getDate()).padStart(2, "0");
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const year = d.getFullYear();
  return `${day}/${month}/${year}`;
};

/**
 * Ánh xạ DTO ApiSavedJob từ backend sang SavedJob hiển thị trên giao diện người dùng.
 * @param api DTO việc làm đã lưu trả về từ API
 * @returns Model việc làm đã lưu cho UI
 */
export function mapApiSavedJob(api: ApiSavedJob): SavedJob {
  return {
    jobId: api.jobId,
    title: api.title,
    company: api.companyName,
    companyLogo: api.companyLogoUrl ?? undefined,
    location: api.locationName ?? "Toàn quốc",
    salaryMin: toMillions(api.salaryMin),
    salaryMax: toMillions(api.salaryMax),
    deadline: formatDeadline(api.deadline),
    isActive: api.isActive,
    isExpired: api.isExpired,
    savedAt: api.savedAt,
  };
}

/**
 * Service quản lý các thao tác API liên quan đến việc làm đã lưu của ứng viên.
 */
export const savedJobsService = {
  /**
   * Lấy danh sách việc làm đã lưu có phân trang.
   * @param page Số thứ tự trang (mặc định: 1)
   * @param pageSize Số lượng mục trên mỗi trang (mặc định: 10)
   * @param signal AbortSignal để hủy request khi component unmount
   */
  async list(page = 1, pageSize = 10, signal?: AbortSignal): Promise<SavedJobsResult> {
    const res = await fetcher<ApiPaged<ApiSavedJob>>(
      `/api/candidate/saved-jobs?pageIndex=${page}&pageSize=${pageSize}`,
      {
        method: "GET",
        auth: true,
        signal,
      },
    );

    return {
      items: res.items.map(mapApiSavedJob),
      total: res.totalCount,
      page: res.pageIndex,
      pageSize: res.pageSize,
      totalPages: res.totalPages,
      hasPreviousPage: res.hasPreviousPage,
      hasNextPage: res.hasNextPage,
    };
  },

  /**
   * Chuyển đổi trạng thái lưu / bỏ lưu một việc làm.
   * @param jobId Mã định danh công việc
   * @returns true nếu chuyển sang ĐÃ LƯU, false nếu chuyển sang ĐÃ BỎ LƯU
   */
  async toggleSave(jobId: string): Promise<boolean> {
    return fetcher<boolean>(`/api/candidate/jobs/${jobId}/save`, {
      method: "POST",
      auth: true,
    });
  },

  /**
   * Hủy lưu một việc làm (gọi toggleSave).
   * @param jobId Mã định danh công việc cần bỏ lưu
   */
  async unsave(jobId: string): Promise<boolean> {
    return this.toggleSave(jobId);
  },
};
