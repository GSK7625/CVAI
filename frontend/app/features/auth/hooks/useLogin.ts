import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useLocation, useNavigate } from "react-router";
import { authService } from "../services/authService";
import { useAuthStore, type Role } from "~/stores/useAuthStore";
import { useUIStore } from "~/stores/useUIStore";
import type { AuthResponseDto } from "../types";
import { getDefaultDashboard, getSafeReturnUrl } from "../constants";

export function normalizeRole(role?: string): Role {
  const r = (role ?? "").trim().toLowerCase();
  if (r.includes("employer") || r.includes("hr")) return "employer";
  if (r.includes("admin")) return "admin";
  return "candidate";
}

function applySession(result: AuthResponseDto, inputEmail?: string): Role {
  const userObj = result.user;
  const role = normalizeRole(result.role);
  useAuthStore.getState().setSession({
    user: {
      id: result.id ?? userObj?.id ?? "",
      email: result.email ?? userObj?.email ?? inputEmail ?? "",
      fullName: result.fullName ?? userObj?.fullName ?? "",
      role,
    },
    accessToken: result.accessToken,
    refreshToken: result.refreshToken,
  });
  return role;
}

export function useLogin() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const location = useLocation();
  const showToast = useUIStore((s) => s.showToast);

  return useMutation({
    mutationFn: (input: { email: string; password: string }) =>
      authService().login(input),
    onSuccess: (result, variables) => {
      // Xóa toàn bộ cache query cũ trước khi áp dụng session mới
      queryClient.removeQueries({ type: "all" });
      const role = applySession(result, variables.email);
      showToast("Đăng nhập thành công", "success");
      // Single owner: Nguồn duy nhất quyết định đích đến sau login.
      // Ưu tiên returnTo (đã validate internal path), fallback theo role mặc định.
      const returnTo = new URLSearchParams(location.search).get("returnTo");
      const safeReturn = getSafeReturnUrl(returnTo);
      const targetUrl = safeReturn ?? getDefaultDashboard(role);
      navigate(targetUrl, { replace: true });
    },
  });
}
