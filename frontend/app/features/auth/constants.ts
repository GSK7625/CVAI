import type { Role } from "~/stores/useAuthStore";

/**
 * Danh sách tất cả các route đăng nhập trong hệ thống.
 * Cho phép người dùng đã đăng nhập ở vai trò này truy cập để chuyển đổi sang tài khoản khác.
 */
export const LOGIN_ROUTES = [
  "/login",
  "/login-employer",
  "/login-admin",
] as const;

export type LoginRoute = (typeof LOGIN_ROUTES)[number];

/**
 * Kiểm tra xem pathname có thuộc các route đăng nhập hay không.
 * Tự động chuẩn hóa trailing slash (ví dụ: "/login/" -> "/login").
 */
export function isLoginRoute(pathname: string): boolean {
  const normalized = pathname.replace(/\/+$/, "") || "/";
  return (LOGIN_ROUTES as readonly string[]).includes(normalized);
}

/**
 * Lấy URL trang chủ mặc định theo từng vai trò sau khi đăng nhập thành công
 * hoặc khi truy cập các route auth khác (/register, /forgot-password).
 */
export function getDefaultDashboard(role: Role): string {
  switch (role) {
    case "employer":
      return "/hr";
    case "admin":
      return "/admin";
    case "candidate":
    default:
      return "/";
  }
}

/**
 * Xác thực và trả về returnTo an toàn (chỉ chấp nhận internal path),
 * ngăn chặn lỗ hổng Open Redirect.
 */
export function getSafeReturnUrl(rawUrl?: string | null): string | null {
  if (!rawUrl || typeof rawUrl !== "string") return null;
  const trimmed = rawUrl.trim();
  // Chỉ chấp nhận internal path: bắt đầu bằng 1 dấu '/' và không bắt đầu bằng '//' hoặc '/\'
  if (trimmed.startsWith("/") && !trimmed.startsWith("//") && !trimmed.startsWith("/\\")) {
    return trimmed;
  }
  return null;
}
