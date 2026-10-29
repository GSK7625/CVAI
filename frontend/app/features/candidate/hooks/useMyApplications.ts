/**
 * @file useMyApplications.ts
 * @description Hook truy vấn danh sách hồ sơ việc làm đã ứng tuyển của ứng viên (FC-81b, P3-UC06).
 * @architecture Sử dụng TanStack Query với candidateQueryKeys.applications.list(filters), hỗ trợ keepPreviousData khi chuyển trang/tab.
 */

import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { applicationsService } from "../services/applicationsService";
import { candidateQueryKeys } from "../queries/candidateQueryKeys";
import { useAuthStore } from "~/stores/useAuthStore";
import type { ApplicationFilters } from "../types";

export function useMyApplications(filters: ApplicationFilters) {
  const user = useAuthStore((s) => s.user);

  return useQuery({
    queryKey: candidateQueryKeys.applications.list(filters),
    queryFn: ({ signal }) => applicationsService.list(filters, signal),
    enabled: !!user && user.role === "candidate",
    placeholderData: keepPreviousData,
    staleTime: 60 * 1000,
  });
}
