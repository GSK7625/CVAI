import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export type Role = "candidate" | "employer" | "admin";

export interface AuthUser {
  id: string;
  email: string;
  fullName: string;
  role: Role;
}

export type User = AuthUser;


interface AuthState {
  user: AuthUser | null;
  accessToken: string | null;
  refreshToken: string | null;
  setSession: (session: {
    user: AuthUser;
    accessToken: string;
    refreshToken: string;
  }) => void;
  updateTokens: (tokens: { accessToken: string; refreshToken: string }) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      setSession: ({ user, accessToken, refreshToken }) =>
        set({ user, accessToken, refreshToken }),
      updateTokens: ({ accessToken, refreshToken }) => set({ accessToken, refreshToken }),
      logout: () => set({ user: null, accessToken: null, refreshToken: null }),
    }),
    {
      name: "futurecv-auth",
      storage: createJSONStorage(() => localStorage),
    },
  ),
);
