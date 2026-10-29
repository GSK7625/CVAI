import { create } from "zustand";

export type ToastVariant = "success" | "error" | "info";

export interface ToastItem {
  id: number;
  message: string;
  variant: ToastVariant;
}

interface UIState {
  toasts: ToastItem[];
  showToast: (message: string, variant?: ToastVariant) => void;
  dismissToast: (id: number) => void;
}

let nextToastId = 1;

export const useUIStore = create<UIState>((set) => ({
  toasts: [],
  showToast: (message, variant = "info") => {
    const id = nextToastId++;
    set((state) => ({ toasts: [...state.toasts, { id, message, variant }] }));
    if (typeof window !== "undefined") {
      window.setTimeout(() => {
        set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) }));
      }, 5000);
    }
  },
  dismissToast: (id) =>
    set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
}));
