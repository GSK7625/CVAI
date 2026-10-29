import { useMutation } from "@tanstack/react-query";
import { authService } from "../services/authService";
import type { ForgotPasswordDto } from "../types";
import { useUIStore } from "~/stores/useUIStore";

export function useForgotPassword() {
  const showToast = useUIStore((s) => s.showToast);

  return useMutation({
    mutationFn: (dto: ForgotPasswordDto) => authService().forgotPassword(dto),
    onError: (error) => {
      showToast(error.message, "error");
    },
  });
}
