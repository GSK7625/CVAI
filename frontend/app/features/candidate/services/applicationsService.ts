/**
 * @file applicationsService.ts
 * @description Candidate Applications Service: Giao tiếp API quản lý hồ sơ ứng tuyển của ứng viên (FC-81b, P3-UC06, P3-UC07).
 * @architecture
 * - Gọi trực tiếp backend API qua fetcher (auth: true), KHÔNG mock dữ liệu cá nhân.
 * - Chuẩn hóa tiền lương VND sang triệu đồng để đồng bộ hiển thị với JobCard và JobList.
 */

import { fetcher } from "~/lib/fetcher";
import type {
  ApiApplicationDetail,
  ApiApplicationListItem,
  ApiPaged,
  ApplicationFilters,
  ApplicationListItem,
  ApplicationListResult,
} from "../types";

const toMillions = (vnd: number) => Math.round((vnd / 1_000_000) * 10) / 10;

/**
 * Ánh xạ DTO từ backend sang model giao diện ApplicationListItem
 */
function mapApplicationListItem(item: ApiApplicationListItem): ApplicationListItem {
  return {
    id: item.id,
    jobId: item.jobId,
    jobTitle: item.jobTitle,
    companyId: item.companyId,
    companyName: item.companyName,
    companyLogo: item.companyLogoUrl ?? undefined,
    location: item.locationName ?? "Toàn quốc",
    salaryMin: item.salaryMin != null ? toMillions(item.salaryMin) : null,
    salaryMax: item.salaryMax != null ? toMillions(item.salaryMax) : null,
    status: item.status,
    matchScore: item.matchScore,
    appliedAt: item.appliedAt,
    updatedAt: item.updatedAt,
  };
}

export const applicationsService = {
  /**
   * Lấy danh sách hồ sơ ứng tuyển của ứng viên hiện tại với bộ lọc trạng thái và phân trang.
   */
  async list(filters: ApplicationFilters, signal?: AbortSignal): Promise<ApplicationListResult> {
    const params = new URLSearchParams();
    if (filters.status?.trim()) {
      params.set("status", filters.status.trim());
    }
    params.set("pageIndex", String(filters.page ?? 1));
    params.set("pageSize", String(filters.pageSize ?? 10));

    const res = await fetcher<ApiPaged<ApiApplicationListItem>>(
      `/api/candidate/applications?${params.toString()}`,
      {
        method: "GET",
        auth: true,
        signal,
      },
    );

    return {
      items: res.items.map(mapApplicationListItem),
      total: res.totalCount,
      page: res.pageIndex,
      pageSize: res.pageSize,
      totalPages: res.totalPages,
      hasPreviousPage: res.hasPreviousPage,
      hasNextPage: res.hasNextPage,
    };
  },

  /**
   * Xem chi tiết một hồ sơ ứng tuyển kèm lịch sử xử lý (timeline) và giải thích match score.
   */
  async detail(id: string, signal?: AbortSignal): Promise<ApiApplicationDetail> {
    return fetcher<ApiApplicationDetail>(`/api/candidate/applications/${id}`, {
      method: "GET",
      auth: true,
      signal,
    });
  },

  /**
   * Rút đơn ứng tuyển (chỉ khả dụng khi trạng thái là Applied hoặc Screening).
   */
  async withdraw(id: string, reason?: string): Promise<boolean> {
    return fetcher<boolean>(`/api/candidate/applications/${id}/withdraw`, {
      method: "PATCH",
      auth: true,
      body: { reason: reason?.trim() || null },
    });
  },
};
