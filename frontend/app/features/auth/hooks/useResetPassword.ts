import { useMutation } from "@tanstack/react-query";
import { authService } from "../services/authService";
import type { ResetPasswordDto } from "../types";
import { useUIStore } from "~/stores/useUIStore";

export function useResetPassword() {
  const showToast = useUIStore((s) => s.showToast);

  return useMutation({
    mutationFn: (dto: ResetPasswordDto) => authService().resetPassword(dto),
    onError: (error) => {
      showToast(error.message, "error");
    },
  });
}
