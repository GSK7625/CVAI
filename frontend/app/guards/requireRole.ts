import { redirect } from "react-router";
import { useAuthStore, type Role } from "~/stores/useAuthStore";
import { requireAuth } from "./requireAuth";

/** Guard role ngoài component: PHẢI gọi qua `.getState()` (không dùng hook). */
export function requireRole(roles: Role[], returnTo?: string): { user: NonNullable<ReturnType<typeof useAuthStore.getState>["user"]> } | never {
  const { user } = requireAuth(returnTo);
  if (!roles.includes(user.role)) {
    throw redirect(user.role === "employer" ? "/hr" : "/");
  }
  return { user };
}
