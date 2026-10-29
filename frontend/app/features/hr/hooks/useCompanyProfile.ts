import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useUIStore } from "~/stores/useUIStore";
import { hrQueryKeys } from "../queries/hrQueryKeys";
import { hrService } from "../services/hrService";
import type { CompanyProfileInput } from "../types";

export function useCompanyProfile() {
  return useQuery({
    queryKey: hrQueryKeys.company(),
    queryFn: ({ signal }) => hrService.getCompany(signal),
  });
}

function useCompanyMutation(mode: "create" | "update") {
  const queryClient = useQueryClient();
  const showToast = useUIStore((state) => state.showToast);
  return useMutation({
    mutationFn: (input: CompanyProfileInput) =>
      mode === "create" ? hrService.createCompany(input) : hrService.updateCompany(input),
    onSuccess: async () => {
      showToast(mode === "create" ? "Đã tạo hồ sơ công ty" : "Đã cập nhật hồ sơ công ty", "success");
      await queryClient.invalidateQueries({ queryKey: hrQueryKeys.company() });
    },
  });
}

export function useCreateCompany() {
  return useCompanyMutation("create");
}

export function useUpdateCompany() {
  return useCompanyMutation("update");
}

export function useUploadCompanyLogo() {
  const queryClient = useQueryClient();
  const showToast = useUIStore((state) => state.showToast);
  return useMutation({
    mutationFn: (file: File) => hrService.uploadCompanyLogo(file),
    onSuccess: async () => {
      showToast("Đã cập nhật logo công ty", "success");
      await queryClient.invalidateQueries({ queryKey: hrQueryKeys.company() });
    },
  });
}
