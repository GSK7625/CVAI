import { IconCircleCheck, IconCircleX, IconInfoCircle, IconX } from "@tabler/icons-react";
import { useUIStore, type ToastVariant } from "~/stores/useUIStore";
import { cn } from "~/lib/cn";

const icons: Record<ToastVariant, typeof IconInfoCircle> = {
  success: IconCircleCheck,
  error: IconCircleX,
  info: IconInfoCircle,
};

const styles: Record<ToastVariant, string> = {
  success: "border-success/30 text-success",
  error: "border-danger/30 text-danger",
  info: "border-navy/30 text-navy",
};

export function ToastViewport() {
  const toasts = useUIStore((s) => s.toasts);
  const dismissToast = useUIStore((s) => s.dismissToast);

  return (
    <div
      aria-live="polite"
      className="pointer-events-none fixed bottom-6 right-6 z-toast flex w-full max-w-sm flex-col gap-3"
    >
      {toasts.map((toast) => {
        const Icon = icons[toast.variant];
        return (
          <div
            key={toast.id}
            className={cn(
              "pointer-events-auto flex items-start gap-3 rounded-default border bg-surface px-4 py-3 shadow-overlay",
              styles[toast.variant],
            )}
          >
            <Icon size={20} stroke={1.6} className="mt-0.5 shrink-0" />
            <p className="flex-1 text-label font-medium text-ink">{toast.message}</p>
            <button
              type="button"
              aria-label="Đóng thông báo"
              className="text-ink-muted transition-colors hover:text-ink"
              onClick={() => dismissToast(toast.id)}
            >
              <IconX size={16} stroke={2} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
