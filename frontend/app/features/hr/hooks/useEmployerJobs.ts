import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useUIStore } from "~/stores/useUIStore";
import { hrQueryKeys } from "../queries/hrQueryKeys";
import { hrService } from "../services/hrService";
import type { EmployerJobFilters, JobRequest } from "../types";

export function useEmployerJobs(filters: EmployerJobFilters) {
  return useQuery({
    queryKey: hrQueryKeys.jobs.list(filters),
    queryFn: ({ signal }) => hrService.getJobs(filters, signal),
    placeholderData: (previous) => previous,
  });
}

export function useEmployerJob(id: string | null) {
  return useQuery({
    queryKey: hrQueryKeys.jobs.detail(id ?? ""),
    queryFn: ({ signal }) => hrService.getJob(id!, signal),
    enabled: Boolean(id),
  });
}

export function useHrMasterData() {
  return useQuery({
    queryKey: hrQueryKeys.masterData(),
    queryFn: ({ signal }) => hrService.getMasterData(signal),
    staleTime: 60 * 60 * 1000,
  });
}

function useRefreshJobs() {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: hrQueryKeys.jobs.all() });
}

export function useCreateEmployerJob() {
  const refreshJobs = useRefreshJobs();
  const showToast = useUIStore((state) => state.showToast);
  return useMutation({
    mutationFn: (input: JobRequest) => hrService.createJob(input),
    onSuccess: async () => {
      showToast("Đã tạo tin tuyển dụng", "success");
      await refreshJobs();
    },
  });
}

export function useUpdateEmployerJob() {
  const queryClient = useQueryClient();
  const refreshJobs = useRefreshJobs();
  const showToast = useUIStore((state) => state.showToast);
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: JobRequest }) => hrService.updateJob(id, input),
    onSuccess: async (job) => {
      showToast("Đã cập nhật tin tuyển dụng", "success");
      await Promise.all([
        refreshJobs(),
        queryClient.invalidateQueries({ queryKey: hrQueryKeys.jobs.detail(job.id) }),
      ]);
    },
  });

}

export function useToggleEmployerJob() {
  const refreshJobs = useRefreshJobs();
  const showToast = useUIStore((state) => state.showToast);
  return useMutation({
    mutationFn: (id: string) => hrService.toggleJobStatus(id),
    onSuccess: async (isActive) => {
      showToast(isActive ? "Đã mở lại tin tuyển dụng" : "Đã đóng tin tuyển dụng", "success");
      await refreshJobs();
    },
  });
}

export function useDeleteEmployerJob() {
  const refreshJobs = useRefreshJobs();
  const showToast = useUIStore((state) => state.showToast);
  return useMutation({
    mutationFn: (id: string) => hrService.deleteJob(id),
    onSuccess: async () => {
      showToast("Đã xóa tin tuyển dụng", "success");
      await refreshJobs();
    },
  });
}
