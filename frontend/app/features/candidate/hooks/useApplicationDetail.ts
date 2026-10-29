/**
 * @file useApplicationDetail.ts
 * @description Hook truy vấn thông tin chi tiết một hồ sơ ứng tuyển (FC-81b, P3-UC06).
 * @architecture Gọi GET /api/candidate/applications/{id} trả về dữ liệu timeline và độ phù hợp AI.
 */

import { useQuery } from "@tanstack/react-query";
import { applicationsService } from "../services/applicationsService";
import { candidateQueryKeys } from "../queries/candidateQueryKeys";
import { useAuthStore } from "~/stores/useAuthStore";

export function useApplicationDetail(id?: string) {
  const user = useAuthStore((s) => s.user);

  return useQuery({
    queryKey: candidateQueryKeys.applications.detail(id ?? ""),
    queryFn: ({ signal }) => {
      if (!id) throw new Error("Mã đơn ứng tuyển không được để trống.");
      return applicationsService.detail(id, signal);
    },
    enabled: Boolean(id) && !!user && user.role === "candidate",
    staleTime: 60 * 1000,
  });
}
