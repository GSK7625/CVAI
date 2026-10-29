import { redirect } from "react-router";
import { useAuthStore } from "~/stores/useAuthStore";

/** Guard ngoài component: PHẢI gọi qua `.getState()` (không dùng hook). */
export function requireAuth(returnTo?: string): { user: NonNullable<ReturnType<typeof useAuthStore.getState>["user"]> } | never {
  const { user } = useAuthStore.getState();
  if (!user) {
    const to = returnTo ? `?returnTo=${encodeURIComponent(returnTo)}` : "";
    throw redirect(`/login${to}`);
  }
  return { user };
}
