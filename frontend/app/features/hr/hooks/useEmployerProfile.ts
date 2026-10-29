import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useUIStore } from "~/stores/useUIStore";
import { hrQueryKeys } from "../queries/hrQueryKeys";
import { hrService } from "../services/hrService";
import type { EmployerProfileInput } from "../types";

export function useEmployerProfile() {
  return useQuery({
    queryKey: hrQueryKeys.profile(),
    queryFn: ({ signal }) => hrService.getProfile(signal),
  });
}

export function useUpdateEmployerProfile() {
  const queryClient = useQueryClient();
  const showToast = useUIStore((state) => state.showToast);
  return useMutation({
    mutationFn: (input: EmployerProfileInput) => hrService.updateProfile(input),
    onSuccess: async () => {
      showToast("Đã cập nhật hồ sơ nhà tuyển dụng", "success");
      await queryClient.invalidateQueries({ queryKey: hrQueryKeys.profile() });
    },
  });
}

export function useUploadEmployerAvatar() {
  const queryClient = useQueryClient();
  const showToast = useUIStore((state) => state.showToast);
  return useMutation({
    mutationFn: (file: File) => hrService.uploadAvatar(file),
    onSuccess: async () => {
      showToast("Đã cập nhật ảnh đại diện", "success");
      await queryClient.invalidateQueries({ queryKey: hrQueryKeys.profile() });
    },
  });
}
