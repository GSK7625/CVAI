/**
 * @file useWithdrawApplication.ts
 * @description Hook rút đơn ứng tuyển việc làm (FC-81b, P3-UC07).
 * @architecture Gửi request PATCH /api/candidate/applications/{id}/withdraw, invalidate applications.all khi thành công.
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { applicationsService } from "../services/applicationsService";
import { candidateQueryKeys } from "../queries/candidateQueryKeys";
import { useUIStore } from "~/stores/useUIStore";

export function useWithdrawApplication() {
  const queryClient = useQueryClient();
  const showToast = useUIStore((s) => s.showToast);

  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) =>
      applicationsService.withdraw(id, reason),
    onSuccess: async () => {
      showToast("Đã rút đơn ứng tuyển thành công.", "success");
      await queryClient.invalidateQueries({
        queryKey: candidateQueryKeys.applications.all,
      });
    },
    onError: (err: Error) => {
      showToast(err.message || "Rút đơn ứng tuyển thất bại.", "error");
    },
  });
}
