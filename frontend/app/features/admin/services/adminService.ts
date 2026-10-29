import { fetcher } from "~/lib/fetcher";
import type {
  AdminUserResponse,
  AuditLogQueryFilter,
  AuditLogResponse,
  CompanyProfileResponse,
  CompanyQueryFilter,
  LockUserRequest,
  PagedResult,
  UpdateCompanyStatusRequest,
  UserQueryFilter,
  JobListResponse,
  AdminJobFilterRequest,
  ApproveJobRequest,
  AdminDashboardStatsResponse,
} from "../types";

function buildQueryString(params: object): string {
  const filtered = Object.entries(params as Record<string, unknown>).filter(
    ([_, value]) => value != null && value !== "",
  );
  if (filtered.length === 0) return "";
  const query = new URLSearchParams(
    filtered.map(([key, value]) => [key, String(value)]),
  ).toString();
  return `?${query}`;
}

export function adminService() {
  return {
    // User Management
    getUsers: (filter: UserQueryFilter) =>
      fetcher<PagedResult<AdminUserResponse>>(
        `/api/admin/users${buildQueryString(filter)}`,
        { method: "GET", auth: true },
      ),

    lockUser: (userId: string, request: LockUserRequest) =>
      fetcher<boolean>(`/api/admin/users/${userId}/lock`, {
        method: "POST",
        body: request,
        auth: true,
      }),

    unlockUser: (userId: string) =>
      fetcher<boolean>(`/api/admin/users/${userId}/unlock`, {
        method: "POST",
        auth: true,
      }),

    // Company Management
    getCompanies: (filter: CompanyQueryFilter) =>
      fetcher<PagedResult<CompanyProfileResponse>>(
        `/api/admin/companies${buildQueryString(filter)}`,
        { method: "GET", auth: true },
      ),

    updateCompanyStatus: (companyId: string, request: UpdateCompanyStatusRequest) =>
      fetcher<CompanyProfileResponse>(`/api/admin/companies/${companyId}/status`, {
        method: "PUT",
        body: request,
        auth: true,
      }),

    approveCompany: (companyId: string) =>
      fetcher<boolean>(`/api/admin/companies/${companyId}/approve`, {
        method: "POST",
        auth: true,
      }),

    rejectCompany: (companyId: string, reason: string) =>
      fetcher<boolean>(`/api/admin/companies/${companyId}/reject`, {
        method: "POST",
        body: { reason },
        auth: true,
      }),

    // Audit Logs
    getAuditLogs: (filter: AuditLogQueryFilter) =>
      fetcher<PagedResult<AuditLogResponse>>(
        `/api/admin/audit-logs${buildQueryString(filter)}`,
        { method: "GET", auth: true },
      ),

    // Job Management
    getJobs: (filter: AdminJobFilterRequest) =>
      fetcher<PagedResult<JobListResponse>>(
        `/api/admin/jobs${buildQueryString(filter)}`,
        { method: "GET", auth: true },
      ),

    moderateJob: (jobId: string, request: ApproveJobRequest) =>
      fetcher<boolean>(`/api/admin/jobs/${jobId}/approval`, {
        method: "PATCH",
        body: request,
        auth: true,
      }),

    // Dashboard Statistics
    getDashboardStats: () =>
      fetcher<AdminDashboardStatsResponse>("/api/admin/dashboard", {
        method: "GET",
        auth: true,
      }),
  };
}
