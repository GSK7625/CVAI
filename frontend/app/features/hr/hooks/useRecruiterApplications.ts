import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useUIStore } from "~/stores/useUIStore";
import { hrQueryKeys } from "../queries/hrQueryKeys";
import { hrService } from "../services/hrService";
import type {
  RecruiterApplicationFilters,
  UpdateApplicationStatusRequest,
} from "../types";

export function useRecruiterApplications(jobId: string, filters: RecruiterApplicationFilters) {
  return useQuery({
    queryKey: hrQueryKeys.applications.list(jobId, filters),
    queryFn: ({ signal }) => hrService.getJobApplications(jobId, filters, signal),
    enabled: Boolean(jobId),
    placeholderData: (previous) => previous,
  });
}

export function useRecruiterApplication(id: string | null) {
  return useQuery({
    queryKey: hrQueryKeys.applications.detail(id ?? ""),
    queryFn: ({ signal }) => hrService.getApplication(id!, signal),
    enabled: Boolean(id),
  });
}

export function useRecruitmentPipeline(jobId: string) {
  return useQuery({
    queryKey: hrQueryKeys.applications.pipeline(jobId),
    queryFn: ({ signal }) => hrService.getRecruitmentPipeline(jobId, signal),
    enabled: Boolean(jobId),
  });
}

function useRefreshApplications() {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: hrQueryKeys.applications.all() });
}

export function useUpdateApplicationStatus() {
  const refreshApplications = useRefreshApplications();
  const showToast = useUIStore((state) => state.showToast);
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: UpdateApplicationStatusRequest }) =>
      hrService.updateApplicationStatus(id, input),
    onSuccess: async () => {
      showToast("Đã cập nhật trạng thái ứng viên", "success");
      await refreshApplications();
    },
  });
}
